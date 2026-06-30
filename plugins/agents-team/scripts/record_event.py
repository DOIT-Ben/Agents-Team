#!/usr/bin/env python3
"""Record one privacy-safe Agents-Team runtime event locally."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from team_collaboration.telemetry import EVENT_TYPES, TelemetryError, record_event


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a local Agents-Team runtime event.")
    parser.add_argument("run_id")
    parser.add_argument("event_type", choices=sorted(EVENT_TYPES))
    parser.add_argument("--trace-id")
    parser.add_argument("--cohort-id")
    parser.add_argument("--host-name", default="codex")
    parser.add_argument("--host-version", default="unknown")
    parser.add_argument("--provider", default="unknown")
    parser.add_argument("--model", default="unknown")
    parser.add_argument("--task-category", default="unknown")
    parser.add_argument("--risk-level", default="unknown")
    parser.add_argument("--final-status")
    parser.add_argument("--actor-role")
    parser.add_argument("--status")
    parser.add_argument("--reason-code")
    parser.add_argument("--stage")
    parser.add_argument("--duration-ms", type=int)
    parser.add_argument("--intervention-count", type=int)
    parser.add_argument("--rework-count", type=int)
    parser.add_argument("--token-count", type=int)
    parser.add_argument("--cost-estimate", type=float)
    parser.add_argument("--independent", choices=["yes", "no"])
    parser.add_argument("--state-dir", type=Path)
    args = parser.parse_args()
    metadata = {
        "actorRole": args.actor_role,
        "status": args.status,
        "reasonCode": args.reason_code,
        "stage": args.stage,
        "durationMs": args.duration_ms,
        "interventionCount": args.intervention_count,
        "reworkCount": args.rework_count,
        "tokenCount": args.token_count,
        "costEstimate": args.cost_estimate,
        "independent": None if args.independent is None else args.independent == "yes",
    }
    metadata = {key: value for key, value in metadata.items() if value is not None}
    try:
        result = record_event(
            args.run_id,
            args.event_type,
            state_dir=args.state_dir,
            trace_id=args.trace_id,
            cohort_id=args.cohort_id,
            host_name=args.host_name,
            host_version=args.host_version,
            provider=args.provider,
            model=args.model,
            task_category=args.task_category,
            risk_level=args.risk_level,
            final_status=args.final_status,
            metadata=metadata,
        )
    except TelemetryError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({
        "status": result["status"],
        "runId": result["event"]["runId"],
        "eventType": result["event"]["eventType"],
        "path": result["path"],
        "redactions": result["event"]["redactions"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
