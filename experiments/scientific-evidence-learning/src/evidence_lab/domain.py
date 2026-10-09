"""Immutable domain objects; no filesystem, model framework or runner dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Measurement:
    record_id: str
    option: str
    context: str
    value: float
    source_row: int

    def __post_init__(self) -> None:
        if not self.record_id or not self.option or not self.context or not isfinite(self.value):
            raise ValueError("Measurement requires named identities and a finite recorded value")
        if self.source_row < 2:
            raise ValueError("source_row counts the CSV header as row 1")


@dataclass(frozen=True)
class ExperimentTable:
    table_id: str
    source_id: str
    group_id: str
    conditions: tuple[tuple[str, str], ...]
    records: tuple[Measurement, ...]

    def __post_init__(self) -> None:
        if not self.records:
            raise ValueError("Empty experimental table")
        cells = {(r.option, r.context) for r in self.records}
        if len(cells) != len(self.records):
            raise ValueError("Duplicate condition cell; replicates require a separate data model")
        if len({r.record_id for r in self.records}) != len(self.records):
            raise ValueError("Duplicate record identity")
        if len(cells) != len(self.options) * len(self.contexts):
            raise ValueError("Only complete measured tables are supported; no imputation")

    @property
    def options(self) -> tuple[str, ...]:
        return tuple(sorted({r.option for r in self.records}))

    @property
    def contexts(self) -> tuple[str, ...]:
        return tuple(sorted({r.context for r in self.records}))


@dataclass(frozen=True)
class DecisionCase:
    case_id: str
    table: ExperimentTable
    split: str
    target_context: str
    objective: str = "conditional_max"

    def __post_init__(self) -> None:
        if self.split not in {"train", "validation", "test"}:
            raise ValueError("Unknown split")
        if self.target_context not in self.table.contexts:
            raise ValueError("Target must occur in the measured table")
        if self.objective not in {"conditional_max", "conditional_min", "pooled_max"}:
            raise ValueError("Unknown objective")
