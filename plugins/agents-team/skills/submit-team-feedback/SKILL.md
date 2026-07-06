---
name: submit-team-feedback
description: Use when a user wants to submit Agents-Team feedback, create a Beta feedback GitHub Issue, report a plugin problem, or says 我要提交反馈, 提交反馈到 GitHub, 反馈到仓库, or 帮我提 issue
---

# Submit Team Feedback

## Entry Gate

Start from the user's current feedback intent. If the user only says "提交反馈" or "submit feedback", ask for the missing expected behavior and actual behavior only when they cannot be inferred from the current session.

## Workflow

1. Collect only user-approved context: current conversation facts, explicit error text, explicit command output, `AGENTS.md` managed-block state, `.codex/team-collaboration.json`, and small redacted snippets the user wants to publish.
2. Do not read `.env`, credential files, private source files, full test logs, full CI artifacts, customer material, or unrelated repository content.
3. Convert the context into a JSON object with these fields when available: `pluginVersion`, `stage`, `environment`, `projectType`, `summary`, `expected`, `actual`, `steps`, `evidence`, and `lessons`.
4. Preview the GitHub Issue draft first:
   `python ../../scripts/submit_feedback.py feedback.json`
5. Show the title, body summary, and privacy-sensitive snippets that were redacted. Ask the user to confirm that the draft is safe to publish.
6. Submit only after explicit user approval; `--apply` is the only path that may call `gh issue create`:
   `python ../../scripts/submit_feedback.py feedback.json --apply`
7. If `gh` is not authenticated or missing, return the preview and tell the user to submit it manually through the `Beta feedback` Issue template.

## Forbidden

- Do not silently upload telemetry, logs, source code, paths, tokens, remote URLs, or identities.
- Do not create a GitHub Issue before the user has reviewed the generated draft.
- Do not claim that redaction is perfect. If unsure, omit the questionable content.
- Do not submit feedback to any repository other than `DOIT-Ben/Agents-Team` unless the user explicitly chooses another repo.

## Exit Gate

Return either a preview that needs confirmation or a created GitHub Issue URL. If submission fails, return the sanitized failure reason and the preview body.

## Evidence

Record which local sources were used, which sources were intentionally skipped, whether `--apply` was confirmed, and the resulting Issue URL or failure status.
