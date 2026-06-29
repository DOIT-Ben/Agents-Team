---
name: review-team-goal
description: Use when an implemented Agents-Team change needs findings-first review against correctness, tests, security, scope, and rollback requirements
---

# Review Team Goal

## Entry Gate

Require the linked Goal Issue, final diff, current-head identity, implementation evidence, test results, task boundary, and rollback. A reviewer who participated in implementation cannot provide independent approval.

## Workflow

1. Map the final diff to every required outcome and declared file boundary.
2. Review correctness, edge cases, compatibility, failure handling, and regressions.
3. Review whether tests demonstrate behavior and whether evidence belongs to the current change.
4. Inspect authorization, secrets, inputs, dependencies, data, and production impact when relevant.
5. Check complexity, repository conventions, rollback viability, and unexplained scope deviation.
6. Report findings first, ordered by severity, with exact locations and remediation.

## Forbidden

- Do not lead with a summary while hiding actionable findings.
- Do not approve code authored in the same implementation context as independent QA.
- Do not turn preferences or unrelated refactors into blockers.
- Do not accept stale, self-signed, mocked, or incomplete evidence.

## Exit Gate

Return PASS only when no blocking finding remains and required evidence is current and complete. Otherwise return FAIL or BLOCKED with exact remediation.

## Evidence

Record reviewed commit, files, Goal mapping, findings by severity, tests checked, security scope, boundary result, rollback assessment, assumptions, and verdict.
