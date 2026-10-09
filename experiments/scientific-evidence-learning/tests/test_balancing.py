import unittest
from itertools import combinations

from helpers import case  # noqa: F401

from evidence_lab.balancing import balanced_subset


class BalanceTests(unittest.TestCase):
    def test_upstream_optimizer_agrees_with_exhaustive_small_design(self):
        features = [{"group": i // 4, "answer": i % 2} for i in range(8)]
        reference = [0, 1, 4, 5]
        scores = [0.0, 1.0, 3.0, 2.0, 2.0, 4.0, 1.0, 5.0]

        def counts(indices):
            return tuple(
                sum(features[i][field] == value for i in indices)
                for field in ("group", "answer")
                for value in (0, 1)
            )

        feasible = [ids for ids in combinations(range(8), 4) if counts(ids) == counts(reference)]
        for maximize in (True, False):
            selected, report = balanced_subset(features, reference, scores, maximize, 41)
            expected = (max if maximize else min)(sum(scores[i] for i in ids) for ids in feasible)
            self.assertEqual(sum(scores[i] for i in selected), expected)
            self.assertEqual(counts(selected), counts(reference))
            self.assertEqual(report["mip_gap"], 0.0)


if __name__ == "__main__":
    unittest.main()
