"""Read-only adapter for the previously audited Ahneman/Doyle data.

Grouping and completeness rules follow audit_available_data.py and
audit_scope_contrasts.py. Those scripts have write-on-import side effects, so
the reusable extraction is isolated here instead of importing their entrypoints.
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from .domain import DecisionCase, ExperimentTable, Measurement
from .storage import digest, stable_id

SOURCE = "10.1126/science.aar5169"


def load_chemistry(
    path: Path, expected_sha256: str | None = None
) -> tuple[list[ExperimentTable], dict]:
    before = digest(path)
    if expected_sha256 and before != expected_sha256:
        raise ValueError("Source checksum differs from the declared audited dataset")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Empty chemistry dataset")
    cells, identities, wells = set(), set(), set()
    groups: dict[tuple, list[Measurement]] = defaultdict(list)
    for row in rows:
        key = (row["plate"], row["base"], row["additive"])
        cell = (*key, row["ligand"], row["aryl_halide"])
        well = (row["plate"], row["row"], row["col"])
        if cell in cells or row["condition_id"] in identities or well in wells:
            raise ValueError("Duplicate cell, identity or physical well in audited input")
        cells.add(cell)
        identities.add(row["condition_id"])
        wells.add(well)
        groups[key].append(
            Measurement(
                row["condition_id"],
                row["ligand"],
                row["aryl_halide"],
                float(row["yield"]),
                int(row["source_raw_csv_row"]),
            )
        )
    options = {r["ligand"] for r in rows}
    contexts = {r["aryl_halide"] for r in rows}
    tables, excluded = [], []
    for key, records in sorted(groups.items()):
        if {(r.option, r.context) for r in records} != {(o, c) for o in options for c in contexts}:
            excluded.append({"conditions": key, "record_count": len(records)})
            continue
        tables.append(
            ExperimentTable(
                stable_id(SOURCE, key),
                SOURCE,
                stable_id(SOURCE, key[0], key[2]),  # all bases for an additive stay together
                tuple(zip(("plate", "base", "additive"), key)),
                tuple(sorted(records, key=lambda r: (r.context, r.option))),
            )
        )
    if not tables:
        raise ValueError("No complete observed factorial blocks")
    if digest(path) != before:
        raise ValueError("Source changed while reading")
    return tables, {
        "source_id": SOURCE,
        "source_sha256": before,
        "input_rows": len(rows),
        "complete_tables": len(tables),
        "included_rows": sum(len(t.records) for t in tables),
        "split_groups": len({t.group_id for t in tables}),
        "excluded_incomplete_groups": excluded,
        "independent_research_sources": 1,
        "limits": [
            "Record comparisons are not causal effects or independent replicates.",
            "Additive-group holdout is within-study; plates are shared across splits.",
            "No missing results are filled or measurement noise invented.",
        ],
    }


def split_tables(
    tables: list[ExperimentTable], seed: int, validation_fraction: float, test_fraction: float
) -> dict[str, str]:
    if not 0 < validation_fraction < 1 or not 0 < test_fraction < 1:
        raise ValueError("Validation and test fractions must be strictly between zero and one")
    if validation_fraction + test_fraction >= 1:
        raise ValueError("Training fraction must be positive")
    groups = sorted({t.group_id for t in tables})
    random.Random(seed).shuffle(groups)  # identities only; never stratify on test outcomes
    n_val, n_test = (
        max(1, round(len(groups) * validation_fraction)),
        max(1, round(len(groups) * test_fraction)),
    )
    if n_val + n_test >= len(groups):
        raise ValueError("Not enough groups for three disjoint splits")
    result = {}
    for i, group in enumerate(groups):
        result[group] = "validation" if i < n_val else "test" if i < n_val + n_test else "train"
    return result


def make_cases(tables: list[ExperimentTable], splits: dict[str, str]) -> list[DecisionCase]:
    return [
        DecisionCase(stable_id(t.table_id, c, objective), t, splits[t.group_id], c, objective)
        for t in tables
        for c in t.contexts
        for objective in ("conditional_max", "conditional_min")
    ]


def case_to_dict(case: DecisionCase) -> dict:
    return asdict(case)


def case_from_dict(row: dict) -> DecisionCase:
    t = row["table"]
    table = ExperimentTable(
        t["table_id"],
        t["source_id"],
        t["group_id"],
        tuple(tuple(x) for x in t["conditions"]),
        tuple(Measurement(**r) for r in t["records"]),
    )
    return DecisionCase(
        row["case_id"], table, row["split"], row["target_context"], row["objective"]
    )
