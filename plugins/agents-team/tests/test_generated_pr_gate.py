import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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

    def test_configured_risk_path_category_must_match_pr_classification(self):
        body = VALID_PR.replace("plugins/agents-team/scripts/team_collaboration/: protectedFiles", "plugins/agents-team/scripts/team_collaboration/: standard")
        errors = MODULE.validate(
            body,
            VALID_ISSUE,
            "abc123",
            changed_files=["plugins/agents-team/scripts/team_collaboration/contracts.py"],
            risk_config={"protectedFiles": ["plugins/agents-team/scripts/team_collaboration/"]},
        )
        self.assertTrue(any("configured risk category" in error and "protectedFiles" in error for error in errors))

    def test_configured_production_path_requires_l3(self):
        body = VALID_PR.replace("plugins/agents-team/scripts/team_collaboration/: protectedFiles", "plugins/agents-team/scripts/team_collaboration/: productionPaths")
        errors = MODULE.validate(
            body,
            VALID_ISSUE,
            "abc123",
            changed_files=["plugins/agents-team/scripts/team_collaboration/contracts.py"],
            risk_config={"productionPaths": ["plugins/agents-team/scripts/team_collaboration/"]},
        )
        self.assertTrue(any("requires L3" in error and "productionPaths" in error for error in errors))

    def test_overlapping_configured_risk_paths_use_highest_risk_category(self):
        body = VALID_PR.replace("plugins/agents-team/scripts/team_collaboration/: protectedFiles", "plugins/agents-team/scripts/team_collaboration/: productionPaths")
        errors = MODULE.validate(
            body,
            VALID_ISSUE,
            "abc123",
            changed_files=["plugins/agents-team/scripts/team_collaboration/contracts.py"],
            risk_config={
                "protectedFiles": ["plugins/agents-team/"],
                "productionPaths": ["plugins/agents-team/scripts/team_collaboration/"],
            },
        )
        self.assertTrue(any("requires L3" in error and "productionPaths" in error for error in errors))

    def test_configured_risk_paths_normalize_backslashes_before_matching(self):
        body = VALID_PR.replace("plugins/agents-team/scripts/team_collaboration/: protectedFiles", "plugins/agents-team/scripts/team_collaboration/: productionPaths")
        errors = MODULE.validate(
            body,
            VALID_ISSUE,
            "abc123",
            changed_files=["plugins/agents-team/scripts/team_collaboration/contracts.py"],
            risk_config={"productionPaths": ["plugins\\agents-team\\scripts\\team_collaboration\\"]},
        )
        self.assertTrue(any("requires L3" in error and "productionPaths" in error for error in errors))

    def test_pr_risk_classification_uses_most_specific_matching_path(self):
        body = VALID_PR.replace(
            "- plugins/agents-team/scripts/team_collaboration/: protectedFiles\n- plugins/agents-team/tests/: standard",
            "- plugins/agents-team/: standard\n- plugins/agents-team/scripts/team_collaboration/: productionPaths\n- plugins/agents-team/tests/: standard",
        ).replace("L2", "L3")
        issue = VALID_L3_ISSUE
        errors = MODULE.validate(
            body,
            issue,
            "abc123",
            approval_event=VALID_L3_APPROVAL,
            changed_files=["plugins/agents-team/scripts/team_collaboration/contracts.py"],
            risk_config={"productionPaths": ["plugins\\agents-team\\scripts\\team_collaboration\\"]},
        )
        self.assertFalse(any("configured risk category" in error for error in errors))

    def test_project_config_risk_must_be_object_for_standalone_gate(self):
        self.assertIn("risk must be an object", MODULE.config_shape_errors({"risk": []}))

    def test_malformed_risk_config_is_fail_closed(self):
        errors = MODULE.validate(
            VALID_PR,
            VALID_ISSUE,
            "abc123",
            changed_files=["plugins/agents-team/scripts/team_collaboration/contracts.py"],
            risk_config={"productionPaths": "plugins/agents-team/scripts/team_collaboration/"},
        )
        self.assertTrue(any("invalid risk config" in error and "productionPaths" in error for error in errors))

    def test_l1_does_not_require_risk_path_classification(self):
        body = VALID_PR.replace("L2", "L1").replace("## Risk path classification\n- plugins/agents-team/scripts/team_collaboration/: protectedFiles\n- plugins/agents-team/tests/: standard\n", "")
        issue = VALID_ISSUE.replace("L2", "L1")
        errors = MODULE.validate(body, issue, "abc123", changed_files=["README.md"])
        self.assertFalse(any("Risk path classification" in error for error in errors))

    def test_risk_detection_ignores_l3_template_text_outside_risk_sections(self):
        body = VALID_PR + "\n## L3 approval event\n\nrisk: L3\ncommitSha: abc123\n"
        self.assertEqual(MODULE.risk_from_contract(body, VALID_ISSUE, []), "L2")
        timeline = [
            {"event": "labeled", "label": {"name": "status:draft"}},
            {"event": "labeled", "label": {"name": "status:ready"}},
            {"event": "labeled", "label": {"name": "status:in-progress"}},
        ]
        risk = MODULE.risk_from_contract(body, VALID_ISSUE, [])
        self.assertEqual(MODULE.validate_status_timeline(timeline, current_status="in-progress", risk=risk), [])

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

    def test_qa_evidence_must_be_https_artifact(self):
        body = VALID_PR.replace("证据：https://github.com/example/actions/runs/1", "证据：manual notes only")
        errors = MODULE.validate(body, VALID_ISSUE, "abc123")
        self.assertTrue(any("QA evidence artifact must be an HTTPS URL" in error for error in errors))

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

    def test_status_timeline_blocks_skipped_transitions(self):
        timeline = [
            {"event": "labeled", "label": {"name": "status:draft"}},
            {"event": "labeled", "label": {"name": "status:ready"}},
            {"event": "labeled", "label": {"name": "status:pass"}},
        ]
        errors = MODULE.validate_status_timeline(timeline, current_status="pass", risk="L2")
        self.assertTrue(any("illegal status transition" in error and "ready -> pass" in error for error in errors))

    def test_status_timeline_requires_draft_start_and_required_history(self):
        errors = MODULE.validate_status_timeline(
            [{"event": "labeled", "label": {"name": "status:pass"}}],
            current_status="pass",
            risk="L2",
        )
        self.assertTrue(any("must start at draft" in error for error in errors))

        errors = MODULE.validate_status_timeline(
            [{"event": "labeled", "label": {"name": "status:mergeable"}}],
            current_status="mergeable",
            risk="L2",
        )
        self.assertTrue(any("must start at draft" in error for error in errors))

        errors = MODULE.validate_status_timeline(
            [
                {"event": "labeled", "label": {"name": "status:ready"}},
                {"event": "labeled", "label": {"name": "status:in-progress"}},
            ],
            current_status="in-progress",
            risk="L2",
        )
        self.assertTrue(any("must start at draft" in error for error in errors))

    def test_status_timeline_accepts_ordered_transitions(self):
        timeline = [
            {"event": "labeled", "label": {"name": "status:draft"}},
            {"event": "labeled", "label": {"name": "status:ready"}},
            {"event": "labeled", "label": {"name": "status:in-progress"}},
            {"event": "labeled", "label": {"name": "status:implemented"}},
            {"event": "labeled", "label": {"name": "status:verifying"}},
            {"event": "labeled", "label": {"name": "status:pass"}},
        ]
        self.assertEqual(MODULE.validate_status_timeline(timeline, current_status="pass", risk="L2"), [])

    def test_multiple_current_status_labels_are_rejected(self):
        self.assertEqual(MODULE.status_from_labels(["status:ready", "status:pass"]), "")

    def test_validate_rejects_multiple_current_status_labels(self):
        errors = MODULE.validate(VALID_PR, VALID_ISSUE, "abc123", labels=["status:ready", "status:pass"])
        self.assertTrue(any("exactly one recognized status" in error for error in errors))

    def test_main_validates_pr_timeline_not_linked_issue_timeline(self):
        event = {
            "repository": {"full_name": "owner/repo"},
            "pull_request": {
                "number": 99,
                "draft": False,
                "body": VALID_PR.replace("结论：PASS", "验证阶段：verify\n结论：PASS"),
                "head": {"sha": "abc123"},
                "labels": [{"name": "status:pass"}],
            },
        }
        timeline = [
            {"event": "labeled", "label": {"name": "status:draft"}},
            {"event": "labeled", "label": {"name": "status:ready"}},
            {"event": "labeled", "label": {"name": "status:in-progress"}},
            {"event": "labeled", "label": {"name": "status:implemented"}},
            {"event": "labeled", "label": {"name": "status:verifying"}},
            {"event": "labeled", "label": {"name": "status:pass"}},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event_path = root / "event.json"
            issue_path = root / "issue.md"
            changed_files_path = root / "changed-files.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            issue_path.write_text(VALID_ISSUE, encoding="utf-8")
            changed_files_path.write_text(json.dumps(["plugins/agents-team/scripts/team_collaboration/contracts.py"]), encoding="utf-8")
            calls = []

            def fake_fetch_timeline(repo, number, token):
                calls.append((repo, number, token))
                return timeline

            argv = [
                "validate_pr_contract.py",
                "--event", str(event_path),
                "--issue-body-file", str(issue_path),
                "--changed-files-file", str(changed_files_path),
            ]
            with patch.dict(os.environ, {"GITHUB_TOKEN": "token"}), \
                patch("sys.argv", argv), \
                patch.object(MODULE, "fetch_issue_timeline", side_effect=fake_fetch_timeline), \
                patch.object(MODULE, "fetch_check_runs", return_value=VALID_CHECK_RUNS), \
                patch.object(MODULE, "load_required_check_names", return_value=[]):
                self.assertEqual(MODULE.main(), 0)

        self.assertEqual(calls, [("owner/repo", 99, "token")])

    def test_main_rejects_multiple_current_status_labels(self):
        event = {
            "repository": {"full_name": "owner/repo"},
            "pull_request": {
                "number": 99,
                "draft": False,
                "body": VALID_PR.replace("结论：PASS", "验证阶段：verify\n结论：PASS"),
                "head": {"sha": "abc123"},
                "labels": [{"name": "status:ready"}, {"name": "status:pass"}],
            },
        }
        timeline = [
            {"event": "labeled", "label": {"name": "status:draft"}},
            {"event": "labeled", "label": {"name": "status:ready"}},
            {"event": "labeled", "label": {"name": "status:in-progress"}},
            {"event": "labeled", "label": {"name": "status:implemented"}},
            {"event": "labeled", "label": {"name": "status:verifying"}},
            {"event": "labeled", "label": {"name": "status:pass"}},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event_path = root / "event.json"
            issue_path = root / "issue.md"
            changed_files_path = root / "changed-files.json"
            timeline_path = root / "timeline.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            issue_path.write_text(VALID_ISSUE, encoding="utf-8")
            changed_files_path.write_text(json.dumps(["plugins/agents-team/scripts/team_collaboration/contracts.py"]), encoding="utf-8")
            timeline_path.write_text(json.dumps(timeline), encoding="utf-8")

            argv = [
                "validate_pr_contract.py",
                "--event", str(event_path),
                "--issue-body-file", str(issue_path),
                "--changed-files-file", str(changed_files_path),
                "--timeline-file", str(timeline_path),
            ]
            with patch.dict(os.environ, {"GITHUB_TOKEN": "token"}), \
                patch("sys.argv", argv), \
                patch.object(MODULE, "fetch_check_runs", return_value=VALID_CHECK_RUNS), \
                patch.object(MODULE, "load_required_check_names", return_value=[]):
                self.assertEqual(MODULE.main(), 1)

    def test_l3_status_timeline_does_not_claim_work_start_ordering(self):
        timeline = [
            {"event": "labeled", "label": {"name": "status:draft"}},
            {"event": "labeled", "label": {"name": "status:ready"}},
            {"event": "labeled", "label": {"name": "status:in-progress"}},
        ]
        self.assertEqual(MODULE.validate_status_timeline(timeline, current_status="in-progress", risk="L3"), [])

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

    def test_required_check_names_ignore_unrelated_failed_checks(self):
        payload = {
            "check_runs": [
                {**VALID_CHECK_RUNS["check_runs"][0], "name": "required-test"},
                {**VALID_CHECK_RUNS["check_runs"][1], "name": "unrelated-experiment", "conclusion": "failure"},
            ]
        }
        self.assertEqual(MODULE.validate_check_runs(payload, "abc123", required_names=["required-test"]), [])

    def test_missing_required_check_name_is_rejected(self):
        errors = MODULE.validate_check_runs(VALID_CHECK_RUNS, "abc123", required_names=["missing-required-test"])
        self.assertTrue(any("required GitHub Check missing-required-test" in error for error in errors))

    def test_required_check_name_rejects_same_name_failure(self):
        payload = {
            "check_runs": [
                {**VALID_CHECK_RUNS["check_runs"][0], "name": "required-test", "conclusion": "success"},
                {**VALID_CHECK_RUNS["check_runs"][1], "name": "required-test", "conclusion": "failure"},
            ]
        }
        errors = MODULE.validate_check_runs(payload, "abc123", required_names=["required-test"])
        self.assertTrue(any("required GitHub Check required-test did not pass" in error for error in errors))

    def test_required_check_names_config_shape_is_fail_closed(self):
        self.assertEqual(MODULE.required_check_names_from_config({"enforcement": {"requiredCheckNames": ["required-test"]}}), (["required-test"], []))
        _, errors = MODULE.required_check_names_from_config({"enforcement": {"requiredCheckNames": "required-test"}})
        self.assertTrue(any("requiredCheckNames" in error for error in errors))
        _, errors = MODULE.required_check_names_from_config({"enforcement": {"requiredCheckNames": [""]}})
        self.assertTrue(any("requiredCheckNames" in error for error in errors))

    def test_l3_text_approval_without_event_is_rejected(self):
        errors = MODULE.validate(VALID_PR, VALID_L3_ISSUE, "abc123")
        self.assertTrue(any("fail-closed" in error and "--approval-event-file" in error for error in errors))

    def test_l3_approval_event_must_match_head(self):
        event = {**VALID_L3_APPROVAL, "commitSha": "old456"}
        errors = MODULE.validate(VALID_PR, VALID_L3_ISSUE, "abc123", approval_event=event)
        self.assertTrue(any("approval event commitSha" in error for error in errors))

    def test_valid_l3_approval_event_passes(self):
        self.assertEqual(MODULE.validate(VALID_PR, VALID_L3_ISSUE, "abc123", approval_event=VALID_L3_APPROVAL), [])

if __name__ == "__main__":
    unittest.main()
