"""Deterministic engineering-phase and worker-role routing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParallelFacts:
    independent_tasks: bool
    disjoint_files: bool
    stable_contracts: bool
    independent_tests: bool

    def allowed(self) -> bool:
        return all(
            (
                self.independent_tasks,
                self.disjoint_files,
                self.stable_contracts,
                self.independent_tests,
            )
        )


@dataclass(frozen=True)
class RouteDecision:
    phase: str
    skill: str
    role: str
    risk: str
    can_parallel: bool


ROUTES = {
    "plan": ("plan-team-goal", "goal-planner"),
    "build": ("build-team-goal", "implementation-worker"),
    "debug": ("debug-team-goal", "test-engineer"),
    "review": ("review-team-goal", "code-reviewer"),
    "ship": ("ship-team-goal", "independent-verifier"),
}

STATE_PHASE = {
    "draft": "plan",
    "ready": "plan",
    "in-progress": "build",
    "implemented": "review",
    "verifying": "review",
    "pass": "ship",
    "mergeable": "ship",
}

INTENT_PHASES = (
    ({"fail", "failing", "failed", "error", "bug", "debug", "timeout", "broken"}, "debug"),
    ({"review", "audit", "inspect"}, "review"),
    ({"ship", "release", "deploy", "deliver"}, "ship"),
    ({"plan", "design", "decompose", "break down"}, "plan"),
    ({"build", "implement", "code", "fix"}, "build"),
)


def _phase_from_intent(intent: str) -> str | None:
    normalized = intent.lower()
    for terms, phase in INTENT_PHASES:
        if any(term in normalized for term in terms):
            return phase
    return None


def route_work(
    *,
    intent: str,
    status: str,
    risk: str,
    parallel: ParallelFacts | None = None,
) -> RouteDecision:
    normalized_risk = risk.upper()
    if normalized_risk not in {"L1", "L2", "L3"}:
        raise ValueError(f"unknown risk: {risk}")

    intent_phase = _phase_from_intent(intent)
    status_phase = STATE_PHASE.get(status.strip().lower())

    # Failure language is actionable even when the lifecycle still says build.
    if intent_phase == "debug":
        phase = "debug"
    elif status_phase is not None:
        phase = status_phase
    elif intent_phase is not None:
        phase = intent_phase
    else:
        raise ValueError(f"cannot route status={status!r} intent={intent!r}")

    skill, role = ROUTES[phase]
    return RouteDecision(
        phase=phase,
        skill=skill,
        role=role,
        risk=normalized_risk,
        can_parallel=parallel.allowed() if parallel is not None else False,
    )
