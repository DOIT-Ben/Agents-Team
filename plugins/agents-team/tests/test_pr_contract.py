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

## Goal 对照

Goal achieved with evidence.

## 实际改动

Implementation summary.

## 范围偏差

None.

## 必须完成证据

- item: test output

## 验收门禁结果

- tests passed

## 任务边界检查

No boundary violation.

## QA 结论

PASS

## 剩余风险

None.

## 回滚方式

Revert PR.
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

## 依赖与阻塞

None.
"""


class PrContractTests(unittest.TestCase):
    def test_valid_pr_and_issue_pass(self):
        errors = module.validate(VALID_PR, issue_bodies={12: VALID_ISSUE}, require_issue_lookup=True)
        self.assertEqual(errors, [])

    def test_placeholder_pr_fails(self):
        body = VALID_PR.replace("Closes #12", "Closes #").replace("PASS", "待验收")
        errors = module.validate(body)
        self.assertTrue(any("Issue" in error for error in errors))
        self.assertTrue(any("待验收" in error for error in errors))

    def test_missing_issue_fields_fail(self):
        errors = module.validate(VALID_PR, issue_bodies={12: "## Goal\nOnly goal."}, require_issue_lookup=True)
        self.assertTrue(any("必须完成" in error for error in errors))
        self.assertTrue(any("任务边界" in error for error in errors))

    def test_l3_issue_requires_confirmation_plan_and_rollback(self):
        l3_issue = VALID_ISSUE.replace("L2", "L3 真实 Provider")
        errors = module.validate(VALID_PR, issue_bodies={12: l3_issue}, require_issue_lookup=True)
        self.assertTrue(any("用户确认" in error for error in errors))
        self.assertTrue(any("方案" in error for error in errors))
        self.assertTrue(any("回滚" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
