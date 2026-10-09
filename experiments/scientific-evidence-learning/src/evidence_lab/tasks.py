"""Evidence presentation, explicit shortcut rules and objective scoring.

Gold labels and rule diagnostics are never included in model requests. Alias
permutations rename entire option identities, never reassign chemical outcomes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import fmean

from .domain import DecisionCase
from .storage import stable_id

DEVELOPMENT_RULES = ("pooled_max", "first_context")
HELD_OUT_RULES = ("last_context", "largest_single_record")


def utilities(case: DecisionCase) -> dict[str, float]:
    values = {}
    for option in case.table.options:
        records = [
            r
            for r in case.table.records
            if r.option == option
            and (case.objective == "pooled_max" or r.context == case.target_context)
        ]
        values[option] = fmean(r.value for r in records) * (
            -1 if case.objective == "conditional_min" else 1
        )
    return values


def winners(values: dict[str, float], tolerance: float = 1e-9) -> tuple[str, ...]:
    best = max(values.values())
    return tuple(sorted(k for k, v in values.items() if abs(v - best) <= tolerance))


def rule_choice(case: DecisionCase, rule: str) -> str:
    if rule == "scoped":
        return winners(utilities(case))[0]
    values = {}
    for option in case.table.options:
        rows = [r for r in case.table.records if r.option == option]
        if rule == "pooled_max":
            value = fmean(r.value for r in rows)
        elif rule == "largest_single_record":
            value = max(r.value for r in rows)
        elif rule in {"first_context", "last_context"}:
            context = case.table.contexts[0 if rule == "first_context" else -1]
            value = next(r.value for r in rows if r.context == context)
        else:
            raise ValueError(f"Unknown baseline rule: {rule}")
        values[option] = value
    return winners(values)[0]


def diagnostics(case: DecisionCase) -> dict:
    scores = utilities(case)
    gold = winners(scores)
    ordered = sorted(scores.values(), reverse=True)
    return {
        "gold": list(gold),
        "margin": ordered[0] - ordered[1],
        "rule_rejected": {
            name: rule_choice(case, name) not in gold
            for name in (*DEVELOPMENT_RULES, *HELD_OUT_RULES)
        },
    }


@dataclass(frozen=True)
class Presentation:
    prefix: str
    question: str
    aliases: tuple[tuple[str, str], ...]  # public name/alias association in ordinary tasks
    record_spans: tuple[tuple[str, int, int], ...]

    @property
    def prompt(self) -> str:
        return self.prefix + self.question


def present(case: DecisionCase, variant: str = "canonical", seed: int = 0) -> Presentation:
    if variant not in {"canonical", "reversed", "shuffled", "structured", "checklist"}:
        raise ValueError("Unknown presentation")
    rng = random.Random(int(stable_id(case.table.table_id, seed), 16))
    options = list(case.table.options)
    rng.shuffle(options)
    aliases = tuple(zip(options, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(options)]))
    labels = dict(aliases)
    rows = list(case.table.records)
    if variant == "reversed":
        rows.reverse()
    elif variant == "shuffled":
        rng.shuffle(rows)
    prefix = (
        "These are historical measured records, not simulated reactions. Values are recorded "
        "yields in percent; comparisons refer only to this finite table.\n"
    )
    prefix += "Fixed conditions: " + "; ".join(f"{k}={v}" for k, v in case.table.conditions) + "\n"
    prefix += "Options: " + "; ".join(f"{label}={name}" for name, label in aliases) + "\n"
    spans = []
    record_labels = {r.record_id: f"R{i:02d}" for i, r in enumerate(case.table.records)}
    for r in rows:
        line = (
            f"context={r.context} | option={labels[r.option]} | yield={r.value!r}\n"
            if variant == "structured"
            else f"With substrate {r.context}, option {labels[r.option]} has recorded yield {r.value!r}.\n"
        )
        line = record_labels[r.record_id] + ": " + line
        start = len(prefix)
        prefix += line
        spans.append((r.record_id, start, len(prefix)))
    question = "\n"
    if variant == "checklist":
        question += "Check the requested scope and comparison direction before deciding.\n"
    if case.objective == "pooled_max":
        question += (
            "Select the option with the highest equally weighted mean over all listed substrates."
        )
    else:
        direction = "highest" if case.objective == "conditional_max" else "lowest"
        question += f"For substrate {case.target_context}, select the option with the {direction} recorded yield."
    question += '\nReturn only a JSON object of the form {"choice":"A"}.\n'
    return Presentation(prefix, question, aliases, tuple(spans))


def score_choice(case: DecisionCase, choice: str | None, presentation: Presentation) -> dict:
    reverse = {label: name for name, label in presentation.aliases}
    if choice not in reverse:
        return {"valid": False, "correct": None, "regret_pp": None}
    scores = utilities(case)
    option = reverse[choice]
    return {
        "valid": True,
        "correct": option in winners(scores),
        "regret_pp": max(scores.values()) - scores[option],
    }
