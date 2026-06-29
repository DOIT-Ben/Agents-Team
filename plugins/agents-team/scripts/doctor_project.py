#!/usr/bin/env python3
"""Print a read-only Agents-Team project health report."""

import argparse
import json
from pathlib import Path

from team_collaboration.doctor import doctor_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose team collaboration health without modifying the repository.")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    result = doctor_project(args.project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return {"healthy": 0, "warning": 2, "blocked": 1}[str(result["status"])]


if __name__ == "__main__":
    raise SystemExit(main())
