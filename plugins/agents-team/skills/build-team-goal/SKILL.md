---
name: build-team-goal
description: Use when a planned Agents-Team task is ready for test-first incremental implementation inside explicit file boundaries
---

# Build Team Goal

## Entry Gate

Require a valid routed task with allowed files, forbidden files, acceptance evidence, and no unresolved blocker. L3 work requires the recorded user decision before any implementation.

## Workflow

1. Read the assigned task, relevant code, tests, and repository conventions.
2. Write one focused failing test for the next behavior and verify that it fails for the intended reason.
3. Implement the smallest change that makes the test pass.
4. Run the focused test, then the relevant regression suite.
5. Inspect the diff for boundary violations, unrelated refactors, weakened tests, secrets, and generated noise.
6. Repeat in small slices until the assigned task, not the whole Goal, is satisfied.
7. Return exact evidence to the main Codex for integration.

## Forbidden

- Do not modify forbidden or unassigned files.
- Do not write production behavior before a failing test unless the user explicitly approved a documented exception.
- Do not delete, skip, weaken, or relabel failing tests to obtain a pass.
- Do not self-approve QA, merge readiness, or whole-Goal completion.

## Exit Gate

The assigned behavior passes focused and regression verification, the diff remains within boundaries, and all failures or skips are explained. Otherwise return FAIL or BLOCKED.

## Evidence

Record changed files, the RED and GREEN commands, exit codes, passed/failed/skipped counts, current commit or working-tree identity, behavior result, boundary check, and remaining risk.
