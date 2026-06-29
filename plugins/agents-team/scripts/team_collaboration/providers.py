"""Select built-in or compatible external engineering workflow skills."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


BUILTIN = {
    "plan": "plan-team-goal",
    "build": "build-team-goal",
    "debug": "debug-team-goal",
    "review": "review-team-goal",
    "ship": "ship-team-goal",
}

EXTERNAL = {
    "plan": "planning-and-task-breakdown",
    "build": "incremental-implementation",
    "debug": "debugging-and-error-recovery",
    "review": "code-review-and-quality",
    "ship": "shipping-and-launch",
}


@dataclass(frozen=True)
class ProviderDecision:
    provider: str
    skill: str
    phase: str


def select_provider(phase: str, *, available_skills: Iterable[str]) -> ProviderDecision:
    normalized = phase.strip().lower()
    if normalized not in BUILTIN:
        raise ValueError(f"unknown phase: {phase}")

    available = set(available_skills)
    external = EXTERNAL[normalized]
    if external in available:
        return ProviderDecision("external", external, normalized)
    return ProviderDecision("builtin", BUILTIN[normalized], normalized)
