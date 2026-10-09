"""Finite blind-identity experiment with exact permutation posterior.

The observation model replays real recorded values without noise. Public views
contain no permutation, RNG seed, original row IDs or hidden true answer.
Policies receive immutable PublicView objects, never an Environment reference.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import permutations
from statistics import fmean

from .domain import ExperimentTable

Mapping = tuple[int, ...]  # alias index -> original option index
Action = tuple[int, int]  # alias index, context index


@dataclass(frozen=True)
class Observation:
    alias: int
    context: int
    value: float


@dataclass(frozen=True)
class PublicView:
    option_names: tuple[str, ...]
    contexts: tuple[str, ...]
    reference: tuple[tuple[float, ...], ...]  # original option, context
    target: int
    observations: tuple[Observation, ...] = ()

    def __post_init__(self) -> None:
        n = len(self.option_names)
        if not 2 <= n <= 6 or len(self.reference) != n or not self.contexts:
            raise ValueError("Exact enumeration supports 2–6 options and nonempty contexts")
        if not 0 <= self.target < len(self.contexts):
            raise ValueError("Unknown target context")
        if any(
            len(row) != len(self.contexts) or any(not math.isfinite(v) for v in row)
            for row in self.reference
        ):
            raise ValueError("Invalid finite reference matrix")

    def posterior(self) -> tuple[Mapping, ...]:
        return tuple(
            p
            for p in permutations(range(len(self.option_names)))
            if all(self.reference[p[o.alias]][o.context] == o.value for o in self.observations)
        )

    def legal_actions(self) -> tuple[Action, ...]:
        seen = {(o.alias, o.context) for o in self.observations}
        return tuple(
            (a, c)
            for a in range(len(self.option_names))
            for c in range(len(self.contexts))
            if (a, c) not in seen
        )

    def payload(self) -> dict:
        return {
            "options": list(self.option_names),
            "contexts": list(self.contexts),
            "reference": [list(row) for row in self.reference],
            "blind_aliases": list("ABCDEF"[: len(self.option_names)]),
            "target_context": self.contexts[self.target],
            "observations": [
                {"sample": "ABCDEF"[o.alias], "context": self.contexts[o.context], "value": o.value}
                for o in self.observations
            ],
        }


def public_reference(table: ExperimentTable, context: str) -> PublicView:
    cells = {(r.option, r.context): r.value for r in table.records}
    return PublicView(
        table.options,
        table.contexts,
        tuple(tuple(cells[o, c] for c in table.contexts) for o in table.options),
        table.contexts.index(context),
    )


class BlindEnvironment:
    def __init__(self, initial: PublicView, mapping: Mapping, budget: int):
        if initial.observations or sorted(mapping) != list(range(len(initial.option_names))):
            raise ValueError("Require fresh public view and a bijective identity assignment")
        if type(budget) is not int or budget < 0:
            raise ValueError("Budget must be a nonnegative integer")
        self.__mapping = mapping
        self.__budget = budget
        self.__view = initial

    @property
    def view(self) -> PublicView:
        return self.__view

    def query(self, action: Action) -> Observation:
        if len(self.__view.observations) >= self.__budget:
            raise ValueError("Query budget exhausted")
        if action not in self.__view.legal_actions():
            raise ValueError("Illegal or repeated query")
        alias, context = action
        value = self.__view.reference[self.__mapping[alias]][context]
        observation = Observation(alias, context, value)
        self.__view = PublicView(
            self.__view.option_names,
            self.__view.contexts,
            self.__view.reference,
            self.__view.target,
            (*self.__view.observations, observation),
        )
        return observation

    def score(self, alias: int) -> dict:
        if type(alias) is not int or not 0 <= alias < len(self.__mapping):
            raise ValueError("Unknown blind alias")
        values = [row[self.__view.target] for row in self.__view.reference]
        regret = max(values) - values[self.__mapping[alias]]
        return {
            "correct": regret <= 1e-9,
            "regret_pp": regret,
            "queries": len(self.__view.observations),
        }


def expected_values(view: PublicView, posterior: tuple[Mapping, ...] | None = None) -> list[float]:
    states = view.posterior() if posterior is None else posterior
    if not states:
        raise ValueError("Observations are inconsistent with the declared reference table")
    return [
        fmean(view.reference[p[a]][view.target] for p in states)
        for a in range(len(view.option_names))
    ]


def decide(view: PublicView) -> int:
    values = expected_values(view)
    return max(range(len(values)), key=lambda a: (round(values[a], 10), -a))


def prior_success_bound(view: PublicView) -> float:
    if view.observations:
        raise ValueError("Prior bound requires no observations")
    states = view.posterior()
    best = max(row[view.target] for row in view.reference)
    return max(
        sum(abs(view.reference[p[a]][view.target] - best) <= 1e-9 for p in states) / len(states)
        for a in range(len(view.option_names))
    )


def choose_query(view: PublicView, policy: str, rng) -> Action:
    actions = view.legal_actions()
    if not actions:
        raise ValueError("No legal actions remain")
    if policy == "random":
        return rng.choice(actions)
    if policy == "round_robin":
        # Query target-context values of previously unqueried aliases first.
        return min(actions, key=lambda a: (a[1] != view.target, a[0], a[1]))
    if policy not in {"information_gain", "myopic_bayes_risk"}:
        raise ValueError("Unknown query policy")
    states = view.posterior()
    scores = []
    for action in actions:
        alias, context = action
        groups = defaultdict(list)
        for p in states:
            groups[view.reference[p[alias]][context]].append(p)
        if policy == "information_gain":
            counts = Counter({v: len(ps) for v, ps in groups.items()})
            score = -sum((n / len(states)) * math.log2(n / len(states)) for n in counts.values())
        else:
            # Expected utility after ONE observation; explicitly not a horizon-optimal planner.
            score = sum(
                len(ps) / len(states) * max(expected_values(view, tuple(ps)))
                for ps in groups.values()
            )
        scores.append(score)
    return actions[max(range(len(actions)), key=lambda i: (round(scores[i], 10), -i))]
