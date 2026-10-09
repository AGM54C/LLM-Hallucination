"""Plan, stream, and independently rescore the fixed V4 development experiment."""

from __future__ import annotations

import argparse
import hashlib
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from evidence_lab.storage import canonical, digest, read_json, read_jsonl, verify, write_json
from evidence_lab.workflows import new_run
from evidence_lab_v2.presentations import position_audit, present_order
from evidence_lab_v3.controls import joint_prompt as v3_prompt
from evidence_lab_v3.controls import v3_sources

from .factorial import (
    VERSION,
    conditions_for,
    joint_prompt,
    remap_presentation,
    request_identity,
    score_response,
    select_paired_cases,
    validate_protocol,
)
from .reporting import LIMITATIONS, summarize, write_tables

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "configs/controls_v4.json"
REFERENCE_FILES = ("specification.json", "summary.json", "model.json", "responses.jsonl")
MODEL_FIELDS = (
    "model_files_sha256",
    "adapter_files_sha256",
    "thinking_mode",
    "chat_template",
    "decoding",
    "dtype",
    "attention",
    "max_length",
    "max_new_tokens",
)


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sources():
    paths = v3_sources()
    package = Path(__file__).resolve().parent
    for path in (
        ROOT / "run_v4.py",
        ROOT / "scripts/run_next_v4.sh",
        *sorted(package.glob("*.py")),
    ):
        paths[path.relative_to(ROOT).as_posix()] = path
    return paths


def load_reference(dataset, directory, cases):
    specification = read_json(directory / "specification.json")
    summary = read_json(directory / "summary.json")
    if specification.get("schema") != "behavior-controls-v3":
        raise ValueError("Reference must be a completed V3 control run")
    if summary.get("status") != "complete" or (directory / "failure.json").exists():
        raise ValueError("Reference is incomplete")
    if specification.get("dataset_freeze_sha256") != digest(dataset / "freeze.json"):
        raise ValueError("Reference and dataset freeze differ")
    if specification.get("split") != "validation" or specification.get("order_seed") != 0:
        raise ValueError("Reference must use validation and order seed zero")
    ids = specification["case_ids"]
    if len(set(ids)) != len(ids) or len(ids) != specification["cases"]:
        raise ValueError("Invalid V3 reference case list")
    if not {c.case_id for c in cases}.issubset(ids):
        raise ValueError("V3 reference does not cover planned cases")
    expected = {(cid, "public_compare", "canonical") for cid in ids}
    expected |= {
        (cid, kind, variant)
        for cid in ids
        for kind in ("cached_compare", "joint")
        for variant in ("canonical", "shuffled")
    }
    rows = read_jsonl(directory / "responses.jsonl")
    actual = [(r["case_id"], r["kind"], r["variant"]) for r in rows]
    if len(set(actual)) != len(actual) or set(actual) != expected:
        raise ValueError("Missing, duplicate or unexpected V3 reference rows")
    if sum(r["executed"] is True for r in rows) != specification["requests"]:
        raise ValueError("V3 reference request count differs from specification")
    lookup = {c.case_id: c for c in cases}
    result = {}
    for row in rows:
        if row["kind"] != "joint" or row["case_id"] not in lookup:
            continue
        case = lookup[row["case_id"]]
        presentation = present_order(case, row["variant"], 0)
        if row["order_seed"] != 0 or row["prompt"] != v3_prompt(case, presentation):
            raise ValueError("V3 reference prompt does not reconstruct")
        condition = {"variant": row["variant"], "alias_rotation": 0, "output_order": "ABCD"}
        evaluation = score_response(case, condition, presentation, row["response"])
        for name in ("decision", "program_decision"):
            if evaluation["scores"][name] != row["scores"][name]:
                raise ValueError("V3 reference score does not reconstruct: " + name)
        for key in ("valid", "correct"):
            if evaluation["scores"]["values"][key] != row["scores"]["values"][key]:
                raise ValueError("V3 reference value score does not reconstruct")
        result[(case.case_id, row["variant"])] = evaluation
    return result


