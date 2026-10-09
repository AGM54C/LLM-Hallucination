"""Use-case orchestration. Scientific functions remain independently testable."""

from __future__ import annotations

import json
import platform
import random
from collections import defaultdict
from itertools import permutations
from pathlib import Path

from .analysis import paired_group_difference, summarize
from .blinding import BlindEnvironment, choose_query, decide, prior_success_bound, public_reference
from .data import case_from_dict, case_to_dict, load_chemistry, make_cases, split_tables
from .domain import DecisionCase
from .models import TextModel, parse_choice
from .sampling import select_balanced, select_matched, training_pool
from .storage import (
    canonical,
    digest,
    freeze,
    read_json,
    read_jsonl,
    verify,
    write_json,
    write_jsonl,
)
from .tasks import (
    DEVELOPMENT_RULES,
    HELD_OUT_RULES,
    diagnostics,
    present,
    rule_choice,
    score_choice,
)


def new_run(out: Path, backend: TextModel | None = None) -> None:
    out.mkdir(parents=True, exist_ok=False)
    write_json(
        out / "environment.json",
        {"python": platform.python_version(), "platform": platform.platform()},
    )
    if backend is not None:
        write_json(
            out / "model.json",
            getattr(backend, "metadata", {"kind": "test_model_port_without_checkpoint"}),
        )


def prepare(config_path: Path, out: Path, difficulty_path: Path | None = None) -> dict:
    config = read_json(config_path)
    if config.get("schema") != "evidence-lab-pilot-v1":
        raise ValueError("Unknown experiment configuration schema")
    source = (config_path.parent / config["data_path"]).resolve()
    tables, audit = load_chemistry(source, config["expected_sha256"])
    splits = split_tables(
        tables, config["split_seed"], config["validation_fraction"], config["test_fraction"]
    )
    cases = make_cases(tables, splits)
    pool = training_pool(cases)
    maximum_cases = [c for c in cases if c.objective == "conditional_max"]
    audit["conditional_max_tasks"] = len(maximum_cases)
    audit["strict_pooled_rule_contrasts"] = sum(
        diagnostics(c)["rule_rejected"]["pooled_max"] for c in maximum_cases
    )
    audit["tied_maximum_tasks"] = sum(len(diagnostics(c)["gold"]) > 1 for c in maximum_cases)
    audit["eligible_training_tasks"] = len(pool)
    audit["tie_policy"] = (
        "All co-optima accepted in evaluation; tied maxima excluded from single-target SFT."
    )
    difficulty = None
    if difficulty_path:
        rows = read_jsonl(difficulty_path)
        if len({r["case_id"] for r in rows}) != len(rows):
            raise ValueError("Duplicate difficulty records")
        difficulty = {r["case_id"]: r["nll"] for r in rows}
    method = config.get("selection_method", "joint_strata")
    if method not in {"joint_strata", "balanced_marginals"}:
        raise ValueError("Unknown selection method")
    selector = select_balanced if method == "balanced_marginals" else select_matched
    arms, selection = selector(
        pool, config["training_cases_per_arm"], config["selection_seed"], difficulty
    )
    # Compute row membership before exporting anything; aliases/rewrites cannot cross splits.
    ownership = {}
    for case in cases:
        for record in case.table.records:
            if ownership.setdefault(record.record_id, case.split) != case.split:
                raise ValueError("A physical measurement crossed data partitions")
    new_run(out)
    write_json(out / "config.json", config)
    write_json(out / "audit.json", audit)
    write_json(out / "splits.json", splits)
    write_json(out / "selection.json", selection)
    write_jsonl(out / "cases.jsonl", (case_to_dict(c) for c in cases))
    for name, selected in arms.items():
        rows = []
        variant = "shuffled" if name == "random_order_augmentation" else "canonical"
        for case in selected:
            presentation = present(case, variant)
            gold = diagnostics(case)["gold"][0]
            completion = json.dumps(
                {"choice": dict(presentation.aliases)[gold]}, separators=(",", ":")
            )
            rows.append(
                {
                    "case_id": case.case_id,
                    "group_id": case.table.group_id,
                    "split": "train",
                    "prompt": presentation.prompt,
                    "completion": completion,
                }
            )
        write_jsonl(out / "training" / f"{name}.jsonl", rows)
    source_files = {"data": source, "config": config_path}
    if difficulty_path:
        source_files["measured_difficulty"] = difficulty_path
    package = Path(__file__).parent
    for path in package.glob("*.py"):
        snapshot = out / "code_snapshot" / path.name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(path.read_bytes())
    source_files.update({f"code/{p.name}": p for p in package.glob("*.py")})
    freeze(out, source_files)
    return {
        "out": str(out),
        "cases": len(cases),
        "audit": audit,
        "selection_coverage": {k: v["coverage"] for k, v in selection["arms"].items()},
        "scientific_conclusion": None,
    }


def load_cases(dataset: Path, split: str) -> list[DecisionCase]:
    verify(dataset)
    cases = [case_from_dict(row) for row in read_jsonl(dataset / "cases.jsonl")]
    selected = cases if split == "all" else [c for c in cases if c.split == split]
    if not selected:
        raise ValueError("Requested split is empty")
    return selected


