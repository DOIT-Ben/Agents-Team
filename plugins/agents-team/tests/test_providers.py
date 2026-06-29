import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.providers import select_provider  # noqa: E402


class ProviderTests(unittest.TestCase):
    def test_builtin_provider_is_default(self):
        result = select_provider("plan", available_skills=set())
        self.assertEqual(result.provider, "builtin")
        self.assertEqual(result.skill, "plan-team-goal")

    def test_compatible_external_skill_can_be_selected(self):
        result = select_provider("plan", available_skills={"planning-and-task-breakdown"})
        self.assertEqual(result.provider, "external")
        self.assertEqual(result.skill, "planning-and-task-breakdown")

    def test_unrelated_external_skills_do_not_disable_fallback(self):
        result = select_provider("debug", available_skills={"frontend-ui-engineering"})
        self.assertEqual(result.provider, "builtin")
        self.assertEqual(result.skill, "debug-team-goal")

    def test_unknown_phase_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown phase"):
            select_provider("invent", available_skills=set())


if __name__ == "__main__":
    unittest.main()
