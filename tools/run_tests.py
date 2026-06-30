#!/usr/bin/env python3
"""Run the complete plugin test suite and write machine-readable release evidence."""

from __future__ import annotations

import argparse
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Agents-Team tests and write release evidence.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/test-results.json")
    parser.add_argument("--verbosity", type=int, choices=[1, 2], default=2)
    args = parser.parse_args()
    started = timestamp()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "plugins/agents-team/tests"))
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=args.verbosity).run(suite)
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    report = {
        "testEvidenceSchemaVersion": 1,
        "status": "passed" if result.wasSuccessful() else "failed",
        "command": "python tools/run_tests.py --output dist/test-results.json",
        "startedAt": started,
        "finishedAt": timestamp(),
        "testsRun": result.testsRun,
        "passed": result.testsRun - failed - errors - skipped,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
