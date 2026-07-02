import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.initialize import TEMPLATE_TARGETS  # noqa: E402


TEMPLATES = PLUGIN_ROOT / "templates" / "project"


class TemplateContractTests(unittest.TestCase):
    def test_standard_issue_form_is_goal_first_and_has_hard_boundaries(self):
        text = (TEMPLATES / "team-goal.yml").read_text(encoding="utf-8")
        labels = ["Goal", "必须完成", "验收门禁", "任务边界", "风险等级", "依赖与阻塞条件", "失败处理与回滚"]
        positions = [text.index(label) for label in labels]
        self.assertEqual(positions, sorted(positions))
        for label in labels[:4]:
            section = text[text.index(label) :]
            self.assertIn("required: true", section)

    def test_critical_issue_form_forces_l3_confirmation(self):
        text = (TEMPLATES / "critical-goal.yml").read_text(encoding="utf-8")
        self.assertIn("L3", text)
        self.assertIn("用户确认", text)
        self.assertIn("required: true", text)

    def test_pr_template_contains_delivery_evidence_fields(self):
        text = (TEMPLATES / "pull_request_template.md").read_text(encoding="utf-8")
        headings = [
            "关联任务", "风险等级", "实际改动", "范围偏差", "必须完成项证据",
            "Worker ownership", "测试门禁", "行为验收", "QA 独立性与结论", "剩余风险", "回滚方式", "失败记录",
        ]
        for heading in headings:
            self.assertIn(f"## {heading}", text)
        for field in ["command", "exitCode", "passed", "failed", "skipped", "timestamp", "commitSha", "artifact"]:
            self.assertIn(field, text)
        for field in ["验收者", "实现上下文", "QA 上下文", "验证阶段", "证据"]:
            self.assertIn(field, text)
        for field in ["L3 approval event", "actor", "scope", "risk", "commitSha"]:
            self.assertIn(field, text)
        for field in ["仓库相对路径", "changed files", "Gate 阻断"]:
            self.assertIn(field, text)

    def test_generated_gate_validates_pr_issue_and_current_head_evidence(self):
        validator = (TEMPLATES / "validate_pr_contract.py").read_text(encoding="utf-8")
        for phrase in ["GITHUB_TOKEN", "head.sha", "commitSha", "timestamp", "Issue", "check-runs", "pulls/{number}/files", "changed_files"]:
            self.assertIn(phrase, validator)
        workflow = (TEMPLATES / "collaboration-gate.yml").read_text(encoding="utf-8")
        self.assertNotIn("\n  push:\n", workflow)
        for phrase in [
            "pull-requests: read", "issues: read", "validate_pr_contract.py",
            "GITHUB_EVENT_PATH", "edited", "ready_for_review",
        ]:
            self.assertIn(phrase, workflow)

    def test_initialization_skill_explains_bootstrap_gate(self):
        skill = (PLUGIN_ROOT / "skills" / "initialize-team-collaboration" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ["bootstrap", "synchronize", "开放 PR", "edited"]:
            self.assertIn(phrase, skill)

    def test_initializer_materializes_protocol_2_gate_and_doctor(self):
        self.assertEqual(TEMPLATE_TARGETS["validate_pr_contract.py"], ".codex/scripts/validate_pr_contract.py")
        self.assertEqual(TEMPLATE_TARGETS["doctor_team_collaboration.py"], ".codex/scripts/doctor_team_collaboration.py")

    def test_agents_block_contains_core_non_negotiable_rules(self):
        text = (TEMPLATES / "agents-managed-block.md").read_text(encoding="utf-8")
        for phrase in ["Goal", "必须完成", "验收门禁", "任务边界", "L1", "L2", "L3", "QA"]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
