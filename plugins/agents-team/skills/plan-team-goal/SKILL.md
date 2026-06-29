---
name: plan-team-goal
description: Use when an approved Agents-Team Goal must be decomposed into bounded, dependency-ordered, independently verifiable tasks
---

# Plan Team Goal

## Entry Gate

Require a valid Goal contract. L2/L3 require a linked Issue; L3 also requires an approved approach, cost and irreversible-impact disclosure, and rollback decision before implementation begins.

## Workflow

1. Read the Goal, required outcomes, acceptance gates, task boundary, risk, dependencies, and rollback.
2. Inspect only the code and tests needed to identify ownership and interfaces.
3. Split work into small tasks whose output can be verified independently.
4. Give every task allowed files, forbidden files, dependencies, exact verification, expected evidence, and a role.
5. Order tasks by dependency and mark blockers that require user or environment input.
6. Recheck that completing all tasks satisfies every required outcome without expanding the Goal.

## Forbidden

- Do not modify business code or tests.
- Do not replace observable acceptance criteria with implementation descriptions.
- Do not hide uncertainty or silently choose between conflicting requirements.
- Do not assign overlapping files to parallel workers.

## Exit Gate

Every task is bounded, dependency-ordered, role-owned, independently verifiable, and mapped to at least one required outcome. Any unresolved blocker is explicit.

## Evidence

Return the task list, dependency graph in prose or structured data, allowed and forbidden files, exact commands or behavior checks, expected artifacts, risk, and blockers.
