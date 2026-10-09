"""Behavioral decomposition: value retrieval, relation retrieval and decision."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from .models import TextModel, parse_choice
from .storage import write_json, write_jsonl
from .tasks import present, score_choice
from .workflows import load_cases, new_run


def score_values(text: str, expected: dict[str, float], tolerance: float = 0.0005) -> dict:
    try:
        parsed = json.loads(text)
        if (
            not isinstance(parsed, dict)
            or set(parsed) != {"values"}
            or not isinstance(parsed["values"], dict)
        ):
            raise ValueError("Expected exactly one values dictionary")
        values = parsed["values"]
        if set(values) != set(expected) or any(
            type(v) not in (float, int) or not math.isfinite(v) for v in values.values()
        ):
            raise ValueError("Missing/non-numeric/non-finite fields")
    except (ValueError, TypeError):
        return {"valid": False, "correct": None}
    return {
        "valid": True,
        "correct": all(abs(values[k] - expected[k]) <= tolerance for k in expected),
    }


def run_readouts(
    dataset: Path, out: Path, backend: TextModel, variants: list[str], limit: int
) -> dict:
    if limit < 1:
        raise ValueError("Readout pilot limit must be positive")
    cases = [c for c in load_cases(dataset, "validation") if c.objective == "conditional_max"][
        :limit
    ]
    new_run(out, backend)
    rows, requests = [], []
    for case in cases:
        record_labels = {r.record_id: f"R{i:02d}" for i, r in enumerate(case.table.records)}
        target_rows = [r for r in case.table.records if r.context == case.target_context]
        for variant in variants:
            p = present(case, variant)
            labels = dict(p.aliases)
            expected_values = {record_labels[r.record_id]: r.value for r in target_rows}
            expected_relations = {labels[r.option]: r.value for r in target_rows}
            prompts = {
                "value": p.prefix
                + "\nCopy the recorded yields of records "
                + ", ".join(expected_values)
                + '. Return only {"values":{"record_label":number,...}} with at least four decimal places.',
                "relation": p.prefix
                + f"\nFor substrate {case.target_context}, report each option's recorded yield. "
                + 'Return only {"values":{"option_alias":number,...}} with at least four decimal places.',
                "decision": p.prompt,
            }
            scores = {}
            for kind, prompt in prompts.items():
                completion = backend.complete(prompt)
                result = (
                    score_choice(case, parse_choice(completion.text), p)
                    if kind == "decision"
                    else score_values(
                        completion.text, expected_values if kind == "value" else expected_relations
                    )
                )
                scores[kind] = result
                requests.append(
                    {
                        "case_id": case.case_id,
                        "variant": variant,
                        "kind": kind,
                        "prompt": prompt,
                        "response": completion.text,
                        "input_tokens": completion.input_tokens,
                        "output_tokens": completion.output_tokens,
                    }
                )
            rows.append(
                {
                    "case_id": case.case_id,
                    "group_id": case.table.group_id,
                    "variant": variant,
                    "scores": scores,
                }
            )
    patterns = Counter()
    for row in rows:
        patterns[
            "/".join(
                f"{kind}={score['correct'] if score['valid'] else 'invalid'}"
                for kind, score in row["scores"].items()
            )
        ] += 1
    write_jsonl(out / "responses.jsonl", requests)
    write_jsonl(out / "scores.jsonl", rows)
    report = {
        "kind": "behavioral_readout_decomposition",
        "cases": len(cases),
        "value_tolerance_pp": 0.0005,
        "patterns": dict(patterns),
        "limits": "Explicit readouts are observable behavior, not hidden-state decodability or causal mechanism proof.",
        "scientific_conclusion": None,
    }
    write_json(out / "summary.json", report)
    return report
