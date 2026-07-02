import importlib.util
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = PLUGIN_ROOT / "templates" / "project" / "validate_pr_contract.py"
SPEC = importlib.util.spec_from_file_location("generated_pr_gate", VALIDATOR)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

VALID_ISSUE = """## Goal
用户可以完成一次可观察的上传流程。
## 必须完成
- [ ] 上传成功并返回资源标识
## 验收门禁
运行单元测试且退出码为零。
## 任务边界
严禁修改认证、计费和部署配置。
## 风险等级
L2
## 依赖与阻塞条件
本地测试环境和固定测试数据可用。
## 失败处理与回滚
保留失败输出并回滚当前 PR。
"""

VALID_PR = """## 关联任务
Closes #12
## 风险等级
L2
## 实际改动
实现上传流程。
## 范围偏差
无偏差。
## 必须完成项证据
- [x] 上传成功测试通过
## 测试门禁
gate: test:unit
command: python3 -m unittest
exitCode: 0
passed: 12
failed: 0
skipped: 0
timestamp: 2026-06-30T12:00:00Z
commitSha: abc123
artifact: https://github.com/example/actions/runs/1
## 行为验收
预期和实际均返回资源标识。
## QA 独立性与结论
独立上下文：是
验收者：independent-verifier
实现上下文：implement-session-1
QA 上下文：qa-session-1
commitSha：abc123
结论：PASS
证据：https://github.com/example/actions/runs/1
## 剩余风险
无已知剩余风险。
## 回滚方式
回滚当前 PR。
## 失败记录
无失败记录。
"""


class GeneratedPrGateTests(unittest.TestCase):
    def test_valid_current_head_contract_passes(self):
        self.assertEqual(MODULE.validate(VALID_PR, VALID_ISSUE, "abc123"), [])

    def test_stale_commit_evidence_is_rejected(self):
        errors = MODULE.validate(VALID_PR, VALID_ISSUE, "def456")
        self.assertTrue(any("head.sha" in error for error in errors))

    def test_invalid_timestamp_is_rejected(self):
        errors = MODULE.validate(VALID_PR.replace("2026-06-30T12:00:00Z", "yesterday"), VALID_ISSUE, "abc123")
        self.assertTrue(any("timestamp" in error for error in errors))

    def test_non_independent_qa_is_rejected(self):
        errors = MODULE.validate(VALID_PR.replace("独立上下文：是", "独立上下文：否"), VALID_ISSUE, "abc123")
        self.assertTrue(any("independent" in error for error in errors))

    def test_missing_qa_evidence_fields_are_rejected(self):
        body = VALID_PR.replace("验收者：independent-verifier\n", "").replace("QA 上下文：qa-session-1\n", "")
        errors = MODULE.validate(body, VALID_ISSUE, "abc123")
        self.assertTrue(any("QA evidence missing" in error for error in errors))

    def test_stale_qa_evidence_is_rejected(self):
        body = VALID_PR.replace("commitSha：abc123", "commitSha：old456")
        errors = MODULE.validate(body, VALID_ISSUE, "abc123")
        self.assertTrue(any("QA evidence commitSha" in error for error in errors))

    def test_matching_qa_and_implementation_context_is_rejected(self):
        body = VALID_PR.replace("QA 上下文：qa-session-1", "QA 上下文：implement-session-1")
        errors = MODULE.validate(body, VALID_ISSUE, "abc123")
        self.assertTrue(any("QA context must differ" in error for error in errors))

if __name__ == "__main__":
    unittest.main()
