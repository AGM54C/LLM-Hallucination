"""Small causal intervention primitives using public PyTorch hooks.

Positions are selected from evidence-only prefixes. The experiment must freeze
module/record choices on development data. A whole-state patch does not identify
a unique semantic mechanism; controls and held-out confirmation are required.
"""

from __future__ import annotations

from contextlib import contextmanager


def hidden_tensor(output):
    value = output[0] if isinstance(output, tuple) else output
    if value.ndim != 3 or value.shape[0] != 1:
        raise ValueError("Interventions require [1, sequence, hidden] module outputs")
    return value


@contextmanager
def capture_token(module, position: int):
    captured = {}

    def hook(_module, _inputs, output):
        hidden = hidden_tensor(output)
        if not 0 <= position < hidden.shape[1]:
            raise ValueError("Capture position outside evidence prefix")
        captured["state"] = hidden[0, position].detach().clone()

    handle = module.register_forward_hook(hook)
    try:
        yield captured
    finally:
        handle.remove()


@contextmanager
def patch_token(module, position: int, donor, control: str = "donor"):
    if control not in {"donor", "norm_matched_rotation", "identity"}:
        raise ValueError("Unknown intervention control")

    def hook(_module, _inputs, output):
        hidden = hidden_tensor(output)
        if not 0 <= position < hidden.shape[1] or donor.shape != hidden[0, position].shape:
            raise ValueError("Patch position/dimension mismatch")
        replacement = donor.to(hidden.device, dtype=hidden.dtype)
        original = hidden[0, position]
        if control == "identity":
            replacement = original
        elif control == "norm_matched_rotation":
            replacement = original + (replacement - original).roll(1)
        updated = hidden.clone()
        updated[0, position] = replacement
        return (updated, *output[1:]) if isinstance(output, tuple) else updated

    handle = module.register_forward_hook(hook)
    try:
        yield
    finally:
        handle.remove()


def token_for_span(tokenizer, rendered: str, raw_prefix: str, span: tuple[int, int]) -> int:
    offset = rendered.find(raw_prefix)
    if offset < 0 or rendered.find(raw_prefix, offset + 1) >= 0:
        raise ValueError("Evidence prefix must occur exactly once in the rendered prompt")
    start, end = offset + span[0], offset + span[1]
    encoded = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    matches = [i for i, (a, b) in enumerate(encoded["offset_mapping"]) if a < end and b > start]
    if not matches:
        raise ValueError("No token overlaps selected evidence record")
    return matches[-1]
