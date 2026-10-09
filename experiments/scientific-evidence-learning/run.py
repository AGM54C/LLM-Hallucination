"""Checkout-local CLI; installation is optional for the standard-library core."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from evidence_lab.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
