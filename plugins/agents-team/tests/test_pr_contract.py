import importlib.util
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = PLUGIN_ROOT / "templates" / "project" / "validate_pr_contract.py"
spec = importlib.util.spec_from_file_location("validate_pr_contract", VALIDATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


VALID_PR = """## 关联任务

Closes #12

## 风险等级

L2

## 实际改动

Implementation summary.

## 范围偏差

None.

## 必须完成项证据

- [x] item: test output

## 测试门禁

gate: test:unit
command: py -3 -m unittest
exitCode: 0
passed: 12
failed: 0
skipped: 0
timestamp: 2026-06-30T10:00:00Z
commitSha: abc123
artifact: https://github.com/example/actions/runs/1

## 行为验收

Expected and actual behavior match.

## QA 独立性与结论

- 独立上下文：是
- 结论：PASS

## 剩余风险

None.

## 回滚方式

Revert PR.

## 失败记录

无失败记录。
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

Revert the change and rerun tests.
"""


class PrContractTests(unittest.TestCase):
    def test_valid_pr_and_issue_pass(self):
        errors = module.validate(VALID_PR, VALID_ISSUE, "abc123")
        self.assertEqual(errors, [])

    def test_placeholder_pr_fails(self):
        body = VALID_PR.replace("Closes #12", "Closes #").replace("PASS", "待验收")
        errors = module.validate(body, VALID_ISSUE, "abc123")
        self.assertTrue(any("Issue" in error for error in errors))
        self.assertTrue(any("placeholder" in error for error in errors))

    def test_missing_issue_fields_fail(self):
        errors = module.validate(VALID_PR, "## Goal\nOnly goal.", "abc123")
        self.assertTrue(any("必须完成" in error for error in errors))
        self.assertTrue(any("任务边界" in error for error in errors))

    def test_l3_issue_requires_confirmation_plan_and_rollback(self):
        l3_issue = VALID_ISSUE.replace("L2", "L3 真实 Provider").split("## 失败处理与回滚")[0]
        errors = module.validate(VALID_PR.replace("L2", "L3"), l3_issue, "abc123")
        self.assertTrue(any("用户确认" in error for error in errors))
        self.assertTrue(any("方案" in error for error in errors))
        self.assertTrue(any("failure handling" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
