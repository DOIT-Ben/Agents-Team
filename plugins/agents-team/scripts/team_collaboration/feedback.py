"""Privacy-safe local beta feedback export helpers."""

from __future__ import annotations

import json
import re
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


def export_feedback(feedback: dict[str, Any], output_path: Path, *, apply: bool) -> dict[str, Any]:
    preview = preview_feedback_export(feedback, output_path=output_path)
    if not apply:
        return {"status": "preview", "preview": preview, "outputPath": str(output_path)}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(preview, encoding="utf-8")
    return {"status": "written", "outputPath": str(output_path)}
