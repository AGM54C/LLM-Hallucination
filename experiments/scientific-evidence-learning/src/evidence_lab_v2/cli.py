"""Separate versioned CLI; reads and verifies the original frozen datasets."""

import argparse
import json
import sys
from pathlib import Path

from evidence_lab.cli import thinking_value
from evidence_lab.storage import canonical

from .diagnostics import plan, run, select_cases
from .presentations import VARIANTS


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for mode in ("diagnose", "orders"):
        command = commands.add_parser(mode)
        command.add_argument("--dataset", type=Path, required=True)
        command.add_argument("--model", type=Path, required=True)
        command.add_argument("--adapter", type=Path)
        command.add_argument("--out", type=Path, required=True)
        command.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
        command.add_argument("--thinking-mode", choices=["auto", "on", "off"], default="off")
        command.add_argument("--max-length", type=int, default=8192)
        command.add_argument("--max-new-tokens", type=int, default=256)
        command.add_argument(
            "--objectives",
            nargs="+",
            choices=["conditional_max", "conditional_min"],
            default=["conditional_max"],
        )
        command.add_argument(
            "--variants",
            nargs="+",
            choices=VARIANTS,
            default=["canonical", "shuffled"] if mode == "diagnose" else list(VARIANTS),
        )
        command.add_argument(
            "--order-seeds", nargs="+", type=int, default=[0] if mode == "diagnose" else [0, 1, 2]
        )
        command.add_argument(
            "--limit", type=int, help="Optional balanced smoke subset; omitted means all cases"
        )
        command.add_argument(
            "--dry-run",
            action="store_true",
            help="Verify data and request counts without model loading or output writes",
        )
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if not (args.model / "config.json").is_file():
            raise ValueError("Supply the full local model snapshot")
        if args.adapter and not (args.adapter / "adapter_config.json").is_file():
            raise ValueError("Adapter configuration missing")
        if args.out.exists():
            raise FileExistsError("Output exists; choose a new output directory")
        if args.max_length < 1 or args.max_new_tokens < 1:
            raise ValueError("Token limits must be positive")
        cases = select_cases(args.dataset, args.objectives, args.limit)
        specification = plan(
            args.dataset,
            cases,
            args.variants,
            args.order_seeds,
            args.command,
            args.model,
            args.adapter,
        )
        specification["generation_settings"] = {
            "device": args.device,
            "thinking_mode": args.thinking_mode,
            "max_length": args.max_length,
            "max_new_tokens": args.max_new_tokens,
            "chat_template": True,
            "decoding": "greedy",
        }
        print(canonical({k: v for k, v in specification.items() if k != "case_ids"}), flush=True)
        if args.dry_run:
            return 0
        from evidence_lab.models import HuggingFaceModel

        backend = HuggingFaceModel(
            args.model,
            device=args.device,
            adapter_path=args.adapter,
            max_length=args.max_length,
            max_new_tokens=args.max_new_tokens,
            use_chat_template=True,
            enable_thinking=thinking_value(args.thinking_mode),
        )
        result = run(
            args.dataset,
            args.out,
            backend,
            cases,
            args.variants,
            args.order_seeds,
            args.command,
            specification,
        )
        print(
            json.dumps(
                {k: v for k, v in result.items() if k != "by_group"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (ValueError, FileNotFoundError, FileExistsError, ImportError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2
