"""Software regression checks only; no model-ability or scientific conclusions."""

import json
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path

from helpers import case

from evidence_lab.data import case_to_dict
from evidence_lab.models import Completion
from evidence_lab.storage import freeze, read_json, read_jsonl, verify, write_jsonl
from evidence_lab.tasks import present, score_choice
from evidence_lab_v2.diagnostics import (
    build_requests,
    choose_from_values,
    parse_values,
    plan,
    run,
    score_readout,
    select_cases,
)
from evidence_lab_v2.presentations import conditions, position_audit, present_order


def grouped_case():
    original = case(split="validation")
    table = replace(
        original.table,
        records=tuple(sorted(original.table.records, key=lambda r: (r.context, r.option))),
    )
    return replace(original, table=table)


class PresentationV2Tests(unittest.TestCase):
    def test_bridge_prompts_are_byte_identical_to_v1(self):
        example = grouped_case()
        for variant in ["canonical", "reversed", "shuffled"]:
            self.assertEqual(present_order(example, variant, 0), present(example, variant))

    def test_order_changes_preserve_facts_aliases_and_question(self):
        example = grouped_case()
        reference = present(example)
        for variant in ["shuffled", "block_shuffled", "within_block_shuffled"]:
            for seed in [0, 1, 2, 37]:
                changed = present_order(example, variant, seed)
                self.assertEqual(changed.aliases, reference.aliases)
                self.assertEqual(changed.question, reference.question)
                self.assertEqual(
                    Counter(changed.prefix.splitlines()), Counter(reference.prefix.splitlines())
                )
                self.assertEqual(
                    {r[0] for r in changed.record_spans}, {r[0] for r in reference.record_spans}
                )
                original_chunks = {
                    rid: reference.prefix[start:end] for rid, start, end in reference.record_spans
                }
                self.assertEqual(
                    {rid: changed.prefix[start:end] for rid, start, end in changed.record_spans},
                    original_chunks,
                )

    def test_blocks_remain_contiguous_and_within_order_is_preserved(self):
        example = grouped_case()
        contexts = {r.record_id: r.context for r in example.table.records}
        original_blocks = {
            c: [r.record_id for r in example.table.records if r.context == c]
            for c in example.table.contexts
        }
        for seed in range(5):
            changed = present_order(example, "block_shuffled", seed)
            ids = [r[0] for r in changed.record_spans]
            for context, block in original_blocks.items():
                indices = [i for i, rid in enumerate(ids) if contexts[rid] == context]
                self.assertEqual(indices, list(range(min(indices), max(indices) + 1)))
                self.assertEqual([ids[i] for i in indices], block)

    def test_within_block_permutation_keeps_context_positions(self):
        example = grouped_case()
        contexts = {r.record_id: r.context for r in example.table.records}
        original_order = [r.context for r in example.table.records]
        changed = present_order(example, "within_block_shuffled", 2)
        self.assertEqual([contexts[rid] for rid, _, _ in changed.record_spans], original_order)
        audit = position_audit(example, changed)
        self.assertEqual(audit["target_record_span_rows"], 4)

    def test_repeated_seeds_do_not_repeat_unchanged_condition(self):
        settings = conditions(["canonical", "reversed", "shuffled"], [0, 1, 2])
        self.assertEqual(len(settings), 5)
        with self.assertRaises(ValueError):
            conditions(["shuffled"], [0, 0])
        with self.assertRaises(ValueError):
            conditions(["canonical", "canonical"], [0])
        with self.assertRaises(ValueError):
            present_order(grouped_case(), "canonical", 1)


class ReadoutV2Tests(unittest.TestCase):
    def test_real_json_keys_and_null_skeleton_without_gold_instructions(self):
        example = grouped_case()
        prompts, expected = build_requests(example, present(example))
        for kind in ["value", "relation"]:
            suffix = prompts[kind].split("Use this structure", 1)[1]
            payload = json.loads(suffix.split("answer: ", 1)[1])
            self.assertEqual(set(payload["values"]), set(expected[kind]))
            self.assertTrue(all(value is None for value in payload["values"].values()))
        self.assertEqual(prompts["decision"], present(example).prompt)

    def test_duplicate_and_non_numeric_json_is_invalid(self):
        for text in [
            '{"values":{"A":1,"A":2}}',
            '{"values":{"A":1},"values":{"A":1}}',
            '{"values":{"A":true}}',
            '{"values":{"A":null}}',
            '{"values":{"A":NaN}}',
            '{"values":{"A":Infinity}}',
            '{"values":{"A":"1.0"}}',
            '{"values":{"A":1,"B":2}}',
            '```json\n{"values":{"A":1}}\n```',
        ]:
            values, error = parse_values(text, ["A"])
            self.assertIsNone(values, text)
            self.assertIsNotNone(error)
        values, error = parse_values('{"values":{"A":1.0000}}', ["A"])
        self.assertEqual(values, {"A": 1.0})
        self.assertIsNone(error)

    def test_numeric_tolerance_and_error_separation(self):
        good, _ = score_readout('{"values":{"A":1.2346}}', {"A": 1.234567})
        wrong, _ = score_readout('{"values":{"A":1.25}}', {"A": 1.234567})
        invalid, _ = score_readout('{"values":{"A":null}}', {"A": 1.234567})
        self.assertTrue(good["correct"])
        self.assertTrue(wrong["valid"])
        self.assertFalse(wrong["correct"])
        self.assertFalse(invalid["valid"])
        self.assertIsNone(invalid["correct"])

    def test_program_decision_uses_reported_values_not_gold(self):
        example = grouped_case()
        presentation = present(example)
        labels = dict(presentation.aliases)
        invented = {labels[option]: float(option == "ligand1") for option in example.table.options}
        answer = choose_from_values(invented, "conditional_max")
        self.assertEqual(answer, labels["ligand1"])
        self.assertFalse(score_choice(example, answer, presentation)["correct"])
        self.assertIsNone(choose_from_values(None, "conditional_max"))
        self.assertEqual(choose_from_values({"B": 3, "A": 3}, "conditional_min"), "A")


