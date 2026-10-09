"""Scientific-control integrity and recoverable logging; no real-model claims."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from helpers import case

from evidence_lab.data import case_to_dict
from evidence_lab.models import Completion
from evidence_lab.storage import freeze, read_json, read_jsonl, write_jsonl
from evidence_lab.tasks import present
from evidence_lab_v2.diagnostics import build_requests, choose_from_values
from evidence_lab_v2.diagnostics import plan as v2_plan
from evidence_lab_v2.diagnostics import run as v2_run
from evidence_lab_v2.presentations import present_order
from evidence_lab_v3.controls import (
    cache_key,
    comparison_prompt,
    joint_prompt,
    load_cache,
    make_plan,
    parse_joint,
    public_values,
    requests_for,
    run,
)


class ControlPromptTests(unittest.TestCase):
    def test_comparison_uses_supplied_values_and_alias_order_not_gold(self):
        prompt = comparison_prompt({"D": 1.2, "A": 99.0, "B": 4.0, "C": 3.0}, "conditional_min")
        self.assertIn('"A":99.0,"B":4.0,"C":3.0,"D":1.2', prompt)
        self.assertIn("lowest", prompt)
        self.assertNotIn("highest", prompt)

    def test_public_filter_only_removes_other_substrates_and_keeps_aliases(self):
        example = case(split="validation")
        p = present(example)
        expected = {
            dict(p.aliases)[r.option]: r.value
            for r in example.table.records
            if r.context == example.target_context
        }
        self.assertEqual(public_values(example, p), expected)
        self.assertEqual(public_values(replace(example, objective="conditional_min"), p), expected)
        text = joint_prompt(example, p)
        skeleton = json.loads(text.split("not an answer: ")[1])
        self.assertEqual(list(skeleton), ["values", "choice"])
        self.assertTrue(all(v is None for v in skeleton["values"].values()))
        self.assertIsNone(skeleton["choice"])

    def test_joint_requires_values_before_choice_and_rejects_duplicate_keys(self):
        for text in [
            '{"choice":"A","values":{"A":1}}',
            '{"values":{"A":1,"A":2},"choice":"A"}',
            '{"values":{"A":1},"choice":"A","choice":"B"}',
            '```json\n{"values":{"A":1},"choice":"A"}\n```',
        ]:
            _, choice, error = parse_joint(text, ["A"])
            self.assertIsNone(choice)
            self.assertIsNotNone(error)
        values, choice, error = parse_joint('{"values":{"A":1.2},"choice":"A"}', ["A"])
        self.assertEqual((values, choice, error), ({"A": 1.2}, "A", None))

    def test_value_format_failure_is_separate_from_parseable_choice(self):
        for value in ["true", "null", '"1.0"', "NaN"]:
            values, choice, error = parse_joint(
                '{"values":{"A":' + value + '},"choice":"A"}', ["A"]
            )
            self.assertIsNone(values)
            self.assertEqual(choice, "A")
            self.assertIsNotNone(error)


class ControlWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.dataset = self.root / "dataset"
        self.example = case(split="validation")
        self.minimum = replace(self.example, case_id="case-min", objective="conditional_min")
        write_jsonl(self.dataset / "cases.jsonl", map(case_to_dict, [self.example, self.minimum]))
        freeze(self.dataset, {})
        self.model = self.root / "model"
        self.model.mkdir()
        self.metadata = {
            "model_path": str(self.model.resolve()),
            "adapter_path": None,
            "model_files_sha256": {},
            "adapter_files_sha256": {},
            "thinking_mode": "off",
            "chat_template": True,
            "decoding": "greedy",
            "dtype": "torch.bfloat16",
            "attention": "eager",
        }
        expected = {}
        for variant in ["canonical", "shuffled"]:
            p = present_order(self.example, variant)
            prompts, answers = build_requests(self.example, p)
            for kind in ["value", "relation"]:
                expected[prompts[kind]] = json.dumps({"values": answers[kind]})
            expected[prompts["decision"]] = json.dumps({"choice": "A"})
        metadata = self.metadata

        class FakeV2:
            def __init__(self):
                self.metadata = metadata

            def complete(self, prompt):
                return Completion(expected[prompt], 20, 10)

        self.cache_dir = self.root / "cache"
        spec = v2_plan(self.dataset, [self.example], ["canonical", "shuffled"], [0], "diagnose")
        v2_run(
            self.dataset,
            self.cache_dir,
            FakeV2(),
            [self.example],
            ["canonical", "shuffled"],
            [0],
            "diagnose",
            spec,
        )
        self.cache = load_cache(self.dataset, self.cache_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def fake_backend(self, fail_after=None):
        metadata = self.metadata
        expected = {}
        for c in [self.example, self.minimum]:
            for kind, variant, prompt, values in requests_for(c, self.cache):
                if kind == "joint":
                    values = public_values(c, present_order(c, variant))
                    answer = {"values": values, "choice": choose_from_values(values, c.objective)}
                else:
                    answer = {"choice": choose_from_values(values, c.objective)}
                expected[prompt] = json.dumps(answer)

        class Fake:
            def __init__(self):
                self.metadata = metadata
                self.calls = 0

            def complete(self, prompt):
                if self.calls == fail_after:
                    raise RuntimeError("test interruption")
                self.calls += 1
                return Completion(expected[prompt], 15, 10)

        return Fake()

    def specification(self):
        return make_plan(
            self.dataset, self.cache_dir, [self.example, self.minimum], self.cache, self.model, None
        )

    def test_same_direction_free_readout_is_reused_without_gold_repair(self):
        self.assertEqual(cache_key(self.example, "canonical"), cache_key(self.minimum, "canonical"))
        cached = self.cache[cache_key(self.example, "canonical")]
        cached["values"] = {"A": 321.0, "B": 0.0, "C": 1.0, "D": 2.0}
        request = next(
            r
            for r in requests_for(self.example, self.cache)
            if r[:2] == ("cached_compare", "canonical")
        )
        self.assertIn('"A":321.0', request[2])
        self.assertEqual(request[3], cached["values"])

    def test_budget_counts_skips_and_rejects_wrong_adapter(self):
        self.assertEqual(self.specification()["requests"], 10)
        self.cache[cache_key(self.example, "canonical")]["values"] = None
        plan = self.specification()
        self.assertEqual(plan["requests"], 8)
        self.assertEqual(plan["skipped_upstream_invalid"], {"cached_compare": 2})
        with self.assertRaises(ValueError):
            make_plan(
                self.dataset,
                self.cache_dir,
                [self.example],
                self.cache,
                self.model,
                self.root / "wrong-adapter",
            )

    def test_complete_workflow_logs_costs_and_correct_decisions(self):
        out = self.root / "run"
        report = run(
            self.dataset,
            self.cache_dir,
            out,
            self.fake_backend(),
            [self.example, self.minimum],
            self.cache,
            self.specification(),
        )
        self.assertEqual(report["requests"], 10)
        self.assertEqual(len(read_jsonl(out / "responses.jsonl")), 10)
        self.assertTrue(all(r["all_attempt_accuracy"] == 1.0 for r in report["endpoints"].values()))
        cost = report["costs"]["conditional_max/canonical/cached_compare"]
        self.assertEqual(cost["upstream_calls_per_standalone_workflow"], 1)
        self.assertEqual(cost["upstream_input_tokens_per_standalone_workflow"], 20)
        self.assertTrue((out / "code_snapshot/run_v3.py").exists())

    def test_interruption_preserves_completed_requests_without_summary(self):
        out = self.root / "interrupted"
        with self.assertRaises(RuntimeError):
            run(
                self.dataset,
                self.cache_dir,
                out,
                self.fake_backend(fail_after=2),
                [self.example, self.minimum],
                self.cache,
                self.specification(),
            )
        self.assertEqual(len(read_jsonl(out / "responses.jsonl")), 2)
        self.assertFalse((out / "summary.json").exists())
        self.assertEqual(read_json(out / "failure.json")["completed_requests"], 2)

    def test_cache_prompt_mutation_is_rejected(self):
        path = self.cache_dir / "responses.jsonl"
        payload = read_jsonl(path)
        next(r for r in payload if r["kind"] == "relation")["prompt"] += " changed"
        path.write_text("\n".join(json.dumps(r) for r in payload) + "\n")
        with self.assertRaises(ValueError):
            load_cache(self.dataset, self.cache_dir)


if __name__ == "__main__":
    unittest.main()
