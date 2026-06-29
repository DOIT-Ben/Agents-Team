#!/usr/bin/env python3
"""Validate a project adapter."""

import argparse
import json
from pathlib import Path

from team_collaboration.validate import validate_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate team collaboration project files.")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    errors = validate_project(args.project)
    print(json.dumps({"status": "valid" if not errors else "invalid", "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
