"""Descriptive paired analysis; repetitions are not independent study samples."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from itertools import combinations
from statistics import fmean

from evidence_lab_v2.diagnostics import endpoint

from .factorial import VERSION

LIMITATIONS = [
    "Development hypothesis proposed after V3; this is not an independent confirmation.",
    "One source, four study groups, related base/uniform checkpoints; no pseudo-independent p-values.",
    "Max/min and all factorial cells repeat the same table/target blocks.",
    "Primary decision metrics include all assigned attempts; compliance and invalidity are separate.",
    "Correct-value and compliant subsets are post-treatment descriptive subsets, not causal estimates.",
    "Two output orders test early/late halves, not all 24 permutations or every position effect.",
    "Alias changes hold chemical header/record order fixed; option identity remains confounded with those positions.",
    "Matching a candidate rule does not identify an internal algorithm.",
    "V4 adds an explicit inner-key-order instruction; V3 historical contrasts include that prompt change.",
    "No new training or inference about chemical causality; program comparison remains a strong baseline.",
]


def metrics(rows):
    result = {
        "attempts": len(rows),
        "endpoints": {
            name: endpoint([r["evaluation"]["scores"][name] for r in rows])
            for name in ("decision", "values", "program_decision")
        },
    }
    for name in (
        "compliant",
        "outer_order_compliant",
        "output_order_compliant",
        "clean_value_eligible",
        "clean_value_choice_error",
    ):
        result[name] = sum(r["evaluation"][name] is True for r in rows)
    eligible = [r for r in rows if r["evaluation"]["clean_value_eligible"]]
    compliant = [r for r in eligible if r["evaluation"]["compliant"]]
    result["clean_value_invalid_choice"] = sum(
        not r["evaluation"]["scores"]["decision"]["valid"] for r in eligible
    )
    result["clean_error_rate_all_attempts"] = result["clean_value_choice_error"] / len(rows)
    result["clean_error_rate_given_values"] = (
        result["clean_value_choice_error"] / len(eligible) if eligible else None
    )
    result["clean_and_compliant_attempts"] = len(compliant)
    result["clean_and_compliant_errors"] = sum(
        r["evaluation"]["clean_value_choice_error"] for r in compliant
    )
    result["requested_order_distribution"] = dict(Counter(r["output_order"] for r in rows))
    result["actual_order_distribution"] = dict(
        Counter("/".join(r["evaluation"]["actual_output_order"]) for r in rows)
    )
    for subset_name, subset in (
        ("all", rows),
        ("clean_errors", [r for r in rows if r["evaluation"]["clean_value_choice_error"]]),
    ):
        result[subset_name + "_choices"] = {
            field: dict(Counter(str(r["evaluation"][field]) for r in subset))
            for field in ("choice", "chosen_option", "chosen_emitted_position")
        }
        result[subset_name + "_candidate_matches"] = {
            rule: {
                "eligible": sum(
                    r["evaluation"]["candidate_matches"][rule] is not None for r in subset
                ),
                "matches": sum(r["evaluation"]["candidate_matches"][rule] is True for r in subset),
            }
            for rule in ("last_two_emitted", "fixed_letters_cd", "original_cd_options")
        }
    # Disjoint predictions provide more information than raw agreement with an
    # often-correct rule. Keep both the full clean cohort and the error subset.
    disagreements = {}
    for left, right in combinations(
        ("last_two_emitted", "fixed_letters_cd", "original_cd_options"), 2
    ):
        counts = Counter(
            {
                k: 0
                for k in (
                    "eligible",
                    "matches_left",
                    "matches_right",
                    "matches_neither",
                    "errors",
                    "errors_matching_left",
                    "errors_matching_right",
                )
            }
        )
        for row in compliant:
            evaluation = row["evaluation"]
            predictions = evaluation["candidate_predictions_from_emitted_values"]
            a, b = set(predictions[left]), set(predictions[right])
            if not a or not b or not a.isdisjoint(b):
                continue
            choice = evaluation["choice"]
            wrong = evaluation["clean_value_choice_error"]
            counts["eligible"] += 1
            counts["matches_left"] += choice in a
            counts["matches_right"] += choice in b
            counts["matches_neither"] += choice not in a | b
            counts["errors"] += wrong
            counts["errors_matching_left"] += wrong and choice in a
            counts["errors_matching_right"] += wrong and choice in b
        disagreements[left + "_vs_" + right] = dict(counts)
    result["disjoint_rule_predictions_clean_compliant"] = disagreements
    result["cost"] = {
        "new_calls": len(rows),
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "generation_seconds": sum(r["elapsed_seconds"] for r in rows),
        "max_output_tokens_observed": max(r["output_tokens"] for r in rows),
        "hit_generation_budget": sum(r["hit_generation_budget"] for r in rows),
    }
    return result


def paired_statistics(pairs):
    counts = Counter(
        {
            k: 0
            for k in (
                "pairs",
                "fixed",
                "new_errors",
                "both_wrong",
                "both_correct",
                "valid_both",
                "same_semantic_choice",
                "same_letter_choice",
                "clean_compliant_both",
                "clean_compliant_fixed",
                "clean_compliant_new_errors",
            )
        }
    )
    differences = []
    for before, after in pairs:
        a, b = before["scores"]["decision"], after["scores"]["decision"]
        ac, bc = a["correct"] is True, b["correct"] is True
        counts["pairs"] += 1
        counts["fixed"] += not ac and bc
        counts["new_errors"] += ac and not bc
        counts["both_wrong"] += not ac and not bc
        counts["both_correct"] += ac and bc
        if a["valid"] and b["valid"]:
            counts["valid_both"] += 1
            counts["same_semantic_choice"] += before["chosen_option"] == after["chosen_option"]
            counts["same_letter_choice"] += before["choice"] == after["choice"]
            differences.append(b["regret_pp"] - a["regret_pp"])
        if all(r["clean_value_eligible"] and r["compliant"] for r in (before, after)):
            counts["clean_compliant_both"] += 1
            counts["clean_compliant_fixed"] += not ac and bc
            counts["clean_compliant_new_errors"] += ac and not bc
    return {
        **counts,
        "accuracy_delta_pp": 100 * (counts["fixed"] - counts["new_errors"]) / counts["pairs"],
        "mean_regret_delta_pp_valid_pairs": fmean(differences) if differences else None,
    }


def summarize(rows, protocol):
    cells, groups = defaultdict(list), defaultdict(list)
    pivot = {}
    for row in rows:
        label = (
            f"{row['objective']}/{row['variant']}/"
            f"alias={row['alias_rotation']}/order={row['output_order']}"
        )
        cells[label].append(row)
        groups[label + "/group=" + row["group_id"]].append(row)
        key = (row["case_id"], row["variant"], row["alias_rotation"], row["output_order"])
        if key in pivot:
            raise ValueError("Duplicate factorial response")
        pivot[key] = row
    contrasts = defaultdict(list)
    for row in rows:
        candidates = []
        if row["output_order"] != "ABCD":
            candidates.append(("output_order", row["alias_rotation"], "ABCD"))
        if row["alias_rotation"] != 0:
            candidates.append(("alias_mapping", 0, row["output_order"]))
        for factor, rotation, order in candidates:
            baseline = pivot[(row["case_id"], row["variant"], rotation, order)]
            label = (
                f"{factor}/{row['objective']}/{row['variant']}/"
                f"{rotation}:{order}_to_{row['alias_rotation']}:{row['output_order']}"
            )
            pair = (baseline["evaluation"], row["evaluation"])
            contrasts[label + "/all"].append(pair)
            contrasts[label + "/group=" + row["group_id"]].append(pair)
        if row["alias_rotation"] == 0 and row["output_order"] == "ABCD":
            label = f"V3_historical_prompt_bridge/{row['objective']}/{row['variant']}"
            pair = (row["reference_evaluation"], row["evaluation"])
            contrasts[label + "/all"].append(pair)
            contrasts[label + "/group=" + row["group_id"]].append(pair)
    old_errors = [r for r in rows if r["reference_evaluation"]["clean_value_choice_error"]]
    return {
        "schema": VERSION,
        "requests": len(rows),
        "cases": len({r["case_id"] for r in rows}),
        "table_target_blocks": len({(r["table_id"], r["target_context"]) for r in rows}),
        "groups": len({r["group_id"] for r in rows}),
        "protocol": protocol,
        "cells": {key: metrics(value) for key, value in sorted(cells.items())},
        "by_group": {key: metrics(value) for key, value in sorted(groups.items())},
        "paired_contrasts": {
            key: paired_statistics(value) for key, value in sorted(contrasts.items())
        },
        "all_assignments": metrics(rows),
        "v3_error_cohort_secondary_only": metrics(old_errors) if old_errors else None,
        "limitations": LIMITATIONS,
        "scientific_conclusion": None,
    }


def write_tables(out, summary, rows):
    pairs = [{"contrast": key, **value} for key, value in summary["paired_contrasts"].items()]
    with (out / "paired_contrasts.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)
    columns = [
        "request_id",
        "case_id",
        "group_id",
        "table_id",
        "target_context",
        "objective",
        "variant",
        "alias_rotation",
        "output_order",
        "actual_output_order",
        "choice",
        "chosen_option",
        "chosen_emitted_position",
        "values_correct",
        "rank_preserved",
        "correct",
        "regret_pp",
        "clean_value_choice_error",
        "compliant",
        "v3_clean_error",
    ]
    with (out / "errors.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            evaluation = row["evaluation"]
            score = evaluation["scores"]["decision"]
            if score["correct"] is True and evaluation["compliant"]:
                continue
            entry = {key: row[key] for key in columns if key in row}
            for key in (
                "choice",
                "chosen_option",
                "chosen_emitted_position",
                "clean_value_choice_error",
                "compliant",
            ):
                entry[key] = evaluation[key]
            entry.update(
                {
                    "actual_output_order": "/".join(evaluation["actual_output_order"]),
                    "values_correct": evaluation["scores"]["values"]["correct"],
                    "rank_preserved": evaluation["optimum_set_preserved"],
                    "correct": score["correct"],
                    "regret_pp": score["regret_pp"],
                    "v3_clean_error": row["reference_evaluation"]["clean_value_choice_error"],
                }
            )
            writer.writerow(entry)
