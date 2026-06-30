---
name: report-team-feedback
description: Use when a user asks to report an Agents-Team bug, missed defect, false block, context-isolation failure, compatibility problem, privacy concern, feature request, or export a local diagnostic bundle
---

# Report Team Feedback

## Workflow

1. Use the available Python interpreter (`py -3` on Windows when `python3` is unavailable) to run `../../scripts/manage_project.py logs <repo>` and let the user select a `runId`; never infer a different run when the requested ID is missing.
2. Classify the feedback as `bug`, `missed_defect`, `false_block`, `context_isolation`, `compatibility`, `privacy`, or `feature_request`.
3. Collect severity, expected result, actual result, reproduction steps, optional 1–5 rating, and whether the user would use Agents-Team again.
4. Run `manage_project.py feedback` without `--confirm`. Show the complete redacted preview and the reported redaction categories.
5. Ask for explicit confirmation only after the preview. Without confirmation, stop without writing a feedback bundle or opening GitHub.
6. After confirmation, rerun with `--confirm`. Use `--open-issue` only when the user also asks to open GitHub.
7. Explain that the generated Issue remains a draft until the user submits it. Point out the separate `diagnostics.json` attachment; never attach it silently.

## Privacy Boundary

- Runtime records remain local by default and contain structured metadata rather than prompts, model output, source code, environment values, credentials, email addresses, repository URLs, or raw absolute paths.
- Never weaken redaction to make a report easier to reproduce. Ask the user to add the minimum safe reproduction separately.
- Treat a P0/P1 privacy or data-loss report as release-blocking and direct security vulnerabilities to GitHub Private Security Advisories rather than a public Issue.

Read `../../references/runtime-feedback.md` for commands, retention, feedback fields, and deletion behavior.
