#!/usr/bin/env python3
"""Evaluate an offline Agents-Team Beta dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "agents-team" / "scripts"))

from team_collaboration.evaluation import EvaluationError, evaluate_beta  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate paired Beta runs without uploading them.")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-stable", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.dataset.read_text(encoding="utf-8"))
        report = evaluate_beta(data)
    except (OSError, json.JSONDecodeError, EvaluationError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if args.require_stable and report["decision"] != "stable_candidate":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
