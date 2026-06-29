"""Load role contracts and compose bounded worker prompts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


ROLE_NAMES = (
    "goal-planner",
    "implementation-worker",
    "test-engineer",
    "code-reviewer",
    "security-auditor",
    "independent-verifier",
)


def load_role_contract(plugin_root: Path, role: str) -> str:
    if role not in ROLE_NAMES:
        raise ValueError(f"unknown role: {role}")
    path = plugin_root.resolve() / "references" / "roles" / f"{role}.md"
    return path.read_text(encoding="utf-8")


def _paths(title: str, values: Iterable[str]) -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    rendered = "\n".join(f"- {value}" for value in items) if items else "- None declared"
    return f"## {title}\n\n{rendered}"


def compose_role_prompt(
    plugin_root: Path,
    role: str,
    *,
    issue: str,
    allowed_files: Iterable[str],
    forbidden_files: Iterable[str],
) -> str:
    contract = load_role_contract(plugin_root, role)
    return "\n\n".join(
        (
            contract.rstrip(),
            "## Goal Contract\n\n" + issue.strip(),
            _paths("Allowed Files", allowed_files),
            _paths("Forbidden Files", forbidden_files),
            "Report only within this role contract. Do not broaden the Goal or claim whole-Goal completion.",
        )
    ) + "\n"
