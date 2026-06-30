#!/usr/bin/env python3
"""Check, repair, upgrade, or remove the project adapter."""

import argparse
import json
from pathlib import Path

from team_collaboration.feedback import FeedbackError, export_feedback, prepare_github_issue
from team_collaboration.initialize import InitializationError
from team_collaboration.manage import manage_project
from team_collaboration.telemetry import delete_logs, list_runs, read_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage an Agents-Team project adapter and local runtime records.")
    parser.add_argument("action", choices=["check", "repair", "upgrade", "remove", "feedback", "logs", "delete-logs"])
    parser.add_argument("project", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", action="store_true", help="Write the reviewed feedback bundle locally.")
    parser.add_argument("--open-issue", action="store_true", help="Open a GitHub draft after local export.")
    parser.add_argument("--run-id")
    parser.add_argument("--feedback-type", choices=[
        "bug", "missed_defect", "false_block", "context_isolation", "compatibility", "privacy", "feature_request",
    ])
    parser.add_argument("--severity", choices=["P0", "P1", "P2", "P3"], default="P2")
    parser.add_argument("--expected-result")
    parser.add_argument("--actual-result")
    parser.add_argument("--reproduction-steps")
    parser.add_argument("--user-rating", type=int)
    parser.add_argument("--would-use-again", choices=["yes", "no"])
    parser.add_argument("--content-attachment-consent", action="store_true")
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "feedback":
            required = {
                "--run-id": args.run_id,
                "--feedback-type": args.feedback_type,
                "--expected-result": args.expected_result,
                "--actual-result": args.actual_result,
                "--reproduction-steps": args.reproduction_steps,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise FeedbackError("missing required feedback arguments: " + ", ".join(missing))
            if args.open_issue and not args.confirm:
                raise FeedbackError("--open-issue requires --confirm after reviewing the preview")
            result = export_feedback(
                run_id=args.run_id,
                feedback_type=args.feedback_type,
                severity=args.severity,
                expected_result=args.expected_result,
                actual_result=args.actual_result,
                reproduction_steps=args.reproduction_steps,
                state_dir=args.state_dir,
                output_dir=args.output,
                confirmed=args.confirm,
                user_rating=args.user_rating,
                would_use_again=None if args.would_use_again is None else args.would_use_again == "yes",
                content_attachment_consent=args.content_attachment_consent,
            )
            if args.open_issue:
                result["github"] = prepare_github_issue(Path(result["directory"]), args.feedback_type)
        elif args.action == "logs":
            result = {
                "status": "local_only",
                "runs": read_run(args.run_id, state_dir=args.state_dir) if args.run_id else list_runs(state_dir=args.state_dir),
            }
        elif args.action == "delete-logs":
            candidates = [args.run_id] if args.run_id else [item["runId"] for item in list_runs(state_dir=args.state_dir)]
            result = delete_logs(args.run_id, state_dir=args.state_dir) if args.apply else {
                "status": "preview",
                "deleteRuns": candidates,
                "applyRequired": True,
            }
        else:
            result = manage_project(args.project, Path(__file__).resolve().parents[1], args.action, apply=args.apply)
    except (FeedbackError, InitializationError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("status") in {"invalid", "blocked"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
