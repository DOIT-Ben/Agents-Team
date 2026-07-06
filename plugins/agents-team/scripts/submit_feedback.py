#!/usr/bin/env python3
"""Preview or create a GitHub beta feedback Issue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from team_collaboration.feedback import preview_feedback_issue, submit_feedback_issue


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview or create a privacy-reviewed Agents-Team feedback Issue.")
    parser.add_argument("input", type=Path, help="JSON feedback input file")
    parser.add_argument("--repo", default="DOIT-Ben/Agents-Team", help="GitHub repo in owner/name format")
    parser.add_argument("--apply", action="store_true", help="create the GitHub Issue with gh after review")
    args = parser.parse_args()

    feedback = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(feedback, dict):
        print("feedback input must be a JSON object", file=sys.stderr)
        return 2

    if not args.apply:
        print(preview_feedback_issue(feedback, repo=args.repo), end="")
        return 0

    result = submit_feedback_issue(feedback, repo=args.repo, apply=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "submitted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
