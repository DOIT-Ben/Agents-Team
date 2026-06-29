"""Validate a generated project adapter and detect managed drift."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .config import ConfigError, load_config
from .managed_block import ManagedBlockError, extract_agents_block


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


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
    for target, expected_hash in config["managedFiles"].items():
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
