"""Privacy-safe local beta feedback export helpers."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


REDACTION = "[REDACTED]"
SENSITIVE_KEY_PARTS = (
    "authorization",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "password",
    "secret",
    "token",
)
SECRET_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9][A-Za-z0-9_-]{8,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"https://[^\s/@]+@github\.com/[^/\s]+/[^/\s)]+", re.IGNORECASE),
    re.compile(r"ssh://git@github\.com/[^/\s]+/[^/\s)]+", re.IGNORECASE),
    re.compile(r"git@github\.com:[^/\s]+/[^\s)]+", re.IGNORECASE),
    re.compile(r"https://github\.com/[^/\s]+/[^/\s)]+", re.IGNORECASE),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"[A-Z]:\\[^\r\n\t]+", re.IGNORECASE),
    re.compile(r"C:\\Users\\[^\\\s]+", re.IGNORECASE),
    re.compile(r"/(Users|home)/[^/\s]+[^\r\n\t]*"),
]


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _redact_string(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(REDACTION, redacted)
    return redacted


def redact_feedback(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: REDACTION if _is_sensitive_key(str(key)) else redact_feedback(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_feedback(item) for item in value]
    if isinstance(value, tuple):
        return [redact_feedback(item) for item in value]
    if isinstance(value, str):
        return _redact_string(value)
    return value


def preview_feedback_export(feedback: dict[str, Any], *, output_path: Path | None = None) -> str:
    payload = {
        "status": "preview",
        "outputPath": str(output_path) if output_path is not None else None,
        "feedback": redact_feedback(feedback),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _text(value: Any, *, default: str = "Not provided") -> str:
    if value is None:
        return default
    if isinstance(value, list):
        lines = [f"{index}. {_text(item, default='')}" for index, item in enumerate(value, start=1)]
        return "\n".join(line for line in lines if line.strip()) or default
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, indent=2)
    text = str(value).strip()
    return text or default


def _field(feedback: dict[str, Any], *names: str, default: str = "Not provided") -> str:
    for name in names:
        if name in feedback:
            return _text(feedback[name], default=default)
    return default


def _title(value: str) -> str:
    first_line = value.replace("\r", "\n").split("\n", 1)[0].strip()
    return first_line[:120] or "Agents-Team Beta feedback"


def build_feedback_issue(feedback: dict[str, Any], *, reviewed: bool = False) -> dict[str, str]:
    redacted = redact_feedback(feedback)
    if not isinstance(redacted, dict):
        redacted = {}

    known_fields = {
        "actual",
        "actual-behavior",
        "actualBehavior",
        "env",
        "environment",
        "evidence",
        "expected",
        "expected-behavior",
        "expectedBehavior",
        "logs",
        "lessons",
        "plugin-version",
        "pluginVersion",
        "project-type",
        "projectType",
        "redactedEvidence",
        "reproduction",
        "reproductionSteps",
        "stage",
        "stack",
        "steps",
        "summary",
        "title",
        "version",
    }
    additional_context = {key: value for key, value in redacted.items() if key not in known_fields}
    summary = _title(_field(redacted, "summary", "title", default="Agents-Team Beta feedback"))
    title = summary if summary.startswith("[Beta feedback]:") else f"[Beta feedback]: {summary}"
    privacy_check = "x" if reviewed else " "
    body = "\n".join(
        [
            "### Plugin version",
            _field(redacted, "pluginVersion", "plugin-version", "version", default="0.3.0"),
            "",
            "### Stage",
            _field(redacted, "stage"),
            "",
            "### Environment",
            _field(redacted, "environment", "env"),
            "",
            "### Project type",
            _field(redacted, "projectType", "project-type", "stack"),
            "",
            "### Expected behavior",
            _field(redacted, "expected", "expectedBehavior", "expected-behavior"),
            "",
            "### Actual behavior",
            _field(redacted, "actual", "actualBehavior", "actual-behavior"),
            "",
            "### Reproduction steps",
            _field(redacted, "steps", "reproduction", "reproductionSteps", default="Not provided"),
            "",
            "### Redacted evidence",
            "```text",
            _field(redacted, "evidence", "redactedEvidence", "logs", "lessons", default="Not provided"),
            "```",
            "",
            "### Additional redacted context",
            "```json",
            _text(additional_context, default="{}"),
            "```",
            "",
            "### Privacy check",
            f"- [{privacy_check}] I reviewed this draft and removed secrets, tokens, private source code, customer information, and unredacted repository details.",
        ]
    )
    return {"title": title, "body": body}


def preview_feedback_issue(feedback: dict[str, Any], *, repo: str = "DOIT-Ben/Agents-Team") -> str:
    issue = build_feedback_issue(feedback)
    payload = {
        "status": "preview",
        "repo": repo,
        "title": issue["title"],
        "body": issue["body"],
        "nextStep": "Review the draft. Re-run with --apply only after confirming it is safe to publish.",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def submit_feedback_issue(
    feedback: dict[str, Any],
    *,
    repo: str = "DOIT-Ben/Agents-Team",
    apply: bool,
    runner=subprocess.run,
) -> dict[str, Any]:
    issue = build_feedback_issue(feedback, reviewed=apply)
    if not apply:
        return {"status": "preview", "repo": repo, **issue}

    with tempfile.TemporaryDirectory() as temp:
        body_file = Path(temp) / "agents-team-feedback.md"
        body_file.write_text(issue["body"], encoding="utf-8")
        command = [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            issue["title"],
            "--body-file",
            str(body_file),
            "--label",
            "beta-feedback",
        ]
        try:
            result = runner(command, text=True, encoding="utf-8", capture_output=True)
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            return {"status": "failed", "error": _redact_string(str(exc)), "repo": repo, **issue}
    if result.returncode != 0:
        return {
            "status": "failed",
            "repo": repo,
            "stderr": redact_feedback(result.stderr.strip()),
            "stdout": redact_feedback(result.stdout.strip()),
            **issue,
        }
    return {"status": "submitted", "repo": repo, "issueUrl": result.stdout.strip()}


def export_feedback(feedback: dict[str, Any], output_path: Path, *, apply: bool) -> dict[str, Any]:
    preview = preview_feedback_export(feedback, output_path=output_path)
    if not apply:
        return {"status": "preview", "preview": preview, "outputPath": str(output_path)}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(preview, encoding="utf-8")
    return {"status": "written", "outputPath": str(output_path)}
