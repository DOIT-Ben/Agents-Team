---
name: verify-team-goal
description: Use when a completed L2 or L3 Goal or pull request requires independent acceptance evidence
---

# Verify Team Goal

## Independence Gate

Run in a 全新上下文 that did not implement the change. If no independent context is available, report that independent QA is blocked; never simulate independence.

## Read-Only Workflow

1. Read the Issue, final PR diff, runtime entry points, and test commands. Do not rely on the implementer's completion narrative.
2. Map every 必须完成 item to observable evidence.
3. Execute all 验收门禁 commands and record commands, exit codes, pass/fail counts, and unexpected skips.
4. Exercise the real user path, including failure, retry, refresh, persistence, and boundary cases required by the Issue.
5. Inspect for 任务边界 violations and unrelated changes.
6. Return exactly PASS or FAIL using `../../references/qa-contract.md`.

This Skill is 只读: it must not modify business code, tests, the Issue contract, or the acceptance threshold. It must not quietly repair discovered defects. Any missing evidence, failed required test, unresolved P0/P1, unmet Goal, or boundary violation requires FAIL.

硬规则：不得修改代码、测试或验收标准。

The QA output belongs in the PR. Include untested risks even when the result is PASS.
