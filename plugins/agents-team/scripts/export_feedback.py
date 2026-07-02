#!/usr/bin/env python3
"""Preview or write a redacted local beta feedback export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from team_collaboration.feedback import export_feedback, preview_feedback_export


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview or write a privacy-safe local feedback export.")
    parser.add_argument("input", type=Path, help="JSON feedback input file")
    parser.add_argument("--output", type=Path, help="export artifact path")
    parser.add_argument("--apply", action="store_true", help="write the redacted export artifact")
    args = parser.parse_args()

    feedback = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(feedback, dict):
        print("feedback input must be a JSON object", file=sys.stderr)
        return 2

    if args.apply:
        if args.output is None:
            print("--output is required with --apply", file=sys.stderr)
            return 2
        result = export_feedback(feedback, args.output, apply=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(preview_feedback_export(feedback, output_path=args.output), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
