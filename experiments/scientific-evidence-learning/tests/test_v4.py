"""Semantic invariance, factorial coverage and recovery; synthetic fixtures only."""

import copy
import json
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path

from helpers import case

from evidence_lab.data import case_to_dict
from evidence_lab.models import Completion
from evidence_lab.storage import digest, freeze, read_json, read_jsonl, write_json, write_jsonl
from evidence_lab_v2.diagnostics import choose_from_values
from evidence_lab_v2.presentations import present_order
from evidence_lab_v3.controls import joint_prompt as v3_prompt
from evidence_lab_v3.controls import public_values
from evidence_lab_v4.factorial import (
    conditions_for,
    joint_prompt,
    parse_joint,
    remap_presentation,
    score_response,
    select_paired_cases,
    validate_protocol,
)
from evidence_lab_v4.reporting import summarize
from evidence_lab_v4.runner import DEFAULT_CONFIG, load_reference, make_plan, run, verify_run


class FactorialTests(unittest.TestCase):
    def setUp(self):
        self.example = case(split="validation")
        self.protocol = read_json(DEFAULT_CONFIG)

    def test_mapping_keeps_physical_records_and_changes_every_occurrence(self):
        for variant in ("canonical", "shuffled"):
            original = present_order(self.example, variant)
            self.assertEqual(remap_presentation(self.example, variant, 0), original)
            occurrences = {}
            for rotation in range(4):
                presentation = remap_presentation(self.example, variant, rotation)
                self.assertEqual(
                    [r[0] for r in original.record_spans], [r[0] for r in presentation.record_spans]
                )
                self.assertEqual(
                    [o for o, _ in original.aliases], [o for o, _ in presentation.aliases]
                )
                mapping = dict(presentation.aliases)
                records = {r.record_id: r for r in self.example.table.records}
                for rid, start, end in presentation.record_spans:
                    record = records[rid]
                    line = presentation.prefix[start:end]
                    self.assertIn(
                        f"option {mapping[record.option]} has recorded yield {record.value!r}", line
                    )
                    self.assertIn(f"substrate {record.context}", line)
                values = public_values(self.example, presentation)
                for option, alias in presentation.aliases:
                    occurrences.setdefault(option, []).append(alias)
                    expected = next(
                        r.value
                        for r in self.example.table.records
                        if r.option == option and r.context == self.example.target_context
                    )
                    self.assertEqual(values[alias], expected)
            self.assertTrue(all(sorted(v) == list("ABCD") for v in occurrences.values()))

    def test_full_cross_is_independent_of_answers_and_shared_by_max_min(self):
        cells = conditions_for(self.example, self.protocol)
        self.assertEqual(len(cells), 8)
        self.assertEqual(Counter(c["alias_rotation"] for c in cells), {0: 2, 1: 2, 2: 2, 3: 2})
        self.assertEqual(Counter(c["output_order"] for c in cells), {"ABCD": 4, "CDAB": 4})
        minimum = replace(self.example, objective="conditional_min", case_id="min")
        self.assertEqual(cells, conditions_for(minimum, self.protocol))
        changed = replace(
            self.example,
            table=replace(
                self.example.table,
                records=tuple(replace(r, value=100 - r.value) for r in self.example.table.records),
            ),
        )
        self.assertEqual(cells, conditions_for(changed, self.protocol))

    def test_only_order_instruction_and_null_skeleton_change_with_output_order(self):
        presentation = remap_presentation(self.example, "shuffled", 2)
        a = joint_prompt(self.example, presentation, "ABCD")
        b = joint_prompt(self.example, presentation, "CDAB")
        before_a, skeleton_a = a.split("null is not an answer: ")
        before_b, skeleton_b = b.split("null is not an answer: ")
        self.assertEqual(before_a.replace("A, B, C, D", "C, D, A, B"), before_b)
        for text, order in ((skeleton_a, "ABCD"), (skeleton_b, "CDAB")):
            obj = json.loads(text)
            self.assertEqual(list(obj["values"]), list(order))
            self.assertTrue(all(v is None for v in obj["values"].values()))
            self.assertIsNone(obj["choice"])

    def test_actual_order_is_preserved_and_noncompliance_not_a_missing_choice(self):
        text = '{"choice":"A","values":{"C":3,"D":4,"A":1,"B":2}}'
        result = parse_joint(text, "ABCD")
        self.assertEqual(result["choice"], "A")
        self.assertEqual(result["actual_output_order"], list("CDAB"))
        self.assertFalse(result["outer_order_compliant"])
        self.assertFalse(result["output_order_compliant"])

    def test_reject_ambiguous_or_nonfinite_numbers_and_multichar_choices(self):
        for text in (
            '{"values":{"A":1,"A":2,"B":3,"C":4,"D":5},"choice":"A"}',
            '```json\n{"values":{"A":1,"B":2,"C":3,"D":4},"choice":"A"}\n```',
        ):
            parsed = parse_joint(text, "ABCD")
            self.assertIsNone(parsed["values"])
            self.assertIsNone(parsed["choice"])
        for value in ("true", '"1.0"', "NaN", "null", "1e999"):
            parsed = parse_joint(
                '{"values":{"A":' + value + ',"B":2,"C":3,"D":4},"choice":"A"}', "ABCD"
            )
            self.assertIsNone(parsed["values"])
            self.assertEqual(parsed["choice"], "A")
        for choice in ("", "AB", "BCD", "E"):
            parsed = parse_joint(
                json.dumps({"values": dict.fromkeys("ABCD", 1), "choice": choice}), "ABCD"
            )
            self.assertIsNone(parsed["choice"])

    def test_scoring_uses_semantic_identity_after_every_mapping_and_objective(self):
        for objective in ("conditional_max", "conditional_min"):
            example = replace(self.example, objective=objective)
            for condition in conditions_for(example, self.protocol):
                presentation = remap_presentation(
                    example, condition["variant"], condition["alias_rotation"]
                )
                values = public_values(example, presentation)
                choice = choose_from_values(values, objective)
                response = json.dumps(
                    {"values": {a: values[a] for a in condition["output_order"]}, "choice": choice}
                )
                result = score_response(example, condition, presentation, response)
                self.assertTrue(result["scores"]["decision"]["correct"])
                self.assertEqual(result["scores"]["decision"]["regret_pp"], 0)
                self.assertTrue(result["compliant"])
                self.assertTrue(result["optimum_set_preserved"])

    def test_rounding_changed_optimum_is_not_labeled_clean_comparison_error(self):
        # Rounded numbers can be within readout tolerance but change the winner set.
        records = tuple(
            replace(
                r,
                value={"ligand0": 1.0002, "ligand1": 1.0001, "ligand2": 0.0, "ligand3": 0.0}[
                    r.option
                ],
            )
            for r in self.example.table.records
        )
        example = replace(self.example, table=replace(self.example.table, records=records))
        condition = {"variant": "shuffled", "alias_rotation": 0, "output_order": "ABCD"}
        presentation = remap_presentation(example, "shuffled", 0)
        aliases = dict(presentation.aliases)
        values = {a: round(v, 3) for a, v in public_values(example, presentation).items()}
        result = score_response(
            example,
            condition,
            presentation,
            json.dumps({"values": values, "choice": aliases["ligand1"]}),
        )
        self.assertTrue(result["scores"]["values"]["correct"])
        self.assertFalse(result["scores"]["decision"]["correct"])
        self.assertFalse(result["optimum_set_preserved"])
        self.assertFalse(result["clean_value_choice_error"])

    def test_protocol_rejects_partial_mapping_and_duplicate_cells(self):
        for key, value in (
            ("alias_rotations", [0, 2]),
            ("alias_rotations", [False, 1, 2, 3]),
            ("output_orders", ["ABCD", "ABCD"]),
            ("output_orders", ["ABCD", "ABCC"]),
            ("variants", ["test"]),
            ("max_new_tokens", 0),
        ):
            protocol = {**self.protocol, key: value}
            with self.assertRaises(ValueError):
                validate_protocol(protocol)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.dataset, self.reference, self.model = [self.root / n for n in ("data", "v3", "model")]
        self.reference.mkdir()
        self.model.mkdir()
        example = case(split="validation")
        self.cases = [example, replace(example, case_id="min", objective="conditional_min")]
        write_jsonl(self.dataset / "cases.jsonl", map(case_to_dict, self.cases))
        freeze(self.dataset, {})
        self.protocol = read_json(DEFAULT_CONFIG)
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
            "max_length": 8192,
            "max_new_tokens": 256,
        }
        rows = []
        for example in self.cases:
            for kind, variant in [
                ("public_compare", "canonical"),
                ("cached_compare", "canonical"),
                ("cached_compare", "shuffled"),
                ("joint", "canonical"),
                ("joint", "shuffled"),
            ]:
                presentation = present_order(example, variant)
                values = public_values(example, presentation)
                response = json.dumps(
                    {
                        "values": {a: values[a] for a in "ABCD"},
                        "choice": choose_from_values(values, example.objective),
                    }
                )
                condition = {"variant": variant, "alias_rotation": 0, "output_order": "ABCD"}
                evaluation = score_response(example, condition, presentation, response)
                rows.append(
                    {
                        "case_id": example.case_id,
                        "kind": kind,
                        "variant": variant,
                        "order_seed": 0,
                        "executed": True,
                        "prompt": v3_prompt(example, presentation),
                        "response": response,
                        "scores": evaluation["scores"],
                    }
                )
        write_json(
            self.reference / "specification.json",
            {
                "schema": "behavior-controls-v3",
                "dataset_freeze_sha256": digest(self.dataset / "freeze.json"),
                "cases": 2,
                "case_ids": [c.case_id for c in self.cases],
                "requests": 10,
                "split": "validation",
                "order_seed": 0,
            },
        )
        write_json(self.reference / "summary.json", {"status": "complete"})
        write_json(self.reference / "model.json", self.metadata)
        write_jsonl(self.reference / "responses.jsonl", rows)
        self.refs = load_reference(self.dataset, self.reference, self.cases)
        self.plan = make_plan(
            self.dataset, self.reference, self.cases, self.protocol, self.model, None, None
        )

    def tearDown(self):
        self.tmp.cleanup()

    def backend(self, fail_after=None):
        answers = {}
        for example in self.cases:
            for condition in conditions_for(example, self.protocol):
                presentation = remap_presentation(
                    example, condition["variant"], condition["alias_rotation"]
                )
                values = public_values(example, presentation)
                answers[joint_prompt(example, presentation, condition["output_order"])] = (
                    json.dumps(
                        {
                            "values": {a: values[a] for a in condition["output_order"]},
                            "choice": choose_from_values(values, example.objective),
                        }
                    )
                )
        metadata = self.metadata

        class Fake:
            def __init__(self):
                self.metadata = metadata
                self.calls = 0

            def complete(self, prompt):
                if self.calls == fail_after:
                    raise RuntimeError("synthetic interruption")
                self.calls += 1
                return Completion(answers[prompt], 100, 80)

        return Fake()

    def test_full_run_replays_exactly_and_all_cells_are_present(self):
        out = self.root / "run"
        result = run(out, self.backend(), self.cases, self.refs, self.plan)
        self.assertEqual(result["requests"], 16)
        self.assertEqual(result["all_assignments"]["compliant"], 16)
        self.assertEqual(verify_run(out), result)
        self.assertTrue((out / "errors.csv").is_file())
        self.assertTrue(
            all(v["accuracy_delta_pp"] == 0 for v in result["paired_contrasts"].values())
        )
        with self.assertRaises(FileExistsError):
            run(out, self.backend(), self.cases, self.refs, self.plan)

    def test_interruption_retains_finished_rows_and_no_success_marker(self):
        out = self.root / "run"
        with self.assertRaises(RuntimeError):
            run(out, self.backend(fail_after=3), self.cases, self.refs, self.plan)
        self.assertEqual(len(read_jsonl(out / "responses.jsonl")), 3)
        self.assertEqual(read_json(out / "failure.json")["completed_requests"], 3)
        self.assertFalse((out / "summary.json").exists())

    def test_rescoring_rejects_mutated_prompt(self):
        out = self.root / "run"
        run(out, self.backend(), self.cases, self.refs, self.plan)
        rows = read_jsonl(out / "responses.jsonl")
        rows[0]["prompt"] += " changed"
        (out / "responses.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "prompt"):
            verify_run(out)

    def test_reference_mismatch_and_duplicate_are_rejected_before_model_load(self):
        with self.assertRaisesRegex(ValueError, "mismatched"):
            make_plan(
                self.dataset,
                self.reference,
                self.cases,
                self.protocol,
                self.model,
                self.root / "other-adapter",
                None,
            )
        rows = read_jsonl(self.reference / "responses.jsonl")
        rows[-1] = copy.deepcopy(rows[-2])
        (self.reference / "responses.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_reference(self.dataset, self.reference, self.cases)

    def test_smoke_selects_paired_objectives_without_referencing_past_errors(self):
        selected = select_paired_cases(self.dataset, limit_blocks=1)
        self.assertEqual([c.objective for c in selected], ["conditional_max", "conditional_min"])
        self.assertEqual(selected[0].target_context, selected[1].target_context)

    def test_summary_keeps_wrong_and_noncompliant_attempts(self):
        out = self.root / "run"
        run(out, self.backend(), self.cases, self.refs, self.plan)
        rows = read_jsonl(out / "responses.jsonl")
        row = rows[0]
        row["evaluation"]["compliant"] = False
        row["evaluation"]["scores"]["decision"].update({"correct": False, "regret_pp": 9.0})
        result = summarize(rows, self.protocol)
        self.assertEqual(result["all_assignments"]["attempts"], 16)
        self.assertEqual(result["all_assignments"]["compliant"], 15)
        self.assertEqual(
            result["all_assignments"]["endpoints"]["decision"]["all_attempt_accuracy"], 15 / 16
        )


if __name__ == "__main__":
    unittest.main()
