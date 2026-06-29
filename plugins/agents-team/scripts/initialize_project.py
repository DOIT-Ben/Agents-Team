#!/usr/bin/env python3
"""Initialize the team collaboration project adapter."""

import argparse
import json
from pathlib import Path

from team_collaboration.initialize import InitializationError, initialize_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize team collaboration in a Git repository.")
    parser.add_argument("project", type=Path)
    parser.add_argument("--apply", action="store_true", help="Write the previewed changes.")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow an explicitly reviewed dirty worktree.")
    args = parser.parse_args()
    try:
        result = initialize_project(args.project, Path(__file__).resolve().parents[1], apply=args.apply, allow_dirty=args.allow_dirty)
    except InitializationError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
