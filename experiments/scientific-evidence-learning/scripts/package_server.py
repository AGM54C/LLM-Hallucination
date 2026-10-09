"""Build a small portable source/data bundle; excludes environments, credentials and weights."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    workspace = project.parent
    files = []
    for folder in ("src", "configs", "tests", "scripts", "docs"):
        files.extend(
            p
            for p in (project / folder).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        )
    files.extend(
        p
        for p in project.iterdir()
        if p.is_file()
        and (
            p.name in {"README.md", "pyproject.toml", "run.py", ".gitignore"}
            or (p.name.startswith("requirements-") and p.suffix == ".txt")
        )
    )
    files.extend(
        [
            workspace
            / "chemical-materials-pilot-20261004/sources/chemistry/buchwald_hartwig_annotated.csv",
            workspace / "高风险候选-20261004/有限表条件对照-可构造性检查.json",
        ]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    manifest = {}
    with zipfile.ZipFile(args.out, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            name = path.relative_to(workspace).as_posix()
            archive.write(path, name)
            manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        archive.writestr("BUNDLE-MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    print(
        json.dumps(
            {"path": str(args.out), "files": len(manifest), "bytes": args.out.stat().st_size},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