class WorkflowV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.dataset = self.root / "dataset"
        self.example = grouped_case()
        write_jsonl(self.dataset / "cases.jsonl", [case_to_dict(self.example)])
        self.source = self.root / "source.txt"
        self.source.write_text("original", encoding="utf-8")
        freeze(self.dataset, {"fixture": self.source})

    def tearDown(self):
        self.tmp.cleanup()

    def backend(self, fail_after=None, mutate=False):
        prompts, expected = build_requests(self.example, present(self.example))
        wrong = dict(present(self.example).aliases)["ligand1"]
        answers = [
            json.dumps({"values": expected["value"]}),
            json.dumps({"values": expected["relation"]}),
            json.dumps({"choice": wrong}),
        ]
        source = self.source

        class Fake:
            def __init__(self):
                self.prompts = []

            def complete(self, prompt):
                if fail_after is not None and len(self.prompts) == fail_after:
                    raise RuntimeError("deliberate interruption")
                self.prompts.append(prompt)
                if mutate:
                    source.write_text("changed", encoding="utf-8")
                return Completion(answers[(len(self.prompts) - 1) % len(answers)], 10, 5)

        return Fake(), prompts

    def test_streamed_run_separation_provenance_and_no_feedback(self):
        backend, prompts = self.backend()
        out = self.root / "run"
        specification = plan(self.dataset, [self.example], ["canonical"], [0], "diagnose")
        result = run(
            self.dataset,
            out,
            backend,
            [self.example],
            ["canonical"],
            [0],
            "diagnose",
            specification,
        )
        self.assertEqual(result["requests"], 3)
        self.assertEqual(backend.prompts, [prompts[k] for k in ["value", "relation", "decision"]])
        row = read_jsonl(out / "scores.jsonl")[0]
        self.assertTrue(row["scores"]["relation_program_decision"]["correct"])
        self.assertFalse(row["scores"]["decision"]["correct"])
        self.assertEqual(
            result["separations"]["conditional_max/canonical/seed=0"][
                "both_readouts_correct_decision_wrong"
            ],
            1,
        )
        self.assertTrue((out / "code_snapshot/run_v2.py").is_file())
        self.assertTrue(read_json(out / "specification.json")["code_files_sha256"])
        verify(self.dataset)
        with self.assertRaises(FileExistsError):
            run(
                self.dataset,
                out,
                backend,
                [self.example],
                ["canonical"],
                [0],
                "diagnose",
                specification,
            )

    def test_partial_requests_survive_interruption_without_complete_summary(self):
        backend, _ = self.backend(fail_after=1)
        out = self.root / "interrupted"
        specification = plan(self.dataset, [self.example], ["canonical"], [0], "diagnose")
        with self.assertRaises(RuntimeError):
            run(
                self.dataset,
                out,
                backend,
                [self.example],
                ["canonical"],
                [0],
                "diagnose",
                specification,
            )
        self.assertEqual(len(read_jsonl(out / "responses.jsonl")), 1)
        self.assertFalse((out / "summary.json").exists())
        self.assertEqual(read_json(out / "failure.json")["completed_requests"], 1)

    def test_midrun_input_mutation_prevents_success(self):
        backend, _ = self.backend(mutate=True)
        out = self.root / "mutated"
        specification = plan(self.dataset, [self.example], ["canonical"], [0], "diagnose")
        with self.assertRaises(ValueError):
            run(
                self.dataset,
                out,
                backend,
                [self.example],
                ["canonical"],
                [0],
                "diagnose",
                specification,
            )
        self.assertFalse((out / "summary.json").exists())
        self.assertTrue((out / "failure.json").exists())

    def test_default_full_split_and_smoke_group_table_coverage(self):
        examples = []
        for group in range(4):
            for block in range(3):
                for target in self.example.table.contexts:
                    table = replace(
                        self.example.table, group_id=f"g{group}", table_id=f"t{group}-{block}"
                    )
                    examples.append(
                        replace(
                            self.example,
                            table=table,
                            target_context=target,
                            case_id=f"{group}-{block}-{target}",
                        )
                    )
        dataset = self.root / "larger"
        write_jsonl(dataset / "cases.jsonl", map(case_to_dict, examples))
        freeze(dataset, {})
        selected = select_cases(dataset, ["conditional_max"])
        self.assertEqual(len(selected), 24)
        smoke = select_cases(dataset, ["conditional_max"], 12)
        self.assertEqual(len({c.table.group_id for c in smoke}), 4)
        self.assertEqual(len({c.table.table_id for c in smoke}), 12)
        self.assertEqual(smoke, select_cases(dataset, ["conditional_max"], 12))
        preview = plan(dataset, selected, ["canonical", "shuffled"], [0], "diagnose")
        self.assertEqual(preview["requests"], 144)


if __name__ == "__main__":
    unittest.main()
