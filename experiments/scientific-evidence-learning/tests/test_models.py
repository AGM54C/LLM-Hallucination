import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

from helpers import PROJECT, case

from evidence_lab.data import case_to_dict
from evidence_lab.interventions import capture_token, patch_token
from evidence_lab.models import HuggingFaceModel, completion_features, render_prompt
from evidence_lab.storage import freeze, read_json, write_jsonl
from evidence_lab.training import CompletionCollator, run_training

HAS_MODELS = (
    importlib.util.find_spec("transformers") is not None
    and importlib.util.find_spec("peft") is not None
)


class PromptRenderingTests(unittest.TestCase):
    def test_thinking_flag_is_forwarded_and_unsupported_flags_are_visible(self):
        class Tokenizer:
            chat_template = "fixture"

            def __init__(self):
                self.calls = []

            def apply_chat_template(self, messages, **kwargs):
                self.calls.append(kwargs)
                return "rendered"

        tokenizer = Tokenizer()
        self.assertEqual(render_prompt(tokenizer, "prompt", True, False), "rendered")
        self.assertEqual(tokenizer.calls[-1]["enable_thinking"], False)
        self.assertEqual(render_prompt(tokenizer, "prompt", True, True), "rendered")
        self.assertEqual(tokenizer.calls[-1]["enable_thinking"], True)
        render_prompt(tokenizer, "prompt", True)
        self.assertNotIn("enable_thinking", tokenizer.calls[-1])

        class LegacyTokenizer:
            chat_template = "fixture"

            def apply_chat_template(self, messages, **kwargs):
                if "enable_thinking" in kwargs:
                    raise TypeError("unexpected keyword argument 'enable_thinking'")
                return "rendered"

        with self.assertRaises(TypeError):
            render_prompt(LegacyTokenizer(), "prompt", True, False)


