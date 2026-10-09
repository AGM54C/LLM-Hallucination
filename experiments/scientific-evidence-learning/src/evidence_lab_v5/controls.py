"""Compare the EXACT V4 emitted values, with/without the original table prefix."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from evidence_lab.storage import (
    canonical,
    digest,
    read_json,
    read_jsonl,
    stable_id,
    verify,
    write_json,
)
from evidence_lab.tasks import score_choice
from evidence_lab.workflows import new_run
from evidence_lab_v2.diagnostics import _unique_object
from evidence_lab_v4.factorial import optima, remap_presentation, select_paired_cases
from evidence_lab_v4.runner import assert_model, text_digest
from evidence_lab_v4.runner import sources as v4_sources
from evidence_lab_v4.runner import verify_run as verify_v4

from .reporting import LIMITATIONS, summarize, write_tables

VERSION = "fixed-readout-context-v5"
CONTEXTS = ("numbers_only", "table_and_numbers")
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "configs/controls_v5.json"
SOURCE_FILES = (
    "specification.json",
    "summary.json",
    "protocol.json",
    "model.json",
    "responses.jsonl",
)


def validate_protocol(protocol):
    if set(protocol) != {
        "schema",
        "contexts",
        "request_order_seed",
        "max_length",
        "max_new_tokens",
    }:
        raise ValueError("Unexpected V5 protocol fields")
    if protocol["schema"] != VERSION or protocol["contexts"] != list(CONTEXTS):
        raise ValueError("V5 requires both fixed context conditions")
    if type(protocol["request_order_seed"]) is not int or protocol["request_order_seed"] < 0:
        raise ValueError("Invalid request order seed")
    # Preserve the V4 generation settings; the actual choice completion is much shorter.
    if protocol["max_length"] != 8192 or protocol["max_new_tokens"] != 256:
        raise ValueError("Use the fixed V4 token budgets")
    return protocol


def literal_values(source_row):
    if not source_row["evaluation"]["scores"]["values"]["valid"]:
        return None
    response = source_row["response"]
    match = re.match(r'\s*\{\s*"values"\s*:\s*', response)
    if not match:
        raise ValueError("V4 source does not begin with a literal values object")
    payload, end = json.JSONDecoder(object_pairs_hook=_unique_object).raw_decode(
        response, match.end()
    )
    expected = source_row["evaluation"]["values"]
    if payload != expected or list(payload) != source_row["evaluation"]["actual_output_order"]:
        raise ValueError("Literal values differ from the verified V4 readout")
    # Slice the original bytes-as-text: no float reserialization, no sorting, no
    # rounding, and no substitution with measurement truth or previous choice.
    return response[match.end() : end]


def comparison_prompt(case, source_row, context):
    if context not in CONTEXTS:
        raise ValueError("Unsupported context condition")
    literal = literal_values(source_row)
    if literal is None:
        return None
    direction = "highest" if case.objective == "conditional_max" else "lowest"
    comparison = (
        "The following four recorded yields are supplied for one numerical comparison.\n"
        + f"Target substrate: {case.target_context}.\n"
        + '{"values":'
        + literal
        + "}\n"
        + "Use only these four supplied numbers for this comparison; do not replace them "
        "using any other records. Select the option alias with the "
        + direction
        + " supplied yield. If values are exactly tied, choose any tied optimum.\n"
        'Return exactly one JSON object with the single key "choice", whose value is the '
        "selected alias string. No prose or Markdown.\n"
    )
    if context == "numbers_only":
        return comparison
    presentation = remap_presentation(case, source_row["variant"], source_row["alias_rotation"])
    return presentation.prefix + "\n" + comparison


def conditions_for(source_row, protocol):
    result = list(CONTEXTS)
    seed = stable_id(VERSION, source_row["request_id"], protocol["request_order_seed"])
    random.Random(int(seed, 16)).shuffle(result)
    return result


def parse_choice(text):
    try:
        payload = json.loads(text, object_pairs_hook=_unique_object)
        if not isinstance(payload, dict) or set(payload) != {"choice"}:
            return None, "wrong_schema"
        choice = payload["choice"]
        if not isinstance(choice, str) or choice not in list("ABCD"):
            return None, "invalid_choice"
        return choice, None
    except (ValueError, TypeError):
        return None, "invalid_json_or_duplicate_key"


def score_response(case, source_row, text):
    values = source_row["evaluation"]["values"]
    choice, error = parse_choice(text) if text is not None else (None, "upstream_invalid_values")
    presentation = remap_presentation(case, source_row["variant"], source_row["alias_rotation"])
    comparison_valid = values is not None and choice is not None
    return {
        "choice": choice,
        "parse_error": error,
        "scores": {
            "decision": score_choice(case, choice, presentation),
            "comparison": {
                "valid": comparison_valid,
                "correct": choice in optima(values, case.objective) if comparison_valid else None,
            },
        },
    }


def load_source(dataset, directory, cases):
    verified = verify_v4(directory)
    specification = read_json(directory / "specification.json")
    if specification["limit_blocks"] is not None:
        raise ValueError("Use completed full V4 controls, not a V4 smoke run")
    if specification["dataset_freeze_sha256"] != digest(dataset / "freeze.json"):
        raise ValueError("Dataset differs from V4 source")
    if specification["protocol"]["variants"] != ["shuffled"]:
        raise ValueError("V5 is fixed to the completed shuffled V4 experiment")
    if specification["protocol"]["output_orders"] != ["ABCD", "CDAB"]:
        raise ValueError("V4 output orders differ")
    ids = {c.case_id for c in cases}
    if not ids.issubset(specification["case_ids"]):
        raise ValueError("Selected cases are not covered by V4")
    rows = [r for r in read_jsonl(directory / "responses.jsonl") if r["case_id"] in ids]
    if len(rows) != len(cases) * 8 or verified["cases"] != specification["cases"]:
        raise ValueError("Source is not the complete eight-cell factorial")
    for row in rows:
        literal_values(row)
    return rows


def sources():
    paths = v4_sources()
    for path in [
        ROOT / "run_v5.py",
        ROOT / "scripts/run_next_v5.sh",
        *sorted(Path(__file__).resolve().parent.glob("*.py")),
    ]:
        paths[path.relative_to(ROOT).as_posix()] = path
    return paths


def identity(source, context):
    return {
        **{
            key: source[key]
            for key in (
                "case_id",
                "table_id",
                "target_context",
                "group_id",
                "objective",
                "variant",
                "alias_rotation",
                "output_order",
            )
        },
        "request_id": stable_id(VERSION, source["request_id"], context),
        "source_request_id": source["request_id"],
        "context": context,
    }


def make_plan(dataset, source_dir, cases, source_rows, protocol, model, adapter, limit_blocks):
    validate_protocol(protocol)
    verify(dataset)
    metadata = read_json(source_dir / "model.json")
    if model.resolve() != Path(metadata["model_path"]).resolve():
        raise ValueError("Model differs from V4 source")
    if metadata["adapter_path"] != (str(adapter.resolve()) if adapter else None):
        raise ValueError("Adapter differs from V4 source")
    for filename in metadata["model_files_sha256"]:
        if not (model / filename).is_file():
            raise FileNotFoundError(model / filename)
    if adapter:
        for filename in metadata["adapter_files_sha256"]:
            if not (adapter / filename).is_file():
                raise FileNotFoundError(adapter / filename)
    lookup = {c.case_id: c for c in cases}
    request_hash = hashlib.sha256()
    new_calls = 0
    for source in source_rows:
        for context in conditions_for(source, protocol):
            prompt = comparison_prompt(lookup[source["case_id"]], source, context)
            row = {
                **identity(source, context),
                "prompt_sha256": text_digest(prompt) if prompt else None,
            }
            request_hash.update((canonical(row) + "\n").encode("utf-8"))
            new_calls += prompt is not None
    return {
        "schema": VERSION,
        "development_only": True,
        "split": "validation",
        "dataset": str(dataset.resolve()),
        "dataset_freeze_sha256": digest(dataset / "freeze.json"),
        "source_directory": str(source_dir.resolve()),
        "source_files_sha256": {name: digest(source_dir / name) for name in SOURCE_FILES},
        "model_path": str(model.resolve()),
        "adapter_path": str(adapter.resolve()) if adapter else None,
        "protocol": protocol,
        "limit_blocks": limit_blocks,
        "case_ids": [c.case_id for c in cases],
        "cases": len(cases),
        "source_rows": len(source_rows),
        "attempts": len(source_rows) * 2,
        "requests": new_calls,
        "upstream_failed_attempts": len(source_rows) * 2 - new_calls,
        "ordered_request_manifest_sha256": request_hash.hexdigest(),
        "limitations": LIMITATIONS,
    }


def check_inputs(specification, hashes):
    dataset, source = Path(specification["dataset"]), Path(specification["source_directory"])
    verify(dataset)
    if digest(dataset / "freeze.json") != specification["dataset_freeze_sha256"]:
        raise ValueError("Dataset freeze changed")
    for name, sha in specification["source_files_sha256"].items():
        if digest(source / name) != sha:
            raise ValueError("V4 source changed: " + name)
    if hashes != {name: digest(path) for name, path in sources().items()}:
        raise ValueError("Run code changed")


def make_record(case, source, context, completion, elapsed, protocol):
    prompt = comparison_prompt(case, source, context)
    if (completion is None) != (prompt is None):
        raise ValueError("Only invalid upstream values may skip a generation")
    text = completion.text if completion else None
    return {
        **identity(source, context),
        "prompt": prompt,
        "prompt_sha256": text_digest(prompt) if prompt is not None else None,
        "values_json_literal": literal_values(source),
        "response": text,
        "executed": completion is not None,
        "elapsed_seconds": elapsed,
        "input_tokens": completion.input_tokens if completion else 0,
        "output_tokens": completion.output_tokens if completion else 0,
        "hit_generation_budget": completion.output_tokens >= protocol["max_new_tokens"]
        if completion
        else False,
        "source_choice": source["evaluation"]["choice"],
        "source_scores": source["evaluation"]["scores"],
        "source_clean_value_eligible": source["evaluation"]["clean_value_eligible"],
        "source_clean_value_choice_error": source["evaluation"]["clean_value_choice_error"],
        "source_input_tokens": source["input_tokens"],
        "source_output_tokens": source["output_tokens"],
        **score_response(case, source, text),
    }


def run(out, backend, cases, source_rows, specification):
    if out.exists():
        raise FileExistsError("Choose a new output directory; prior results stay intact")
    protocol = specification["protocol"]
    assert_model(backend.metadata, Path(specification["source_directory"]), protocol)
    paths = sources()
    hashes = {name: digest(path) for name, path in paths.items()}
    check_inputs(specification, hashes)
    new_run(out, backend)
    write_json(out / "protocol.json", protocol)
    write_json(
        out / "specification.json",
        {
            **specification,
            "code_files_sha256": hashes,
            "started_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    for name, path in paths.items():
        destination = out / "code_snapshot" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())
    lookup, rows = {c.case_id: c for c in cases}, []
    started = perf_counter()
    new_calls = 0
    try:
        with (out / "responses.jsonl").open("x", encoding="utf-8") as stream:
            for index, source in enumerate(source_rows, 1):
                case = lookup[source["case_id"]]
                for context in conditions_for(source, protocol):
                    prompt = comparison_prompt(case, source, context)
                    completion, elapsed = None, 0.0
                    if prompt is not None:
                        begin = perf_counter()
                        completion = backend.complete(prompt)
                        elapsed = perf_counter() - begin
                        new_calls += 1
                    row = make_record(case, source, context, completion, elapsed, protocol)
                    stream.write(canonical(row) + "\n")
                    stream.flush()
                    rows.append(row)
                if index % 8 == 0 or index == len(source_rows):
                    print(
                        f"Completed {index}/{len(source_rows)} source responses; {new_calls}/{specification['requests']} new calls",
                        flush=True,
                    )
        check_inputs(specification, hashes)
        if len(rows) != specification["attempts"] or new_calls != specification["requests"]:
            raise ValueError("Attempts or calls differ from the frozen plan")
        summary = summarize(rows, protocol)
        write_tables(out, summary, rows)
        write_json(
            out / "summary.json",
            {
                **summary,
                "status": "complete",
                "finished_utc": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds_excluding_model_load": perf_counter() - started,
            },
        )
        return summary
    except BaseException as exc:
        write_json(
            out / "failure.json",
            {
                "status": "incomplete",
                "exception": type(exc).__name__,
                "message": str(exc),
                "completed_attempts": len(rows),
                "completed_calls": new_calls,
            },
        )
        raise


def verify_run(directory):
    from evidence_lab.models import Completion

    specification, saved = (
        read_json(directory / "specification.json"),
        read_json(directory / "summary.json"),
    )
    if saved.get("status") != "complete" or (directory / "failure.json").exists():
        raise ValueError("V5 run is incomplete")
    dataset, source_dir = Path(specification["dataset"]), Path(specification["source_directory"])
    protocol = validate_protocol(read_json(directory / "protocol.json"))
    cases = select_paired_cases(dataset, specification["limit_blocks"])
    source_rows = load_source(dataset, source_dir, cases)
    model = Path(specification["model_path"])
    adapter = Path(specification["adapter_path"]) if specification["adapter_path"] else None
    plan = make_plan(
        dataset,
        source_dir,
        cases,
        source_rows,
        protocol,
        model,
        adapter,
        specification["limit_blocks"],
    )
    if any(specification.get(key) != value for key, value in plan.items()):
        raise ValueError("V5 plan does not reconstruct")
    check_inputs(specification, specification["code_files_sha256"])
    for name, sha in specification["code_files_sha256"].items():
        if digest(directory / "code_snapshot" / name) != sha:
            raise ValueError("Code snapshot changed: " + name)
    assert_model(read_json(directory / "model.json"), source_dir, protocol)
    rows = read_jsonl(directory / "responses.jsonl")
    requests = [
        (source, context) for source in source_rows for context in conditions_for(source, protocol)
    ]
    if len(rows) != len(requests):
        raise ValueError("Missing V5 response rows")
    lookup = {c.case_id: c for c in cases}
    for row, (source, context) in zip(rows, requests):
        if not math.isfinite(row["elapsed_seconds"]) or row["elapsed_seconds"] < 0:
            raise ValueError("Invalid generation time")
        for key in ("input_tokens", "output_tokens"):
            if type(row[key]) is not int or row[key] < (1 if row["executed"] else 0):
                raise ValueError("Invalid token accounting")
        completion = (
            Completion(row["response"], row["input_tokens"], row["output_tokens"])
            if row["executed"]
            else None
        )
        expected = make_record(
            lookup[source["case_id"]], source, context, completion, row["elapsed_seconds"], protocol
        )
        if row != expected:
            raise ValueError(
                "V5 response identity, prompt, literal values, or scoring does not reconstruct"
            )
    summary = summarize(rows, protocol)
    if any(saved.get(key) != value for key, value in summary.items()):
        raise ValueError("V5 summary does not reconstruct")
    with tempfile.TemporaryDirectory() as temporary:
        write_tables(Path(temporary), summary, rows)
        for filename in ("paired_contrasts.csv", "errors.csv"):
            if (Path(temporary) / filename).read_bytes() != (directory / filename).read_bytes():
                raise ValueError("V5 CSV does not reconstruct: " + filename)
    return summary


def gate(directories, config):
    protocol = validate_protocol(read_json(config))
    for directory in directories:
        result = verify_run(directory)
        specification = read_json(directory / "specification.json")
        if result["protocol"] != protocol or specification["limit_blocks"] != 4:
            raise ValueError("Smoke protocol or case selection differs")
        if result["cases"] != 8 or result["groups"] != 4 or result["attempts"] != 128:
            raise ValueError(
                "Smoke must cover four groups, paired max/min and all 16 context/cell requests"
            )
        for context, metrics in result["by_context"].items():
            if metrics["invalid_generated_choices"] or metrics["cost"]["budget_hits"]:
                raise ValueError("Inspect generated format failures or truncation: " + context)
        print(
            canonical(
                {
                    "run": str(directory),
                    "requests": result["requests"],
                    "attempts": result["attempts"],
                }
            )
        )
    print("V5_SMOKE_FORMAT_AND_INTEGRITY_GATE_OK", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "run"):
        child = sub.add_parser(command)
        for name in ("dataset", "source", "model"):
            child.add_argument("--" + name, type=Path, required=True)
        child.add_argument("--adapter", type=Path)
        child.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
        child.add_argument("--limit-blocks", type=int)
        if command == "run":
            child.add_argument("--out", type=Path, required=True)
            child.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    child = sub.add_parser("verify")
    child.add_argument("--run", type=Path, required=True)
    child = sub.add_parser("gate")
    child.add_argument("--runs", type=Path, nargs="+", required=True)
    child.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = verify_run(args.run)
            print(
                canonical(
                    {
                        "status": "V5_VERIFIED",
                        "requests": result["requests"],
                        "attempts": result["attempts"],
                    }
                )
            )
        elif args.command == "gate":
            gate(args.runs, args.config)
        else:
            if args.command == "run" and args.out.exists():
                raise FileExistsError("Output exists; preserve it and choose a new run tag")
            protocol = validate_protocol(read_json(args.config))
            cases = select_paired_cases(args.dataset, args.limit_blocks)
            source_rows = load_source(args.dataset, args.source, cases)
            plan = make_plan(
                args.dataset,
                args.source,
                cases,
                source_rows,
                protocol,
                args.model,
                args.adapter,
                args.limit_blocks,
            )
            print(canonical({k: v for k, v in plan.items() if k != "case_ids"}), flush=True)
            if args.command == "plan":
                return 0
            from evidence_lab.models import HuggingFaceModel

            backend = HuggingFaceModel(
                args.model,
                adapter_path=args.adapter,
                device=args.device,
                max_length=protocol["max_length"],
                max_new_tokens=protocol["max_new_tokens"],
                use_chat_template=True,
                enable_thinking=False,
            )
            result = run(args.out, backend, cases, source_rows, plan)
            print(
                canonical(
                    {"status": "complete", "requests": result["requests"], "output": str(args.out)}
                ),
                flush=True,
            )
        return 0
    except (ValueError, KeyError, FileNotFoundError, FileExistsError, ImportError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
