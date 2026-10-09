"""Ordinary completion-only SFT using upstream Trainer and PEFT.

No custom optimizer, scheduler, attention implementation, or claimed new loss.
This isolates the proposed data intervention before adding training components.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .models import completion_features
from .storage import digest, read_jsonl, write_json


class CompletionCollator:
    def __init__(self, pad_token_id: int):
        self.pad_token_id = pad_token_id

    def __call__(self, features: list[dict]) -> dict:
        import torch

        width = max(len(row["input_ids"]) for row in features)
        batch = {key: [] for key in ("input_ids", "attention_mask", "labels")}
        for row in features:
            for key, pad in (
                ("input_ids", self.pad_token_id),
                ("attention_mask", 0),
                ("labels", -100),
            ):
                batch[key].append(row[key] + [pad] * (width - len(row[key])))
        return {k: torch.tensor(v, dtype=torch.long) for k, v in batch.items()}


def tokenize_training(tokenizer, rows: list[dict], config: dict) -> tuple[list[dict], dict]:
    if not rows or any(r.get("split") != "train" for r in rows):
        raise ValueError("Only explicitly marked training rows may enter SFT")
    if len({r["case_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate training case IDs")
    features = [
        completion_features(
            tokenizer,
            r["prompt"],
            r["completion"],
            config["max_length"],
            config["use_chat_template"],
            config.get("enable_thinking"),
        )
        for r in rows
    ]
    lengths = [len(f["input_ids"]) for f in features]
    return features, {
        "examples": len(rows),
        "input_tokens_per_epoch": sum(lengths),
        "max_sequence_tokens": max(lengths),
        "supervised_tokens_per_epoch": sum(sum(v != -100 for v in f["labels"]) for f in features),
        "completion_counts": dict(Counter(r["completion"] for r in rows)),
        "truncation": "forbidden",
        "loss": "ordinary completion-only causal language-model cross entropy",
    }


def run_training(model_path: Path, train_path: Path, config: dict, out: Path, device: str) -> dict:
    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import Trainer, TrainingArguments, set_seed

    from .models import HuggingFaceModel

    if out.exists():
        raise FileExistsError("Use a new training output directory")
    enable_thinking = config.get("enable_thinking")
    if enable_thinking not in (None, True, False):
        raise ValueError("enable_thinking must be true, false, or null")
    set_seed(config["seed"])
    backend = HuggingFaceModel(
        model_path,
        device=device,
        max_length=config["max_length"],
        use_chat_template=config["use_chat_template"],
        enable_thinking=enable_thinking,
    )
    rows = read_jsonl(train_path)
    features, token_audit = tokenize_training(backend.tokenizer, rows, config)
    model = get_peft_model(
        backend.model,
        LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=config["lora_rank"],
            lora_alpha=config["lora_alpha"],
            lora_dropout=config["lora_dropout"],
            target_modules=config["target_modules"],
            bias="none",
        ),
    )
    model.config.use_cache = False
    if config["gradient_checkpointing"]:
        model.enable_input_require_grads()
    bf16 = config["precision"] == "bfloat16" and device.startswith("cuda")
    if bf16 and not torch.cuda.is_bf16_supported():
        raise ValueError("Requested bfloat16 is unsupported by this GPU")
    out.mkdir(parents=True)
    write_json(
        out / "inputs.json",
        {
            "model_path": str(model_path.resolve()),
            "training_file_sha256": digest(train_path),
            "config": config,
            "device": device,
            "effective_precision": "bfloat16" if bf16 else "float32",
            "token_audit": token_audit,
            "model_files_sha256": backend.metadata["model_files_sha256"],
            "model_metadata": backend.metadata,
        },
    )
    arguments = TrainingArguments(
        output_dir=str(out / "checkpoints"),
        max_steps=config["max_steps"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config["warmup_ratio"],
        weight_decay=config["weight_decay"],
        max_grad_norm=config["max_grad_norm"],
        lr_scheduler_type="cosine",
        optim="adamw_torch",
        bf16=bf16,
        fp16=False,
        use_cpu=device == "cpu",
        gradient_checkpointing=config["gradient_checkpointing"],
        gradient_checkpointing_kwargs={"use_reentrant": False},
        save_strategy="no",
        eval_strategy="no",
        logging_steps=1,
        seed=config["seed"],
        data_seed=config["seed"],
        report_to=[],
        dataloader_num_workers=0,
        remove_unused_columns=False,
    )
    trainer = Trainer(
        model=model,
        args=arguments,
        train_dataset=features,
        data_collator=CompletionCollator(backend.tokenizer.pad_token_id),
    )
    result = trainer.train()
    trainer.save_model(str(out / "adapter"))
    backend.tokenizer.save_pretrained(str(out / "adapter"))
    trainer.save_state()
    report = {
        "metrics": result.metrics,
        "global_step": trainer.state.global_step,
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "scientific_conclusion": None,
        "budget_note": "Fixed steps/batch; actual token exposure and elapsed time must also be compared across arms.",
    }
    write_json(out / "training_result.json", report)
    return report
