"""Parse and validate Goal Issue and delivery PR Markdown contracts."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .diagnostics import Finding


ISSUE_SECTIONS = ["Goal", "必须完成", "验收门禁", "任务边界", "风险等级", "依赖与阻塞条件", "失败处理与回滚"]
PR_SECTIONS = ["关联任务", "风险等级", "实际改动", "范围偏差", "必须完成项证据", "测试门禁", "行为验收", "QA 独立性与结论", "剩余风险", "回滚方式", "失败记录"]
HEADING = re.compile(r"^#{2,6}\s+(.+?)\s*$", re.MULTILINE)
CHECKBOX = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+)$", re.MULTILINE)
ISSUE_LINK = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)\b", re.IGNORECASE)


def parse_sections(body: str) -> dict[str, str]:
    matches = list(HEADING.finditer(body or ""))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1).strip()] = body[start:end].strip()
    return sections


def extract_linked_issue(body: str) -> int | None:
    match = ISSUE_LINK.search(body or "")
    return int(match.group(1)) if match else None


def _missing(section: str, location: str) -> Finding:
    return Finding("AT-CONTRACT-001", "error", location, f"required section is missing: {section}", f"add a non-empty {section} section", section)


def _is_vague(value: str) -> bool:
    normalized = re.sub(r"[\s。.!！]", "", value).lower()
    return normalized in {"", "无", "none", "n/a", "na", "待定"} or len(normalized) < 6


def _risk_from(sections: dict[str, str], labels: Iterable[str] = ()) -> str:
    candidates = [sections.get("风险等级", ""), *labels]
    for candidate in candidates:
        match = re.search(r"\bL([123])\b", candidate, re.IGNORECASE)
        if match:
            return "L" + match.group(1)
    return ""


def validate_issue_contract(body: str) -> list[Finding]:
    sections = parse_sections(body)
    findings = [_missing(section, "Issue contract") for section in ISSUE_SECTIONS if not sections.get(section, "").strip()]
    if findings:
        return findings

    for section in ("Goal", "验收门禁", "任务边界", "依赖与阻塞条件", "失败处理与回滚"):
        if _is_vague(sections[section]):
            findings.append(Finding("AT-CONTRACT-002", "error", f"Issue/{section}", f"section is vague: {section}", "replace placeholders with observable and enforceable detail", sections[section]))

    if not CHECKBOX.search(sections["必须完成"]):
        findings.append(Finding("AT-CONTRACT-005", "error", "Issue/必须完成", "at least one checklist item is required", "add measurable checklist items", sections["必须完成"]))

    risk = _risk_from(sections)
    if not risk:
        findings.append(Finding("AT-CONTRACT-007", "error", "Issue/风险等级", "risk must be L1, L2 or L3", "select one risk level", sections["风险等级"]))
    if risk == "L3" and not sections.get("L3 方案与用户确认", "").strip():
        findings.append(Finding("AT-CONTRACT-006", "error", "Issue/L3 方案与用户确认", "L3 contract has no explicit user decision", "record approach, alternatives, cost, risk, rollback and approval", "missing"))
    return findings


def validate_pr_contract(body: str, issue_body: str, labels: Iterable[str]) -> list[Finding]:
    sections = parse_sections(body)
    findings = [_missing(section, "PR contract") for section in PR_SECTIONS if not sections.get(section, "").strip()]
    if extract_linked_issue(body) is None:
        findings.append(Finding("AT-CONTRACT-003", "error", "PR/关联任务", "PR does not close a numbered Issue", "add Closes #<issue-number>", sections.get("关联任务", "")))

    issue_findings = validate_issue_contract(issue_body)
    findings.extend(issue_findings)

    evidence_items = CHECKBOX.findall(sections.get("必须完成项证据", ""))
    if not evidence_items or any(mark.lower() != "x" for mark, _ in evidence_items):
        findings.append(Finding("AT-CONTRACT-004", "error", "PR/必须完成项证据", "mandatory evidence checklist is incomplete", "map every mandatory item to checked observable evidence", sections.get("必须完成项证据", "")))

    risk = _risk_from(sections, labels)
    qa = sections.get("QA 独立性与结论", "")
    if risk in {"L2", "L3"}:
        independent = bool(re.search(r"独立上下文\s*[：:]\s*是", qa))
        if not independent:
            findings.append(Finding("AT-QA-001", "error", "PR/QA 独立性与结论", "QA independence is missing or false", "run QA in a fresh context and record 独立上下文：是", qa))
        if not re.search(r"结论\s*[：:]\s*PASS\b", qa, re.IGNORECASE):
            findings.append(Finding("AT-QA-002", "error", "PR/QA 独立性与结论", "QA verdict is not PASS", "resolve defects and rerun independent QA", qa))

    tests = sections.get("测试门禁", "")
    if not re.search(r"exitCode\s*[：:]\s*0\b", tests, re.IGNORECASE) or not re.search(r"failed\s*[：:]\s*0\b", tests, re.IGNORECASE):
        findings.append(Finding("AT-GATE-004", "error", "PR/测试门禁", "test evidence lacks successful exit code or failure count", "record exact command, exitCode, passed, failed and skipped counts", tests))

    return findings
