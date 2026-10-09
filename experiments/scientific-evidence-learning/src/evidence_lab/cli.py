"""Explicit, composable experiment commands. Default commands never use the network."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import sys
from pathlib import Path

from .storage import read_json, verify, write_jsonl


def thinking_value(mode: str) -> bool | None:
    """Translate the user-facing mode into the tokenizer flag.

    ``None`` means omit the keyword and use the tokenizer/model default.  We keep
    this distinct from ``False`` because Qwen3's default is thinking enabled.
    """
    if mode == "auto":
        return None
    if mode == "on":
        return True
    if mode == "off":
        return False
    raise ValueError(f"Unknown thinking mode: {mode}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    prep = commands.add_parser("prepare")
    prep.add_argument("--config", type=Path, required=True)
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument("--difficulty", type=Path)
    check = commands.add_parser("verify")
    check.add_argument("--dataset", type=Path, required=True)
    for name in (
        "rules",
        "blind",
        "blind-evaluate",
        "evaluate",
        "difficulty",
        "diagnose",
        "intervene",
        "train",
    ):
        cmd = commands.add_parser(name)
        cmd.add_argument("--dataset", type=Path, required=True)
        cmd.add_argument("--out", type=Path, required=True)
        if name in {"rules", "blind", "evaluate", "blind-evaluate"}:
            cmd.add_argument(
                "--split", choices=["train", "validation", "test", "all"], default="validation"
            )
        if name in {"evaluate", "difficulty", "diagnose", "intervene", "train", "blind-evaluate"}:
            cmd.add_argument("--model", type=Path, required=True)
            cmd.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
            cmd.add_argument(
                "--thinking-mode",
                choices=["auto", "on", "off"],
                default="auto",
                help="Chat-template thinking flag; auto omits the keyword",
            )
        if name in {"evaluate", "difficulty", "diagnose", "intervene", "blind-evaluate"}:
            cmd.add_argument("--plain-text", action="store_true")
            cmd.add_argument("--max-length", type=int, default=8192)
            cmd.add_argument("--max-new-tokens", type=int, default=256)
            cmd.add_argument("--adapter", type=Path)
        if name in {"evaluate", "diagnose"}:
            cmd.add_argument(
                "--variants",
                nargs="+",
                default=["canonical", "reversed", "shuffled", "structured", "checklist"],
            )
            cmd.add_argument("--limit", type=int, default=12 if name == "diagnose" else None)
        if name == "intervene":
            cmd.add_argument(
                "--module", required=True, help="Exact get_submodule path, e.g. model.layers.12"
            )
            cmd.add_argument("--record-index", type=int, default=0)
            cmd.add_argument("--limit", type=int, default=4)
        if name == "blind-evaluate":
            cmd.add_argument("--budget", type=int, default=2)
            cmd.add_argument("--episodes", type=int, default=12)
            cmd.add_argument("--seed", type=int, default=71)
        if name == "train":
            cmd.add_argument("--config", type=Path, required=True)
            cmd.add_argument(
                "--arm",
                choices=[
                    "uniform",
                    "low_disagreement",
                    "high_disagreement",
                    "random_order_augmentation",
                    "hard_examples",
                ],
                required=True,
            )
    return p


def doctor() -> dict:
    deps = {}
    for name in ("torch", "transformers", "peft", "accelerate", "modelscope"):
        found = importlib.util.find_spec(name) is not None
        deps[name] = {
            "present": found,
            "version": importlib.metadata.version(name) if found else None,
        }
    return {
        "python": sys.version,
        "packages": deps,
        "network_used": False,
        "model_weight_check": "Pass an explicit complete local snapshot to model commands",
    }


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        from . import workflows as w

        if args.command == "doctor":
            result = doctor()
        elif args.command == "prepare":
            result = w.prepare(args.config, args.out, args.difficulty)
        elif args.command == "verify":
            m = verify(args.dataset)
            result = {"verified": True, "artifacts": len(m["files"]), "sources": len(m["sources"])}
        elif args.command == "rules":
            result = w.run_rule_baselines(args.dataset, args.out, args.split)
        elif args.command == "blind":
            result = w.run_blind_baselines(args.dataset, args.out, args.split)
            result = {k: v for k, v in result.items() if k != "table_audits"}
        elif args.command == "train":
            from .training import run_training

            verify(args.dataset)
            config = read_json(args.config)
            if args.thinking_mode != "auto":
                config["enable_thinking"] = thinking_value(args.thinking_mode)
            result = run_training(
                args.model,
                args.dataset / "training" / f"{args.arm}.jsonl",
                config,
                args.out,
                args.device,
            )
        else:
            from .models import HuggingFaceModel

            verify(args.dataset)  # fail before loading weights if frozen inputs changed
            backend = HuggingFaceModel(
                args.model,
                device=args.device,
                max_length=args.max_length,
                max_new_tokens=args.max_new_tokens,
                use_chat_template=not args.plain_text,
                enable_thinking=thinking_value(args.thinking_mode),
                adapter_path=args.adapter,
            )
            if args.command == "evaluate":
                result = w.evaluate(
                    args.dataset, args.out, args.split, backend, args.variants, args.limit
                )
            elif args.command == "blind-evaluate":
                from .blind_agent import evaluate_blind

                result = evaluate_blind(
                    args.dataset,
                    args.out,
                    backend,
                    args.budget,
                    args.episodes,
                    args.seed,
                    args.split,
                )
            elif args.command == "intervene":
                from .mechanism import run_interventions

                result = run_interventions(
                    args.dataset, args.out, backend, args.module, args.record_index, args.limit
                )
            elif args.command == "diagnose":
                from .readouts import run_readouts

                result = run_readouts(args.dataset, args.out, backend, args.variants, args.limit)
            else:
                from .sampling import training_pool
                from .tasks import diagnostics, present

                cases = training_pool(w.load_cases(args.dataset, "train"))
                w.new_run(args.out, backend)
                rows = []
                for case in cases:
                    p = present(case)
                    label = dict(p.aliases)[diagnostics(case)["gold"][0]]
                    answer = json.dumps({"choice": label}, separators=(",", ":"))
                    rows.append(
                        {
                            "case_id": case.case_id,
                            "nll": backend.answer_losses(p.prompt, [answer])[0],
                        }
                    )
                write_jsonl(args.out / "difficulty.jsonl", rows)
                result = {
                    "training_cases": len(rows),
                    "out": str(args.out),
                    "scientific_conclusion": None,
                }
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, FileExistsError, FileNotFoundError, ImportError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
