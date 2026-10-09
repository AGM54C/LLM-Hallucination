"""Matched training-set interventions; only training cases can enter selection."""

from __future__ import annotations

import random
from collections import Counter, defaultdict

from .domain import DecisionCase
from .tasks import DEVELOPMENT_RULES, diagnostics, present


def training_pool(cases: list[DecisionCase]) -> list[DecisionCase]:
    """Single-target SFT excludes tied maxima; evaluation keeps all co-optima valid."""
    return [
        c
        for c in cases
        if c.split == "train"
        and c.objective == "conditional_max"
        and len(diagnostics(c)["gold"]) == 1
    ]


def coverage(cases: list[DecisionCase]) -> dict:
    if not cases:
        raise ValueError("Empty coverage set")
    rejected = [diagnostics(c)["rule_rejected"] for c in cases]
    rates = {rule: sum(r[rule] for r in rejected) / len(cases) for rule in DEVELOPMENT_RULES}
    return {
        "n": len(cases),
        "rejection_fraction_by_development_rule": rates,
        "minimum_rejection_fraction": min(rates.values()),
        "mean_rejection_fraction": sum(rates.values()) / len(rates),
        "eliminated_rule_fraction": sum(x > 0 for x in rates.values()) / len(rates),
        "definition": "Finite prespecified rule-family diagnostics; not a new theorem or latent-mechanism label",
    }


