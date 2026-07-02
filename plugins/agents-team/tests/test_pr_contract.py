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

## Worker ownership

- plugins/agents-team/scripts/team_collaboration/
- plugins/agents-team/tests/

## Risk path classification

- plugins/agents-team/scripts/team_collaboration/: protectedFiles
- plugins/agents-team/tests/: standard

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

VALID_L3_APPROVAL = {
    "actor": "owner",
    "timestamp": "2026-07-01T08:00:00+00:00",
    "scope": "Issue #12 L3 provider change",
    "risk": "L3",
    "commitSha": HEAD_SHA,
}


class PrContractTests(unittest.TestCase):
    def test_valid_pr_and_issue_pass(self):
        errors = module.validate(VALID_PR, VALID_ISSUE, HEAD_SHA)
        self.assertEqual(errors, [])

    def test_worker_diff_boundary_allows_owned_files(self):
        errors = module.validate(
            VALID_PR,
            VALID_ISSUE,
            HEAD_SHA,
            changed_files=[
                "plugins/agents-team/scripts/team_collaboration/contracts.py",
                "plugins/agents-team/tests/test_pr_contract.py",
            ],
        )
        self.assertEqual(errors, [])

    def test_worker_diff_boundary_blocks_unowned_files(self):
        errors = module.validate(VALID_PR, VALID_ISSUE, HEAD_SHA, changed_files=["README.md"])
        self.assertTrue(any("outside Worker ownership" in error for error in errors))

    def test_l2_requires_risk_path_classification_for_changed_files(self):
        body = VALID_PR.replace("## Risk path classification\n\n- plugins/agents-team/scripts/team_collaboration/: protectedFiles\n- plugins/agents-team/tests/: standard\n\n", "")
        errors = module.validate(
            body,
            VALID_ISSUE,
            HEAD_SHA,
            changed_files=["plugins/agents-team/scripts/team_collaboration/contracts.py"],
        )
        self.assertTrue(any("Risk path classification" in error for error in errors))

    def test_l2_blocks_unclassified_changed_file(self):
        errors = module.validate(VALID_PR, VALID_ISSUE, HEAD_SHA, changed_files=["README.md"])
        self.assertTrue(any("not covered by Risk path classification" in error for error in errors))

    def test_l1_does_not_require_risk_path_classification(self):
        body = VALID_PR.replace("L2", "L1").replace("## Risk path classification\n\n- plugins/agents-team/scripts/team_collaboration/: protectedFiles\n- plugins/agents-team/tests/: standard\n\n", "")
        issue = VALID_ISSUE.replace("L2", "L1")
        errors = module.validate(body, issue, HEAD_SHA, changed_files=["README.md"])
        self.assertFalse(any("Risk path classification" in error for error in errors))

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

    def test_l2_requires_verifiable_qa_fields(self):
        body = VALID_PR.replace("验收者: independent-verifier\n", "").replace("QA 上下文: qa-session-1\n", "")
        errors = module.validate(body, VALID_ISSUE, HEAD_SHA)
        self.assertTrue(any("QA evidence missing" in error for error in errors))

    def test_stale_qa_evidence_fails(self):
        errors = module.validate(VALID_PR, VALID_ISSUE, "different-head")
        self.assertTrue(any("QA evidence commitSha" in error for error in errors))

    def test_qa_context_must_differ_from_implementation_context(self):
        body = VALID_PR.replace("QA 上下文: qa-session-1", "QA 上下文: implement-session-1")
        errors = module.validate(body, VALID_ISSUE, HEAD_SHA)
        self.assertTrue(any("QA context must differ" in error for error in errors))

    def test_l3_issue_requires_confirmation_plan_and_rollback(self):
        l3_issue = VALID_ISSUE.replace("L2", "L3 真实 Provider")
        errors = module.validate(VALID_PR, l3_issue, HEAD_SHA)
        self.assertTrue(any("用户确认" in error for error in errors))
        self.assertTrue(any("方案" in error for error in errors))
        self.assertTrue(any("回滚" in error for error in errors))

    def test_valid_l3_issue_passes(self):
        errors = module.validate(VALID_PR, VALID_L3_ISSUE, HEAD_SHA, approval_event=VALID_L3_APPROVAL)
        self.assertEqual(errors, [])

    def test_l3_text_approval_without_event_fails(self):
        errors = module.validate(VALID_PR, VALID_L3_ISSUE, HEAD_SHA)
        self.assertTrue(any("L3 approval event" in error for error in errors))

    def test_l3_approval_event_must_match_head(self):
        event = {**VALID_L3_APPROVAL, "commitSha": "old456"}
        errors = module.validate(VALID_PR, VALID_L3_ISSUE, HEAD_SHA, approval_event=event)
        self.assertTrue(any("approval event commitSha" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
