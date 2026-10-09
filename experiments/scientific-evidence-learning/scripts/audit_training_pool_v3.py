"""Train-only feasibility audit. Produces no training examples or checkpoints."""

from __future__ import annotations

import argparse
import bisect
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evidence_lab.models import completion_features  # noqa: E402
from evidence_lab.sampling import training_pool  # noqa: E402
from evidence_lab.storage import digest, read_json, read_jsonl, verify, write_json  # noqa: E402
from evidence_lab.tasks import DEVELOPMENT_RULES, diagnostics, present  # noqa: E402
from evidence_lab.workflows import load_cases  # noqa: E402


def subset_stats(indices, difficulty, scores, token_counts):
    import numpy as np

    x = np.asarray(difficulty)[indices]
    return {
        "n": len(indices),
        "mean_rule_rejection_fraction": float(
            np.mean(np.asarray(scores)[indices]) / len(DEVELOPMENT_RULES)
        ),
        "nll_mean": float(x.mean()),
        "nll_std": float(x.std()),
        "nll_quantiles": dict(
            zip(
                ["q0", "q25", "q50", "q75", "q90", "q95", "q100"],
                map(float, np.quantile(x, [0, 0.25, 0.5, 0.75, 0.9, 0.95, 1])),
            )
        ),
        "prompt_tokens_total": int(sum(token_counts[i][0] for i in indices)),
        "completion_tokens_total": int(sum(token_counts[i][1] for i in indices)),
    }


