"""Fixed V4 readouts, with and without their original table context."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from evidence_lab_v5.controls import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
