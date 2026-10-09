"""Synthetic fixtures ONLY for software tests; not experimental evidence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidence_lab.domain import DecisionCase, ExperimentTable, Measurement  # noqa: E402


def table():
    values = ((9.0, 1.0), (5.0, 8.0), (2.0, 3.0), (0.0, 2.0))
    records = tuple(
        Measurement(f"r{a}{c}", f"ligand{a}", f"context{c}", values[a][c], a * 2 + c + 2)
        for a in range(4)
        for c in range(2)
    )
    return ExperimentTable("fixture", "synthetic-test-only", "g1", (("plate", "test"),), records)


def case(objective="conditional_max", split="train"):
    return DecisionCase("case-" + objective, table(), split, "context0", objective)


PROJECT = Path(__file__).resolve().parents[1]
DATA = (
    PROJECT.parent
    / "chemical-materials-pilot-20261004/sources/chemistry/buchwald_hartwig_annotated.csv"
)
