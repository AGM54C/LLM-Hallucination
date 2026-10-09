"""Independent rendering factors, strict parsing, and semantic decision scoring.

The table's physical records, numeric facts, chemical option order in the header,
target, and objective stay fixed. Only aliases and requested output order change.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict, deque

from evidence_lab.storage import stable_id
from evidence_lab.tasks import Presentation, score_choice
from evidence_lab_v2.diagnostics import (
    TOLERANCE,
    _unique_object,
    choose_from_values,
    parse_values,
    select_cases,
)
from evidence_lab_v2.presentations import present_order
from evidence_lab_v3.controls import public_values

VERSION = "output-order-alias-v4"
ALIASES = "ABCD"
OBJECTIVES = ("conditional_max", "conditional_min")


def validate_protocol(protocol):
    expected = {
        "schema",
        "variants",
        "output_orders",
        "alias_rotations",
        "request_order_seed",
        "max_length",
        "max_new_tokens",
    }
    if set(protocol) != expected or protocol["schema"] != VERSION:
        raise ValueError("Unsupported V4 protocol schema/fields")
    for key in ("variants", "output_orders", "alias_rotations"):
        values = protocol[key]
        if not isinstance(values, list) or not values or len(set(values)) != len(values):
            raise ValueError("Protocol factors must be nonempty and unique: " + key)
    if set(protocol["variants"]) - {"canonical", "shuffled"}:
        raise ValueError("Unsupported table-order control")
    if any(not isinstance(s, str) or sorted(s) != list(ALIASES) for s in protocol["output_orders"]):
        raise ValueError("Each output order must be a permutation of ABCD")
    if "ABCD" not in protocol["output_orders"] or len(protocol["output_orders"]) < 2:
        raise ValueError("Include ABCD and at least one alternative output order")
    if any(type(n) is not int for n in protocol["alias_rotations"]):
        raise ValueError("Alias rotations must be integers")
    if set(protocol["alias_rotations"]) != {0, 1, 2, 3}:
        raise ValueError("All four alias rotations are required for balanced coverage")
    for key in ("request_order_seed", "max_length", "max_new_tokens"):
        if type(protocol[key]) is not int or protocol[key] < (0 if key.endswith("seed") else 1):
            raise ValueError("Invalid integer setting: " + key)
    if protocol["max_new_tokens"] >= protocol["max_length"]:
        raise ValueError("Generation budget must leave room for the prompt")
    return protocol


def select_paired_cases(dataset, limit_blocks=None):
    """Select table/target blocks, retaining both objectives; never select on errors."""
    if limit_blocks is not None and (type(limit_blocks) is not int or limit_blocks < 1):
        raise ValueError("limit-blocks must be positive")
    blocks = defaultdict(dict)
    for case in select_cases(dataset, list(OBJECTIVES)):
        key = (case.table.group_id, case.table.table_id, case.target_context)
        if case.objective in blocks[key]:
            raise ValueError("Duplicate table/target/objective in validation")
        blocks[key][case.objective] = case
    groups = defaultdict(list)
    for key, pair in blocks.items():
        if set(pair) != set(OBJECTIVES):
            raise ValueError("Each table/target block needs both max and min")
        groups[key[0]].append((stable_id("v4-case-order", *key), pair))
    queues = {g: deque(pair for _, pair in sorted(rows)) for g, rows in sorted(groups.items())}
    selected = []
    while queues and (limit_blocks is None or len(selected) // 2 < limit_blocks):
        for group in list(queues):
            pair = queues[group].popleft()
            selected.extend(pair[objective] for objective in OBJECTIVES)
            if not queues[group]:
                del queues[group]
            if limit_blocks is not None and len(selected) // 2 == limit_blocks:
                break
    return selected


def remap_presentation(case, variant, rotation):
    if type(rotation) is not int or rotation not in range(4):
        raise ValueError("Alias rotation must be 0, 1, 2 or 3")
    original = present_order(case, variant, 0)
    if sorted(alias for _, alias in original.aliases) != list(ALIASES):
        raise ValueError("V4 requires exactly four options")
    translate = {a: ALIASES[(i + rotation) % 4] for i, a in enumerate(ALIASES)}
    aliases = tuple((option, translate[alias]) for option, alias in original.aliases)
    old_alias, new_alias = dict(original.aliases), dict(aliases)
    old_header = "Options: " + "; ".join(f"{a}={o}" for o, a in original.aliases) + "\n"
    new_header = "Options: " + "; ".join(f"{a}={o}" for o, a in aliases) + "\n"
    prefix = original.prefix[: original.record_spans[0][1]]
    if prefix.count(old_header) != 1:
        raise ValueError("Unexpected public option header")
    prefix = prefix.replace(old_header, new_header, 1)
    records = {r.record_id: r for r in case.table.records}
    spans = []
    for rid, start, end in original.record_spans:
        option = records[rid].option
        chunk = original.prefix[start:end]
        token = f"option {old_alias[option]} has recorded yield"
        if chunk.count(token) != 1:
            raise ValueError("Unexpected record rendering")
        chunk = chunk.replace(token, f"option {new_alias[option]} has recorded yield", 1)
        start = len(prefix)
        prefix += chunk
        spans.append((rid, start, len(prefix)))
    return Presentation(prefix, original.question, aliases, tuple(spans))


def joint_prompt(case, presentation, order):
    if sorted(order) != list(ALIASES):
        raise ValueError("Invalid requested output order")
    direction = "highest" if case.objective == "conditional_max" else "lowest"
    skeleton = {"values": {alias: None for alias in order}, "choice": None}
    return (
        presentation.prefix
        + f"\nFor substrate {case.target_context}, first copy the recorded yield for each "
        "option alias, then select the option with the "
        + direction
        + " recorded yield. If values are exactly tied, choose any tied optimum.\n"
        "Return exactly one JSON object with keys values then choice, in that order. "
        "Inside values use this exact key order: " + ", ".join(order) + ". "
        "Include every option alias once, with a numeric yield and at least four decimal places. "
        "After values, set choice to the selected alias string. No prose or Markdown. "
        "Replace every null in this structure; null is not an answer: "
        + json.dumps(skeleton, separators=(",", ":"))
    )


def conditions_for(case, protocol):
    conditions = [
        {"variant": variant, "alias_rotation": rotation, "output_order": order}
        for variant in protocol["variants"]
        for rotation in protocol["alias_rotations"]
        for order in protocol["output_orders"]
    ]
    # All cells are measured; only execution order is shuffled. Max/min use the
    # same schedule for their shared block. No prior output enters another request.
    seed = stable_id(
        "v4-execution", case.table.table_id, case.target_context, protocol["request_order_seed"]
    )
    random.Random(int(seed, 16)).shuffle(conditions)
    return conditions


def request_identity(case, condition):
    return {
        "request_id": stable_id(VERSION, case.case_id, condition),
        "case_id": case.case_id,
        "table_id": case.table.table_id,
        "group_id": case.table.group_id,
        "target_context": case.target_context,
        "objective": case.objective,
        "order_seed": 0,
        **condition,
    }


def parse_joint(text, order):
    result = {
        "values": None,
        "choice": None,
        "actual_output_order": [],
        "outer_order_compliant": False,
        "output_order_compliant": False,
        "parse_error": None,
    }
    try:
        payload = json.loads(text, object_pairs_hook=_unique_object)
        if not isinstance(payload, dict) or set(payload) != {"values", "choice"}:
            result["parse_error"] = "wrong_top_level_schema"
            return result
        result["outer_order_compliant"] = list(payload) == ["values", "choice"]
        if isinstance(payload["values"], dict):
            result["actual_output_order"] = list(payload["values"])
        result["output_order_compliant"] = result["actual_output_order"] == list(order)
        # Keep a valid choice even if values/order are invalid: the primary decision
        # endpoint includes every assigned attempt; compliance is reported separately.
        if isinstance(payload["choice"], str) and payload["choice"] in list(ALIASES):
            result["choice"] = payload["choice"]
        values, error = parse_values(json.dumps({"values": payload["values"]}), ALIASES)
        result["values"] = values
        result["parse_error"] = error or ("invalid_choice" if result["choice"] is None else None)
    except (ValueError, TypeError, OverflowError):
        result["parse_error"] = "invalid_json_or_duplicate_key"
    return result


def optima(values, objective, subset=None):
    if values is None:
        return []
    keys = list(values) if subset is None else list(subset)
    if not keys or any(key not in values for key in keys):
        return []
    optimum = (max if objective == "conditional_max" else min)(values[key] for key in keys)
    return sorted(key for key in keys if abs(values[key] - optimum) <= 1e-9)


def score_response(case, condition, presentation, text):
    parsed = parse_joint(text, condition["output_order"])
    values, choice = parsed["values"], parsed["choice"]
    expected = public_values(case, presentation)
    values_correct = (
        all(abs(values[key] - number) <= TOLERANCE for key, number in expected.items())
        if values is not None
        else None
    )
    rank_preserved = (
        optima(values, case.objective) == optima(expected, case.objective)
        if values is not None
        else None
    )
    decision = score_choice(case, choice, presentation)
    compliant = bool(
        parsed["outer_order_compliant"]
        and parsed["output_order_compliant"]
        and values is not None
        and decision["valid"]
    )
    # The original C/D chemical identities are fixed before any V4 mapping.
    original_cd = {option for option, alias in present_order(case).aliases if alias in "CD"}
    current_cd_options = [a for o, a in presentation.aliases if o in original_cd]
    subsets = {
        "last_two_emitted": parsed["actual_output_order"][-2:],
        "fixed_letters_cd": list("CD"),
        "original_cd_options": current_cd_options,
    }
    predictions = {name: optima(values, case.objective, keys) for name, keys in subsets.items()}
    # Never read serialized dict order later: canonical log encoding sorts dicts.
    actual_order = parsed["actual_output_order"]
    reverse = {alias: option for option, alias in presentation.aliases}
    return {
        **parsed,
        "expected_values": expected,
        "aliases": [[o, a] for o, a in presentation.aliases],
        "scores": {
            "decision": decision,
            "values": {"valid": values is not None, "correct": values_correct},
            "program_decision": score_choice(
                case, choose_from_values(values, case.objective), presentation
            ),
        },
        "compliant": compliant,
        "optimum_set_preserved": rank_preserved,
        "clean_value_eligible": values_correct is True and rank_preserved is True,
        "clean_value_choice_error": (
            values_correct is True and rank_preserved is True and decision["correct"] is False
        ),
        "chosen_option": reverse.get(choice),
        "chosen_emitted_position": actual_order.index(choice) + 1
        if choice in actual_order
        else None,
        "chosen_requested_position": condition["output_order"].index(choice) + 1
        if choice
        else None,
        "candidate_predictions_from_emitted_values": predictions,
        "candidate_matches": {
            name: choice in aliases if aliases and choice else None
            for name, aliases in predictions.items()
        },
        "choice_consistent_with_values": choice in optima(values, case.objective)
        if values is not None and choice
        else None,
    }
