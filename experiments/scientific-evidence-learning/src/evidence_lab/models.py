"""Model ports and a local Hugging Face adapter; no credentials or hidden labels."""

from __future__ import annotations

import importlib.metadata
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .storage import digest


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int


class TextModel(Protocol):
    def complete(self, prompt: str) -> Completion: ...


def parse_choice(text: str) -> str | None:
    """Same strict single-object policy as the existing Responses pilot parser."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(value, dict) or set(value) != {"choice"}:
        return None
    return value["choice"] if isinstance(value["choice"], str) else None


def render_prompt(
    tokenizer,
    prompt: str,
    use_chat_template: bool,
    enable_thinking: bool | None = None,
) -> str:
    if use_chat_template:
        if not tokenizer.chat_template:
            raise ValueError(
                "This tokenizer has no chat template; explicitly select plain-text mode"
            )
        kwargs = {"tokenize": False, "add_generation_prompt": True}
        if enable_thinking is not None:
            # Do not catch TypeError here: an unsupported thinking-mode argument is a
            # model/template compatibility error and must be visible in the run.
            kwargs["enable_thinking"] = enable_thinking
        return tokenizer.apply_chat_template([{"role": "user", "content": prompt}], **kwargs)
    return prompt


def completion_features(
    tokenizer,
    prompt: str,
    answer: str,
    max_length: int,
    use_chat_template: bool,
    enable_thinking: bool | None = None,
) -> dict:
    text = render_prompt(tokenizer, prompt, use_chat_template, enable_thinking)
    prefix = tokenizer.encode(text, add_special_tokens=False)
    target = tokenizer.encode(answer, add_special_tokens=False)
    if tokenizer.eos_token_id is None:
        raise ValueError("Tokenizer needs an explicit EOS token")
    target.append(tokenizer.eos_token_id)
    if not prefix or len(prefix) + len(target) > max_length:
        raise ValueError("Empty prefix or sequence exceeds limit; silent truncation is forbidden")
    return {
        "input_ids": prefix + target,
        "attention_mask": [1] * (len(prefix) + len(target)),
        "labels": [-100] * len(prefix) + target,
    }


class HuggingFaceModel:
    """Load only an explicitly supplied local snapshot; never download on import/run."""

    def __init__(
        self,
        model_path: Path,
        *,
        device: str = "cpu",
        max_length: int = 8192,
        max_new_tokens: int = 64,
        use_chat_template: bool = True,
        enable_thinking: bool | None = None,
        adapter_path: Path | None = None,
    ):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if not model_path.is_dir():
            raise ValueError("Supply a complete local model directory")
        if max_length < 1 or max_new_tokens < 1:
            raise ValueError("Token limits must be positive")
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise ValueError("CUDA was selected but is unavailable")
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(model_path), local_files_only=True, trust_remote_code=False, use_fast=True
        )
        dtype = torch.bfloat16 if device.startswith("cuda") else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            local_files_only=True,
            trust_remote_code=False,
            dtype=dtype,
            attn_implementation="eager",
        )
        if adapter_path is not None:
            from peft import PeftModel

            self.model = PeftModel.from_pretrained(
                self.model, str(adapter_path), is_trainable=False
            )
        self.model.to(device).eval()
        self.device, self.max_length = device, max_length
        self.max_new_tokens = max_new_tokens
        self.use_chat_template = use_chat_template
        self.enable_thinking = enable_thinking
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.metadata = {
            "model_path": str(model_path.resolve()),
            "model_files_sha256": {
                p.name: digest(p)
                for p in sorted(model_path.iterdir())
                if p.is_file() and p.suffix in {".json", ".safetensors", ".bin", ".model"}
            },
            "adapter_path": str(adapter_path.resolve()) if adapter_path else None,
            "adapter_files_sha256": (
                {p.name: digest(p) for p in sorted(adapter_path.iterdir()) if p.is_file()}
                if adapter_path
                else {}
            ),
            "device": device,
            "dtype": str(dtype),
            "chat_template": use_chat_template,
            "enable_thinking": enable_thinking,
            "thinking_mode": (
                "auto" if enable_thinking is None else "on" if enable_thinking else "off"
            ),
            "max_length": max_length,
            "max_new_tokens": max_new_tokens,
            "versions": {
                name: importlib.metadata.version(name) for name in ("torch", "transformers")
            },
            "decoding": "greedy",
            "attention": "eager",
            "network_used": False,
        }

    def complete(self, prompt: str) -> Completion:
        import torch

        text = render_prompt(self.tokenizer, prompt, self.use_chat_template, self.enable_thinking)
        inputs = self.tokenizer(
            text, add_special_tokens=False, return_tensors="pt", return_token_type_ids=False
        ).to(self.device)
        n = inputs.input_ids.shape[1]
        if n + self.max_new_tokens > self.max_length:
            raise ValueError("Prompt plus generation budget exceeds context limit")
        with torch.inference_mode():
            result = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        new = result[0, n:]
        return Completion(self.tokenizer.decode(new, skip_special_tokens=True), n, len(new))

    def answer_losses(self, prompt: str, answers: list[str]) -> list[float]:
        """Mean completion-token NLL; used for explicit forced-choice mechanism diagnostics."""
        import torch

        losses = []
        with torch.inference_mode():
            for answer in answers:
                features = completion_features(
                    self.tokenizer,
                    prompt,
                    answer,
                    self.max_length,
                    self.use_chat_template,
                    self.enable_thinking,
                )
                batch = {k: torch.tensor([v], device=self.device) for k, v in features.items()}
                losses.append(float(self.model(**batch, use_cache=False).loss))
        return losses