@unittest.skipUnless(HAS_MODELS, "Optional model dependencies not installed")
class ModelIntegrationTests(unittest.TestCase):
    """A randomly initialized tiny Llama tests plumbing, NEVER scientific ability."""

    @classmethod
    def setUpClass(cls):
        import torch
        from tokenizers import Tokenizer
        from tokenizers.models import WordLevel
        from tokenizers.pre_tokenizers import Whitespace
        from transformers import LlamaConfig, LlamaForCausalLM, PreTrainedTokenizerFast

        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.old_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        torch.manual_seed(31)
        vocab = {
            word: i
            for i, word in enumerate(
                [
                    "[UNK]",
                    "[PAD]",
                    "[BOS]",
                    "[EOS]",
                    "A",
                    "B",
                    "choice",
                    "{",
                    "}",
                    '"',
                    ":",
                    ",",
                    "Select",
                    "the",
                    "highest",
                    "yield",
                    "9",
                    "2",
                    ".",
                    "Record",
                    "context",
                    "option",
                ]
            )
        }
        raw = Tokenizer(WordLevel(vocab, unk_token="[UNK]"))
        raw.pre_tokenizer = Whitespace()
        cls.tokenizer = PreTrainedTokenizerFast(
            tokenizer_object=raw,
            unk_token="[UNK]",
            pad_token="[PAD]",
            bos_token="[BOS]",
            eos_token="[EOS]",
        )
        cls.model = LlamaForCausalLM(
            LlamaConfig(
                vocab_size=len(vocab),
                hidden_size=32,
                intermediate_size=64,
                num_hidden_layers=2,
                num_attention_heads=4,
                num_key_value_heads=2,
                max_position_embeddings=1024,
                bos_token_id=2,
                eos_token_id=3,
                pad_token_id=1,
                attention_dropout=0.0,
            )
        )
        cls.snapshot = cls.root / "tiny-random-fixture"
        cls.model.save_pretrained(cls.snapshot)
        cls.tokenizer.save_pretrained(cls.snapshot)

    @classmethod
    def tearDownClass(cls):
        import torch

        torch.set_num_threads(cls.old_threads)
        cls.tmp.cleanup()

    def test_completion_mask_and_padding_do_not_train_on_prompt(self):
        a = completion_features(self.tokenizer, "Select A .", '{"choice":"A"}', 100, False)
        b = completion_features(
            self.tokenizer, "Select the highest yield .", '{"choice":"B"}', 100, False
        )
        self.assertEqual(a["labels"][:3], [-100] * 3)
        self.assertEqual(a["labels"][-1], self.tokenizer.eos_token_id)
        batch = CompletionCollator(self.tokenizer.pad_token_id)([a, b])
        self.assertTrue((batch["labels"][batch["attention_mask"] == 0] == -100).all())
        with self.assertRaises(ValueError):
            completion_features(self.tokenizer, "Select A .", "A", 2, False)

    def test_hooks_are_removed_and_identity_patch_preserves_logits(self):
        import torch

        model = self.model.eval()
        ids = torch.tensor([[4, 5, 6, 7]])
        module = model.model.layers[0]
        count = len(module._forward_hooks)
        with torch.inference_mode(), capture_token(module, 1) as captured:
            original = model(input_ids=ids).logits.clone()
        with torch.inference_mode(), patch_token(module, 1, captured["state"], "identity"):
            identity = model(input_ids=ids).logits
        self.assertTrue(torch.equal(original, identity))
        with self.assertRaises(RuntimeError), patch_token(module, 1, captured["state"]):
            raise RuntimeError("deliberate exception")
        self.assertEqual(len(module._forward_hooks), count)

    def test_local_generation_and_candidate_loss(self):
        backend = HuggingFaceModel(
            self.snapshot, device="cpu", max_length=128, max_new_tokens=2, use_chat_template=False
        )
        output = backend.complete("Select A .")
        self.assertGreaterEqual(output.output_tokens, 1)
        losses = backend.answer_losses("Select A .", ['{"choice":"A"}', '{"choice":"B"}'])
        self.assertTrue(all(math.isfinite(v) for v in losses))

    def test_full_prefix_intervention_workflow_without_download(self):
        from evidence_lab.mechanism import run_interventions

        dataset = self.root / "mechanism-data"
        write_jsonl(dataset / "cases.jsonl", [case_to_dict(case(split="validation"))])
        freeze(dataset, {})
        backend = HuggingFaceModel(
            self.snapshot, device="cpu", max_length=1024, use_chat_template=False
        )
        out = self.root / "mechanism-result"
        result = run_interventions(dataset, out, backend, "model.layers.0", 0, 1)
        self.assertEqual(result["rows"], 6)
        self.assertFalse(result["selective_mechanism_established"])
        rows = [json.loads(line) for line in (out / "scores.jsonl").read_text().splitlines()]
        scores = {r["condition"]: r["losses"] for r in rows}
        self.assertEqual(scores["identity"], scores["reversed"])
        spec = read_json(out / "specification.json")
        self.assertIn("WITHOUT final question", spec["donor"])

    def test_real_trainer_updates_lora_and_reloads_adapter(self):
        import torch
        from safetensors.torch import load_file

        rows = [
            {
                "case_id": str(i),
                "split": "train",
                "prompt": "Select the highest yield .",
                "completion": '{"choice":"A"}',
            }
            for i in range(2)
        ]
        train_path = self.root / "train.jsonl"
        write_jsonl(train_path, rows)
        config = read_json(PROJECT / "configs/train_lora.json")
        config.update(
            max_length=128,
            max_steps=2,
            gradient_accumulation_steps=1,
            gradient_checkpointing=False,
            precision="float32",
            use_chat_template=False,
            learning_rate=0.001,
        )
        out = self.root / "training"
        report = run_training(self.snapshot, train_path, config, out, "cpu")
        self.assertEqual(report["global_step"], 2)
        weights = load_file(str(out / "adapter/adapter_model.safetensors"))
        self.assertTrue(
            any(torch.count_nonzero(v) > 0 for k, v in weights.items() if "lora_B" in k)
        )
        backend = HuggingFaceModel(
            self.snapshot,
            device="cpu",
            max_length=128,
            use_chat_template=False,
            adapter_path=out / "adapter",
        )
        self.assertTrue(math.isfinite(backend.answer_losses("Select A .", ['{"choice":"A"}'])[0]))
        info = json.loads((out / "inputs.json").read_text(encoding="utf-8"))
        self.assertGreater(len(info["model_files_sha256"]), 0)


if __name__ == "__main__":
    unittest.main()
