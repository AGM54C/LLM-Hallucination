"""Versioned diagnostics; the original run.py and frozen v1 modules stay intact."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from evidence_lab_v2.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
