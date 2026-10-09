"""Independent readout requests, strict parsing, streamed logs and frozen run inputs."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from time import perf_counter

from evidence_lab.models import parse_choice
from evidence_lab.storage import canonical, digest, verify, write_json
from evidence_lab.tasks import score_choice
from evidence_lab.workflows import load_cases, new_run

from .presentations import conditions, position_audit, present_order

VERSION = "behavior-diagnostics-v2"
TOLERANCE = 0.0005
KINDS = ("value", "relation", "decision")


def select_cases(dataset, objectives, limit=None):
    if not objectives or len(set(objectives)) != len(objectives):
        raise ValueError("Select unique objectives")
    if set(objectives) - {"conditional_max", "conditional_min"}:
        raise ValueError("Unsupported objective")
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("Limit must be a positive integer or omitted for the full split")
    pool = [c for c in load_cases(dataset, "validation") if c.objective in objectives]
    # Round-robin across groups and tables for a smoke run; full runs include every case.
    by_group = defaultdict(lambda: defaultdict(list))
    for case in pool:
        by_group[case.table.group_id][case.table.table_id].append(case)
    queues = {}
    for group, tables in sorted(by_group.items()):
        queues[group] = deque(
            deque(sorted(rows, key=lambda c: c.case_id)) for _, rows in sorted(tables.items())
        )
    selected = []
    while queues and (limit is None or len(selected) < limit):
        for group in list(queues):
            tables = queues[group]
            rows = tables.popleft()
            selected.append(rows.popleft())
            if rows:
                tables.append(rows)
            if not tables:
                del queues[group]
            if limit is not None and len(selected) >= limit:
                break
    if not selected:
        raise ValueError("Empty validation selection")
    return selected


def _schema_instruction(keys):
    skeleton = json.dumps({"values": {key: None for key in keys}}, separators=(",", ":"))
    return (
        "\nReturn exactly one valid JSON object, with no prose or Markdown. "
        'The only top-level key is "values". Inside it, use each of the following '
        "quoted keys exactly once: " + ", ".join(json.dumps(k) for k in keys) + ". "
        "Map each key directly to its numeric recorded yield, with at least four decimal "
        "places. Do not repeat keys or add record_label, option_alias, value, or yield fields. "
        "Use this structure, replacing EVERY null with the requested number; "
        "null is a placeholder and is not an acceptable answer: " + skeleton
    )


def build_requests(case, presentation):
    labels = {r.record_id: f"R{i:02d}" for i, r in enumerate(case.table.records)}
    targets = [r for r in case.table.records if r.context == case.target_context]
    aliases = dict(presentation.aliases)
    expected = {
        "value": {labels[r.record_id]: r.value for r in targets},
        "relation": {aliases[r.option]: r.value for r in targets},
    }
    prompts = {
        "value": presentation.prefix
        + "\nCopy the recorded yields for records "
        + ", ".join(expected["value"])
        + "."
        + _schema_instruction(expected["value"]),
        "relation": presentation.prefix + f"\nFor substrate {case.target_context}, "
        "report the recorded yield for each option alias."
        + _schema_instruction(expected["relation"]),
        "decision": presentation.prompt,
    }
    return prompts, expected


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate_json_key")
        obj[key] = value
    return obj


def parse_values(text, keys):
    try:
        payload = json.loads(text, object_pairs_hook=_unique_object)
        if not isinstance(payload, dict) or set(payload) != {"values"}:
            return None, "wrong_top_level_schema"
        values = payload["values"]
        if not isinstance(values, dict) or set(values) != set(keys):
            return None, "missing_or_extra_value_keys"
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values.values()):
            return None, "nonfinite_or_nonnumeric_value"
        return values, None
    except (ValueError, TypeError, OverflowError) as error:
        return None, "duplicate_json_key" if str(error) == "duplicate_json_key" else "invalid_json"


def score_readout(text, expected):
    values, error = parse_values(text, expected)
    return {
        "valid": values is not None,
        "correct": None
        if values is None
        else all(abs(values[key] - gold) <= TOLERANCE for key, gold in expected.items()),
        "parse_error": error,
    }, values


def choose_from_values(values, objective):
    if values is None:
        return None
    best = (max if objective == "conditional_max" else min)(values.values())
    return min(key for key, value in values.items() if abs(value - best) <= 1e-9)


def endpoint(rows):
    valid = [row for row in rows if row["valid"]]
    result = {
        "attempted": len(rows),
        "valid": len(valid),
        "invalid": len(rows) - len(valid),
        "all_attempt_accuracy": sum(bool(row["correct"]) for row in rows) / len(rows),
        "conditional_accuracy": fmean(bool(row["correct"]) for row in valid) if valid else None,
    }
    if all("regret_pp" in row for row in rows):
        result["mean_regret_pp_valid"] = fmean(row["regret_pp"] for row in valid) if valid else None
    return result


def plan(dataset, cases, variants, order_seeds, mode, model_path=None, adapter_path=None):
    settings = conditions(variants, order_seeds)
    kinds = KINDS if mode == "diagnose" else ("decision",)
    if mode not in {"diagnose", "orders"}:
        raise ValueError("Unknown mode")
    # Recheck every prompt layout without loading a model.
    for case in cases:
        for variant, seed in settings:
            presentation = present_order(case, variant, seed)
            assert len(presentation.record_spans) == len(case.table.records)
    return {
        "schema": VERSION,
        "mode": mode,
        "split": "validation",
        "cases": len(cases),
        "groups": len({c.table.group_id for c in cases}),
        "tables": len({c.table.table_id for c in cases}),
        "objectives": dict(Counter(c.objective for c in cases)),
        "case_ids": [c.case_id for c in cases],
        "conditions": [{"variant": v, "order_seed": s} for v, s in settings],
        "requests": len(cases) * len(settings) * len(kinds),
        "dataset": str(dataset.resolve()),
        "dataset_freeze_sha256": digest(dataset / "freeze.json"),
        "model_path": str(model_path.resolve()) if model_path else None,
        "adapter_path": str(adapter_path.resolve()) if adapter_path else None,
        "value_tolerance_pp": TOLERANCE,
        "alias_seed": 0,
        "order_seed_0_shuffled": "identical to v1 shuffled prompt",
        "readout_requests": "independent; no prior output is injected into another request",
        "program_decision": "argmax/argmin of model relation readout only; alias-lexicographic ties",
        "limitations": [
            "Four within-study groups are not independent research sources.",
            "Ordering also changes record positions/span; these are logged, not matched.",
            "Explicit readout success does not establish hidden-state mechanisms.",
        ],
    }


def code_sources():
    package = Path(__file__).resolve().parent
    root = package.parents[1]
    paths = [
        root / "run_v2.py",
        *sorted(package.glob("*.py")),
        *sorted((package.parent / "evidence_lab").glob("*.py")),
    ]
    return {str(path.relative_to(root)).replace("\\", "/"): path for path in paths}


def run(dataset, out, backend, cases, variants, order_seeds, mode, specification):
    if out.exists():
        raise FileExistsError(
            "Use a new output directory; incomplete runs are never silently reused"
        )
    verify(dataset)
    sources = code_sources()
    hashes = {name: digest(path) for name, path in sources.items()}
    new_run(out, backend)
    for name, path in sources.items():
        target = out / "code_snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    write_json(
        out / "specification.json",
        {
            **specification,
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "code_files_sha256": hashes,
        },
    )
    aggregate, by_group, separations = defaultdict(list), defaultdict(list), defaultdict(Counter)
    n_requests, n_pairs = 0, 0
    started = perf_counter()
    try:
        with (
            (out / "responses.jsonl").open("x", encoding="utf-8") as raw_stream,
            (out / "scores.jsonl").open("x", encoding="utf-8") as score_stream,
        ):
            for case_index, case in enumerate(cases, 1):
                for variant, seed in conditions(variants, order_seeds):
                    presentation = present_order(case, variant, seed)
                    prompts, expected = build_requests(case, presentation)
                    scores, values = {}, {}
                    identity = {
                        "case_id": case.case_id,
                        "group_id": case.table.group_id,
                        "table_id": case.table.table_id,
                        "objective": case.objective,
                        "variant": variant,
                        "order_seed": seed,
                    }
                    for kind in KINDS if mode == "diagnose" else ("decision",):
                        request_started = perf_counter()
                        completion = backend.complete(prompts[kind])
                        elapsed = perf_counter() - request_started
                        if kind == "decision":
                            scores[kind] = score_choice(
                                case, parse_choice(completion.text), presentation
                            )
                        else:
                            scores[kind], values[kind] = score_readout(
                                completion.text, expected[kind]
                            )
                        raw_stream.write(
                            canonical(
                                {
                                    **identity,
                                    "kind": kind,
                                    "prompt": prompts[kind],
                                    "response": completion.text,
                                    "input_tokens": completion.input_tokens,
                                    "output_tokens": completion.output_tokens,
                                    "elapsed_seconds": elapsed,
                                    "score": scores[kind],
                                }
                            )
                            + "\n"
                        )
                        raw_stream.flush()
                        n_requests += 1
                    if mode == "diagnose":
                        choice = choose_from_values(values["relation"], case.objective)
                        scores["relation_program_decision"] = score_choice(
                            case, choice, presentation
                        )
                    record = {**identity, **position_audit(case, presentation), "scores": scores}
                    score_stream.write(canonical(record) + "\n")
                    score_stream.flush()
                    n_pairs += 1
                    label = f"{case.objective}/{variant}/seed={seed}"
                    for kind, score in scores.items():
                        aggregate[f"{label}/{kind}"].append(score)
                        by_group[f"{label}/{kind}/{case.table.group_id}"].append(score)
                    if mode == "diagnose":
                        separation = separations[label]
                        separation["case_presentations"] += 1
                        separation["relation_correct_decision_wrong"] += int(
                            scores["relation"]["correct"] is True
                            and scores["decision"]["correct"] is False
                        )
                        separation["both_readouts_correct_decision_wrong"] += int(
                            scores["value"]["correct"] is True
                            and scores["relation"]["correct"] is True
                            and scores["decision"]["correct"] is False
                        )
                print(
                    f"Completed {case_index}/{len(cases)} cases; {n_requests} requests", flush=True
                )
        # Refuse to mark a run complete if its inputs changed mid-run.
        verify(dataset)
        if digest(dataset / "freeze.json") != specification["dataset_freeze_sha256"]:
            raise ValueError("Dataset freeze changed during run")
        if {name: digest(path) for name, path in sources.items()} != hashes:
            raise ValueError("Diagnostic source changed during run")
        report = {
            "schema": VERSION,
            "status": "complete",
            "mode": mode,
            "cases": len(cases),
            "groups": specification["groups"],
            "tables": specification["tables"],
            "requests": n_requests,
            "case_presentations": n_pairs,
            "elapsed_seconds_excluding_model_load": perf_counter() - started,
            "endpoints": {key: endpoint(rows) for key, rows in sorted(aggregate.items())},
            "by_group": {key: endpoint(rows) for key, rows in sorted(by_group.items())},
            "separations": dict(separations),
            "scientific_conclusion": None,
            "limitations": specification["limitations"],
            "finished_utc": datetime.now(timezone.utc).isoformat(),
        }
        assert n_requests == specification["requests"]
        write_json(out / "summary.json", report)
        return report
    except BaseException as error:
        write_json(
            out / "failure.json",
            {
                "status": "incomplete",
                "exception": type(error).__name__,
                "message": str(error),
                "completed_requests": n_requests,
                "completed_presentations": n_pairs,
            },
        )
        raise
