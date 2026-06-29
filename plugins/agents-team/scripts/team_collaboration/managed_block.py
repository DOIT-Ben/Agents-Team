"""Safely add or update the managed section in AGENTS.md."""

from __future__ import annotations

import re


START_PREFIX = "<!-- TEAM-COLLABORATION:START"
END_MARKER = "<!-- TEAM-COLLABORATION:END -->"
BLOCK_RE = re.compile(
    r"<!-- TEAM-COLLABORATION:START(?: [^>]*)? -->\n.*?\n<!-- TEAM-COLLABORATION:END -->\n?",
    re.DOTALL,
)


class ManagedBlockError(ValueError):
    """Raised when managed markers are missing, duplicated, or unbalanced."""


def merge_agents_block(existing: str, content: str, protocol_version: str) -> str:
    starts = existing.count(START_PREFIX)
    ends = existing.count(END_MARKER)
    if starts != ends or starts > 1:
        raise ManagedBlockError("AGENTS.md has unbalanced or duplicate team collaboration markers")

    block = (
        f"<!-- TEAM-COLLABORATION:START protocol={protocol_version} -->\n"
        f"{content.rstrip()}\n"
        f"{END_MARKER}\n"
    )
    if starts == 1:
        return BLOCK_RE.sub(block, existing, count=1)

    separator = "" if not existing or existing.endswith("\n") else "\n"
    if existing and not existing.endswith("\n\n"):
        separator += "\n"
    return f"{existing}{separator}{block}"


def extract_agents_block(existing: str) -> str:
    matches = BLOCK_RE.findall(existing)
    if len(matches) != 1:
        raise ManagedBlockError("AGENTS.md must contain exactly one team collaboration block")
    return matches[0]


def remove_agents_block(existing: str) -> str:
    starts = existing.count(START_PREFIX)
    ends = existing.count(END_MARKER)
    if starts != 1 or ends != 1:
        raise ManagedBlockError("AGENTS.md must contain exactly one team collaboration block")
    match = BLOCK_RE.search(existing)
    if match is None:
        raise ManagedBlockError("team collaboration block is malformed")
    before = existing[: match.start()]
    after = existing[match.end() :]
    if before.endswith("\n\n"):
        before = before[:-1]
    return before + after
