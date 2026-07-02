import importlib.util
import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.contracts import validate_pr_contract  # noqa: E402


VALIDATOR = PLUGIN_ROOT / "templates" / "project" / "validate_pr_contract.py"
SPEC = importlib.util.spec_from_file_location("generated_pr_gate_parity", VALIDATOR)
GENERATED = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GENERATED)

HEAD_SHA = "abc123"
CHANGED_FILES = ["plugins/agents-team/scripts/team_collaboration/contracts.py"]

VALID_ISSUE = """## Goal
Ship the feature.

## 必须完成

- [ ] Evidence exists.

## 验收门禁

- Tests pass.

## 任务边界

- Do not modify auth.

## 风险等级

L2

## 依赖与阻塞条件

Local test environment is available; missing dependencies block execution.

## 失败处理与回滚

Revert the PR.
"""

VALID_PR = f"""## 关联任务

Closes #12

## 风险等级

L2

## 实际改动

Implementation summary.

## 范围偏差

None.

## Worker ownership

- plugins/agents-team/scripts/team_collaboration/

## Risk path classification

- plugins/agents-team/scripts/team_collaboration/: protectedFiles

## 必须完成项证据

- [x] item: test output

## 测试门禁

gate: CI
command: python -m unittest discover -s plugins/agents-team/tests -v
exitCode: 0
passed: 174
failed: 0
skipped: 0
timestamp: 2026-07-01T08:00:00+00:00
commitSha: {HEAD_SHA}
artifact: https://github.com/DOIT-Ben/Agents-Team/actions/runs/1

## 行为验收

Expected behavior is covered by tests.

## QA 独立性与结论

独立上下文: 是
验收者: independent-verifier
实现上下文: implement-session-1
QA 上下文: qa-session-1
commitSha: {HEAD_SHA}
结论: PASS
证据: https://github.com/DOIT-Ben/Agents-Team/actions/runs/1

## 剩余风险

None.

## 回滚方式

Revert PR.

## 失败记录

None.
"""


def core_messages(pr_body: str) -> list[str]:
    return [
        finding.message
        for finding in validate_pr_contract(
            pr_body,
            VALID_ISSUE,
            ["risk:L2"],
            current_sha=HEAD_SHA,
            changed_files=CHANGED_FILES,
        )
    ]


class ContractSemanticParityTests(unittest.TestCase):
    def test_core_and_generated_accept_same_valid_contract(self):
        self.assertEqual(core_messages(VALID_PR), [])
        self.assertEqual(GENERATED.validate(VALID_PR, VALID_ISSUE, HEAD_SHA, changed_files=CHANGED_FILES), [])

    def test_core_and_generated_reject_missing_test_timestamp(self):
        pr_body = VALID_PR.replace("timestamp: 2026-07-01T08:00:00+00:00\n", "")
        self.assertTrue(any("timestamp" in message for message in core_messages(pr_body)))
        self.assertTrue(any("timestamp" in error for error in GENERATED.validate(pr_body, VALID_ISSUE, HEAD_SHA, changed_files=CHANGED_FILES)))

    def test_core_and_generated_reject_stale_test_commit(self):
        pr_body = VALID_PR.replace(f"commitSha: {HEAD_SHA}", "commitSha: stale456", 1)
        self.assertTrue(any("current head" in message for message in core_messages(pr_body)))
        self.assertTrue(any("head.sha" in error for error in GENERATED.validate(pr_body, VALID_ISSUE, HEAD_SHA, changed_files=CHANGED_FILES)))


if __name__ == "__main__":
    unittest.main()
