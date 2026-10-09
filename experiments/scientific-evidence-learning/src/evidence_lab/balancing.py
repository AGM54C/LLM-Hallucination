"""Marginally balanced subset selection via SciPy's upstream HiGHS MILP solver."""

from __future__ import annotations


def balanced_subset(
    features: list[dict], reference: list[int], scores: list[float], maximize: bool, seed: int
) -> tuple[list[int], dict]:
    import numpy as np
    import scipy
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import csc_matrix

    n = len(features)
    if n != len(scores) or not reference or len(set(reference)) != len(reference):
        raise ValueError("Invalid feature, score or reference lengths")
    if any(type(i) is not int or not 0 <= i < n for i in reference):
        raise ValueError("Reference index outside candidate pool")
    categories = sorted({(name, str(value)) for row in features for name, value in row.items()})
    matrix = np.array(
        [[float(str(row.get(name)) == value) for row in features] for name, value in categories],
        dtype=float,
    )
    matrix = np.vstack([np.ones(n), matrix])
    target = matrix[:, reference].sum(axis=1)
    objective = np.asarray(scores, dtype=float)
    if not np.isfinite(objective).all():
        raise ValueError("Selection scores must be finite")
    # Stable small tie-breaking perturbation; the dominant objective is recorded separately.
    perturbation = np.random.default_rng(seed).uniform(-1e-9, 1e-9, n)
    result = milp(
        c=(-objective if maximize else objective) + perturbation,
        integrality=np.ones(n),
        bounds=Bounds(0, 1),
        constraints=LinearConstraint(csc_matrix(matrix), target, target),
        options={"time_limit": 30, "mip_rel_gap": 0.0},
    )
    if not result.success:
        raise ValueError(f"Balanced design did not solve to optimality: {result.message}")
    chosen = np.flatnonzero(np.rint(result.x)).tolist()
    if len(chosen) != len(reference) or not np.array_equal(matrix[:, chosen].sum(axis=1), target):
        raise ValueError("Solver output failed independent exact marginal checks")
    return chosen, {
        "solver": "scipy.optimize.milp/HiGHS",
        "scipy_version": scipy.__version__,
        "marginal_constraints": len(categories),
        "objective_sum": float(objective[chosen].sum()),
        "mip_gap": float(result.mip_gap),
        "status": int(result.status),
    }
