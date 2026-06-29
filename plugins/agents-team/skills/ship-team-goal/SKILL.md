---
name: ship-team-goal
description: Use when an Agents-Team Goal is approaching merge or release and must prove current-head CI, independent QA, residual risk, and rollback readiness
---

# Ship Team Goal

## Entry Gate

Require a valid PR and Issue contract, current PR head SHA, complete implementation and behavior evidence, independent QA for L2/L3, and every required CI context. Missing GitHub access, provider access, or release evidence is BLOCKED.

## Workflow

1. Confirm the PR head SHA and reject evidence from older commits.
2. Verify required CI runs completed successfully for the same head.
3. Verify every required outcome, behavior gate, security gate, and failure record.
4. Verify independent QA identity and context for L2/L3.
5. For L3, verify approved cost, secret handling, real-provider smoke, irreversible impact, and rollback evidence.
6. Check remaining risk, rollback commands, monitoring, and ownership after merge.
7. Recommend MERGEABLE only when all fail-closed gates pass.

## Forbidden

- Do not infer success from a green run on another commit.
- Do not downgrade missing permissions, tokens, environments, providers, or artifacts to N/A without contract approval.
- Do not perform production, paid, destructive, or irreversible actions without explicit authorization.
- Do not mark the Goal mergeable while QA, CI, required outcomes, or rollback remain incomplete.

## Exit Gate

Return PASS and MERGEABLE only for complete current-head evidence. Return FAIL for a disproved gate and BLOCKED for unavailable required evidence or authority.

## Evidence

Record head SHA, CI run URLs and conclusions, Goal-item evidence, QA identity and verdict, L3 smoke when required, residual risk, rollback, monitoring, and final verdict.
