"""Paired context effects and complete two-call workflow accounting."""

import csv
from collections import Counter, defaultdict
from statistics import fmean

from evidence_lab_v2.diagnostics import endpoint

LIMITATIONS = [
    "Development after inspecting V4, on one source and four groups; no independent confirmation.",
    "Alias/order cells and max/min reuse the same 165 table/target blocks.",
    "The two checkpoints are related, not independent replications.",
    "The primary intervention is table context present versus absent in two NEW comparison requests.",
    "V4 joint versus V5 comparisons also change the prompt, request boundary, and provenance of the numbers.",
    "Improvement over V4 does not isolate an internal mechanism or establish the original direct trajectory's knowledge.",
    "V4 values and their exact JSON number literals are preserved, including incorrect numbers; no gold repair.",
    "Invalid V4 values cause logged upstream failures; they are not discarded from workflow accuracy.",
    "Correct-source and previous-error cohorts are secondary, fixed before V5, and not independent datasets.",
    "Program comparison uses the same model readout and remains the strong numerical baseline.",
    "No new training, test-set evaluation, causal chemistry claim, or pseudo-independent p-values.",
]


def metrics(rows):
    executed = [r for r in rows if r["executed"]]
    clean = [r for r in rows if r["source_clean_value_eligible"]]
    old_errors = [r for r in rows if r["source_clean_value_choice_error"]]
    return {
        "attempts": len(rows),
        "executed": len(executed),
        "upstream_failures": len(rows) - len(executed),
        "decision": endpoint([r["scores"]["decision"] for r in rows]),
        "comparison_of_supplied_values": endpoint([r["scores"]["comparison"] for r in rows]),
        "source_joint_decision": endpoint([r["source_scores"]["decision"] for r in rows]),
        "source_program_decision": endpoint([r["source_scores"]["program_decision"] for r in rows]),
        "invalid_generated_choices": sum(not r["scores"]["decision"]["valid"] for r in executed),
        "clean_source_eligible": len(clean),
        "clean_source_wrong_choice": sum(
            r["scores"]["decision"]["correct"] is False for r in clean
        ),
        "clean_source_invalid_choice": sum(not r["scores"]["decision"]["valid"] for r in clean),
        "previous_clean_errors_secondary": len(old_errors),
        "previous_clean_errors_now_correct": sum(
            r["scores"]["decision"]["correct"] is True for r in old_errors
        ),
        "new_errors_from_previously_correct": sum(
            r["source_scores"]["decision"]["correct"] is True
            and r["scores"]["decision"]["correct"] is not True
            for r in rows
        ),
        "cost": {
            "new_calls": len(executed),
            "new_input_tokens": sum(r["input_tokens"] for r in rows),
            "new_output_tokens": sum(r["output_tokens"] for r in rows),
            "new_generation_seconds": sum(r["elapsed_seconds"] for r in rows),
            "max_output_tokens_observed": max((r["output_tokens"] for r in rows), default=0),
            "budget_hits": sum(r["hit_generation_budget"] for r in rows),
            "upstream_calls_per_standalone_workflow_total": len(rows),
            "upstream_input_tokens_per_standalone_workflow_total": sum(
                r["source_input_tokens"] for r in rows
            ),
            "upstream_output_tokens_per_standalone_workflow_total": sum(
                r["source_output_tokens"] for r in rows
            ),
        },
    }


def paired_statistics(pairs):
    counts = Counter(
        {
            key: 0
            for key in [
                "pairs",
                "fixed",
                "new_errors",
                "both_correct",
                "both_wrong",
                "valid_both",
                "same_choice",
                "source_values_correct_pairs",
                "source_values_correct_fixed",
                "source_values_correct_new_errors",
            ]
        }
    )
    changes = []
    for before, after in pairs:
        a, b = before["scores"]["decision"], after["scores"]["decision"]
        ac, bc = a["correct"] is True, b["correct"] is True
        counts["pairs"] += 1
        counts["fixed"] += not ac and bc
        counts["new_errors"] += ac and not bc
        counts["both_correct"] += ac and bc
        counts["both_wrong"] += not ac and not bc
        if a["valid"] and b["valid"]:
            counts["valid_both"] += 1
            counts["same_choice"] += before["choice"] == after["choice"]
            changes.append(b["regret_pp"] - a["regret_pp"])
        if after["source_clean_value_eligible"]:
            counts["source_values_correct_pairs"] += 1
            counts["source_values_correct_fixed"] += not ac and bc
            counts["source_values_correct_new_errors"] += ac and not bc
    return {
        **counts,
        "accuracy_delta_pp": 100 * (counts["fixed"] - counts["new_errors"]) / counts["pairs"],
        "regret_delta_pp_valid_pairs": fmean(changes) if changes else None,
    }


