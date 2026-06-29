#!/usr/bin/env python3
"""Check, repair, upgrade, or remove the project adapter."""

import argparse
import json
from pathlib import Path

from team_collaboration.initialize import InitializationError
from team_collaboration.manage import manage_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage a team collaboration project adapter.")
    parser.add_argument("action", choices=["check", "repair", "upgrade", "remove"])
    parser.add_argument("project", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        result = manage_project(args.project, Path(__file__).resolve().parents[1], args.action, apply=args.apply)
    except (InitializationError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("status") == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
