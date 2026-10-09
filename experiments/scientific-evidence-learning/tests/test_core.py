import json
import random
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from itertools import permutations
from pathlib import Path

from helpers import DATA, case, table

from evidence_lab.analysis import paired_group_difference
from evidence_lab.blind_agent import run_episode
from evidence_lab.blinding import (
    BlindEnvironment,
    choose_query,
    decide,
    prior_success_bound,
    public_reference,
)
from evidence_lab.data import load_chemistry, make_cases, split_tables
from evidence_lab.models import Completion, parse_choice
from evidence_lab.readouts import score_values
from evidence_lab.sampling import select_matched, training_pool
from evidence_lab.storage import freeze, read_jsonl, verify, write_json
from evidence_lab.tasks import diagnostics, present, score_choice, utilities, winners


class DomainTests(unittest.TestCase):
    def test_value_readout_format_and_tolerance(self):
        expected = {"A": 4.222222, "B": 6.0}
        self.assertTrue(score_values('{"values":{"A":4.2222,"B":6}}', expected)["correct"])
        self.assertFalse(score_values('{"values":{"A":6,"B":4.2222}}', expected)["correct"])
        self.assertFalse(score_values('{"values":{"A":true,"B":6}}', expected)["valid"])

    def test_incomplete_and_duplicate_cells_rejected(self):
        t = table()
        with self.assertRaises(ValueError):
            replace(t, records=t.records[:-1])
        with self.assertRaises(ValueError):
            replace(t, records=(*t.records, t.records[0]))

    def test_nonfinite_values_rejected(self):
        with self.assertRaises(ValueError):
            replace(table().records[0], value=float("nan"))

    def test_scope_and_objective_controls(self):
        c = case()
        self.assertEqual(winners(utilities(c)), ("ligand0",))
        self.assertEqual(winners(utilities(case("pooled_max"))), ("ligand1",))
        self.assertEqual(winners(utilities(case("conditional_min"))), ("ligand3",))
        self.assertTrue(diagnostics(c)["rule_rejected"]["pooled_max"])

    def test_question_change_keeps_evidence_and_aliases_fixed(self):
        a, b = present(case()), present(case("conditional_min"))
        self.assertEqual(a.prefix, b.prefix)
        self.assertEqual(a.aliases, b.aliases)
        self.assertNotEqual(a.question, b.question)

    def test_order_controls_preserve_exact_evidence(self):
        a, b = present(case()), present(case(), "reversed")
        self.assertEqual(Counter(a.prefix.splitlines()), Counter(b.prefix.splitlines()))
        self.assertEqual(a.question, b.question)
        self.assertEqual(
            {rid for rid, _, _ in a.record_spans}, {rid for rid, _, _ in b.record_spans}
        )
        self.assertNotEqual(a.prefix, b.prefix)

    def test_invalid_output_not_scored_as_reasoning_failure(self):
        self.assertIsNone(parse_choice("answer is A"))
        self.assertIsNone(parse_choice('{"choice":"A","extra":1}'))
        self.assertEqual(parse_choice('```json\n{"choice":"A"}\n```'), "A")
        score = score_choice(case(), None, present(case()))
        self.assertFalse(score["valid"])
        self.assertIsNone(score["correct"])

    def test_regret_matches_hand_calculation(self):
        c, p = case(), present(case())
        score = score_choice(c, dict(p.aliases)["ligand1"], p)
        self.assertEqual(score["regret_pp"], 4.0)


