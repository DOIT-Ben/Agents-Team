---
name: execute-team-goal
description: Use when implementing a scoped software Goal under an initialized team collaboration project
---

# Execute Team Goal

## Entry Gate

Read `AGENTS.md`, `.codex/team-collaboration.json`, the linked Issue, and relevant code. L2/L3 work must have an Issue containing, in order: Goal, 必须完成, 验收门禁, 任务边界, risk, and dependencies. Stop and repair the Issue if any field is absent or vague.

## Workflow

1. Reclassify the task using L1/L2/L3 in `../../references/risk-classification.md`.
2. For L3, present approach, alternatives, cost, risk, evidence, and rollback; wait for user approval.
3. Choose direct execution, one worker, or parallel workers. Parallelize only independent tasks with stable contracts, non-overlapping files, and independent tests.
4. Give each worker the Issue plus allowed/forbidden files. Workers may claim only code-level completion.
5. Integrate results, inspect the diff, check every 必须完成 item, run the specified tests, and reject out-of-bound changes.
6. Update the PR with evidence and remaining risks.
7. L2/L3 require 独立 QA through `verify-team-goal` in a fresh context. This skill may not self-approve its implementation.

Never change the Goal silently, bypass a failing gate, delete a failing test, add unexplained skip/xfail, or use mock evidence to claim a real integration works.

Read `../../references/issue-contract.md` for the complete contract.
