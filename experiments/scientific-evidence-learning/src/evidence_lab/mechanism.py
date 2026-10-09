"""Development-only evidence-prefix patch experiment; never a mechanism verdict."""

from __future__ import annotations

import json
from pathlib import Path

from .interventions import capture_token, patch_token, token_for_span
from .models import HuggingFaceModel, render_prompt
from .storage import digest, write_json, write_jsonl
from .tasks import present, score_choice
from .workflows import load_cases, new_run


def run_interventions(
    dataset: Path,
    out: Path,
    backend: HuggingFaceModel,
    module_path: str,
    record_index: int,
    limit: int,
) -> dict:
    import torch

    if record_index < 0 or limit < 1:
        raise ValueError("record_index must be nonnegative and limit positive")
    cases = [c for c in load_cases(dataset, "validation") if c.objective == "conditional_max"][
        :limit
    ]
    module = backend.model.get_submodule(module_path)
    rows = []
    new_run(out, backend)
    write_json(
        out / "specification.json",
        {
            "stage": "development_only",
            "module_path": module_path,
            "record_index": record_index,
            "case_ids": [c.case_id for c in cases],
            "donor": "canonical evidence prefix WITHOUT final question",
            "recipient": "reversed records plus final question",
            "dataset_freeze_sha256": digest(dataset / "freeze.json"),
            "readout": "argmin mean completion-token NLL over explicit JSON choices, not free generation",
            "limitation": "Whole record-end residual patch; does not isolate a relation-only subspace.",
        },
    )
    for case in cases:
        donor, recipient = present(case, "canonical"), present(case, "reversed")
        if record_index >= len(donor.record_spans):
            raise ValueError("Record index outside evidence")
        record_id, start, end = donor.record_spans[record_index]
        prefix_rendered = render_prompt(
            backend.tokenizer,
            donor.prefix,
            backend.use_chat_template,
            backend.enable_thinking,
        )
        donor_position = token_for_span(
            backend.tokenizer, prefix_rendered, donor.prefix, (start, end)
        )
        recipient_span = next((a, b) for rid, a, b in recipient.record_spans if rid == record_id)
        recipient_rendered = render_prompt(
            backend.tokenizer,
            recipient.prompt,
            backend.use_chat_template,
            backend.enable_thinking,
        )
        recipient_position = token_for_span(
            backend.tokenizer, recipient_rendered, recipient.prefix, recipient_span
        )
        other = donor.record_spans[(record_index + 1) % len(donor.record_spans)]
        other_position = token_for_span(
            backend.tokenizer, prefix_rendered, donor.prefix, (other[1], other[2])
        )
        tokens = backend.tokenizer(
            prefix_rendered,
            add_special_tokens=False,
            return_tensors="pt",
            return_token_type_ids=False,
        ).to(backend.device)
        with (
            torch.inference_mode(),
            capture_token(module, donor_position) as captured,
            capture_token(module, other_position) as unrelated,
        ):
            backend.model(**tokens, use_cache=False)
        answers = [json.dumps({"choice": a}, separators=(",", ":")) for _, a in recipient.aliases]
        labels = [a for _, a in recipient.aliases]
        for name in (
            "canonical",
            "reversed",
            "identity",
            "norm_matched_rotation",
            "donor",
            "other_record_donor",
        ):
            p = donor if name == "canonical" else recipient
            if name in {"canonical", "reversed"}:
                losses = backend.answer_losses(p.prompt, answers)
            else:
                state = unrelated["state"] if name == "other_record_donor" else captured["state"]
                control = "donor" if name == "other_record_donor" else name
                with patch_token(module, recipient_position, state, control):
                    losses = backend.answer_losses(p.prompt, answers)
            choice = labels[min(range(len(losses)), key=losses.__getitem__)]
            rows.append(
                {
                    "case_id": case.case_id,
                    "group_id": case.table.group_id,
                    "condition": name,
                    "losses": dict(zip(labels, losses)),
                    "record_id": record_id,
                    "donor_token": donor_position,
                    "recipient_token": recipient_position,
                    **score_choice(case, choice, p),
                }
            )
    write_jsonl(out / "scores.jsonl", rows)
    report = {
        "cases": len(cases),
        "rows": len(rows),
        "scientific_conclusion": None,
        "stage": "development_intervention_feasibility",
        "selective_mechanism_established": False,
    }
    write_json(out / "summary.json", report)
    return report
