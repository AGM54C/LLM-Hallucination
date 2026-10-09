"""Descriptive endpoints and paired group bootstrap; no automatic scientific verdict."""

from __future__ import annotations

import random
from collections import defaultdict
from statistics import fmean


def summarize(rows: list[dict]) -> dict:
    valid = [r for r in rows if r.get("valid", True)]
    return {
        "attempted": len(rows),
        "valid": len(valid),
        "invalid": len(rows) - len(valid),
        "conditional_accuracy": fmean(float(r["correct"]) for r in valid) if valid else None,
        "all_attempt_accuracy": sum(bool(r.get("correct")) for r in rows) / len(rows)
        if rows
        else None,
        "mean_regret_pp_valid": fmean(r["regret_pp"] for r in valid) if valid else None,
    }


def paired_group_difference(
    left: list[dict],
    right: list[dict],
    metric: str = "correct",
    seed: int = 20261006,
    samples: int = 2000,
) -> dict:
    """Equal-weight additive groups; conditional complete pairs and missingness reported.

    These groups share a study and plates. The interval is a within-study
    resampling diagnostic, not an independent-source population confidence claim.
    """
    if type(samples) is not int or samples < 1:
        raise ValueError("Bootstrap samples must be positive")

    def index(rows):
        result = {}
        for row in rows:
            key = row["case_id"]
            if key in result:
                raise ValueError(
                    "Duplicate case in paired comparison; separate seeds/variants first"
                )
            result[key] = row
        return result

    a, b = index(left), index(right)
    grouped = defaultdict(list)
    for key in sorted(a.keys() & b.keys()):
        if a[key]["group_id"] != b[key]["group_id"]:
            raise ValueError("Pair group mismatch")
        if a[key].get("valid", True) and b[key].get("valid", True):
            if a[key][metric] is not None and b[key][metric] is not None:
                grouped[a[key]["group_id"]].append(float(b[key][metric]) - float(a[key][metric]))
    differences = [fmean(v) for _, v in sorted(grouped.items())]
    result = {
        "direction": "right minus left",
        "metric": metric,
        "complete_pairs": sum(map(len, grouped.values())),
        "groups": len(grouped),
        "unpaired_or_invalid": len(a.keys() | b.keys()) - sum(map(len, grouped.values())),
        "mean_difference": fmean(differences) if differences else None,
        "within_study_group_bootstrap_95": None,
        "limitation": "Shared study/plate dependence remains; no cross-source inference.",
    }
    if len(differences) >= 2:
        rng = random.Random(seed)
        boot = sorted(fmean(rng.choices(differences, k=len(differences))) for _ in range(samples))
        result["within_study_group_bootstrap_95"] = [
            boot[int(0.025 * (samples - 1))],
            boot[int(0.975 * (samples - 1))],
        ]
    return result
