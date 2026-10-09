"""Separate numeric comparison, cached extraction, and explicit serial output.

These are behavioral controls, not probes of a natural direct-decision trajectory.
All model-facing values come from the public table or a recorded model response.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from evidence_lab.cli import thinking_value
from evidence_lab.data import case_from_dict
from evidence_lab.models import parse_choice
from evidence_lab.storage import canonical, digest, read_json, read_jsonl, verify, write_json
from evidence_lab.tasks import score_choice
from evidence_lab.workflows import new_run
from evidence_lab_v2.diagnostics import (
    _unique_object,
    build_requests,
    choose_from_values,
    code_sources,
    endpoint,
    parse_values,
    score_readout,
    select_cases,
)
from evidence_lab_v2.presentations import position_audit, present_order

VARIANTS = ("canonical", "shuffled")
KINDS = ("public_compare", "cached_compare", "joint")
VERSION = "behavior-controls-v3"


def comparison_prompt(values, objective):
    if objective not in {"conditional_max", "conditional_min"}:
        raise ValueError("Unsupported comparison")
    direction = "highest" if objective == "conditional_max" else "lowest"
    # Alphabetical alias order; never sort on the values or the correct answer.
    return (
        "The following numeric recorded yields refer to one substrate. "
        "Use only these numbers.\n"
        + json.dumps({"values": dict(sorted(values.items()))}, separators=(",", ":"))
        + f"\nSelect the option alias with the {direction} recorded yield. "
        "If values are exactly tied, choose any tied optimum.\n"
        'Return only a JSON object of the form {"choice":"A"}.\n'
    )


def public_values(case, presentation):
    aliases = dict(presentation.aliases)
    return {
        aliases[r.option]: r.value for r in case.table.records if r.context == case.target_context
    }


def joint_prompt(case, presentation):
    direction = "highest" if case.objective == "conditional_max" else "lowest"
    aliases = sorted(alias for _, alias in presentation.aliases)
    skeleton = {"values": {alias: None for alias in aliases}, "choice": None}
    return (
        presentation.prefix
        + f"\nFor substrate {case.target_context}, first copy the recorded yield for each "
        "option alias, then select the option with the "
        + direction
        + " recorded yield. If values are exactly tied, choose any tied optimum.\n"
        "Return exactly one JSON object with keys values then choice, in that order. "
        "Inside values include every option alias once, with a numeric yield and at least "
        "four decimal places. After values, set choice to the selected alias string. "
        "No prose or Markdown. Replace every null in this structure; null is not an answer: "
        + json.dumps(skeleton, separators=(",", ":"))
    )


def parse_joint(text, keys):
    try:
        payload = json.loads(text, object_pairs_hook=_unique_object)
        if not isinstance(payload, dict) or list(payload) != ["values", "choice"]:
            return None, None, "wrong_schema_or_emission_order"
        values, error = parse_values(json.dumps({"values": payload["values"]}), keys)
        choice = payload["choice"]
        if not isinstance(choice, str) or choice not in keys:
            return values, None, error or "invalid_choice"
        return values, choice, error
    except (ValueError, TypeError, OverflowError):
        return None, None, "invalid_json_or_duplicate_key"


def cache_key(case, variant):
    # V2 queried values only for max tasks. Its relation prompt is direction-free,
    # so the identical recorded readout is usable as input to either comparison.
    return case.table.table_id, case.target_context, variant


def load_cache(dataset, cache_dir):
    verify(dataset)
    specification = read_json(cache_dir / "specification.json")
    summary = read_json(cache_dir / "summary.json")
    if summary.get("status") != "complete" or specification.get("mode") != "diagnose":
        raise ValueError("Use completed V2 readouts, not an order run or partial run")
    if specification["dataset_freeze_sha256"] != digest(dataset / "freeze.json"):
        raise ValueError("Cache and dataset freeze differ")
    if (cache_dir / "failure.json").exists():
        raise ValueError("Cache contains a failure marker")
    cases = {c.case_id: c for c in map(case_from_dict, read_jsonl(dataset / "cases.jsonl"))}
    result = {}
    responses = read_jsonl(cache_dir / "responses.jsonl")
    if len(responses) != specification["requests"]:
        raise ValueError("Incomplete V2 response log")
    identities = [(r["case_id"], r["variant"], r["order_seed"], r["kind"]) for r in responses]
    expected_ids = {
        (cid, cond["variant"], cond["order_seed"], kind)
        for cid in specification["case_ids"]
        for cond in specification["conditions"]
        for kind in ("value", "relation", "decision")
    }
    if len(set(identities)) != len(identities) or set(identities) != expected_ids:
        raise ValueError("Duplicate, missing or unexpected cache responses")
    for row in responses:
        if row["kind"] != "relation" or row["variant"] not in VARIANTS:
            continue
        case = cases[row["case_id"]]
        if case.split != "validation" or row["order_seed"] != 0:
            raise ValueError("Cache must use validation, order seed 0")
        presentation = present_order(case, row["variant"], 0)
        prompts, expected = build_requests(case, presentation)
        if row["prompt"] != prompts["relation"]:
            raise ValueError("Cached relation prompt differs from the frozen public prompt")
        score, values = score_readout(row["response"], expected["relation"])
        if score != row["score"]:
            raise ValueError("Cached readout score differs from recomputation")
        key = cache_key(case, row["variant"])
        if key in result:
            raise ValueError("Duplicate table/target/variant cache record")
        result[key] = {
            "values": values,
            "score": score,
            "source_case_id": case.case_id,
            "response": row["response"],
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
        }
    return result


def requests_for(case, cache):
    original = present_order(case)
    values = public_values(case, original)
    yield "public_compare", "canonical", comparison_prompt(values, case.objective), values
    for variant in VARIANTS:
        presentation = present_order(case, variant)
        cached = cache[cache_key(case, variant)]["values"]
        prompt = comparison_prompt(cached, case.objective) if cached is not None else None
        yield "cached_compare", variant, prompt, cached
        yield "joint", variant, joint_prompt(case, presentation), None


def v3_sources():
    paths = code_sources()
    package = Path(__file__).resolve().parent
    root = package.parents[1]
    paths["run_v3.py"] = root / "run_v3.py"
    paths.update({str(p.relative_to(root)).replace("\\", "/"): p for p in package.glob("*.py")})
    return paths


def make_plan(dataset, cache_dir, cases, cache, model, adapter):
    metadata = read_json(cache_dir / "model.json")
    if Path(metadata["model_path"]).resolve() != model.resolve():
        raise ValueError("Model path differs from V2 readout source")
    expected_adapter = str(adapter.resolve()) if adapter else None
    if metadata.get("adapter_path") != expected_adapter:
        raise ValueError("Base/uniform model and cached readouts are mismatched")
    # Catch incomplete migration before loading the model.
    for name in metadata["model_files_sha256"]:
        if not (model / name).is_file():
            raise FileNotFoundError(model / name)
    planned = Counter()
    skipped = Counter()
    for case in cases:
        for kind, _, prompt, _ in requests_for(case, cache):
            (planned if prompt is not None else skipped)[kind] += 1
    return {
        "schema": VERSION,
        "split": "validation",
        "cases": len(cases),
        "groups": len({c.table.group_id for c in cases}),
        "tables": len({c.table.table_id for c in cases}),
        "objectives": dict(Counter(c.objective for c in cases)),
        "case_ids": [c.case_id for c in cases],
        "requests": sum(planned.values()),
        "requests_by_kind": dict(planned),
        "skipped_upstream_invalid": dict(skipped),
        "dataset": str(dataset.resolve()),
        "dataset_freeze_sha256": digest(dataset / "freeze.json"),
        "cache_directory": str(cache_dir.resolve()),
        "cache_files_sha256": {
            p.name: digest(p)
            for p in [
                cache_dir / name
                for name in ["specification.json", "model.json", "responses.jsonl", "summary.json"]
            ]
        },
        "model_path": str(model.resolve()),
        "adapter_path": expected_adapter,
        "variants": list(VARIANTS),
        "order_seed": 0,
        "limitations": [
            "Development only: one source, four groups, existing validation split.",
            "Public filtering gives the correct scope; it is a component control, not autonomous extraction.",
            "Cached comparison is a two-request workflow; include the earlier extraction tokens/call.",
            "Joint output changes the task and compute; success does not show evidence was used in the earlier direct trajectory.",
            "Same readout reused for min and max: the two tasks are paired, not independent samples.",
            "No internal mechanism, new training method, or independent confirmation is established.",
        ],
    }


def run(dataset, cache_dir, out, backend, cases, cache, specification):
    if out.exists():
        raise FileExistsError("Choose a new output directory")
    verify(dataset)
    sources = v3_sources()
    hashes = {name: digest(path) for name, path in sources.items()}
    old_metadata = read_json(cache_dir / "model.json")
    for field in ["model_files_sha256", "adapter_files_sha256"]:
        if backend.metadata.get(field) != old_metadata.get(field):
            raise ValueError("Loaded model/checkpoint differs from cached readout source")
    for field in ["thinking_mode", "chat_template", "decoding", "dtype", "attention"]:
        if backend.metadata.get(field) != old_metadata.get(field):
            raise ValueError("Generation mode differs from cache: " + field)
    new_run(out, backend)
    for name, path in sources.items():
        target = out / "code_snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    write_json(
        out / "specification.json",
        {
            **specification,
            "code_files_sha256": hashes,
            "started_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    aggregate, groups, costs = defaultdict(list), defaultdict(list), defaultdict(Counter)
    n_requests, n_attempts = 0, 0
    started = perf_counter()
    try:
        with (
            (out / "responses.jsonl").open("x", encoding="utf-8") as raw,
            (out / "scores.jsonl").open("x", encoding="utf-8") as scored,
        ):
            for i, case in enumerate(cases, 1):
                for kind, variant, prompt, supplied_values in requests_for(case, cache):
                    presentation = present_order(case, variant)
                    identity = {
                        "case_id": case.case_id,
                        "table_id": case.table.table_id,
                        "group_id": case.table.group_id,
                        "objective": case.objective,
                        "variant": variant,
                        "order_seed": 0,
                        "kind": kind,
                    }
                    completion, elapsed = None, 0.0
                    if prompt is not None:
                        begin = perf_counter()
                        completion = backend.complete(prompt)
                        elapsed = perf_counter() - begin
                        n_requests += 1
                    text = completion.text if completion else None
                    values, error = None, None
                    if kind == "joint":
                        values, choice, error = parse_joint(text, public_values(case, presentation))
                    else:
                        choice = parse_choice(text) if text is not None else None
                    scores = {"decision": score_choice(case, choice, presentation)}
                    if kind == "joint":
                        expected = public_values(case, presentation)
                        scores["values"] = score_readout(json.dumps({"values": values}), expected)[
                            0
                        ]
                        scores["program_decision"] = score_choice(
                            case, choose_from_values(values, case.objective), presentation
                        )
                    # Arithmetic self-consistency also accepts all co-optimal aliases.
                    compare_values = values if kind == "joint" else supplied_values
                    consistent = None
                    if compare_values is not None and choice in compare_values:
                        optimum = (max if case.objective == "conditional_max" else min)(
                            compare_values.values()
                        )
                        consistent = abs(compare_values[choice] - optimum) <= 1e-9
                    label = f"{case.objective}/{variant}/{kind}"
                    cost = costs[label]
                    cost["attempts"] += 1
                    cost["new_calls"] += int(completion is not None)
                    cost["new_input_tokens"] += completion.input_tokens if completion else 0
                    cost["new_output_tokens"] += completion.output_tokens if completion else 0
                    upstream = cache[cache_key(case, variant)] if kind == "cached_compare" else None
                    if upstream:
                        cost["upstream_calls_per_standalone_workflow"] += 1
                        cost["upstream_input_tokens_per_standalone_workflow"] += upstream[
                            "input_tokens"
                        ]
                        cost["upstream_output_tokens_per_standalone_workflow"] += upstream[
                            "output_tokens"
                        ]
                    record = {
                        **identity,
                        "executed": completion is not None,
                        "prompt": prompt,
                        "response": text,
                        "input_tokens": completion.input_tokens if completion else 0,
                        "output_tokens": completion.output_tokens if completion else 0,
                        "elapsed_seconds": elapsed,
                        "parse_error": error,
                        "upstream_case_id": upstream["source_case_id"] if upstream else None,
                        "upstream_response": upstream["response"] if upstream else None,
                        "scores": scores,
                        "choice_consistent_with_supplied_or_emitted_values": consistent,
                    }
                    raw.write(canonical(record) + "\n")
                    raw.flush()
                    scored.write(
                        canonical(
                            {
                                **identity,
                                **position_audit(case, presentation),
                                "scores": scores,
                                "choice_consistent_with_supplied_or_emitted_values": consistent,
                            }
                        )
                        + "\n"
                    )
                    scored.flush()
                    n_attempts += 1
                    for endpoint_name, score in scores.items():
                        aggregate[f"{label}/{endpoint_name}"].append(score)
                        groups[f"{label}/{endpoint_name}/{case.table.group_id}"].append(score)
                print(f"Completed {i}/{len(cases)} cases; {n_requests} new requests", flush=True)
        verify(dataset)
        if digest(dataset / "freeze.json") != specification["dataset_freeze_sha256"]:
            raise ValueError("Dataset changed during run")
        for name, sha in specification["cache_files_sha256"].items():
            if digest(cache_dir / name) != sha:
                raise ValueError("Cache changed during run")
        if hashes != {name: digest(path) for name, path in sources.items()}:
            raise ValueError("Code changed during run")
        if n_requests != specification["requests"]:
            raise ValueError("Request count differs from plan")
        result = {
            "schema": VERSION,
            "status": "complete",
            "cases": len(cases),
            "requests": n_requests,
            "attempts": n_attempts,
            "endpoints": {k: endpoint(v) for k, v in sorted(aggregate.items())},
            "by_group": {k: endpoint(v) for k, v in sorted(groups.items())},
            "costs": dict(costs),
            "elapsed_seconds_excluding_model_load": perf_counter() - started,
            "limitations": specification["limitations"],
            "scientific_conclusion": None,
            "finished_utc": datetime.now(timezone.utc).isoformat(),
        }
        write_json(out / "summary.json", result)
        return result
    except BaseException as exc:
        write_json(
            out / "failure.json",
            {
                "status": "incomplete",
                "exception": type(exc).__name__,
                "message": str(exc),
                "completed_requests": n_requests,
                "completed_attempts": n_attempts,
            },
        )
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["dataset", "readouts", "model", "out"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    parser.add_argument("--thinking-mode", choices=["off"], default="off")
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument(
        "--objectives",
        nargs="+",
        choices=["conditional_max", "conditional_min"],
        default=["conditional_max", "conditional_min"],
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.out.exists():
            raise FileExistsError("Output exists; choose a new path")
        if args.max_length <= 0 or args.max_new_tokens <= 0:
            raise ValueError("Token limits must be positive")
        cache = load_cache(args.dataset, args.readouts)
        cases = select_cases(args.dataset, args.objectives, args.limit)
        plan = make_plan(args.dataset, args.readouts, cases, cache, args.model, args.adapter)
        plan["generation_settings"] = {
            "device": args.device,
            "thinking_mode": args.thinking_mode,
            "max_length": args.max_length,
            "max_new_tokens": args.max_new_tokens,
        }
        print(canonical({k: v for k, v in plan.items() if k != "case_ids"}), flush=True)
        if args.dry_run:
            return 0
        from evidence_lab.models import HuggingFaceModel

        backend = HuggingFaceModel(
            args.model,
            device=args.device,
            adapter_path=args.adapter,
            max_length=args.max_length,
            max_new_tokens=args.max_new_tokens,
            use_chat_template=True,
            enable_thinking=thinking_value(args.thinking_mode),
        )
        summary = run(args.dataset, args.readouts, args.out, backend, cases, cache, plan)
        print(json.dumps({k: v for k, v in summary.items() if k != "by_group"}, indent=2))
        return 0
    except (ValueError, KeyError, FileNotFoundError, FileExistsError, ImportError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
