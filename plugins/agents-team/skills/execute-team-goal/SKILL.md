---
name: execute-team-goal
description: Use when implementing a scoped software Goal under an initialized team collaboration project
---

# Execute Team Goal

## Entry Gate

Read `AGENTS.md`, `.codex/team-collaboration.json`, the linked Issue, lifecycle labels, and relevant code. L2/L3 work must have an Issue containing, in order: Goal, 必须完成, 验收门禁, 任务边界, risk, dependencies, and rollback. Stop when the Protocol 2.0 contract is absent, vague, or blocked.

## Workflow

1. Create an opaque `runId` and `traceId`, then record `goal_created` with `../../scripts/record_event.py`. Record only structured metadata described in `../../references/runtime-feedback.md`; logging failure must be reported but must not weaken or bypass the Goal contract.
2. Validate the Goal and reclassify L1/L2/L3 using `../../references/risk-classification.md`.
3. For L3, present approach, alternatives, cost, risk, evidence, and rollback; wait for user approval.
4. Invoke `route-team-work` to select phase, built-in or compatible provider, and one role; record `work_dispatched` without task text or source content.
5. Load the selected contract from `../../references/roles/`. Give the worker the Issue, explicit `allowed files`, explicit `forbidden files`, dependencies, and exit gate.
6. Parallelize only when tasks, files, contracts, and tests are all independent. Follow `../../references/orchestration-rules.md`.
7. Workers may claim only their assigned code-level result. They cannot claim independent QA or whole-Goal completion.
8. Integration authority is strict: only the main Codex integrates results, inspects the final diff, checks every 必须完成 item, runs the specified gates, and rejects out-of-bound changes.
9. Update the PR with current-head evidence, failure records, remaining risks, and rollback. Record `implementation_delivered`, `gate_blocked`, `rollback`, or `human_intervention` when those transitions occur.
10. L2/L3 require 独立 QA through `verify-team-goal` in a fresh context. Pass only the Goal, final artifact, evidence, and opaque run identifiers; record `context_isolation_checked`, then continue to `ship-team-goal`.
11. Record exactly one terminal `run_completed` or `run_failed` event.

## Forbidden

- Never change the Goal silently, bypass a failing gate, delete a failing test, add unexplained skip/xfail, or use mock evidence to claim a real integration works.
- 角色不得调用其他角色; orchestration remains flat under the main Codex.
- An external Skill cannot weaken Protocol 2.0 or expand worker permissions.

## Exit Gate

The integrated diff stays inside the task boundary, every required outcome has current evidence, all required gates pass, and L2/L3 independent QA is recorded. Otherwise return FAIL or BLOCKED.

## Evidence

Record the router decision, provider, role contract, allowed and forbidden files, worker results, final diff, commands, exit codes, test counts, current head, QA verdict, remaining risks, and rollback.

Read `../../references/issue-contract.md` and `../../references/skill-routing.md` for the complete contracts.