def select_matched(
    cases: list[DecisionCase], n: int, seed: int, difficulty: dict[str, float] | None = None
) -> tuple[dict[str, list[DecisionCase]], dict]:
    if not cases or any(c.split != "train" or c.objective != "conditional_max" for c in cases):
        raise ValueError("Sampling accepts only training conditional_max cases")
    if not 1 <= n <= len(cases):
        raise ValueError(f"Requested {n} cases from a pool of {len(cases)}")
    if len({c.case_id for c in cases}) != len(cases):
        raise ValueError("Duplicate training cases")
    rng = random.Random(seed)
    strata = defaultdict(list)
    details = {}
    for c in cases:
        d = diagnostics(c)
        p = present(c)
        if len(d["gold"]) != 1:
            raise ValueError("Tied training labels require explicit multi-target supervision")
        label = dict(p.aliases)[d["gold"][0]]
        # Match measured margin and length proxies; neither is claimed to be model difficulty.
        key = (
            c.table.source_id,
            c.table.group_id,
            d["gold"][0],
            label,
            min(3, int(d["margin"] // 10)),
            len(p.prompt) // 512,
        )
        strata[key].append(c)
        details[c.case_id] = d
    shuffled = list(cases)
    rng.shuffle(shuffled)
    selected_ids = {c.case_id for c in shuffled[:n]}
    quotas = {key: sum(c.case_id in selected_ids for c in pool) for key, pool in strata.items()}
    arms = {name: [] for name in ("uniform", "low_disagreement", "high_disagreement")}
    if difficulty is not None:
        if set(difficulty) != {c.case_id for c in cases}:
            raise ValueError("Difficulty file must cover exactly the eligible training pool")
        if any(
            not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 <= v < float("inf")
            for v in difficulty.values()
        ):
            raise ValueError("Difficulty must be finite nonnegative base-model loss")
        arms["hard_examples"] = []
    for key, pool in sorted(strata.items()):
        k = quotas[key]
        tie_order = list(pool)
        rng.shuffle(tie_order)

        def score(c):
            return sum(details[c.case_id]["rule_rejected"][r] for r in DEVELOPMENT_RULES)

        arms["uniform"].extend(c for c in pool if c.case_id in selected_ids)
        arms["low_disagreement"].extend(sorted(tie_order, key=score)[:k])
        arms["high_disagreement"].extend(sorted(tie_order, key=score, reverse=True)[:k])
        if difficulty is not None:
            arms["hard_examples"].extend(
                sorted(tie_order, key=lambda c: difficulty[c.case_id], reverse=True)[:k]
            )
    for arm in arms.values():
        arm.sort(key=lambda c: c.case_id)
    arms["random_order_augmentation"] = list(arms["uniform"])
    report = {
        "seed": seed,
        "pool_size": len(cases),
        "n_per_arm": n,
        "matching": [
            "source",
            "additive group",
            "chemical answer",
            "answer alias",
            "record margin bin",
            "character length bin",
        ],
        "model_difficulty_matched": False,
        "difficulty_note": "Hard-example arm exists only with measured base-model losses. Matching these losses needs a later frozen design version.",
        "arms": {
            name: {
                "coverage": coverage(pool),
                "groups": dict(Counter(c.table.group_id for c in pool)),
                "case_ids": [c.case_id for c in pool],
            }
            for name, pool in arms.items()
        },
        "pairwise_overlap": {
            f"{a}/{b}": len({c.case_id for c in arms[a]} & {c.case_id for c in arms[b]})
            for i, a in enumerate(arms)
            for b in list(arms)[i + 1 :]
        },
    }
    return arms, report


def select_balanced(
    cases: list[DecisionCase], n: int, seed: int, difficulty: dict[str, float] | None = None
) -> tuple[dict[str, list[DecisionCase]], dict]:
    """Match separate marginals, avoiding nearly singleton joint strata in small data.

    This is a design intervention, not proof of matching the entire difficulty
    distribution. Candidate features and constraints use training cases only.
    """
    from bisect import bisect_right

    from .balancing import balanced_subset

    arms, report = select_matched(cases, n, seed, difficulty)
    reference_ids = {c.case_id for c in arms["uniform"]}
    reference = [i for i, c in enumerate(cases) if c.case_id in reference_ids]
    thresholds = []
    if difficulty is not None:
        values = sorted(difficulty.values())
        thresholds = sorted({values[int(q * (len(values) - 1))] for q in (0.25, 0.5, 0.75)})
    features, scores = [], []
    for c in cases:
        d, p = diagnostics(c), present(c)
        f = {
            "source": c.table.source_id,
            "group": c.table.group_id,
            "gold": d["gold"][0],
            "alias": dict(p.aliases)[d["gold"][0]],
            "margin_bin": min(3, int(d["margin"] // 10)),
            "length_bin": len(p.prompt) // 512,
        }
        if difficulty is not None:
            f["difficulty_bin"] = bisect_right(thresholds, difficulty[c.case_id])
        features.append(f)
        scores.append(sum(d["rule_rejected"][r] for r in DEVELOPMENT_RULES))
    solver_reports = {}
    for name, maximize, values in (
        ("low_disagreement", False, scores),
        ("high_disagreement", True, scores),
    ):
        selected, info = balanced_subset(features, reference, values, maximize, seed)
        arms[name] = sorted((cases[i] for i in selected), key=lambda c: c.case_id)
        solver_reports[name] = info
    if difficulty is not None:
        selected, info = balanced_subset(
            features, reference, [difficulty[c.case_id] for c in cases], True, seed
        )
        arms["hard_examples"] = sorted((cases[i] for i in selected), key=lambda c: c.case_id)
        solver_reports["hard_examples"] = info
    report.update(
        selection_method="balanced_marginals",
        solvers=solver_reports,
        model_difficulty_matched=difficulty is not None,
        difficulty_note="Measured NLL quartile-bin counts matched only when supplied; continuous loss and joint distributions can still differ.",
        balance_scope="Each named marginal is exact; the joint distribution is not fixed.",
    )
    report["arms"] = {
        name: {
            "coverage": coverage(pool),
            "groups": dict(Counter(c.table.group_id for c in pool)),
            "case_ids": [c.case_id for c in pool],
        }
        for name, pool in arms.items()
    }
    report["pairwise_overlap"] = {
        f"{a}/{b}": len({c.case_id for c in arms[a]} & {c.case_id for c in arms[b]})
        for i, a in enumerate(arms)
        for b in list(arms)[i + 1 :]
    }
    return arms, report
