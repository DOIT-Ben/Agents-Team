import importlib.util
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = PLUGIN_ROOT / "templates" / "project" / "validate_pr_contract.py"
spec = importlib.util.spec_from_file_location("validate_pr_contract", VALIDATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


HEAD_SHA = "abc123"

VALID_PR = f"""## 关联任务

Closes #12

## 风险等级

L2

## 实际改动

Implementation summary.

## 范围偏差

None.

## 必须完成项证据

- item: test output

## 测试门禁

gate: CI
command: python -m unittest discover -s plugins/agents-team/tests -v
exitCode: 0
passed: 116
failed: 0
skipped: 0
timestamp: 2026-07-01T08:00:00+00:00
commitSha: {HEAD_SHA}
artifact: https://github.com/DOIT-Ben/Agents-Team/actions/runs/1

## 行为验收

Expected behavior is covered by tests.

## QA 独立性与结论

独立上下文: 是
结论: PASS

## 剩余风险

None.

## 回滚方式

Revert PR.

## 失败记录

None.
"""

VALID_ISSUE = """## Goal

Ship the feature.

## 必须完成

- Evidence exists.

## 验收门禁

- Tests pass.

## 任务边界

- Do not modify auth.

## 风险等级

L2

## 依赖与阻塞条件

None.

## 失败处理与回滚

Revert the PR.
"""

VALID_L3_ISSUE = VALID_ISSUE.replace("L2", "L3 真实 Provider") + """

## 用户确认

用户确认: approved

## 方案

方案: execute with a staged rollout.

## 回滚

回滚: revert the PR.
"""


class PrContractTests(unittest.TestCase):
    def test_valid_pr_and_issue_pass(self):
        errors = module.validate(VALID_PR, VALID_ISSUE, HEAD_SHA)
        self.assertEqual(errors, [])

    def test_placeholder_pr_fails(self):
        body = VALID_PR.replace("Closes #12", "Closes #").replace("PASS", "待验收")
        errors = module.validate(body, VALID_ISSUE, HEAD_SHA)
        self.assertTrue(any("Issue" in error for error in errors))
        self.assertTrue(any("placeholder" in error.lower() for error in errors))

    def test_missing_issue_fields_fail(self):
        errors = module.validate(VALID_PR, "## Goal\nOnly goal.", HEAD_SHA)
        self.assertTrue(any("必须完成" in error for error in errors))
        self.assertTrue(any("任务边界" in error for error in errors))

    def test_stale_commit_evidence_fails(self):
        errors = module.validate(VALID_PR, VALID_ISSUE, "different-head")
        self.assertTrue(any("does not match head.sha" in error for error in errors))

    def test_l2_requires_independent_qa(self):
        body = VALID_PR.replace("独立上下文: 是", "独立上下文: 否")
        errors = module.validate(body, VALID_ISSUE, HEAD_SHA)
        self.assertTrue(any("independent context" in error for error in errors))

    def test_l3_issue_requires_confirmation_plan_and_rollback(self):
        l3_issue = VALID_ISSUE.replace("L2", "L3 真实 Provider")
        errors = module.validate(VALID_PR, l3_issue, HEAD_SHA)
        self.assertTrue(any("用户确认" in error for error in errors))
        self.assertTrue(any("方案" in error for error in errors))
        self.assertTrue(any("回滚" in error for error in errors))

    def test_valid_l3_issue_passes(self):
        errors = module.validate(VALID_PR, VALID_L3_ISSUE, HEAD_SHA)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
