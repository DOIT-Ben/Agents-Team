import re
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_all_skills_have_trigger_only_frontmatter_and_no_placeholders(self):
        for path in sorted((PLUGIN_ROOT / "skills").glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"TODO|\[TODO", path.as_posix())
            description = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
            self.assertIsNotNone(description, path.as_posix())
            self.assertTrue(description.group(1).startswith("Use when "), path.as_posix())

    def test_initialize_skill_requires_preview_and_confirmation(self):
        text = (PLUGIN_ROOT / "skills/initialize-team-collaboration/SKILL.md").read_text(encoding="utf-8")
        for phrase in ["dry-run", "用户确认", "不得覆盖", "initialize_project.py"]:
            self.assertIn(phrase, text)

    def test_execute_skill_enforces_issue_contract_and_risk(self):
        text = (PLUGIN_ROOT / "skills/execute-team-goal/SKILL.md").read_text(encoding="utf-8")
        for phrase in ["Goal", "必须完成", "验收门禁", "任务边界", "L1", "L2", "L3", "独立 QA"]:
            self.assertIn(phrase, text)

    def test_verify_skill_is_read_only_and_binary(self):
        text = (PLUGIN_ROOT / "skills/verify-team-goal/SKILL.md").read_text(encoding="utf-8")
        for phrase in ["全新上下文", "只读", "PASS", "FAIL", "不得修改"]:
            self.assertIn(phrase, text)

    def test_manage_skill_has_all_supported_actions(self):
        text = (PLUGIN_ROOT / "skills/manage-team-collaboration/SKILL.md").read_text(encoding="utf-8")
        for phrase in ["检查", "升级", "修复", "移除", "manage_project.py"]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
