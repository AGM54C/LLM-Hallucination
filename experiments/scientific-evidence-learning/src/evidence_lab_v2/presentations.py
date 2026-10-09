"""Record-order interventions with fixed aliases, facts, and final questions."""

import random
from collections import defaultdict

from evidence_lab.storage import stable_id
from evidence_lab.tasks import Presentation, present

SEEDED = {"shuffled", "block_shuffled", "within_block_shuffled"}
VARIANTS = ("canonical", "reversed", "shuffled", "block_shuffled", "within_block_shuffled")


def conditions(variants, order_seeds):
    if not variants or len(set(variants)) != len(variants) or set(variants) - set(VARIANTS):
        raise ValueError("Select unique supported variants")
    if not order_seeds or len(set(order_seeds)) != len(order_seeds):
        raise ValueError("Select one or more unique order seeds")
    if any(type(seed) is not int or seed < 0 for seed in order_seeds):
        raise ValueError("Order seeds must be nonnegative integers")
    return [
        (variant, seed)
        for variant in variants
        for seed in (order_seeds if variant in SEEDED else [0])
    ]


def present_order(case, variant="canonical", order_seed=0):
    if variant not in VARIANTS or type(order_seed) is not int or order_seed < 0:
        raise ValueError("Unknown variant or invalid order seed")
    if variant not in SEEDED:
        if order_seed != 0:
            raise ValueError("Unchanged/reversed order has no random seed")
        return present(case, variant)
    if variant == "shuffled" and order_seed == 0:
        # Exact bridge to the already measured v1 shuffled condition.
        return present(case, "shuffled")

    original = present(case)
    chunks = {rid: original.prefix[start:end] for rid, start, end in original.record_spans}
    header = original.prefix[: original.record_spans[0][1]]
    records = list(case.table.records)
    rng = random.Random(int(stable_id("record-order-v2", case.table.table_id, order_seed), 16))
    if variant == "shuffled":
        rng.shuffle(records)
    else:
        blocks = defaultdict(list)
        for record in records:
            blocks[record.context].append(record)
        contexts = list(blocks)
        if variant == "block_shuffled":
            rng.shuffle(contexts)
        else:
            for block in blocks.values():
                rng.shuffle(block)
        records = [record for context in contexts for record in blocks[context]]
    prefix, spans = header, []
    for record in records:
        start = len(prefix)
        prefix += chunks[record.record_id]
        spans.append((record.record_id, start, len(prefix)))
    return Presentation(prefix, original.question, original.aliases, tuple(spans))


def position_audit(case, presentation):
    targets = {r.record_id for r in case.table.records if r.context == case.target_context}
    positions = [i for i, (rid, _, _) in enumerate(presentation.record_spans) if rid in targets]
    return {
        "target_record_positions_zero_based": positions,
        "target_record_span_rows": max(positions) - min(positions) + 1,
        "total_records": len(presentation.record_spans),
    }
