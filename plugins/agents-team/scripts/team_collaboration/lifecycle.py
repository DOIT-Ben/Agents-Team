"""Explicit GitHub-label lifecycle for Goal delivery."""

from __future__ import annotations

from collections.abc import Iterable

from .diagnostics import Finding


STATUS_PREFIX = "status:"
TRANSITIONS = {
    "draft": {"ready"},
    "ready": {"in-progress"},
    "in-progress": {"implemented"},
    "implemented": {"verifying"},
    "verifying": {"pass", "fail"},
    "pass": {"mergeable"},
    "fail": {"in-progress"},
    "mergeable": set(),
}


def status_from_labels(labels: Iterable[str]) -> tuple[str | None, list[Finding]]:
    statuses = [label[len(STATUS_PREFIX):].strip().lower() for label in labels if label.lower().startswith(STATUS_PREFIX)]
    if len(statuses) != 1 or statuses[0] not in TRANSITIONS:
        return None, [Finding(
            "AT-STATE-001",
            "error",
            "GitHub labels",
            "exactly one recognized status label is required",
            "apply one status:draft|ready|in-progress|implemented|verifying|pass|fail|mergeable label",
            ", ".join(statuses) or "none",
        )]
    return statuses[0], []


def validate_transition(previous: str, current: str, *, risk: str, decision_approved: bool = False) -> list[Finding]:
    previous = previous.lower()
    current = current.lower()
    if previous not in TRANSITIONS or current not in TRANSITIONS.get(previous, set()):
        return [Finding(
            "AT-STATE-002",
            "error",
            "Goal lifecycle",
            f"illegal state transition: {previous} -> {current}",
            "return to the last valid state and follow the required gates in order",
            f"{previous}->{current}",
        )]
    if risk == "L3" and previous == "ready" and current == "in-progress" and not decision_approved:
        return [Finding(
            "AT-STATE-003",
            "error",
            "L3 decision",
            "L3 work cannot start without explicit user approval",
            "record the approved design, cost, risk and rollback decision",
            "decision:approved missing",
        )]
    return []
