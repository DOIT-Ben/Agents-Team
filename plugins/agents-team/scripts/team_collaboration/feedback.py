"""Generate user-reviewed, local-only feedback bundles."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from .telemetry import (
    ALLOWED_METADATA,
    EVENT_TYPES,
    IDENTIFIER,
    read_run,
    redact_data,
    state_root,
)


FEEDBACK_SCHEMA_VERSION = 1
FEEDBACK_TYPES = {
    "bug",
    "missed_defect",
    "false_block",
    "context_isolation",
    "compatibility",
    "privacy",
    "feature_request",
}
SEVERITIES = {"P0", "P1", "P2", "P3"}
GITHUB_REPOSITORY = "DOIT-Ben/Agents-Team"
ISSUE_TEMPLATES = {
    "bug": "bug.yml",
    "missed_defect": "missed-defect.yml",
    "false_block": "false-block.yml",
    "context_isolation": "context-isolation.yml",
    "compatibility": "compatibility.yml",
    "privacy": "privacy.yml",
    "feature_request": "feature-request.yml",
}
EVENT_EXPORT_FIELDS = {
    "eventSchemaVersion",
    "eventId",
    "runId",
    "traceId",
    "cohortId",
    "agentsTeamVersion",
    "protocolVersion",
    "hostName",
    "hostVersion",
    "provider",
    "model",
    "os",
    "taskCategory",
    "riskLevel",
    "finalStatus",
    "eventType",
    "timestamp",
}
IDENTIFIER_EVENT_FIELDS = {
    "runId",
    "traceId",
    "cohortId",
    "agentsTeamVersion",
    "protocolVersion",
    "hostName",
    "hostVersion",
    "provider",
    "model",
    "os",
    "taskCategory",
    "riskLevel",
    "finalStatus",
}
KNOWN_REDACTIONS = {"secret", "email", "absolute_path", "repository_url"}


class FeedbackError(ValueError):
    """Raised when a feedback request is incomplete or unsafe."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate(
    feedback_type: str,
    severity: str,
    expected_result: str,
    actual_result: str,
    reproduction_steps: str,
    user_rating: int | None,
) -> None:
    if feedback_type not in FEEDBACK_TYPES:
        raise FeedbackError(f"unsupported feedback_type: {feedback_type}")
    if severity not in SEVERITIES:
        raise FeedbackError(f"unsupported severity: {severity}")
    for name, value in {
        "expected_result": expected_result,
        "actual_result": actual_result,
        "reproduction_steps": reproduction_steps,
    }.items():
        if not isinstance(value, str) or not value.strip():
            raise FeedbackError(f"{name} is required")
        if len(value) > 10000:
            raise FeedbackError(f"{name} must not exceed 10000 characters")
    if user_rating is not None and user_rating not in range(1, 6):
        raise FeedbackError("user_rating must be between 1 and 5")


def _related_feedback_ids(root: Path, run_id: str) -> list[str]:
    index = root / "feedback" / "index.jsonl"
    if index.is_symlink() or index.parent.is_symlink():
        raise FeedbackError("refusing to read a symlinked feedback index")
    if not index.is_file():
        return []
    related = []
    for line in index.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("runId") == run_id and item.get("feedbackId"):
            related.append(str(item["feedbackId"]))
    return related


