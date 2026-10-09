"""Reproduce software checks and real-table development experiments, without network calls."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    dataset, rules, blind = out / "dataset", out / "rules", out / "blind"
    jobs = [
        ("lint", ["-m", "ruff", "check", "src", "tests", "scripts", "run.py"]),
        ("tests", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
        ("doctor", ["run.py", "doctor"]),
        (
            "prepare",
            ["run.py", "prepare", "--config", "configs/pilot_balanced.json", "--out", str(dataset)],
        ),
        ("rules", ["run.py", "rules", "--dataset", str(dataset), "--out", str(rules)]),
        ("blind", ["run.py", "blind", "--dataset", str(dataset), "--out", str(blind)]),
        ("freeze", ["run.py", "verify", "--dataset", str(dataset)]),
    ]
    statuses = []
    for name, arguments in jobs:
        command = [sys.executable, "-X", "utf8", *arguments]
        result = subprocess.run(
            command, cwd=project, capture_output=True, text=True, encoding="utf-8"
        )
        (out / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        statuses.append({"step": name, "returncode": result.returncode, "command": command})
        print(f"{name}: {'PASS' if result.returncode == 0 else 'FAIL'}", flush=True)
        if result.returncode:
            (out / "failed.json").write_text(
                json.dumps(statuses, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            raise SystemExit(result.returncode)
    audit = json.loads((dataset / "audit.json").read_text(encoding="utf-8"))
    selections = json.loads((dataset / "selection.json").read_text(encoding="utf-8"))
    blind_result = json.loads((blind / "summary.json").read_text(encoding="utf-8"))
    summary = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "steps": statuses,
        "data_audit": audit,
        "mean_rule_rejection": {
            name: item["coverage"]["mean_rejection_fraction"]
            for name, item in selections["arms"].items()
        },
        "blind_endpoints": blind_result["endpoints"],
        "pretrained_model_evaluated": False,
        "research_hypothesis_confirmed": False,
        "tiny_random_model_role": "software test only; actual Trainer/LoRA updates and hook operations",
    }
    (out / "verification.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Evidence: {out / 'verification.json'}", flush=True)


if __name__ == "__main__":
    main()
