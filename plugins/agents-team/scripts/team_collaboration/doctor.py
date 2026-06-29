"""Read-only health audit for an initialized project adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ConfigError, load_config
from .diagnostics import Finding, summarize_findings
from .validate import validate_project


def doctor_project(root: Path) -> dict[str, Any]:
    root = root.resolve()
    drift = validate_project(root)
    if drift:
        findings = [Finding(
            "AT-DRIFT-001",
            "error",
            "project adapter",
            error,
            "run manage_project.py check, then repair or upgrade after reviewing drift",
            error,
        ) for error in drift]
        return summarize_findings(findings)

    try:
        config = load_config(root / ".codex/team-collaboration.json")
    except ConfigError as exc:
        return summarize_findings([Finding(
            "AT-SYSTEM-001",
            "error",
            ".codex/team-collaboration.json",
            str(exc),
            "repair the configuration before executing a Goal",
            str(exc),
        )])

    findings: list[Finding] = []
    if not str(config["project"].get("repository", "")).strip():
        findings.append(Finding(
            "AT-SYSTEM-002",
            "warning",
            "project.repository",
            "GitHub repository could not be identified",
            "configure origin or set project.repository explicitly",
            "empty",
        ))
    if not str(config["commands"].get("test", "")).strip():
        findings.append(Finding(
            "AT-SYSTEM-003",
            "warning",
            "commands.test",
            "test command is not configured",
            "set the canonical test command before L2/L3 execution",
            "empty",
        ))
    for field in ("criticalPaths", "protectedFiles"):
        if not config["risk"].get(field):
            findings.append(Finding(
                "AT-CONTRACT-010",
                "warning",
                f"risk.{field}",
                f"{field} has not been classified",
                "review the repository and list paths that require elevated approval",
                "empty",
            ))
    return summarize_findings(findings)
