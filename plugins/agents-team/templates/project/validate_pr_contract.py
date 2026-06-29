#!/usr/bin/env python3
"""Validate an Agents-Team pull request body."""
from __future__ import annotations
import argparse
import re
from pathlib import Path

REQUIRED_HEADINGS = [
    "关联任务",
    "Goal 对照",
    "必须完成证据",
    "验收门禁结果",
    "任务边界检查",
    "QA 结论",
    "剩余风险",
    "回滚方式",
]

UNRESOLVED_PATTERNS = [
    r"Closes\s+#\s*(?:$|\n)",
    r"待验收",
    r"TODO",
    r"待补充",
    r"未填写",
]


def _section(body: str, heading: str) -> str:
    pattern = rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, body)
    return match.group("body").strip() if match else ""


def validate(body: str, *, allow_draft: bool = False) -> list[str]:
    if allow_draft:
        return []
    errors: list[str] = []
    for heading in REQUIRED_HEADINGS:
        if not _section(body, heading):
            errors.append(f"missing or empty PR section: {heading}")
    if not re.search(r"(?:Closes|Fixes|Resolves)\s+#\d+", body, flags=re.I):
        errors.append("PR must link an Issue with Closes/Fixes/Resolves #number")
    for pattern in UNRESOLVED_PATTERNS:
        if re.search(pattern, body, flags=re.I):
            errors.append(f"unresolved PR placeholder or pending value: {pattern}")
    qa = _section(body, "QA 结论")
    if qa and not re.search(r"\b(PASS|N/A)\b", qa):
        errors.append("QA conclusion must be PASS or N/A with reason before merge")
    if re.search(r"\bFAIL\b", qa):
        errors.append("QA conclusion is FAIL")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Agents-Team PR body")
    parser.add_argument("body_file", type=Path)
    parser.add_argument("--draft", action="store_true", help="Skip strict checks for draft PRs")
    args = parser.parse_args()
    errors = validate(args.body_file.read_text(encoding="utf-8"), allow_draft=args.draft)
    if errors:
        print("Agents-Team PR contract failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Agents-Team PR contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
