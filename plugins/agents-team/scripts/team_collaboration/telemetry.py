"""Privacy-first local event records for Agents-Team runs."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


EVENT_SCHEMA_VERSION = 1
PROTOCOL_VERSION = "2.0.0"
RETENTION_DAYS = 14
MAX_LOG_BYTES = 20 * 1024 * 1024
MAX_ROTATED_FILES = 5

EVENT_TYPES = {
    "goal_created",
    "work_dispatched",
    "context_isolation_checked",
    "implementation_delivered",
    "review_started",
    "qa_verdict",
    "human_intervention",
    "gate_blocked",
    "rollback",
    "run_completed",
    "run_failed",
}
ALLOWED_METADATA = {
    "actorRole",
    "status",
    "reasonCode",
    "stage",
    "durationMs",
    "interventionCount",
    "reworkCount",
    "tokenCount",
    "costEstimate",
    "independent",
}
FORBIDDEN_METADATA = {
    "prompt",
    "output",
    "source",
    "sourceCode",
    "environment",
    "env",
    "cookie",
    "authorization",
}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SECRET = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password|cookie|authorization)\s*[:=]\s*([^\s,;]+)"
)
BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*")
EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
WINDOWS_PATH = re.compile(r"(?i)\b[A-Z]:\\(?:[^\\\s]+\\)*[^\\\s,;]*")
HOME_PATH = re.compile(r"(?<!\w)/(?:Users|home)/[^\s,;]+")
REPOSITORY_URL = re.compile(r"(?i)(?:https?|ssh)://[^\s]+|git@[^\s:]+:[^\s]+")


class TelemetryError(ValueError):
    """Raised when runtime metadata violates the local telemetry contract."""


def plugin_version() -> str:
    manifest = Path(__file__).resolve().parents[2] / ".codex-plugin" / "plugin.json"
    try:
        value = json.loads(manifest.read_text(encoding="utf-8"))["version"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise TelemetryError(f"cannot read plugin version: {exc}") from exc
    if not isinstance(value, str) or not value:
        raise TelemetryError("plugin version is missing")
    return value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_timestamp(value: datetime | None = None) -> str:
    current = value or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def state_root(override: Path | None = None) -> Path:
    if override is not None:
        return Path(override).expanduser().resolve()
    configured = os.environ.get("AGENTS_TEAM_STATE_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Agents-Team"
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Agents-Team"
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "agents-team"


def _validate_identifier(value: str, name: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise TelemetryError(f"{name} must be a safe non-empty identifier")
    return value


def redact_text(value: str) -> tuple[str, list[str]]:
    redactions: list[str] = []

    def apply(pattern: re.Pattern[str], replacement: str, reason: str, text: str) -> str:
        updated, count = pattern.subn(replacement, text)
        if count and reason not in redactions:
            redactions.append(reason)
        return updated

    result = value
    result = apply(SECRET, r"\1=[REDACTED_SECRET]", "secret", result)
    result = apply(BEARER, "Bearer [REDACTED_SECRET]", "secret", result)
    result = apply(EMAIL, "[REDACTED_EMAIL]", "email", result)
    result = apply(WINDOWS_PATH, "[REDACTED_PATH]", "absolute_path", result)
    result = apply(HOME_PATH, "[REDACTED_PATH]", "absolute_path", result)
    result = apply(REPOSITORY_URL, "[REDACTED_REPOSITORY]", "repository_url", result)
    return result, redactions


def redact_data(value: Any) -> tuple[Any, list[str]]:
    redactions: list[str] = []
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        output = []
        for item in value:
            cleaned, reasons = redact_data(item)
            output.append(cleaned)
            redactions.extend(reason for reason in reasons if reason not in redactions)
        return output, redactions
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            cleaned, reasons = redact_data(item)
            output[key] = cleaned
            redactions.extend(reason for reason in reasons if reason not in redactions)
        return output, redactions
    return value, redactions


def _validate_metadata(metadata: dict[str, Any]) -> None:
    forbidden = sorted(set(metadata) & FORBIDDEN_METADATA)
    if forbidden:
        raise TelemetryError("forbidden runtime metadata: " + ", ".join(forbidden))
    unknown = sorted(set(metadata) - ALLOWED_METADATA)
    if unknown:
        raise TelemetryError("unsupported runtime metadata: " + ", ".join(unknown))
    for key in ("actorRole", "status", "reasonCode", "stage"):
        if key in metadata and (not isinstance(metadata[key], str) or not IDENTIFIER.fullmatch(metadata[key])):
            raise TelemetryError(f"{key} must be a safe identifier")
    for key in ("durationMs", "interventionCount", "reworkCount", "tokenCount", "costEstimate"):
        if key in metadata and (
            not isinstance(metadata[key], (int, float)) or isinstance(metadata[key], bool) or metadata[key] < 0
        ):
            raise TelemetryError(f"{key} must be a non-negative number")
    if "independent" in metadata and not isinstance(metadata["independent"], bool):
        raise TelemetryError("independent must be boolean")


def _validate_label(value: str | None, name: str) -> None:
    if value is None:
        return
    if not isinstance(value, str) or len(value) > 128 or "\n" in value or "\r" in value:
        raise TelemetryError(f"{name} must be a single-line string no longer than 128 characters")


def _event_files(run_dir: Path) -> list[Path]:
    files = [run_dir / f"events.jsonl.{index}" for index in range(MAX_ROTATED_FILES, 0, -1)]
    files.append(run_dir / "events.jsonl")
    return [path for path in files if path.is_file()]


def read_run(run_id: str, *, state_dir: Path | None = None) -> list[dict[str, Any]]:
    _validate_identifier(run_id, "run_id")
    run_dir = state_root(state_dir) / "runs" / run_id
    if run_dir.is_symlink():
        raise TelemetryError("refusing to read a symlinked run directory")
    events: list[dict[str, Any]] = []
    for path in _event_files(run_dir):
        if path.is_symlink():
            raise TelemetryError("refusing to read a symlinked event log")
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
    return sorted(events, key=lambda item: item.get("timestamp", ""))


def _last_timestamp(run_dir: Path) -> datetime | None:
    try:
        events = read_run(run_dir.name, state_dir=run_dir.parents[1])
        value = events[-1]["timestamp"]
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (IndexError, KeyError, ValueError, json.JSONDecodeError, OSError):
        return None


def purge_expired(*, state_dir: Path | None = None, now: datetime | None = None) -> list[str]:
    root = state_root(state_dir)
    runs_dir = root / "runs"
    if not runs_dir.is_dir():
        return []
    current = now or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    cutoff = current.astimezone(timezone.utc) - timedelta(days=RETENTION_DAYS)
    deleted: list[str] = []
    for run_dir in runs_dir.iterdir():
        if run_dir.is_symlink() or not run_dir.is_dir():
            continue
        last = _last_timestamp(run_dir)
        if last is not None and last < cutoff:
            shutil.rmtree(run_dir)
            deleted.append(run_dir.name)
    return sorted(deleted)


def _rotate(path: Path, incoming_bytes: int) -> None:
    if not path.is_file() or path.stat().st_size + incoming_bytes <= MAX_LOG_BYTES:
        return
    oldest = path.with_name(f"{path.name}.{MAX_ROTATED_FILES}")
    if oldest.exists():
        oldest.unlink()
    for index in range(MAX_ROTATED_FILES - 1, 0, -1):
        source = path.with_name(f"{path.name}.{index}")
        if source.exists():
            source.replace(path.with_name(f"{path.name}.{index + 1}"))
    path.replace(path.with_name(f"{path.name}.1"))


def record_event(
    run_id: str,
    event_type: str,
    *,
    state_dir: Path | None = None,
    trace_id: str | None = None,
    cohort_id: str | None = None,
    host_name: str = "codex",
    host_version: str = "unknown",
    provider: str = "unknown",
    model: str = "unknown",
    task_category: str = "unknown",
    risk_level: str = "unknown",
    final_status: str | None = None,
    metadata: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    _validate_identifier(run_id, "run_id")
    if event_type not in EVENT_TYPES:
        raise TelemetryError(f"unsupported event_type: {event_type}")
    if trace_id is not None:
        _validate_identifier(trace_id, "trace_id")
    if cohort_id is not None:
        _validate_identifier(cohort_id, "cohort_id")
    for name, value in {
        "host_name": host_name,
        "host_version": host_version,
        "provider": provider,
        "model": model,
        "task_category": task_category,
        "risk_level": risk_level,
        "final_status": final_status,
    }.items():
        _validate_label(value, name)
    details = metadata or {}
    _validate_metadata(details)
    cleaned_metadata, redactions = redact_data(details)
    cleaned_fields, field_redactions = redact_data({
        "hostName": host_name,
        "hostVersion": host_version,
        "provider": provider,
        "model": model,
        "taskCategory": task_category,
        "riskLevel": risk_level,
        "finalStatus": final_status,
    })
    for reason in field_redactions:
        if reason not in redactions:
            redactions.append(reason)
    event = {
        "eventSchemaVersion": EVENT_SCHEMA_VERSION,
        "eventId": str(uuid.uuid4()),
        "runId": run_id,
        "traceId": trace_id or run_id,
        "cohortId": cohort_id,
        "agentsTeamVersion": plugin_version(),
        "protocolVersion": PROTOCOL_VERSION,
        "os": platform.system() or "unknown",
        "eventType": event_type,
        "timestamp": iso_timestamp(timestamp),
        **cleaned_fields,
        "metadata": cleaned_metadata,
        "redactions": redactions,
    }
    root = state_root(state_dir)
    purge_expired(state_dir=root)
    path = root / "runs" / run_id / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    _rotate(path, len(serialized.encode("utf-8")))
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(serialized)
    return {"status": "recorded", "path": str(path), "event": event}


def list_runs(*, state_dir: Path | None = None) -> list[dict[str, Any]]:
    root = state_root(state_dir)
    purge_expired(state_dir=root)
    runs_dir = root / "runs"
    if not runs_dir.is_dir():
        return []
    summaries: list[dict[str, Any]] = []
    for run_dir in runs_dir.iterdir():
        if run_dir.is_symlink() or not run_dir.is_dir():
            continue
        events = read_run(run_dir.name, state_dir=root)
        if events:
            summaries.append({
                "runId": run_dir.name,
                "traceId": events[-1].get("traceId"),
                "eventCount": len(events),
                "lastEventType": events[-1].get("eventType"),
                "lastTimestamp": events[-1].get("timestamp"),
            })
    return sorted(summaries, key=lambda item: item["lastTimestamp"], reverse=True)


def delete_logs(run_id: str | None = None, *, state_dir: Path | None = None) -> dict[str, Any]:
    root = state_root(state_dir)
    runs_dir = root / "runs"
    if not runs_dir.is_dir():
        return {"status": "deleted", "deletedRuns": []}
    if run_id is not None:
        _validate_identifier(run_id, "run_id")
        targets = [runs_dir / run_id]
    else:
        targets = [path for path in runs_dir.iterdir() if path.is_dir()]
    deleted = []
    for target in targets:
        if target.is_symlink():
            raise TelemetryError("refusing to delete a symlinked run directory")
        if target.is_dir():
            shutil.rmtree(target)
            deleted.append(target.name)
    return {"status": "deleted", "deletedRuns": sorted(deleted)}
