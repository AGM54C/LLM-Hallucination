"""Bounded model interaction through public blind-sample observations only."""

from __future__ import annotations

import json
import random
from pathlib import Path

from .analysis import summarize
from .blinding import BlindEnvironment, public_reference
from .models import TextModel
from .storage import canonical, write_json, write_jsonl
from .workflows import load_cases, new_run


def run_episode(env: BlindEnvironment, backend: TextModel, budget: int) -> dict:
    transcript = []
    for turn in range(budget + 1):
        view = env.view
        remaining = budget - len(view.observations)
        prompt = (
            "The public reference table lists measured yields by original option and substrate. "
            "A uniformly sampled hidden bijection maps blind aliases to original options. "
            "Choose the blind alias with the highest recorded yield in the target context. "
            "You may query a blind alias at any listed context; each query returns its exact recorded yield. "
            'Return exactly {"query":{"sample":"A","context":"name"}} or {"choice":"A"}. '
            f"Remaining queries: {remaining}. When zero, return a choice.\n"
            + canonical(view.payload())
        )
        completion = backend.complete(prompt)
        transcript.append(
            {
                "turn": turn,
                "prompt": prompt,
                "text": completion.text,
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
            }
        )
        try:
            response = json.loads(completion.text)
            if not isinstance(response, dict):
                raise ValueError("Expected one JSON object")
            if set(response) == {"choice"}:
                label = response["choice"]
                if not isinstance(label, str) or label not in list(
                    "ABCDEF"[: len(view.option_names)]
                ):
                    raise ValueError("Unknown choice")
                return {"valid": True, **env.score("ABCDEF".index(label)), "transcript": transcript}
            if set(response) != {"query"} or not isinstance(response["query"], dict):
                raise ValueError("Expected query or choice")
            query = response["query"]
            if set(query) != {"sample", "context"} or not isinstance(query["sample"], str):
                raise ValueError("Malformed query")
            if query["sample"] not in list("ABCDEF"[: len(view.option_names)]):
                raise ValueError("Unknown query alias")
            if not isinstance(query["context"], str) or query["context"] not in view.contexts:
                raise ValueError("Unknown context")
            env.query(("ABCDEF".index(query["sample"]), view.contexts.index(query["context"])))
        except (ValueError, TypeError, KeyError) as exc:
            return {
                "valid": False,
                "correct": None,
                "regret_pp": None,
                "queries": len(env.view.observations),
                "protocol_error": str(exc),
                "transcript": transcript,
            }
    raise RuntimeError("A bounded episode must finish with a choice or a protocol failure")


def evaluate_blind(
    dataset: Path, out: Path, backend: TextModel, budget: int, episodes: int, seed: int, split: str
) -> dict:
    if not 0 <= budget <= 60 or episodes < 1:
        raise ValueError("Invalid bounded episode configuration")
    cases = [c for c in load_cases(dataset, split) if c.objective == "conditional_max"]
    rng = random.Random(seed)
    chosen = list(cases)
    rng.shuffle(chosen)
    if episodes > len(chosen):
        raise ValueError(
            "Requested more episodes than eligible contexts; explicitly design repeats separately"
        )
    new_run(out, backend)
    rows = []
    for index, case in enumerate(chosen[:episodes]):
        mapping = list(range(len(case.table.options)))
        rng.shuffle(mapping)
        env = BlindEnvironment(
            public_reference(case.table, case.target_context), tuple(mapping), budget
        )
        result = run_episode(env, backend, budget)
        transcript = result.pop("transcript")
        row = {"case_id": case.case_id, "group_id": case.table.group_id, "budget": budget, **result}
        rows.append(row)
        write_json(
            out / "private" / f"episode-{index:04d}.json",
            {
                "mapping": mapping,
                "row": row,
                "transcript": transcript,
            },
        )
    write_jsonl(out / "scores.jsonl", rows)
    report = {
        "kind": "local_model_blind_interaction",
        "split": split,
        "seed_private": seed,
        "summary": summarize(rows),
        "scientific_conclusion": None,
    }
    write_json(out / "summary.json", report)
    return report