def make_plan(dataset, reference, cases, protocol, model, adapter, limit_blocks):
    validate_protocol(protocol)
    verify(dataset)
    metadata = read_json(reference / "model.json")
    if Path(metadata["model_path"]).resolve() != model.resolve():
        raise ValueError("Model path differs from the V3 reference")
    expected_adapter = str(adapter.resolve()) if adapter else None
    if metadata.get("adapter_path") != expected_adapter:
        raise ValueError("Model/adapter and reference are mismatched")
    for name in metadata["model_files_sha256"]:
        if not (model / name).is_file():
            raise FileNotFoundError(model / name)
    for name in metadata["adapter_files_sha256"]:
        if adapter is None or not (adapter / name).is_file():
            raise FileNotFoundError("Missing reference adapter file: " + name)
    request_hash = hashlib.sha256()
    count = 0
    for case in cases:
        for condition in conditions_for(case, protocol):
            presentation = remap_presentation(
                case, condition["variant"], condition["alias_rotation"]
            )
            prompt = joint_prompt(case, presentation, condition["output_order"])
            line = canonical(
                {**request_identity(case, condition), "prompt_sha256": text_digest(prompt)}
            )
            request_hash.update((line + "\n").encode("utf-8"))
            count += 1
    return {
        "schema": VERSION,
        "split": "validation",
        "development_only": True,
        "dataset": str(dataset.resolve()),
        "dataset_freeze_sha256": digest(dataset / "freeze.json"),
        "reference_directory": str(reference.resolve()),
        "reference_files_sha256": {name: digest(reference / name) for name in REFERENCE_FILES},
        "model_path": str(model.resolve()),
        "adapter_path": expected_adapter,
        "protocol": protocol,
        "limit_blocks": limit_blocks,
        "case_ids": [c.case_id for c in cases],
        "cases": len(cases),
        "table_target_blocks": len({(c.table.table_id, c.target_context) for c in cases}),
        "groups": len({c.table.group_id for c in cases}),
        "objectives": dict(Counter(c.objective for c in cases)),
        "requests": count,
        "ordered_request_manifest_sha256": request_hash.hexdigest(),
        "limitations": LIMITATIONS,
    }


def assert_model(metadata, reference, protocol):
    previous = read_json(reference / "model.json")
    for field in MODEL_FIELDS:
        if metadata.get(field) != previous.get(field):
            raise ValueError("Loaded model/generation differs from V3: " + field)
    for field in ("max_length", "max_new_tokens"):
        if metadata[field] != protocol[field]:
            raise ValueError("Loaded model differs from V4 protocol: " + field)


def check_frozen_inputs(specification, code_hashes):
    dataset, reference = Path(specification["dataset"]), Path(specification["reference_directory"])
    verify(dataset)
    if digest(dataset / "freeze.json") != specification["dataset_freeze_sha256"]:
        raise ValueError("Dataset freeze changed")
    for name, sha in specification["reference_files_sha256"].items():
        if digest(reference / name) != sha:
            raise ValueError("V3 reference changed: " + name)
    if code_hashes != {name: digest(path) for name, path in sources().items()}:
        raise ValueError("Run code changed")


def score_record(row):
    return {key: value for key, value in row.items() if key not in ("prompt", "response")}


