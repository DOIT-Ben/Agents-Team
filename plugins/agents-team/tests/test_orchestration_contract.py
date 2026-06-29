import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
EXECUTE_SKILL = PLUGIN_ROOT / "skills" / "execute-team-goal" / "SKILL.md"
SKILL_ROUTING = PLUGIN_ROOT / "references" / "skill-routing.md"
ORCHESTRATION_RULES = PLUGIN_ROOT / "references" / "orchestration-rules.md"


class OrchestrationContractTests(unittest.TestCase):
    def test_execute_skill_uses_router_and_role_contracts(self):
        text = EXECUTE_SKILL.read_text(encoding="utf-8")
        for phrase in ["route-team-work", "references/roles", "allowed files", "forbidden files"]:
            self.assertIn(phrase, text)

    def test_execute_skill_preserves_main_integrator_and_independent_qa(self):
        text = EXECUTE_SKILL.read_text(encoding="utf-8")
        self.assertIn("only the main Codex", text)
        self.assertIn("cannot claim independent QA", text)

    def test_nested_role_dispatch_is_forbidden(self):
        text = ORCHESTRATION_RULES.read_text(encoding="utf-8")
        self.assertIn("角色不得调用其他角色", text)

    def test_routing_reference_preserves_protocol_precedence(self):
        text = SKILL_ROUTING.read_text(encoding="utf-8")
        self.assertIn("Protocol 2.0", text)
        self.assertIn("external", text)
        self.assertIn("builtin", text)


if __name__ == "__main__":
    unittest.main()
