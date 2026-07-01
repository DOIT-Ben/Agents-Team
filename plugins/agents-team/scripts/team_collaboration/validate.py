"""Validate a generated project adapter and detect managed drift."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .config import ConfigError, load_config
from .managed_block import ManagedBlockError, extract_agents_block


EXPECTED_MANAGED_FILES = frozenset(
    {
        "AGENTS.md#TEAM-COLLABORATION",
        ".codex/schemas/team-collaboration.schema.json",
        ".codex/scripts/validate_team_collaboration.py",
        ".codex/scripts/validate_pr_contract.py",
        ".codex/scripts/doctor_team_collaboration.py",
        ".github/ISSUE_TEMPLATE/team-goal.yml",
        ".github/ISSUE_TEMPLATE/critical-goal.yml",
        ".github/pull_request_template.md",
        ".github/workflows/collaboration-gate.yml",
        "docs/adr/README.md",
    }
)


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _managed_file_set_errors(managed_files: dict[str, str]) -> list[str]:
    errors: list[str] = []
    actual = set(managed_files)
    for target in sorted(EXPECTED_MANAGED_FILES - actual):
        errors.append(f"managed file set mismatch: missing {target}")
    for target in sorted(actual - EXPECTED_MANAGED_FILES):
        errors.append(f"managed file set mismatch: unexpected {target}")
    return errors


def validate_project(root: Path) -> list[str]:
    root = root.resolve()
    config_path = root / ".codex" / "team-collaboration.json"
    if not config_path.is_file():
        return ["missing: .codex/team-collaboration.json"]
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        return [str(exc)]

    errors: list[str] = []
    managed_files = config["managedFiles"]
    errors.extend(_managed_file_set_errors(managed_files))
    for target in sorted(EXPECTED_MANAGED_FILES & set(managed_files)):
        expected_hash = managed_files[target]
        if target == "AGENTS.md#TEAM-COLLABORATION":
            path = root / "AGENTS.md"
            if not path.is_file():
                errors.append("missing: AGENTS.md")
                continue
            try:
                data = extract_agents_block(path.read_text(encoding="utf-8")).encode("utf-8")
            except ManagedBlockError as exc:
                errors.append(str(exc))
                continue
        else:
            path = root / target
            if not path.is_file():
                errors.append(f"missing: {target}")
                continue
            data = path.read_bytes()
        if _sha256(data) != expected_hash:
            errors.append(f"managed file drift: {target}")
    return errors
