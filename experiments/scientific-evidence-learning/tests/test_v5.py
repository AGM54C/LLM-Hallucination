"""Literal-preserving comparisons, no answer leakage, paired logging and recovery."""

import copy
import json
import unittest

import test_v4 as fixtures_v4

from evidence_lab.models import Completion
from evidence_lab.storage import read_json, read_jsonl
from evidence_lab_v4.factorial import optima, remap_presentation
from evidence_lab_v4.runner import run as run_v4
from evidence_lab_v5.controls import (
    DEFAULT_CONFIG,
    comparison_prompt,
    conditions_for,
    literal_values,
    load_source,
    make_plan,
    make_record,
    parse_choice,
    run,
    score_response,
    verify_run,
)


class FixedReadoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = fixtures_v4.WorkflowTests()
        cls.fixture.setUp()
        f = cls.fixture
        cls.source_dir = f.root / "v4-source"
        run_v4(cls.source_dir, f.backend(), f.cases, f.refs, f.plan)
        cls.rows = load_source(f.dataset, cls.source_dir, f.cases)
        cls.lookup = {c.case_id: c for c in f.cases}
        cls.protocol = read_json(DEFAULT_CONFIG)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.tearDown()

    def source(self):
        return copy.deepcopy(self.rows[0])

    def plan(self):
        f = self.fixture
        return make_plan(
            f.dataset, self.source_dir, f.cases, self.rows, self.protocol, f.model, None, None
        )

    def backend(self, fail_after=None):
        expected = {}
        for source in self.rows:
            case = self.lookup[source["case_id"]]
            for context in conditions_for(source, self.protocol):
                choice = optima(source["evaluation"]["values"], case.objective)[0]
                expected[comparison_prompt(case, source, context)] = json.dumps({"choice": choice})
        metadata = self.fixture.metadata

        class Fake:
            def __init__(self):
                self.metadata, self.calls = metadata, 0

            def complete(self, prompt):
                if self.calls == fail_after:
                    raise RuntimeError("synthetic V5 interruption")
                self.calls += 1
                return Completion(expected[prompt], 80, 8)

        return Fake()

    def test_exact_number_literals_order_and_wrong_readout_are_preserved(self):
        source = self.source()
        source["response"] = (
            '{"values":{"C":9.0000,"D":1e1,"A":-0.0000,"B":7.12345000},"choice":"C"}'
        )
        source["evaluation"]["values"] = {"A": -0.0, "B": 7.12345, "C": 9.0, "D": 10.0}
        source["evaluation"]["actual_output_order"] = list("CDAB")
        literal = literal_values(source)
        self.assertEqual(literal, '{"C":9.0000,"D":1e1,"A":-0.0000,"B":7.12345000}')
        prompt = comparison_prompt(self.lookup[source["case_id"]], source, "numbers_only")
        self.assertIn(literal, prompt)
        self.assertNotIn('"choice":"C"', prompt)

    def test_conditions_differ_only_by_original_table_prefix(self):
        for source in self.rows:
            case = self.lookup[source["case_id"]]
            short = comparison_prompt(case, source, "numbers_only")
            long = comparison_prompt(case, source, "table_and_numbers")
            presentation = remap_presentation(case, source["variant"], source["alias_rotation"])
            self.assertEqual(long, presentation.prefix + "\n" + short)
            self.assertNotIn(source["response"], short)

    def test_previous_choice_cannot_change_new_prompt(self):
        source = self.source()
        case = self.lookup[source["case_id"]]
        before = comparison_prompt(case, source, "numbers_only")
        payload = json.loads(source["response"])
        payload["choice"] = "Z"
        source["response"] = json.dumps(payload)
        source["evaluation"]["choice"] = "Z"
        # Whitespace inside values is allowed to differ when source bytes differ;
        # changing only the previous choice in an otherwise identical string is inert.
        modified = self.source()
        start = modified["response"].rindex('"choice"')
        modified["response"] = modified["response"][:start] + '"choice":"Z"}'
        self.assertEqual(before, comparison_prompt(case, modified, "numbers_only"))

    def test_invalid_source_kept_as_failure_not_repaired(self):
        source = self.source()
        source["evaluation"]["scores"]["values"]["valid"] = False
        source["evaluation"]["values"] = None
        source["evaluation"]["clean_value_eligible"] = False
        source["evaluation"]["clean_value_choice_error"] = False
        case = self.lookup[source["case_id"]]
        for context in conditions_for(source, self.protocol):
            self.assertIsNone(comparison_prompt(case, source, context))
            row = make_record(case, source, context, None, 0.0, self.protocol)
            self.assertFalse(row["executed"])
            self.assertFalse(row["scores"]["decision"]["valid"])
            self.assertEqual(row["parse_error"], "upstream_invalid_values")

    def test_upstream_failure_stays_in_end_to_end_denominator_and_skips_two_calls(self):
        f = self.fixture
        original = f.backend()

        class NullReadout:
            metadata = f.metadata

            def complete(self, prompt):
                completion = original.complete(prompt)
                if original.calls == 1:
                    payload = json.loads(completion.text)
                    payload["values"][next(iter(payload["values"]))] = None
                    return Completion(
                        json.dumps(payload), completion.input_tokens, completion.output_tokens
                    )
                return completion

        source_dir = f.root / "v4-one-null"
        run_v4(source_dir, NullReadout(), f.cases, f.refs, f.plan)
        source_rows = load_source(f.dataset, source_dir, f.cases)
        plan = make_plan(
            f.dataset, source_dir, f.cases, source_rows, self.protocol, f.model, None, None
        )
        self.assertEqual(
            (plan["attempts"], plan["requests"], plan["upstream_failed_attempts"]), (32, 30, 2)
        )
        out = f.root / "v5-one-null"
        result = run(out, self.backend(), f.cases, source_rows, plan)
        self.assertEqual(verify_run(out), result)
        for m in result["by_context"].values():
            self.assertEqual(m["upstream_failures"], 1)
            self.assertEqual(m["executed"], 15)
            self.assertEqual(m["decision"]["all_attempt_accuracy"], 15 / 16)

    def test_numeric_comparison_and_measurement_truth_are_separate(self):
        source = self.source()
        case = self.lookup[source["case_id"]]
        values = source["evaluation"]["values"]
        gold = optima(values, case.objective)[0]
        wrong = next(a for a in "ABCD" if a not in optima(values, case.objective))
        source["evaluation"]["values"][wrong] = 999 if case.objective == "conditional_max" else -999
        result = score_response(case, source, json.dumps({"choice": wrong}))
        self.assertNotEqual(gold, wrong)
        self.assertTrue(result["scores"]["comparison"]["correct"])
        self.assertFalse(result["scores"]["decision"]["correct"])

    def test_strict_choice_schema_duplicates_and_multichar_alias(self):
        self.assertEqual(parse_choice('{"choice":"B"}'), ("B", None))
        for text in (
            '{"choice":"A","choice":"B"}',
            '{"choice":"AB"}',
            '{"choice":null}',
            '{"choice":""}',
            '{"choice":"A","other":1}',
            '```json\n{"choice":"A"}\n```',
        ):
            self.assertIsNone(parse_choice(text)[0])

    def test_complete_run_scores_pairs_costs_and_recomputes_csv(self):
        out = self.fixture.root / "v5-complete"
        summary = run(out, self.backend(), self.fixture.cases, self.rows, self.plan())
        self.assertEqual(summary["requests"], 32)
        self.assertEqual(summary["attempts"], 32)
        self.assertEqual(verify_run(out), summary)
        for m in summary["by_context"].values():
            self.assertEqual(m["decision"]["all_attempt_accuracy"], 1.0)
            self.assertEqual(m["cost"]["upstream_calls_per_standalone_workflow_total"], 16)
            self.assertEqual(m["cost"]["new_calls"], 16)
        with self.assertRaises(FileExistsError):
            run(out, self.backend(), self.fixture.cases, self.rows, self.plan())

    def test_interruption_preserves_rows_without_success(self):
        out = self.fixture.root / "v5-interrupted"
        with self.assertRaises(RuntimeError):
            run(out, self.backend(fail_after=3), self.fixture.cases, self.rows, self.plan())
        self.assertEqual(len(read_jsonl(out / "responses.jsonl")), 3)
        self.assertEqual(read_json(out / "failure.json")["completed_calls"], 3)
        self.assertFalse((out / "summary.json").exists())

    def test_rescoring_detects_changed_literal_numbers(self):
        out = self.fixture.root / "v5-corrupted"
        run(out, self.backend(), self.fixture.cases, self.rows, self.plan())
        path = out / "responses.jsonl"
        rows = read_jsonl(path)
        rows[0]["values_json_literal"] = '{"A":0,"B":0,"C":0,"D":0}'
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "does not reconstruct"):
            verify_run(out)

    def test_plan_rejects_adapter_mismatch_and_counts_full_cohort(self):
        self.assertEqual(self.plan()["requests"], 32)
        f = self.fixture
        with self.assertRaisesRegex(ValueError, "Adapter"):
            make_plan(
                f.dataset,
                self.source_dir,
                f.cases,
                self.rows,
                self.protocol,
                f.model,
                f.root / "incorrect-adapter",
                None,
            )


if __name__ == "__main__":
    unittest.main()
