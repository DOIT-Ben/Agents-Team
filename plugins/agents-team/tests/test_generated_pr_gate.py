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
## Worker ownership
- plugins/agents-team/scripts/team_collaboration/
- plugins/agents-team/tests/
## Risk path classification
- plugins/agents-team/scripts/team_collaboration/: protectedFiles
- plugins/agents-team/tests/: standard
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

VALID_CHECK_RUNS = {
    "check_runs": [
        {
            "name": "Python unit tests (ubuntu-latest)",
            "head_sha": "abc123",
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/example/actions/runs/1/job/1",
        },
        {
            "name": "Python unit tests (windows-latest)",
            "head_sha": "abc123",
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/example/actions/runs/1/job/2",
        },
    ]
}

VALID_L3_ISSUE = VALID_ISSUE.replace("L2", "L3 真实 Provider") + """
## 用户确认
用户确认：approved
## 方案
方案：staged rollout.
## 回滚
回滚：revert the PR.
"""

VALID_L3_APPROVAL = {
    "actor": "owner",
    "timestamp": "2026-07-01T08:00:00+00:00",
    "scope": "Issue #12 L3 provider change",
    "risk": "L3",
    "commitSha": "abc123",
}


class GeneratedPrGateTests(unittest.TestCase):
    def test_valid_current_head_contract_passes(self):
        self.assertEqual(MODULE.validate(VALID_PR, VALID_ISSUE, "abc123"), [])

    def test_worker_diff_boundary_allows_owned_files(self):
        errors = MODULE.validate(
            VALID_PR,
            VALID_ISSUE,
            "abc123",
            changed_files=[
                "plugins/agents-team/scripts/team_collaboration/contracts.py",
                "plugins/agents-team/tests/test_generated_pr_gate.py",
            ],
        )
        self.assertEqual(errors, [])

    def test_worker_diff_boundary_blocks_unowned_files(self):
        errors = MODULE.validate(VALID_PR, VALID_ISSUE, "abc123", changed_files=["README.md"])
        self.assertTrue(any("outside Worker ownership" in error for error in errors))

    def test_l2_requires_risk_path_classification_for_changed_files(self):
        body = VALID_PR.replace("## Risk path classification\n- plugins/agents-team/scripts/team_collaboration/: protectedFiles\n- plugins/agents-team/tests/: standard\n", "")
        errors = MODULE.validate(
            body,
            VALID_ISSUE,
            "abc123",
            changed_files=["plugins/agents-team/scripts/team_collaboration/contracts.py"],
        )
        self.assertTrue(any("Risk path classification" in error for error in errors))

    def test_l2_blocks_unclassified_changed_file(self):
        errors = MODULE.validate(VALID_PR, VALID_ISSUE, "abc123", changed_files=["README.md"])
        self.assertTrue(any("not covered by Risk path classification" in error for error in errors))

    def test_l1_does_not_require_risk_path_classification(self):
        body = VALID_PR.replace("L2", "L1").replace("## Risk path classification\n- plugins/agents-team/scripts/team_collaboration/: protectedFiles\n- plugins/agents-team/tests/: standard\n", "")
        issue = VALID_ISSUE.replace("L2", "L1")
        errors = MODULE.validate(body, issue, "abc123", changed_files=["README.md"])
        self.assertFalse(any("Risk path classification" in error for error in errors))

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

    def test_pass_status_requires_explicit_verify_stage(self):
        errors = MODULE.validate(VALID_PR, VALID_ISSUE, "abc123", labels=["status:pass"])
        self.assertTrue(any("verify stage" in error for error in errors))

        verified = VALID_PR.replace("结论：PASS", "验证阶段：verify\n结论：PASS")
        self.assertEqual(MODULE.validate(verified, VALID_ISSUE, "abc123", labels=["status:pass"]), [])

    def test_current_head_github_checks_pass(self):
        self.assertEqual(MODULE.validate_check_runs(VALID_CHECK_RUNS, "abc123"), [])

    def test_missing_github_checks_are_rejected(self):
        errors = MODULE.validate_check_runs({"check_runs": []}, "abc123")
        self.assertTrue(any("GitHub Checks evidence missing" in error for error in errors))

    def test_stale_github_checks_are_rejected(self):
        stale = {"check_runs": [{**VALID_CHECK_RUNS["check_runs"][0], "head_sha": "old456"}]}
        errors = MODULE.validate_check_runs(stale, "abc123")
        self.assertTrue(any("current head" in error for error in errors))

    def test_failed_github_check_is_rejected(self):
        failed = {"check_runs": [{**VALID_CHECK_RUNS["check_runs"][0], "conclusion": "failure"}]}
        errors = MODULE.validate_check_runs(failed, "abc123")
        self.assertTrue(any("did not pass" in error for error in errors))

    def test_l3_text_approval_without_event_is_rejected(self):
        errors = MODULE.validate(VALID_PR, VALID_L3_ISSUE, "abc123")
        self.assertTrue(any("L3 approval event" in error for error in errors))

    def test_l3_approval_event_must_match_head(self):
        event = {**VALID_L3_APPROVAL, "commitSha": "old456"}
        errors = MODULE.validate(VALID_PR, VALID_L3_ISSUE, "abc123", approval_event=event)
        self.assertTrue(any("approval event commitSha" in error for error in errors))

    def test_valid_l3_approval_event_passes(self):
        self.assertEqual(MODULE.validate(VALID_PR, VALID_L3_ISSUE, "abc123", approval_event=VALID_L3_APPROVAL), [])

if __name__ == "__main__":
    unittest.main()
