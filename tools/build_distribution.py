#!/usr/bin/env python3
"""Build a deterministic marketplace ZIP for agents-team."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", "dist", "__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
INCLUDED_ROOTS = [".agents", "plugins", "docs", "tools", "README.md", "CHANGELOG.md", "NOTICE.md", "LICENSE"]


def iter_files():
    for item in INCLUDED_ROOTS:
        path = ROOT / item
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                relative = child.relative_to(ROOT)
                if child.is_file() and not (set(relative.parts) & EXCLUDED_PARTS) and child.suffix not in EXCLUDED_SUFFIXES:
                    yield child


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Codex plugin marketplace archive.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/agents-team-0.3.0.zip")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in iter_files():
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=(2026, 6, 29, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
