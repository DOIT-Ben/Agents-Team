---
name: execute-team-goal
description: Use when implementing a scoped software Goal under an initialized team collaboration project
---

# Execute Team Goal

## Entry Gate

Read `AGENTS.md`, `.codex/team-collaboration.json`, the linked Issue, lifecycle labels, and relevant code. L2/L3 work must have an Issue containing, in order: Goal, 必须完成, 验收门禁, 任务边界, risk, dependencies, and rollback. Stop when the Protocol 2.0 contract is absent, vague, or blocked.

## Workflow

1. Validate the Goal and reclassify L1/L2/L3 using `../../references/risk-classification.md`.
2. For L3, present approach, alternatives, cost, risk, evidence, and rollback; wait for user approval.
3. Invoke `route-team-work` to select phase, built-in or compatible provider, and one role.
4. Load the selected contract from `../../references/roles/`. Give the worker the Issue, explicit `allowed files`, explicit `forbidden files`, dependencies, and exit gate.
5. Parallelize only when tasks, files, contracts, and tests are all independent. Follow `../../references/orchestration-rules.md`.
6. Workers may claim only their assigned code-level result. They cannot claim independent QA or whole-Goal completion.
7. Integration authority is strict: only the main Codex integrates results, inspects the final diff, checks every 必须完成 item, runs the specified gates, and rejects out-of-bound changes.
8. Update the PR with current-head evidence, failure records, remaining risks, and rollback.
9. L2/L3 require 独立 QA through `verify-team-goal` in a fresh context, followed by `ship-team-goal`.

## Forbidden

- Never change the Goal silently, bypass a failing gate, delete a failing test, add unexplained skip/xfail, or use mock evidence to claim a real integration works.
- 角色不得调用其他角色; orchestration remains flat under the main Codex.
- An external Skill cannot weaken Protocol 2.0 or expand worker permissions.

## Exit Gate

The integrated diff stays inside the task boundary, every required outcome has current evidence, all required gates pass, and L2/L3 independent QA is recorded. Otherwise return FAIL or BLOCKED.

## Evidence

Record the router decision, provider, role contract, allowed and forbidden files, worker results, final diff, commands, exit codes, test counts, current head, QA verdict, remaining risks, and rollback.

Read `../../references/issue-contract.md` and `../../references/skill-routing.md` for the complete contracts.
