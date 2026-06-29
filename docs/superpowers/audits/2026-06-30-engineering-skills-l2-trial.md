# Engineering skills integration L2 trial

Date: 2026-06-30

## Trial target

- Repository: `DOIT-Ben/skill-usage`
- Goal Issue: `#1`
- Trial PR: `#2`
- Branch: `test/agents-team-l2-smoke`
- Merge policy: do not merge without a separate decision

## Local evidence

- The generated adapter created 11 managed project files.
- `python .codex/scripts/validate_team_collaboration.py .` exited `0`.
- The local project profile was `generic` because the repository has no root Python project manifest.

## Failure 1: incomplete repository projection

The first projected adapter replaced the repository's existing `AGENTS.md`, and the GitHub comparison showed 117 deleted lines. The root cause was running initialization against an empty local projection instead of a complete checkout. The trial branch restored the original file and appended only the managed block; the resulting comparison has zero deletions.

This is an execution failure, not an initializer hash failure: the empty projection hid the existing file from the initializer. The mechanism now states that initialization from an incomplete projection is invalid.

## Failure 2: workflow bootstrap gap

The ready PR and a subsequent head commit produced no workflow run. GitHub only triggers a `pull_request` workflow when that workflow file already exists on the default branch. A workflow introduced by its own initialization PR therefore cannot validate that PR through `pull_request` alone.

The generated gate now also listens to non-default branch `push` events. On push it uses `GITHUB_TOKEN` to resolve exactly one open PR for the branch and applies the same linked Issue, current-head evidence, timestamp, artifact, and independent QA checks. Missing permissions or ambiguous PR lookup fail closed.

The first failed run also showed that corrected PR evidence needs a trigger that does not change the head SHA. The workflow now listens to `edited` and `ready_for_review`, allowing a PR body correction to re-run validation against the same commit instead of making its own `commitSha` stale.

## Pending remote proof

The updated bootstrap workflow must be copied to the trial branch and exercised twice:

1. Keep incomplete evidence and confirm the push gate fails.
2. Replace it with current-head evidence and independent QA, then confirm success.

Until both runs exist, the integration PR remains Draft and the real-use gate is not complete.