class BlindTests(unittest.TestCase):
    def setUp(self):
        self.view = public_reference(table(), "context0")

    def test_public_inputs_identical_for_all_hidden_assignments(self):
        payloads = set()
        for mapping in permutations(range(4)):
            env = BlindEnvironment(self.view, mapping, 3)
            payloads.add(json.dumps(env.view.payload(), sort_keys=True))
        self.assertEqual(len(payloads), 1)
        self.assertNotIn("r00", next(iter(payloads)))
        self.assertEqual(prior_success_bound(self.view), 0.25)

    def test_prior_bound_handles_ties(self):
        tied = replace(self.view, reference=((9.0, 1.0), (9.0, 8.0), (2.0, 3.0), (0.0, 2.0)))
        self.assertEqual(prior_success_bound(tied), 0.5)

    def test_exhaustive_no_observation_accuracy(self):
        successes = [
            BlindEnvironment(self.view, p, 0).score(decide(self.view))["correct"]
            for p in permutations(range(4))
        ]
        self.assertEqual(sum(successes) / len(successes), 0.25)

    def test_exact_posterior_and_three_query_solution(self):
        for mapping in permutations(range(4)):
            env = BlindEnvironment(self.view, mapping, 3)
            for _ in range(3):
                env.query(choose_query(env.view, "round_robin", random.Random(4)))
                self.assertIn(mapping, env.view.posterior())
            self.assertTrue(env.score(decide(env.view))["correct"])

    def test_query_cost_repeats_and_identity_leakage(self):
        env = BlindEnvironment(self.view, (2, 0, 3, 1), 1)
        obs = env.query((0, 0))
        self.assertEqual(obs.value, 2.0)
        self.assertEqual(set(vars(obs)), {"alias", "context", "value"})
        with self.assertRaises(ValueError):
            env.query((1, 0))
        with self.assertRaises(ValueError):
            BlindEnvironment(self.view, (0, 0, 1, 2), 3)
        env2 = BlindEnvironment(self.view, (0, 1, 2, 3), 2)
        env2.query((0, 0))
        with self.assertRaises(ValueError):
            env2.query((0, 0))

    def test_agent_query_and_decision_path(self):
        class Model:
            def __init__(self):
                self.prompts = []

            def complete(self, prompt):
                self.prompts.append(prompt)
                text = (
                    '{"query":{"sample":"A","context":"context0"}}'
                    if len(self.prompts) == 1
                    else '{"choice":"A"}'
                )
                return Completion(text, 1, 1)

        m = Model()
        result = run_episode(BlindEnvironment(self.view, (0, 1, 2, 3), 1), m, 1)
        self.assertTrue(result["correct"])
        self.assertEqual(result["queries"], 1)
        self.assertNotIn("mapping", m.prompts[0])
        self.assertNotIn("source_row", m.prompts[1])


class ProvenanceTests(unittest.TestCase):
    def test_freeze_detects_source_or_artifact_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_text("input")
            run = root / "run"
            write_json(run / "a.json", {"a": 1})
            freeze(run, {"source": source})
            verify(run)
            source.write_text("changed")
            with self.assertRaises(ValueError):
                verify(run)

    def test_duplicate_pairs_rejected_and_groups_not_rows_resampled(self):
        a = [{"case_id": str(i), "group_id": str(i // 5), "correct": False} for i in range(10)]
        b = [{**r, "correct": True} for r in a]
        report = paired_group_difference(a, b, samples=100)
        self.assertEqual(report["groups"], 2)
        self.assertEqual(report["mean_difference"], 1)
        with self.assertRaises(ValueError):
            paired_group_difference(a + a[:1], b)

    def test_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "bad.jsonl"
            p.write_text('{"value":NaN}')
            with self.assertRaises(ValueError):
                read_jsonl(p)


class RealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables, cls.audit = load_chemistry(DATA)
        cls.splits = split_tables(cls.tables, 20261006, 0.2, 0.2)
        cls.cases = make_cases(cls.tables, cls.splits)

    def test_matches_independent_legacy_audit(self):
        legacy = json.loads(
            (Path(__file__).parent / "fixtures/finite_table_audit.json").read_text(
                encoding="utf-8"
            )
        )
        maximum_cases = [c for c in self.cases if c.objective == "conditional_max"]
        self.assertEqual(len(self.tables), legacy["complete_blocks"])
        self.assertEqual(len(maximum_cases), legacy["block_context_pairs"])
        rejected = sum(diagnostics(c)["rule_rejected"]["pooled_max"] for c in maximum_cases)
        # Legacy pandas idxmax counted 20 all-zero ties as changes of optimal name.
        ties = sum(len(diagnostics(c)["gold"]) > 1 for c in maximum_cases)
        self.assertEqual(rejected, 376)
        self.assertEqual(ties, 20)
        self.assertEqual(rejected + ties, legacy["pairs_with_distinct_scoped_optimum"])
        self.assertEqual(self.audit["source_sha256"], legacy["source_sha256"])

    def test_physical_rows_do_not_cross_splits(self):
        ownership = {}
        for c in self.cases:
            for r in c.table.records:
                ownership.setdefault(r.record_id, set()).add(c.split)
        self.assertTrue(all(len(splits) == 1 for splits in ownership.values()))

    def test_matched_selection_is_reproducible_and_balances_answers(self):
        pool = training_pool(self.cases)
        arms, report = select_matched(pool, 128, 41)
        _, again = select_matched(pool, 128, 41)
        self.assertEqual(report, again)
        labels = []
        for selected in arms.values():
            self.assertEqual(len(selected), 128)
            labels.append(
                Counter(dict(present(c).aliases)[diagnostics(c)["gold"][0]] for c in selected)
            )
        self.assertTrue(all(labels[0] == counts for counts in labels))
        with self.assertRaises(ValueError):
            select_matched(self.cases[:10], 2, 41)
        with self.assertRaises(ValueError):
            select_matched(pool, 128, 41, {"made-up": 0.1})


if __name__ == "__main__":
    unittest.main()