def main():
    import numpy as np
    import scipy
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import csc_matrix
    from scipy.stats import ks_2samp
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Audit output exists; choose a new path")
    manifest = verify(args.dataset)
    freeze_sha = digest(args.dataset / "freeze.json")
    pool = training_pool(load_cases(args.dataset, "train"))
    loss_path = Path(manifest["sources"]["measured_difficulty"]["path"])
    loss_rows = read_jsonl(loss_path)
    loss_lookup = {r["case_id"]: r["nll"] for r in loss_rows}
    if len(loss_lookup) != len(loss_rows) or set(loss_lookup) != {c.case_id for c in pool}:
        raise ValueError("Difficulty must cover exactly the eligible training pool")
    losses = np.array([loss_lookup[c.case_id] for c in pool])
    if not np.isfinite(losses).all() or (losses < 0).any():
        raise ValueError("Invalid base losses")
    selected = set(read_json(args.dataset / "selection.json")["arms"]["uniform"]["case_ids"])
    reference = [i for i, c in enumerate(pool) if c.case_id in selected]
    if len(reference) != len(selected):
        raise ValueError("Uniform selection differs from pool")
    tokenizer = AutoTokenizer.from_pretrained(
        args.model, local_files_only=True, trust_remote_code=False
    )
    quartiles = sorted({sorted(losses)[int(q * (len(losses) - 1))] for q in [0.25, 0.5, 0.75]})
    deciles = sorted({sorted(losses)[int(q / 10 * (len(losses) - 1))] for q in range(1, 10)})
    features, scores, token_counts = [], [], []
    for i, c in enumerate(pool):
        d, p = diagnostics(c), present(c)
        alias = dict(p.aliases)[d["gold"][0]]
        completion = json.dumps({"choice": alias}, separators=(",", ":"))
        encoded = completion_features(tokenizer, p.prompt, completion, 8192, True, False)
        target_n = sum(value != -100 for value in encoded["labels"])
        prefix_n = len(encoded["input_ids"]) - target_n
        token_counts.append((prefix_n, target_n))
        features.append(
            {
                "source": c.table.source_id,
                "group": c.table.group_id,
                "gold": d["gold"][0],
                "alias": alias,
                "margin_bin": min(3, int(d["margin"] // 10)),
                "length_bin": len(p.prompt) // 512,
                "nll_quartile": bisect.bisect_right(quartiles, losses[i]),
                "table": c.table.table_id,
                "target": c.target_context,
                "nll_decile": bisect.bisect_right(deciles, losses[i]),
                "token_bin": prefix_n // 64,
            }
        )
        scores.append(sum(d["rule_rejected"][r] for r in DEVELOPMENT_RULES))
    stages = [
        (
            "legacy_marginals",
            ["source", "group", "gold", "alias", "margin_bin", "length_bin", "nll_quartile"],
            False,
            False,
        ),
        (
            "plus_table_target",
            [
                "source",
                "group",
                "gold",
                "alias",
                "margin_bin",
                "length_bin",
                "nll_quartile",
                "table",
                "target",
            ],
            False,
            False,
        ),
        (
            "plus_fine_difficulty",
            [
                "source",
                "group",
                "gold",
                "alias",
                "margin_bin",
                "length_bin",
                "nll_quartile",
                "table",
                "target",
                "nll_decile",
            ],
            True,
            False,
        ),
        ("plus_exact_token_budget", list(features[0]), True, True),
    ]
    report = {
        "schema": "training-pool-feasibility-v3",
        "dataset_freeze_sha256": freeze_sha,
        "pool_size": len(pool),
        "reference_n": len(reference),
        "reference": subset_stats(reference, losses, scores, token_counts),
        "scipy_version": scipy.__version__,
        "stages": [],
        "training_authorized_by_audit": False,
        "limitations": [
            "Exact named marginals do not imply equal joint distributions or causal identification.",
            "Fine difficulty constraints match decile counts and a mean caliper, not exact continuous distributions.",
            "Same total tokens does not fix gradient noise, minibatch composition or all training dynamics.",
            "This audits one fixed uniform reference, not all designs. No validation/test outcome is used.",
        ],
    }
    n = len(pool)
    for name, fields, caliper, tokens in stages:
        categories = sorted({(key, str(f[key])) for f in features for key in fields})
        matrix = [[1.0] * n] + [
            [float(str(f[key]) == value) for f in features] for key, value in categories
        ]
        if tokens:
            matrix += [[float(x[0]) for x in token_counts], [float(x[1]) for x in token_counts]]
        matrix = np.asarray(matrix)
        target = matrix[:, reference].sum(axis=1)
        lower, upper = target.copy(), target.copy()
        if caliper:
            scale = max(float(losses.std()), 1e-12)
            normalized = (losses - losses.mean()) / scale
            center = normalized[reference].sum()
            matrix = np.vstack([matrix, normalized])
            lower = np.r_[lower, center - 0.02 * len(reference)]
            upper = np.r_[upper, center + 0.02 * len(reference)]
        entry = {
            "name": name,
            "fields": fields,
            "nll_mean_caliper_pool_sd": 0.02 if caliper else None,
            "exact_total_prompt_and_completion_tokens": tokens,
            "arms": {},
        }
        choices = {}
        for arm, sign in [("low", 1), ("high", -1)]:
            result = milp(
                c=sign * np.asarray(scores, dtype=float),
                integrality=np.ones(n),
                bounds=Bounds(0, 1),
                constraints=LinearConstraint(csc_matrix(matrix), lower, upper),
                options={"time_limit": 20.0, "mip_rel_gap": 0.0},
            )
            if not result.success:
                entry["arms"][arm] = {
                    "status": "not_proven_optimal",
                    "solver_status": int(result.status),
                    "message": result.message,
                }
                print(name, arm, "not_proven_optimal", flush=True)
                continue
            picked = np.flatnonzero(np.rint(result.x)).tolist()
            actual = matrix[:, picked].sum(axis=1)
            if len(picked) != len(reference) or not (
                (actual >= lower - 1e-6).all() and (actual <= upper + 1e-6).all()
            ):
                raise ValueError("Solver output failed independent constraint checks")
            for key in fields:
                if Counter(features[i][key] for i in picked) != Counter(
                    features[i][key] for i in reference
                ):
                    raise ValueError("Nonexact marginal: " + key)
            if tokens and tuple(map(sum, zip(*(token_counts[i] for i in picked)))) != tuple(
                map(sum, zip(*(token_counts[i] for i in reference)))
            ):
                raise ValueError("Token budget differs")
            choices[arm] = picked
            entry["arms"][arm] = {
                "status": "optimal",
                "case_ids": [pool[i].case_id for i in picked],
                **subset_stats(picked, losses, scores, token_counts),
            }
            print(name, arm, entry["arms"][arm]["mean_rule_rejection_fraction"], flush=True)
        if set(choices) == {"low", "high"}:
            low, high = choices["low"], choices["high"]
            entry["high_minus_low_rejection_fraction"] = float(
                (np.mean(np.asarray(scores)[high]) - np.mean(np.asarray(scores)[low]))
                / len(DEVELOPMENT_RULES)
            )
            entry["overlap"] = len(set(low) & set(high))
            entry["nll_ks_distance"] = float(ks_2samp(losses[low], losses[high]).statistic)
            entry["nll_mean_difference_pool_sd"] = float(
                (losses[high].mean() - losses[low].mean()) / max(losses.std(), 1e-12)
            )
        report["stages"].append(entry)
    verify(args.dataset)
    if digest(args.dataset / "freeze.json") != freeze_sha:
        raise ValueError("Dataset changed")
    report["script_sha256"] = digest(Path(__file__))
    report["tokenizer_files_sha256"] = {
        name: digest(args.model / name)
        for name in ["tokenizer.json", "tokenizer_config.json", "config.json"]
    }
    write_json(args.out, report)
    print("AUDIT_WRITTEN", args.out, flush=True)


if __name__ == "__main__":
    main()