def run(out, backend, cases, reference_rows, specification):
    if out.exists():
        raise FileExistsError("Keep existing results and choose a new output directory")
    protocol = specification["protocol"]
    assert_model(backend.metadata, Path(specification["reference_directory"]), protocol)
    paths = sources()
    hashes = {name: digest(path) for name, path in paths.items()}
    check_frozen_inputs(specification, hashes)
    new_run(out, backend)
    for name, path in paths.items():
        target = out / "code_snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    write_json(out / "protocol.json", protocol)
    write_json(
        out / "specification.json",
        {
            **specification,
            "code_files_sha256": hashes,
            "started_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    rows = []
    started = perf_counter()
    try:
        with (
            (out / "responses.jsonl").open("x", encoding="utf-8") as raw,
            (out / "scores.jsonl").open("x", encoding="utf-8") as scored,
        ):
            for index, case in enumerate(cases, 1):
                for condition in conditions_for(case, protocol):
                    presentation = remap_presentation(
                        case, condition["variant"], condition["alias_rotation"]
                    )
                    prompt = joint_prompt(case, presentation, condition["output_order"])
                    begin = perf_counter()
                    completion = backend.complete(prompt)
                    elapsed = perf_counter() - begin
                    row = {
                        **request_identity(case, condition),
                        **position_audit(case, presentation),
                        "prompt": prompt,
                        "prompt_sha256": text_digest(prompt),
                        "response": completion.text,
                        "input_tokens": completion.input_tokens,
                        "output_tokens": completion.output_tokens,
                        "elapsed_seconds": elapsed,
                        "hit_generation_budget": completion.output_tokens
                        >= protocol["max_new_tokens"],
                        "evaluation": score_response(
                            case, condition, presentation, completion.text
                        ),
                        "reference_evaluation": reference_rows[
                            (case.case_id, condition["variant"])
                        ],
                    }
                    raw.write(canonical(row) + "\n")
                    raw.flush()
                    scored.write(canonical(score_record(row)) + "\n")
                    scored.flush()
                    rows.append(row)
                print(
                    f"Completed {index}/{len(cases)} cases; {len(rows)}/{specification['requests']} requests",
                    flush=True,
                )
        check_frozen_inputs(specification, hashes)
        if len(rows) != specification["requests"]:
            raise ValueError("Request count differs from plan")
        result = summarize(rows, protocol)
        write_tables(out, result, rows)
        write_json(
            out / "summary.json",
            {
                **result,
                "status": "complete",
                "elapsed_seconds_excluding_model_load": perf_counter() - started,
                "finished_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
        return result
    except BaseException as exc:
        write_json(
            out / "failure.json",
            {
                "status": "incomplete",
                "exception": type(exc).__name__,
                "message": str(exc),
                "completed_requests": len(rows),
            },
        )
        raise


def verify_run(directory):
    specification = read_json(directory / "specification.json")
    summary = read_json(directory / "summary.json")
    if summary.get("status") != "complete" or (directory / "failure.json").exists():
        raise ValueError("Run is incomplete")
    dataset, reference = Path(specification["dataset"]), Path(specification["reference_directory"])
    protocol = validate_protocol(read_json(directory / "protocol.json"))
    cases = select_paired_cases(dataset, specification["limit_blocks"])
    reference_rows = load_reference(dataset, reference, cases)
    model = Path(specification["model_path"])
    adapter = Path(specification["adapter_path"]) if specification["adapter_path"] else None
    rebuilt_plan = make_plan(
        dataset, reference, cases, protocol, model, adapter, specification["limit_blocks"]
    )
    if any(specification.get(key) != value for key, value in rebuilt_plan.items()):
        raise ValueError("Stored plan does not reconstruct")
    check_frozen_inputs(specification, specification["code_files_sha256"])
    for name, sha in specification["code_files_sha256"].items():
        if digest(directory / "code_snapshot" / name) != sha:
            raise ValueError("Code snapshot differs: " + name)
    assert_model(read_json(directory / "model.json"), reference, protocol)
    rows = read_jsonl(directory / "responses.jsonl")
    scores = read_jsonl(directory / "scores.jsonl")
    requests = [(case, condition) for case in cases for condition in conditions_for(case, protocol)]
    if len(rows) != len(requests) or len(scores) != len(rows):
        raise ValueError("Incomplete raw/scored request log")
    for row, scored, (case, condition) in zip(rows, scores, requests):
        identity = request_identity(case, condition)
        if any(row.get(key) != value for key, value in identity.items()):
            raise ValueError("Request identity or schedule differs")
        presentation = remap_presentation(case, condition["variant"], condition["alias_rotation"])
        prompt = joint_prompt(case, presentation, condition["output_order"])
        if row["prompt"] != prompt or row["prompt_sha256"] != text_digest(prompt):
            raise ValueError("Logged prompt does not reconstruct")
        if any(row[key] != value for key, value in position_audit(case, presentation).items()):
            raise ValueError("Table-position audit differs")
        expected = score_response(case, condition, presentation, row["response"])
        if row["evaluation"] != expected or scored != score_record(row):
            raise ValueError("Recorded scores differ from recomputation")
        if row["reference_evaluation"] != reference_rows[(case.case_id, condition["variant"])]:
            raise ValueError("Recorded V3 comparison differs")
        for key in ("input_tokens", "output_tokens"):
            if type(row[key]) is not int or row[key] < 1:
                raise ValueError("Invalid token accounting")
        if not math.isfinite(row["elapsed_seconds"]) or row["elapsed_seconds"] < 0:
            raise ValueError("Invalid time accounting")
        if row["hit_generation_budget"] != (row["output_tokens"] >= protocol["max_new_tokens"]):
            raise ValueError("Truncation flag differs")
    computed = summarize(rows, protocol)
    if any(summary.get(key) != value for key, value in computed.items()):
        raise ValueError("Summary differs from complete raw-response recomputation")
    return computed


def gate(directories, config):
    protocol = validate_protocol(read_json(config))
    for directory in directories:
        summary = verify_run(directory)
        specification = read_json(directory / "specification.json")
        if summary["protocol"] != protocol or specification["limit_blocks"] != 4:
            raise ValueError("Smoke protocol/selection differs from the planned full run")
        if summary["cases"] != 8 or summary["groups"] != 4:
            raise ValueError("Smoke must include max/min in one block from each of four groups")
        metrics = summary["all_assignments"]
        if any(metrics["endpoints"][name]["invalid"] for name in ("decision", "values")):
            raise ValueError("Inspect smoke JSON/value/choice format failures before a full run")
        if metrics["cost"]["hit_generation_budget"]:
            raise ValueError("Inspect smoke generation-budget hits before a full run")
        print(
            canonical(
                {
                    "run": str(directory),
                    "requests": summary["requests"],
                    "order_compliant": metrics["output_order_compliant"],
                    "compliant": metrics["compliant"],
                    "note": "Accuracy and order obedience are outcomes, not gate thresholds.",
                }
            )
        )
    print("V4_SMOKE_FORMAT_AND_INTEGRITY_GATE_OK", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "run"):
        child = sub.add_parser(command)
        for name in ("dataset", "reference", "model"):
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
            print(canonical({"status": "V4_VERIFIED", "requests": result["requests"]}))
        elif args.command == "gate":
            gate(args.runs, args.config)
        else:
            if args.command == "run" and args.out.exists():
                raise FileExistsError("Output already exists; choose a new run tag")
            protocol = validate_protocol(read_json(args.config))
            cases = select_paired_cases(args.dataset, args.limit_blocks)
            references = load_reference(args.dataset, args.reference, cases)
            plan = make_plan(
                args.dataset,
                args.reference,
                cases,
                protocol,
                args.model,
                args.adapter,
                args.limit_blocks,
            )
            print(
                canonical({key: value for key, value in plan.items() if key != "case_ids"}),
                flush=True,
            )
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
            result = run(args.out, backend, cases, references, plan)
            print(
                canonical(
                    {
                        "status": "complete",
                        "requests": result["requests"],
                        "cases": result["cases"],
                        "output": str(args.out),
                    }
                ),
                flush=True,
            )
        return 0
    except (ValueError, KeyError, FileNotFoundError, FileExistsError, ImportError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
