"""Parse and validate Goal Issue and delivery PR Markdown contracts."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime
from typing import Any

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
    found: set[str] = set()
    for candidate in candidates:
        found.update("L" + match for match in re.findall(r"\bL([123])\b", candidate, re.IGNORECASE))
    for risk in ("L3", "L2", "L1"):
        if risk in found:
            return risk
    return ""


def _status_from_labels(labels: Iterable[str]) -> str:
    for label in labels:
        match = re.search(r"\bstatus:([a-z-]+)\b", label, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return ""


def _scalar(block: str, name: str) -> str:
    match = re.search(rf"(?mi)^\s*(?:[-*]\s+)?{re.escape(name)}\s*[：:]\s*(.+?)\s*$", block or "")
    return match.group(1).strip() if match else ""


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_l3_approval_event(event: dict[str, Any] | None, *, current_sha: str | None) -> list[Finding]:
    if event is None:
        return [Finding("AT-QA-007", "error", "L3 approval event", "L3 approval event is missing", "attach a platform or local approval event fixture", "missing")]
    required = {"actor", "timestamp", "scope", "risk", "commitSha"}
    missing = sorted(field for field in required if not str(event.get(field, "")).strip())
    if missing:
        return [Finding("AT-QA-007", "error", "L3 approval event", f"missing L3 approval event fields: {', '.join(missing)}", "record actor, timestamp, scope, risk and commitSha", ", ".join(missing))]
    findings: list[Finding] = []
    if str(event.get("risk", "")).upper() != "L3":
        findings.append(Finding("AT-QA-007", "error", "L3 approval event", "approval event risk is not L3", "record risk: L3", str(event.get("risk", ""))))
    if not _valid_timestamp(event.get("timestamp")):
        findings.append(Finding("AT-QA-007", "error", "L3 approval event", "approval event timestamp is invalid", "record an ISO 8601 timestamp", str(event.get("timestamp", ""))))
    commit_sha = str(event.get("commitSha", "")).strip()
    if current_sha is not None and commit_sha != current_sha:
        findings.append(Finding("AT-QA-007", "error", "L3 approval event", f"approval event commitSha {commit_sha} does not match head.sha {current_sha}", "record an approval event for the current PR head", commit_sha))
    return findings


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


def validate_pr_contract(
    body: str,
    issue_body: str,
    labels: Iterable[str],
    *,
    current_sha: str | None = None,
    approval_event: dict[str, Any] | None = None,
) -> list[Finding]:
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
        required_qa = ["验收者", "实现上下文", "QA 上下文", "commitSha", "证据"]
        missing_qa = [field for field in required_qa if not _scalar(qa, field)]
        if missing_qa:
            findings.append(Finding("AT-QA-003", "error", "PR/QA 独立性与结论", f"missing QA evidence fields: {', '.join(missing_qa)}", "record verifier, separate QA context, commit SHA and evidence artifact", qa))
        qa_commit_sha = _scalar(qa, "commitSha")
        if qa_commit_sha and current_sha is not None and qa_commit_sha != current_sha:
            findings.append(Finding("AT-QA-004", "error", "PR/QA 独立性与结论", f"QA evidence belongs to commit {qa_commit_sha}, not current head {current_sha}", "rerun independent QA on the current PR head", qa_commit_sha))
        implementation_context = _scalar(qa, "实现上下文")
        qa_context = _scalar(qa, "QA 上下文")
        if implementation_context and qa_context and implementation_context == qa_context:
            findings.append(Finding("AT-QA-005", "error", "PR/QA 独立性与结论", "QA context matches implementation context", "run QA in a separate context and record both context identifiers", qa_context))
        if _status_from_labels(labels) == "pass" and _scalar(qa, "验证阶段").lower() != "verify":
            findings.append(Finding("AT-QA-006", "error", "PR/QA 独立性与结论", "PASS status was declared without an explicit verify stage", "record 验证阶段：verify from the verifier before status:pass", qa))
        if risk == "L3":
            findings.extend(validate_l3_approval_event(approval_event, current_sha=current_sha))

    tests = sections.get("测试门禁", "")
    if not re.search(r"exitCode\s*[：:]\s*0\b", tests, re.IGNORECASE) or not re.search(r"failed\s*[：:]\s*0\b", tests, re.IGNORECASE):
        findings.append(Finding("AT-GATE-004", "error", "PR/测试门禁", "test evidence lacks successful exit code or failure count", "record exact command, exitCode, passed, failed and skipped counts", tests))

    return findings
