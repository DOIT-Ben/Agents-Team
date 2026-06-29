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

## Failure 2: incomplete event coverage

An early workflow query returned no runs and was initially attributed to a default-branch bootstrap limitation. That diagnosis was premature: the query had not waited for Actions scheduling. The later logs show that run `28387169091` was a real `pull_request/synchronize` execution using the workflow introduced by the trial branch.

The actual event gap was narrower and reproducible. Correcting PR evidence does not change the head SHA, but the default `pull_request` activity set does not include `edited` or `ready_for_review`. Without those activity types, a corrected body cannot automatically revalidate against the same commit. The gate now declares `opened`, `synchronize`, `reopened`, `ready_for_review`, and `edited`; it does not add a duplicate branch `push` workflow.

## Remote proof

The trial completed the fail-to-pass loop on head `853971d3e643f0ea3e3127e6f9176c798d822a21`:

1. Run `28387169091` failed with missing PR sections, missing Issue rollback, incomplete test evidence, and non-independent QA. The project adapter step passed.
2. Run `28387382762` failed again on the current head while the old PR body was still incomplete.
3. Editing the PR body added the exact contract sections, current head SHA, ISO timestamp, HTTPS artifact, and scoped independent Actions QA. Run `28387426971` passed without changing the head.
4. The successful run URL was written back into the PR evidence. Final revalidation run `28387455597` passed both the project adapter and PR contract steps on the same head.

The trial PR remains unmerged by design. It changes no scanner, privacy, ranking, release, or production behavior, and the final comparison contains zero deleted lines.

## Conclusion

The real-use gate is complete for this scope. Agents-Team now proves three properties on GitHub: incomplete contracts fail closed, corrected evidence can be revalidated without making its own commit SHA stale, and existing project rules survive initialization when a complete checkout is used.
