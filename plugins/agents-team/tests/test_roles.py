import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.roles import ROLE_NAMES, compose_role_prompt, load_role_contract  # noqa: E402


class RoleTests(unittest.TestCase):
    def test_every_role_contract_contains_required_sections(self):
        for role in ROLE_NAMES:
            text = load_role_contract(PLUGIN_ROOT, role)
            for heading in ("## Responsibility", "## Allowed", "## Forbidden", "## Output"):
                self.assertIn(heading, text, role)

    def test_worker_prompt_includes_goal_and_file_boundaries(self):
        prompt = compose_role_prompt(
            PLUGIN_ROOT,
            "implementation-worker",
            issue="Goal: upload",
            allowed_files=["src/upload.py"],
            forbidden_files=["src/auth.py"],
        )
        self.assertIn("Goal: upload", prompt)
        self.assertIn("src/upload.py", prompt)
        self.assertIn("src/auth.py", prompt)

    def test_unknown_role_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown role"):
            load_role_contract(PLUGIN_ROOT, "manager-of-managers")

    def test_role_contract_path_cannot_be_injected(self):
        with self.assertRaisesRegex(ValueError, "unknown role"):
            load_role_contract(PLUGIN_ROOT, "../../README")

    def test_independent_verifier_cannot_implement(self):
        text = load_role_contract(PLUGIN_ROOT, "independent-verifier")
        self.assertIn("must not participate in implementation", text)
        self.assertIn("PASS", text)
        self.assertIn("FAIL", text)
        self.assertIn("BLOCKED", text)


if __name__ == "__main__":
    unittest.main()
