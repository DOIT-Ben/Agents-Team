"""Compose routing, provider selection, delivery evidence, and QA gates."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from .diagnostics import summarize_findings
from .evidence import validate_gate_evidence, validate_qa_evidence
from .providers import select_provider
from .routing import ParallelFacts, route_work


def evaluate_goal_workflow(
    *,
    intent: str,
    status: str,
    risk: str,
    available_skills: Iterable[str],
    gate_records: Iterable[dict[str, Any]],
    qa_evidence: dict[str, Any],
    current_sha: str,
    parallel: ParallelFacts | None = None,
) -> dict[str, Any]:
    route = route_work(intent=intent, status=status, risk=risk, parallel=parallel)
    provider = select_provider(route.phase, available_skills=available_skills)
    findings = validate_gate_evidence(gate_records, current_sha=current_sha)
    findings.extend(validate_qa_evidence(qa_evidence, risk=route.risk, current_sha=current_sha))
    summary = summarize_findings(findings)
    return {
        "route": asdict(route),
        "provider": asdict(provider),
        "status": summary["status"],
        "findings": summary["findings"],
    }
