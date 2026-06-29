import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = PLUGIN_ROOT / "templates" / "project"


class TemplateContractTests(unittest.TestCase):
    def test_standard_issue_form_is_goal_first_and_has_hard_boundaries(self):
        text = (TEMPLATES / "team-goal.yml").read_text(encoding="utf-8")
        labels = ["Goal", "必须完成", "验收门禁", "任务边界", "风险等级", "依赖与阻塞条件"]
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
        headings = ["关联任务", "Goal 对照", "实际改动", "必须完成证据", "验收门禁结果", "任务边界检查", "QA 结论", "剩余风险", "回滚方式"]
        for heading in headings:
            self.assertIn(f"## {heading}", text)

    def test_pr_contract_validator_checks_issue_lookup(self):
        text = (TEMPLATES / "validate_pr_contract.py").read_text(encoding="utf-8")
        for phrase in ["REQUIRED_ISSUE_TERMS", "--require-issue-lookup", "GITHUB_TOKEN", "Goal", "任务边界"]:
            self.assertIn(phrase, text)

    def test_collaboration_gate_runs_pr_contract_validator(self):
        text = (TEMPLATES / "collaboration-gate.yml").read_text(encoding="utf-8")
        self.assertIn("validate_team_collaboration.py", text)
        self.assertIn("validate_pr_contract.py", text)
        self.assertIn("--require-issue-lookup", text)
        self.assertIn("issues: read", text)

    def test_agents_block_contains_core_non_negotiable_rules(self):
        text = (TEMPLATES / "agents-managed-block.md").read_text(encoding="utf-8")
        for phrase in ["Goal", "必须完成", "验收门禁", "任务边界", "L1", "L2", "L3", "QA"]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
