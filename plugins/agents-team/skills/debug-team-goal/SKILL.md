---
name: debug-team-goal
description: Use when an Agents-Team Goal has a reproducible failure, failing gate, unexpected behavior, or uncertain root cause
---

# Debug Team Goal

## Entry Gate

Require the exact symptom, environment, expected behavior, actual behavior, and the narrowest available reproduction. If reproduction depends on missing credentials, provider access, data, or production state, return BLOCKED instead of guessing.

## Workflow

1. Reproduce the failure and preserve the original command, output, exit code, and environment facts.
2. Localize the responsible component before editing.
3. Reduce the failure to the smallest reliable case.
4. State the supported root cause or clearly label the remaining hypothesis.
5. Write a failing regression test that demonstrates the defect.
6. Apply the smallest fix and verify the regression test turns green.
7. Run relevant regression gates and update the failure record.

## Forbidden

- Do not patch before reproducing or localizing the failure.
- Do not claim a hypothesis is the root cause without evidence.
- Do not suppress errors, add unexplained retries, or weaken assertions to hide the symptom.
- Do not erase the original failure record after the fix.

## Exit Gate

The original symptom is reproduced, the root cause is supported, the regression test proves the failure and fix, and relevant gates pass. Otherwise return FAIL or BLOCKED with the next diagnostic action.

## Evidence

Record reproduction steps, original failure, root cause evidence, regression test RED/GREEN results, changed files, complete gate results, and remaining hypotheses.
