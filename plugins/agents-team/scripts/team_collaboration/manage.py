"""Check, repair, upgrade, or remove a project adapter."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .initialize import InitializationError, initialize_project
from .managed_block import remove_agents_block
from .validate import validate_project


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _remove_project(root: Path, *, apply: bool) -> dict[str, Any]:
    import json

    config_path = root / ".codex" / "team-collaboration.json"
    if not config_path.is_file():
        raise InitializationError("project is not initialized")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    delete = [target for target in config.get("managedFiles", {}) if not target.startswith("AGENTS.md#")]
    delete.append(".codex/team-collaboration.json")
    result: dict[str, Any] = {"status": "preview", "delete": sorted(delete), "update": ["AGENTS.md"]}
    if not apply:
        return result

    for target, expected in config.get("managedFiles", {}).items():
        if target.startswith("AGENTS.md#"):
            continue
        path = root / target
        if path.is_file() and _sha256(path.read_bytes()) != expected:
            raise InitializationError(f"refusing to remove modified managed file: {target}")
    agents = root / "AGENTS.md"
    if agents.is_file():
        agents.write_text(remove_agents_block(agents.read_text(encoding="utf-8")), encoding="utf-8")
    for target in delete:
        path = root / target
        if path.is_file():
            path.unlink()
    result["status"] = "applied"
    return result


def manage_project(root: Path, plugin_root: Path, action: str, *, apply: bool = False) -> dict[str, Any]:
    root = root.resolve()
    if action == "check":
        return {"status": "valid" if not validate_project(root) else "invalid", "errors": validate_project(root)}
    if action in {"repair", "upgrade"}:
        drift = [error for error in validate_project(root) if "drift" in error or "managed block" in error]
        if drift:
            raise InitializationError("managed content was modified; preserve, restore, or convert the change before continuing: " + "; ".join(drift))
        return initialize_project(root, plugin_root, apply=apply, allow_dirty=apply)
    if action == "remove":
        return _remove_project(root, apply=apply)
    raise ValueError(f"unsupported management action: {action}")