def summarize(rows, protocol):
    contexts, cells, groups, contrasts = (defaultdict(list) for _ in range(4))
    index = {(r["source_request_id"], r["context"]): r for r in rows}
    if len(index) != len(rows):
        raise ValueError("Duplicate V5 source/context rows")
    for row in rows:
        context = row["context"]
        contexts[context].append(row)
        label = f"{row['objective']}/alias={row['alias_rotation']}/order={row['output_order']}/{context}"
        cells[label].append(row)
        groups[f"{row['objective']}/{context}/group={row['group_id']}"].append(row)
        baseline = {
            "scores": row["source_scores"],
            "choice": row["source_choice"],
            "source_clean_value_eligible": row["source_clean_value_eligible"],
        }
        label = f"V4_joint_to_{context}/{row['objective']}"
        for suffix in ("all", "group=" + row["group_id"]):
            contrasts[label + "/" + suffix].append((baseline, row))
        if context == "numbers_only":
            before = index[(row["source_request_id"], "table_and_numbers")]
            label = "table_and_numbers_to_numbers_only/" + row["objective"]
            for suffix in ("all", "group=" + row["group_id"]):
                contrasts[label + "/" + suffix].append((before, row))
    return {
        "schema": "fixed-readout-context-v5",
        "protocol": protocol,
        "attempts": len(rows),
        "requests": sum(r["executed"] for r in rows),
        "cases": len({r["case_id"] for r in rows}),
        "table_target_blocks": len({(r["table_id"], r["target_context"]) for r in rows}),
        "groups": len({r["group_id"] for r in rows}),
        "by_context": {k: metrics(v) for k, v in sorted(contexts.items())},
        "cells": {k: metrics(v) for k, v in sorted(cells.items())},
        "by_group": {k: metrics(v) for k, v in sorted(groups.items())},
        "paired_contrasts": {k: paired_statistics(v) for k, v in sorted(contrasts.items())},
        "actual_experiment_cost": {
            "new_calls": sum(r["executed"] for r in rows),
            "new_input_tokens": sum(r["input_tokens"] for r in rows),
            "new_output_tokens": sum(r["output_tokens"] for r in rows),
            "new_generation_seconds": sum(r["elapsed_seconds"] for r in rows),
            "new_upstream_calls": 0,
        },
        "limitations": LIMITATIONS,
        "scientific_conclusion": None,
    }


def write_tables(out, summary, rows):
    contrasts = [{"contrast": k, **v} for k, v in summary["paired_contrasts"].items()]
    with (out / "paired_contrasts.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(contrasts[0]))
        writer.writeheader()
        writer.writerows(contrasts)
    fields = [
        "source_request_id",
        "case_id",
        "objective",
        "context",
        "alias_rotation",
        "output_order",
        "executed",
        "choice",
        "source_choice",
        "correct",
        "regret_pp",
        "comparison_correct",
        "source_clean_value_eligible",
        "source_clean_value_choice_error",
        "response",
    ]
    with (out / "errors.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            score = row["scores"]["decision"]
            if score["correct"] is True and row["scores"]["comparison"]["correct"] is True:
                continue
            record = {key: row[key] for key in fields if key in row}
            record.update(
                {
                    "correct": score["correct"],
                    "regret_pp": score["regret_pp"],
                    "comparison_correct": row["scores"]["comparison"]["correct"],
                }
            )
            writer.writerow(record)