def _safe_events(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    safe_events: list[dict[str, Any]] = []
    all_redactions: list[str] = []
    for event in events:
        sanitized: dict[str, Any] = {}
        invalid = bool(set(event) - EVENT_EXPORT_FIELDS - {"metadata", "redactions"})
        for key in EVENT_EXPORT_FIELDS:
            value = event.get(key)
            if value is None:
                sanitized[key] = None
            elif key in IDENTIFIER_EVENT_FIELDS:
                if isinstance(value, str) and IDENTIFIER.fullmatch(value):
                    sanitized[key] = value
                else:
                    invalid = True
            elif key == "eventType":
                if value in EVENT_TYPES:
                    sanitized[key] = value
                else:
                    invalid = True
            elif key == "eventSchemaVersion":
                if value == 1:
                    sanitized[key] = value
                else:
                    invalid = True
            elif key == "eventId":
                try:
                    sanitized[key] = str(uuid.UUID(str(value)))
                except (ValueError, AttributeError):
                    invalid = True
            elif key == "timestamp":
                try:
                    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                    sanitized[key] = parsed.isoformat().replace("+00:00", "Z")
                except ValueError:
                    invalid = True
        metadata: dict[str, Any] = {}
        source_metadata = event.get("metadata")
        if isinstance(source_metadata, dict):
            for key, value in source_metadata.items():
                if key not in ALLOWED_METADATA:
                    invalid = True
                elif key in {"actorRole", "status", "reasonCode", "stage"}:
                    if isinstance(value, str) and IDENTIFIER.fullmatch(value):
                        metadata[key] = value
                    else:
                        invalid = True
                elif key == "independent" and isinstance(value, bool):
                    metadata[key] = value
                elif key != "independent" and isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                    metadata[key] = value
                else:
                    invalid = True
        elif source_metadata is not None:
            invalid = True
        sanitized["metadata"] = metadata
        cleaned, reasons = redact_data(sanitized)
        existing = event.get("redactions")
        if isinstance(existing, list):
            reasons.extend(reason for reason in existing if reason in KNOWN_REDACTIONS)
        if invalid:
            reasons.append("unexpected_or_invalid_field")
        cleaned["redactions"] = sorted(set(reasons))
        safe_events.append(cleaned)
        all_redactions.extend(cleaned["redactions"])
    return safe_events, sorted(set(all_redactions))


def _markdown(payload: dict[str, Any]) -> str:
    event_summary = "\n".join(
        f"- `{event.get('timestamp', 'invalid')}` `{event.get('eventType', 'invalid')}` `{event.get('metadata', {}).get('reasonCode', '')}`"
        for event in payload["diagnosticEvents"]
    ) or "- 无可用事件"
    return f"""# Agents-Team 反馈

## 类型与严重程度

- 类型：`{payload['feedbackType']}`
- 严重程度：`{payload['severity']}`
- 运行编号：`{payload['runId']}`
- 跟踪编号：`{payload['traceId']}`
- 版本：`{payload['agentsTeamVersion']}`

## 预期结果

{payload['expectedResult']}

## 实际结果

{payload['actualResult']}

## 复现步骤

{payload['reproductionSteps']}

## 诊断事件

{event_summary}

## 用户评价

- 评分：{payload['userRating'] if payload['userRating'] is not None else '未填写'}
- 是否愿意再次使用：{payload['wouldUseAgain'] if payload['wouldUseAgain'] is not None else '未填写'}

> 本文件由用户主动导出；提交前仍需检查内容并在 GitHub 页面明确确认。
"""


def export_feedback(
    *,
    run_id: str,
    feedback_type: str,
    severity: str,
    expected_result: str,
    actual_result: str,
    reproduction_steps: str,
    state_dir: Path | None = None,
    confirmed: bool = False,
    output_dir: Path | None = None,
    user_rating: int | None = None,
    would_use_again: bool | None = None,
    content_attachment_consent: bool = False,
) -> dict[str, Any]:
    _validate(feedback_type, severity, expected_result, actual_result, reproduction_steps, user_rating)
    root = state_root(state_dir)
    events = read_run(run_id, state_dir=root)
    if not events:
        raise FeedbackError(f"run not found: {run_id}")
    events, event_redactions = _safe_events(events)
    feedback_id = str(uuid.uuid4())
    trace_id = str(events[-1].get("traceId") or run_id)
    cohort_id = next((event.get("cohortId") for event in events if event.get("cohortId")), None)
    cleaned, redactions = redact_data({
        "expectedResult": expected_result.strip(),
        "actualResult": actual_result.strip(),
        "reproductionSteps": reproduction_steps.strip(),
    })
    payload = {
        "feedbackSchemaVersion": FEEDBACK_SCHEMA_VERSION,
        "feedbackId": feedback_id,
        "feedbackType": feedback_type,
        "runId": run_id,
        "traceId": trace_id,
        "cohortId": cohort_id,
        "severity": severity,
        **cleaned,
        "userRating": user_rating,
        "wouldUseAgain": would_use_again,
        "diagnosticConsent": confirmed,
        "contentAttachmentConsent": bool(content_attachment_consent),
        "redactions": sorted(set(redactions + event_redactions)),
        "createdAt": _iso_now(),
        "agentsTeamVersion": events[-1].get("agentsTeamVersion"),
        "protocolVersion": events[-1].get("protocolVersion"),
        "relatedFeedbackIds": _related_feedback_ids(root, run_id),
        "diagnosticEvents": events,
    }
    preview = {
        "status": "preview",
        "feedbackId": feedback_id,
        "uploadPerformed": False,
        "payload": payload,
        "markdown": _markdown(payload),
    }
    if not confirmed:
        return preview

    base = Path(output_dir).expanduser().resolve() if output_dir else root / "feedback"
    if base.is_symlink():
        raise FeedbackError("refusing to write through a symlinked feedback directory")
    bundle = base / feedback_id
    bundle.mkdir(parents=True, exist_ok=False)
    (bundle / "diagnostics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (bundle / "feedback.md").write_text(preview["markdown"], encoding="utf-8")
    index = root / "feedback" / "index.jsonl"
    index.parent.mkdir(parents=True, exist_ok=True)
    with index.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({
            "feedbackId": feedback_id,
            "runId": run_id,
            "feedbackType": feedback_type,
            "createdAt": payload["createdAt"],
        }, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {
        "status": "exported",
        "feedbackId": feedback_id,
        "directory": str(bundle),
        "uploadPerformed": False,
        "redactions": payload["redactions"],
    }


def _copy_to_clipboard(text: str) -> bool:
    commands: list[list[str]] = []
    if sys.platform == "win32":
        commands.append(["powershell.exe", "-NoProfile", "-Command", "Set-Clipboard -Value ([Console]::In.ReadToEnd())"])
    elif sys.platform == "darwin":
        commands.append(["pbcopy"])
    else:
        commands.extend([["wl-copy"], ["xclip", "-selection", "clipboard"]])
    for command in commands:
        if shutil.which(command[0]) is None:
            continue
        result = subprocess.run(command, input=text, text=True, capture_output=True)
        if result.returncode == 0:
            return True
    return False


def prepare_github_issue(bundle_dir: Path, feedback_type: str) -> dict[str, Any]:
    """Open a user-confirmed GitHub draft; never submit an issue automatically."""
    if feedback_type not in ISSUE_TEMPLATES:
        raise FeedbackError(f"unsupported feedback_type: {feedback_type}")
    bundle = Path(bundle_dir).resolve()
    markdown = bundle / "feedback.md"
    diagnostics = bundle / "diagnostics.json"
    if markdown.is_symlink() or diagnostics.is_symlink():
        raise FeedbackError("refusing to read a symlinked feedback bundle")
    if not markdown.is_file() or not diagnostics.is_file():
        raise FeedbackError("feedback bundle is incomplete")
    payload = json.loads(diagnostics.read_text(encoding="utf-8"))
    title = f"[{payload['feedbackType']}] run {payload['runId']}"
    gh = shutil.which("gh")
    if gh:
        auth = subprocess.run([gh, "auth", "status"], text=True, capture_output=True)
        if auth.returncode == 0:
            result = subprocess.run([
                gh,
                "issue",
                "create",
                "--repo",
                GITHUB_REPOSITORY,
                "--web",
                "--title",
                title,
                "--body-file",
                str(markdown),
            ], text=True, capture_output=True)
            if result.returncode == 0:
                return {
                    "status": "draft_opened",
                    "method": "gh_web",
                    "submissionConfirmed": False,
                    "diagnosticsPath": str(diagnostics),
                }
    copied = _copy_to_clipboard(markdown.read_text(encoding="utf-8"))
    query = urlencode({"template": ISSUE_TEMPLATES[feedback_type], "title": title})
    url = f"https://github.com/{GITHUB_REPOSITORY}/issues/new?{query}"
    opened = webbrowser.open(url)
    return {
        "status": "form_opened" if opened else "form_ready",
        "method": "browser_form",
        "url": url,
        "clipboardCopied": copied,
        "submissionConfirmed": False,
        "diagnosticsPath": str(diagnostics),
    }
