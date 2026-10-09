"""Strict serialization and immutable run artifacts, adapted from the existing pilots."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def stable_id(*parts: Any) -> str:
    return hashlib.sha256(canonical(parts).encode("utf-8")).hexdigest()[:20]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant: {value}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject_constant)


def read_jsonl(path: Path) -> list[dict]:
    result = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            row = json.loads(line, parse_constant=reject_constant)
            if not isinstance(row, dict):
                raise ValueError("Each JSONL record must be an object")
            result.append(row)
    return result


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(canonical(row) + "\n")


def freeze(root: Path, source_files: dict[str, Path]) -> dict:
    """Freeze only declared run inputs/artifacts; never rewrite older pilot files."""
    files = {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob("*")) if p.is_file()}
    manifest = {
        "schema": "evidence-lab-freeze-v1",
        "files": files,
        "sources": {
            name: {"path": str(p.resolve()), "sha256": digest(p)}
            for name, p in source_files.items()
        },
    }
    write_json(root / "freeze.json", manifest)
    return manifest


def verify(root: Path) -> dict:
    manifest = read_json(root / "freeze.json")
    for name, expected in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != expected:
            raise ValueError(f"Frozen artifact changed: {name}")
    for name, entry in manifest["sources"].items():
        if digest(Path(entry["path"])) != entry["sha256"]:
            raise ValueError(f"Frozen source changed: {name}")
    return manifest
