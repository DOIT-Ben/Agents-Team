#!/usr/bin/env python3
"""Validate an Agents-Team pull request body and linked Goal Issue."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REQUIRED_PR_HEADINGS = [
    "关联任务",
    "Goal 对照",
    "必须完成证据",
    "验收门禁结果",
    "任务边界检查",
    "QA 结论",
    "剩余风险",
    "回滚方式",
]

REQUIRED_ISSUE_TERMS = [
    "Goal",
    "必须完成",
    "验收门禁",
    "任务边界",
    "风险等级",
    "依赖与阻塞",
]

UNRESOLVED_PATTERNS = [
    r"Closes\s+#\s*(?:$|\n)",
    r"待验收",
    r"TODO",
    r"待补充",
    r"未填写",
]

LINKED_ISSUE_PATTERN = re.compile(r"(?:Closes|Fixes|Resolves)\s+#(\d+)", re.I)


def _section(body: str, heading: str) -> str:
    pattern = rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, body)
    return match.group("body").strip() if match else ""


def _linked_issues(body: str) -> list[int]:
    seen: set[int] = set()
    issues: list[int] = []
    for match in LINKED_ISSUE_PATTERN.finditer(body):
        number = int(match.group(1))
        if number not in seen:
            issues.append(number)
            seen.add(number)
    return issues


def _fetch_issue_body(repo: str, number: int, token: str) -> str:
    url = f"https://api.github.com/repos/{repo}/issues/{number}"
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "agents-team-collaboration-gate",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"cannot read linked Issue #{number}: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot read linked Issue #{number}: {exc.reason}") from exc
    body = payload.get("body") or ""
    if not isinstance(body, str):
        return ""
    return body


def _validate_issue(number: int, issue_body: str) -> list[str]:
    errors: list[str] = []
    if not issue_body.strip():
        return [f"linked Issue #{number} has an empty body"]
    for term in REQUIRED_ISSUE_TERMS:
        if term not in issue_body:
            errors.append(f"linked Issue #{number} is missing required field: {term}")
    if re.search(r"\bL3\b|关键任务|真实 Provider|生产环境|密钥|费用", issue_body):
        for term in ["用户确认", "方案", "回滚"]:
            if term not in issue_body:
                errors.append(f"linked L3 Issue #{number} is missing: {term}")
    return errors


def validate(body: str, *, allow_draft: bool = False, issue_bodies: dict[int, str] | None = None, require_issue_lookup: bool = False) -> list[str]:
    if allow_draft:
        return []
    errors: list[str] = []
    for heading in REQUIRED_PR_HEADINGS:
        if not _section(body, heading):
            errors.append(f"missing or empty PR section: {heading}")
    linked_issues = _linked_issues(body)
    if not linked_issues:
        errors.append("PR must link an Issue with Closes/Fixes/Resolves #number")
    for pattern in UNRESOLVED_PATTERNS:
        if re.search(pattern, body, flags=re.I):
            errors.append(f"unresolved PR placeholder or pending value: {pattern}")
    qa = _section(body, "QA 结论")
    if qa and not re.search(r"\b(PASS|N/A)\b", qa):
        errors.append("QA conclusion must be PASS or N/A with reason before merge")
    if re.search(r"\bFAIL\b", qa):
        errors.append("QA conclusion is FAIL")
    if require_issue_lookup:
        if issue_bodies is None:
            errors.append("Issue lookup was required but not performed")
        else:
            for number in linked_issues:
                if number not in issue_bodies:
                    errors.append(f"linked Issue #{number} was not fetched")
                else:
                    errors.extend(_validate_issue(number, issue_bodies[number]))
    return errors


def _event_context(event_file: Path) -> tuple[str, bool, str]:
    event = json.loads(event_file.read_text(encoding="utf-8"))
    pull_request = event.get("pull_request") or {}
    body = pull_request.get("body") or ""
    draft = bool(pull_request.get("draft"))
    repo = (event.get("repository") or {}).get("full_name") or os.environ.get("GITHUB_REPOSITORY") or ""
    return body, draft, repo


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Agents-Team PR contract")
    parser.add_argument("body_file", nargs="?", type=Path)
    parser.add_argument("--event", type=Path, help="GitHub event JSON path for pull_request events")
    parser.add_argument("--draft", action="store_true", help="Skip strict checks for draft PRs")
    parser.add_argument("--require-issue-lookup", action="store_true")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    args = parser.parse_args()

    repo = args.repo
    draft = args.draft
    if args.event:
        body, event_draft, event_repo = _event_context(args.event)
        draft = draft or event_draft
        repo = repo or event_repo
    elif args.body_file:
        body = args.body_file.read_text(encoding="utf-8")
    else:
        print("Agents-Team PR contract failed:")
        print("- body file or --event is required")
        return 1

    issue_bodies: dict[int, str] | None = None
    if args.require_issue_lookup and not draft:
        token = os.environ.get(args.token_env, "")
        if not repo:
            issue_bodies = {}
        elif not token:
            print("Agents-Team PR contract failed:")
            print("- Issue lookup requires a repository and GitHub token")
            return 1
        else:
            issue_bodies = {}
            for number in _linked_issues(body):
                try:
                    issue_bodies[number] = _fetch_issue_body(repo, number, token)
                except RuntimeError as exc:
                    issue_bodies[number] = ""
                    print(f"- {exc}", file=sys.stderr)

    errors = validate(body, allow_draft=draft, issue_bodies=issue_bodies, require_issue_lookup=args.require_issue_lookup)
    if errors:
        print("Agents-Team PR contract failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Agents-Team PR contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
