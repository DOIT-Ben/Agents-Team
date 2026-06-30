"""Offline Beta evaluation for paired baseline and Agents-Team runs."""

from __future__ import annotations

from statistics import median
from typing import Any


class EvaluationError(ValueError):
    """Raised when Beta evaluation data is incomplete or inconsistent."""


def _rate(numerator: int | float, denominator: int | float) -> float:
    return 0.0 if not denominator else numerator / denominator


def _required_number(data: dict[str, Any], name: str) -> float:
    value = data.get(name)
    if not isinstance(value, (int, float)) or value < 0:
        raise EvaluationError(f"{name} must be a non-negative number")
    return float(value)


def _success_rate(data: dict[str, Any], successes_name: str, attempts_name: str) -> float:
    successes = _required_number(data, successes_name)
    attempts = _required_number(data, attempts_name)
    if successes > attempts:
        raise EvaluationError(f"{successes_name} cannot exceed {attempts_name}")
    return _rate(successes, attempts)


def _paired_runs(runs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pairs: dict[str, dict[str, dict[str, Any]]] = {}
    for run in runs:
        if not isinstance(run, dict):
            raise EvaluationError("every run must be an object")
        pair_id = run.get("pairId")
        mode = run.get("mode")
        if not isinstance(pair_id, str) or mode not in {"baseline", "agents-team"}:
            raise EvaluationError("every run requires pairId and baseline/agents-team mode")
        if mode in pairs.setdefault(pair_id, {}):
            raise EvaluationError(f"duplicate {mode} run for pair {pair_id}")
        for field in ("runId",):
            if not isinstance(run.get(field), str) or not run[field]:
                raise EvaluationError(f"every run requires non-empty {field}")
        for field in ("verifiedSuccess", "defectEscaped", "firstPass"):
            if not isinstance(run.get(field), bool):
                raise EvaluationError(f"every run requires boolean {field}")
        for field in ("durationSeconds", "cost"):
            value = run.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise EvaluationError(f"every run requires non-negative {field}")
        pairs[pair_id][mode] = run
    incomplete = [pair_id for pair_id, pair in pairs.items() if set(pair) != {"baseline", "agents-team"}]
    if incomplete:
        raise EvaluationError("incomplete pairs: " + ", ".join(sorted(incomplete)))
    ordered = [pairs[key] for key in sorted(pairs)]
    return [pair["baseline"] for pair in ordered], [pair["agents-team"] for pair in ordered]


def _boolean_rate(runs: list[dict[str, Any]], field: str) -> float:
    return _rate(sum(bool(run.get(field)) for run in runs), len(runs))


def evaluate_beta(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("runs"), list):
        raise EvaluationError("evaluation input requires a runs array")
    if not isinstance(data.get("testerFeedback"), list):
        raise EvaluationError("evaluation input requires a testerFeedback array")
    baseline, team = _paired_runs(data["runs"])
    effective_testers = _required_number(data, "effectiveTesters")
    invited_testers = _required_number(data, "invitedTesters")
    if effective_testers > invited_testers:
        raise EvaluationError("effectiveTesters cannot exceed invitedTesters")
    install_rate = _success_rate(data, "installSuccesses", "installAttempts")
    upgrade_rate = _success_rate(data, "upgradeSuccesses", "upgradeAttempts")
    rollback_rate = _success_rate(data, "rollbackSuccesses", "rollbackAttempts")
    diagnostic_rate = _success_rate(data, "reproducibleReports", "diagnosticReports")
    baseline_success = _boolean_rate(baseline, "verifiedSuccess")
    team_success = _boolean_rate(team, "verifiedSuccess")
    baseline_escape = _boolean_rate(baseline, "defectEscaped")
    team_escape = _boolean_rate(team, "defectEscaped")
    escape_reduction = 0.0 if baseline_escape == 0 else (baseline_escape - team_escape) / baseline_escape
    durations_base = [float(run.get("durationSeconds", 0)) for run in baseline]
    durations_team = [float(run.get("durationSeconds", 0)) for run in team]
    costs_base = [float(run.get("cost", 0)) for run in baseline]
    costs_team = [float(run.get("cost", 0)) for run in team]
    duration_increase = _rate(median(durations_team), median(durations_base)) - 1 if median(durations_base) else 0.0
    cost_increase = _rate(median(costs_team), median(costs_base)) - 1 if median(costs_base) else 0.0
    tester_feedback = data["testerFeedback"]
    cohort_ids: set[str] = set()
    ratings: list[float] = []
    reuse: list[bool] = []
    for item in tester_feedback:
        if not isinstance(item, dict):
            raise EvaluationError("testerFeedback items must be objects")
        cohort_id = item.get("cohortId")
        rating = item.get("userRating")
        again = item.get("wouldUseAgain")
        if not isinstance(cohort_id, str) or not cohort_id or cohort_id in cohort_ids:
            raise EvaluationError("testerFeedback requires unique non-empty cohortId values")
        if not isinstance(rating, int) or isinstance(rating, bool) or rating not in range(1, 6):
            raise EvaluationError("testerFeedback userRating must be an integer from 1 to 5")
        if not isinstance(again, bool):
            raise EvaluationError("testerFeedback wouldUseAgain must be boolean")
        cohort_ids.add(cohort_id)
        ratings.append(float(rating))
        reuse.append(again)
    isolation_violations = sum(bool(run.get("contextIsolationViolation")) for run in team)

    metrics = {
        "effectiveTesters": int(effective_testers),
        "realRuns": len(data["runs"]),
        "pairedTasks": len(team),
        "installSuccessRate": install_rate,
        "upgradeSuccessRate": upgrade_rate,
        "rollbackSuccessRate": rollback_rate,
        "diagnosticReproductionRate": diagnostic_rate,
        "baselineVerifiedSuccessRate": baseline_success,
        "agentsTeamVerifiedSuccessRate": team_success,
        "verifiedSuccessLiftPoints": (team_success - baseline_success) * 100,
        "baselineDefectEscapeRate": baseline_escape,
        "agentsTeamDefectEscapeRate": team_escape,
        "defectEscapeReduction": escape_reduction,
        "medianDurationIncrease": duration_increase,
        "medianCostIncrease": cost_increase,
        "contextIsolationViolations": isolation_violations,
        "wouldUseAgainRate": _rate(sum(reuse), len(reuse)),
        "averageUserRating": _rate(sum(ratings), len(ratings)),
        "testerFeedbackCount": len(tester_feedback),
    }
    gates = {
        "effective_testers": effective_testers >= 20,
        "real_runs": len(data["runs"]) >= 100,
        "paired_tasks": len(team) >= 40,
        "install_success": install_rate >= 0.95,
        "upgrade_success": upgrade_rate >= 0.95,
        "rollback_success": rollback_rate >= 0.95,
        "diagnostic_reproduction": diagnostic_rate >= 0.85,
        "no_open_p0_p1_privacy_data_loss": _required_number(data, "openP0P1PrivacyOrDataLoss") == 0,
        "context_isolation": isolation_violations == 0,
        "mechanism_improvement": metrics["verifiedSuccessLiftPoints"] >= 15 or escape_reduction >= 0.30,
        "cost_and_duration": not (duration_increase > 0.50 and cost_increase > 0.50),
        "reuse_intent": metrics["wouldUseAgainRate"] >= 0.70,
        "user_rating": metrics["averageUserRating"] >= 4.0,
        "tester_feedback_coverage": len(tester_feedback) >= effective_testers,
    }
    failed = [name for name, passed in gates.items() if not passed]
    return {
        "evaluationSchemaVersion": 1,
        "decision": "stable_candidate" if not failed else "continue_beta",
        "metrics": metrics,
        "gates": gates,
        "failedGates": failed,
        "note": "Pilot decision data; not a claim of statistical significance.",
    }
