# Local Runtime Records and Feedback

Agents-Team records only structured operational metadata. The default state directory is `%LOCALAPPDATA%\Agents-Team` on Windows, `~/Library/Application Support/Agents-Team` on macOS, and `$XDG_STATE_HOME/agents-team` or `~/.local/state/agents-team` on Linux. `AGENTS_TEAM_STATE_DIR` overrides it for isolated testing.

Commands below use `python3`; use `py -3` on Windows when `python3` is unavailable.

## Event recording

```bash
python3 PLUGIN_ROOT/scripts/record_event.py RUN_ID goal_created --trace-id TRACE_ID --cohort-id B1-07 --risk-level L2
python3 PLUGIN_ROOT/scripts/record_event.py RUN_ID context_isolation_checked --independent yes
python3 PLUGIN_ROOT/scripts/record_event.py RUN_ID qa_verdict --status PASS --reason-code QA-PASS
python3 PLUGIN_ROOT/scripts/record_event.py RUN_ID run_completed --final-status PASS
```

Supported event types are `goal_created`, `work_dispatched`, `context_isolation_checked`, `implementation_delivered`, `review_started`, `qa_verdict`, `human_intervention`, `gate_blocked`, `rollback`, `run_completed`, and `run_failed`.

Logs are retained for 14 days. Each log rotates at 20 MiB and retains at most five rotated files.

## Review, export, and deletion

```bash
python3 PLUGIN_ROOT/scripts/manage_project.py logs REPO
python3 PLUGIN_ROOT/scripts/manage_project.py logs REPO --run-id RUN_ID
python3 PLUGIN_ROOT/scripts/manage_project.py delete-logs REPO --run-id RUN_ID
python3 PLUGIN_ROOT/scripts/manage_project.py delete-logs REPO --run-id RUN_ID --apply
```

Feedback is preview-only unless `--confirm` is present:

```bash
python3 PLUGIN_ROOT/scripts/manage_project.py feedback REPO \
  --run-id RUN_ID --feedback-type bug --severity P2 \
  --expected-result "..." --actual-result "..." \
  --reproduction-steps "..."
```

Add `--confirm` to write `feedback.md` and `diagnostics.json` locally. Add `--open-issue` only after confirmation to open a GitHub draft. No command submits an Issue automatically.

The user can delete runtime logs at any time. Feedback bundles are ordinary local files and can be deleted directly after the user decides they are no longer needed.
