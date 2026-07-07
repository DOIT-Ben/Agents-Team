"""Create a project adapter with dry-run-first and non-destructive writes."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import CONFIG_SCHEMA_VERSION, PLUGIN_ID, PLUGIN_VERSION, PROTOCOL_VERSION
from .config import validate_config
from .inspect import inspect_repository
from .managed_block import extract_agents_block, merge_agents_block


class InitializationError(RuntimeError):
    """Raised when initialization cannot continue without risking project data."""


TEMPLATE_TARGETS = {
    "team-collaboration.schema.json": ".codex/schemas/team-collaboration.schema.json",
    "validate_team_collaboration.py": ".codex/scripts/validate_team_collaboration.py",
    "validate_pr_contract.py": ".codex/scripts/validate_pr_contract.py",
    "doctor_team_collaboration.py": ".codex/scripts/doctor_team_collaboration.py",
    "team-goal.yml": ".github/ISSUE_TEMPLATE/team-goal.yml",
    "critical-goal.yml": ".github/ISSUE_TEMPLATE/critical-goal.yml",
    "pull_request_template.md": ".github/pull_request_template.md",
    "collaboration-gate.yml": ".github/workflows/collaboration-gate.yml",
    "adr-readme.md": "docs/adr/README.md",
}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        raise InitializationError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def _ensure_git(root: Path) -> None:
    if not (root / ".git").exists():
        raise InitializationError("team collaboration requires a Git repository")


def _is_dirty(root: Path) -> bool:
    return bool(_git(root, "status", "--porcelain"))


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temp_name = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_name, path)


def _assert_no_symlink_path(root: Path, target: str) -> None:
    current = root
    for part in Path(target).parts:
        current = current / part
        if current.is_symlink():
            raise InitializationError(f"refusing to access symlinked managed path: {target}")


def _repository_name(root: Path) -> str:
    result = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        return ""
    value = result.stdout.strip().removesuffix(".git")
    if value.startswith("git@") and ":" in value:
        value = value.split(":", 1)[1]
    elif "/" in value:
        value = "/".join(value.rstrip("/").split("/")[-2:])
    return value


def _default_branch(root: Path) -> str:
    result = subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], cwd=root, text=True, capture_output=True)
    return result.stdout.strip() or "main"


def _existing_mechanism(root: Path) -> dict[str, Any]:
    path = root / ".codex" / "team-collaboration.json"
    if not path.is_file():
        return {}
    try:
        mechanism = json.loads(path.read_text(encoding="utf-8"))["mechanism"]
        return mechanism if isinstance(mechanism, dict) else {}
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return {}


def _existing_managed_hashes(root: Path) -> dict[str, str]:
    path = root / ".codex" / "team-collaboration.json"
    if not path.is_file():
        return {}
    try:
        managed = json.loads(path.read_text(encoding="utf-8"))["managedFiles"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return {}
    if not isinstance(managed, dict):
        return {}
    return {key: value for key, value in managed.items() if isinstance(key, str) and isinstance(value, str)}


def _build_config(root: Path, profile: dict[str, Any], managed: dict[str, str]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    existing = _existing_mechanism(root)
    upgraded = existing.get("protocolVersion") not in {None, PROTOCOL_VERSION}
    return {
        "$schema": "./schemas/team-collaboration.schema.json",
        "mechanism": {
            "id": PLUGIN_ID,
            "pluginVersion": PLUGIN_VERSION,
            "protocolVersion": PROTOCOL_VERSION,
            "configSchemaVersion": CONFIG_SCHEMA_VERSION,
            "initializedAt": existing.get("initializedAt") or now,
            "lastUpgradedAt": now if upgraded else existing.get("lastUpgradedAt"),
        },
        "project": {
            "name": root.name,
            "type": profile["projectType"],
            "repository": _repository_name(root),
            "defaultBranch": _default_branch(root),
        },
        "commands": profile["commands"],
        "paths": profile["paths"],
        "risk": {"criticalPaths": [], "protectedFiles": [], "productionPaths": [], "realProviderPaths": []},
        "overrides": {"requireIssueForL1": False, "requireRealSmokeForRelease": True},
        "enforcement": {
            "mode": "strict",
            "failClosedRisks": ["L2", "L3"],
            "requiredCheckNames": [],
            "requireLinkedIssue": {"L1": False, "L2": True, "L3": True},
            "requireIndependentQA": {"L1": False, "L2": True, "L3": True},
            "requireFailureRecord": True,
        },
        "managedFiles": managed,
    }


def initialize_project(root: Path, plugin_root: Path, *, apply: bool = False, allow_dirty: bool = False) -> dict[str, Any]:
    root = root.resolve()
    plugin_root = plugin_root.resolve()
    _ensure_git(root)
    if apply and _is_dirty(root) and not allow_dirty:
        raise InitializationError("working tree is dirty; commit or stash changes before initialization")

    template_root = plugin_root / "templates" / "project"
    for target in ["AGENTS.md", ".codex/team-collaboration.json", *TEMPLATE_TARGETS.values()]:
        _assert_no_symlink_path(root, target)
    agents_content = (template_root / "agents-managed-block.md").read_text(encoding="utf-8")
    existing_agents = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").is_file() else ""
    existing_managed = _existing_managed_hashes(root)
    if "TEAM-COLLABORATION:START" in existing_agents:
        current_block = extract_agents_block(existing_agents).encode("utf-8")
        if existing_managed.get("AGENTS.md#TEAM-COLLABORATION") != _sha256(current_block):
            raise InitializationError("existing AGENTS.md collaboration block was locally modified")
    rendered_agents = merge_agents_block(existing_agents, agents_content, PROTOCOL_VERSION).encode("utf-8")

    rendered: dict[str, bytes] = {"AGENTS.md": rendered_agents}
    for template, target in TEMPLATE_TARGETS.items():
        data = (template_root / template).read_bytes()
        destination = root / target
        if destination.exists() and destination.read_bytes() != data:
            current_hash = _sha256(destination.read_bytes())
            if existing_managed.get(target) != current_hash:
                raise InitializationError(f"existing unmanaged or locally modified target would be overwritten: {target}")
        rendered[target] = data

    managed = {target: _sha256(data) for target, data in sorted(rendered.items()) if target != "AGENTS.md"}
    managed["AGENTS.md#TEAM-COLLABORATION"] = _sha256(extract_agents_block(rendered_agents.decode("utf-8")).encode("utf-8"))
    profile = inspect_repository(root)
    config = _build_config(root, profile, managed)
    errors = validate_config(config)
    if errors:
        raise InitializationError("generated invalid configuration: " + "; ".join(errors))
    rendered[".codex/team-collaboration.json"] = (json.dumps(config, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    create = [target for target in rendered if not (root / target).exists()]
    update = [target for target in rendered if (root / target).exists() and (root / target).read_bytes() != rendered[target]]
    result: dict[str, Any] = {"status": "preview", "create": sorted(create), "update": sorted(update), "profile": profile}
    if not apply:
        return result

    backups: dict[Path, bytes | None] = {}
    try:
        for target, data in rendered.items():
            path = root / target
            backups[path] = path.read_bytes() if path.is_file() else None
            _atomic_write(path, data)
    except Exception:
        for path, data in backups.items():
            if data is None:
                if path.exists():
                    path.unlink()
            else:
                _atomic_write(path, data)
        raise
    result["status"] = "applied"
    return result