def run_rule_baselines(dataset: Path, out: Path, split: str) -> dict:
    cases = load_cases(dataset, split)
    rows = []
    grouped = defaultdict(list)
    for case in cases:
        p = present(case)
        for rule in ("scoped", *DEVELOPMENT_RULES, *HELD_OUT_RULES):
            choice = dict(p.aliases)[rule_choice(case, rule)]
            row = {
                "case_id": case.case_id,
                "group_id": case.table.group_id,
                "table_id": case.table.table_id,
                "split": case.split,
                "objective": case.objective,
                "method": rule,
                **score_choice(case, choice, p),
            }
            rows.append(row)
            grouped[f"{case.objective}/{rule}"].append(row)
    report = {
        "split": split,
        "kind": "deterministic_program_baselines_not_LLM",
        "endpoints": {k: summarize(v) for k, v in grouped.items()},
        "research_sources": len({c.table.source_id for c in cases}),
        "scientific_conclusion": None,
    }
    new_run(out)
    write_jsonl(out / "scores.jsonl", rows)
    write_json(out / "summary.json", report)
    return report


def run_blind_baselines(dataset: Path, out: Path, split: str) -> dict:
    cases = load_cases(dataset, split)
    config = read_json(dataset / "config.json")
    tables = {c.table.table_id: c.table for c in cases}
    budgets = config["blind_budgets"]
    if not budgets or any(type(b) is not int or b < 0 for b in budgets):
        raise ValueError("Blind budgets must be nonnegative integers")
    rows, table_audits = [], []
    for table in tables.values():
        for context in table.contexts[: config["blind_contexts_per_table"]]:
            initial = public_reference(table, context)
            table_audits.append(
                {
                    "table_id": table.table_id,
                    "context": context,
                    "prior_success_bound": prior_success_bound(initial),
                    "unique_value_contexts": sum(
                        len({row[c] for row in initial.reference}) == len(table.options)
                        for c in range(len(table.contexts))
                    ),
                    "contexts": len(table.contexts),
                }
            )
            for rank, mapping in enumerate(permutations(range(len(table.options)))):
                for policy in config["blind_policies"]:
                    # Same public RNG across assignments: private mapping rank cannot choose randomness.
                    for budget in budgets:
                        rng = random.Random(config["selection_seed"])
                        env = BlindEnvironment(initial, mapping, budget)
                        for _ in range(budget):
                            if not env.view.legal_actions():
                                break
                            env.query(choose_query(env.view, policy, rng))
                        row = {
                            "table_id": table.table_id,
                            "group_id": table.group_id,
                            "context": context,
                            "mapping_rank_private": rank,
                            "policy": policy,
                            "budget": budget,
                            **env.score(decide(env.view)),
                        }
                        rows.append(row)
    grouped = defaultdict(list)
    for row in rows:
        grouped[f"{row['policy']}/budget={row['budget']}"].append(row)
    report = {
        "kind": "exhaustive_identity_permutations_with_program_policies",
        "split": split,
        "tables": len(tables),
        "research_sources": len({t.source_id for t in tables.values()}),
        "endpoints": {k: summarize(v) for k, v in grouped.items()},
        "table_audits": table_audits,
        "complete_information_upper_bound": {"accuracy": 1.0, "regret_pp": 0.0},
        "limitations": [
            "Exact noiseless lookup may make identity inference trivial.",
            "Myopic Bayes risk optimizes one observation, not the full horizon.",
            "Permutation episodes are not independent scientific samples.",
            "This is an identity task, not discovery of chemical mechanisms.",
        ],
        "scientific_conclusion": None,
    }
    new_run(out)
    write_jsonl(out / "scores.private.jsonl", rows)
    write_json(out / "summary.json", report)
    return report


def evaluate(
    dataset: Path,
    out: Path,
    split: str,
    backend: TextModel,
    variants: list[str],
    limit: int | None = None,
) -> dict:
    cases = load_cases(dataset, split)
    if limit is not None:
        if limit < 1:
            raise ValueError("Limit must be positive")
        cases = cases[:limit]  # deterministic development subset, never outcome-selected
    new_run(out, backend)
    rows, raw = [], []
    with (out / "responses.jsonl").open("x", encoding="utf-8") as stream:
        for case in cases:
            for variant in variants:
                p = present(case, variant)
                response = backend.complete(p.prompt)
                choice = parse_choice(response.text)
                row = {
                    "case_id": case.case_id,
                    "group_id": case.table.group_id,
                    "objective": case.objective,
                    "variant": variant,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    **score_choice(case, choice, p),
                }
                rows.append(row)
                record = {**row, "prompt": p.prompt, "output_text": response.text}
                stream.write(canonical(record) + "\n")
                stream.flush()
                raw.append(record)
    grouped = defaultdict(list)
    for row in rows:
        grouped[f"{row['objective']}/{row['variant']}"].append(row)
    paired = {}
    if "canonical" in variants:
        for objective in {c.objective for c in cases}:
            for variant in variants:
                if variant != "canonical":
                    paired[f"{objective}/{variant}"] = paired_group_difference(
                        grouped[f"{objective}/canonical"], grouped[f"{objective}/{variant}"]
                    )
    report = {
        "kind": "local_model_behavior",
        "split": split,
        "cases": len(cases),
        "endpoints": {k: summarize(v) for k, v in grouped.items()},
        "paired": paired,
        "dataset_freeze_sha256": digest(dataset / "freeze.json"),
        "scientific_conclusion": None,
    }
    write_json(out / "summary.json", report)
    return report
