"""Validate structured delivery and independent QA evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from .diagnostics import Finding


def _finding(code: str, message: str, remediation: str, location: str = "测试门禁") -> Finding:
    return Finding(code, "error", location, message, remediation, location)


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_gate_evidence(
    records: Iterable[dict[str, Any]],
    *,
    current_sha: str | None = None,
) -> list[Finding]:
    records = list(records)
    if not records:
        return [_finding("AT-GATE-004", "no gate evidence was supplied", "record every required command and result")]

    findings: list[Finding] = []
    required = {
        "gate",
        "command",
        "exitCode",
        "passed",
        "failed",
        "skipped",
        "artifact",
        "timestamp",
        "commitSha",
    }
    for index, record in enumerate(records, start=1):
        location = f"测试门禁[{index}]"
        missing = sorted(required - record.keys())
        if missing:
            findings.append(_finding("AT-GATE-004", f"missing evidence fields: {', '.join(missing)}", "record the complete gate evidence", location))
            continue
        if record["exitCode"] != 0:
            findings.append(_finding("AT-GATE-001", f"command exited with {record['exitCode']}", "fix the failure and rerun the exact command", location))
        if not isinstance(record["failed"], int) or record["failed"] != 0:
            findings.append(_finding("AT-GATE-002", f"failed test count is {record['failed']}", "resolve every failed test before QA", location))
        if isinstance(record["skipped"], int) and record["skipped"] > 0 and not str(record.get("skipReason", "")).strip():
            findings.append(_finding("AT-GATE-003", f"{record['skipped']} tests were skipped without explanation", "record why each skip is expected and safe", location))
        if not _valid_timestamp(record["timestamp"]):
            findings.append(_finding("AT-GATE-004", "evidence timestamp is missing or invalid", "record an ISO 8601 execution timestamp", location))
        commit_sha = str(record["commitSha"]).strip()
        if not commit_sha:
            findings.append(_finding("AT-GATE-004", "evidence commit SHA is empty", "record the exact tested commit SHA", location))
        elif current_sha is not None and commit_sha != current_sha:
            findings.append(_finding("AT-GATE-005", f"evidence belongs to commit {commit_sha}, not current head {current_sha}", "rerun the gate on the current PR head", location))
        if not str(record["command"]).strip() or not str(record["artifact"]).strip():
            findings.append(_finding("AT-GATE-004", "command or artifact is empty", "record the exact command and an inspectable artifact", location))
    return findings


def validate_qa_evidence(evidence: dict[str, Any], *, risk: str) -> list[Finding]:
    if risk == "L1" and not evidence:
        return []
    findings: list[Finding] = []
    if evidence.get("independent") is not True:
        findings.append(Finding("AT-QA-001", "error", "QA 独立性与结论", "QA was not performed in an independent context", "run QA in a fresh context", "independent"))
    if str(evidence.get("verdict", "")).upper() != "PASS":
        findings.append(Finding("AT-QA-002", "error", "QA 独立性与结论", "QA verdict is not PASS", "resolve findings and rerun independent QA", "verdict"))
    return findings
