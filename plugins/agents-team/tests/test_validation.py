import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.initialize import initialize_project  # noqa: E402
from team_collaboration.validate import validate_project  # noqa: E402


def init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)


class ValidationTests(unittest.TestCase):
    def test_fresh_initialized_project_is_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            self.assertEqual(validate_project(root), [])

    def test_generated_template_drift_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            target = root / ".github" / "ISSUE_TEMPLATE" / "team-goal.yml"
            target.write_text(target.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
            self.assertIn("managed file drift: .github/ISSUE_TEMPLATE/team-goal.yml", validate_project(root))

    def test_managed_file_manifest_tampering_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            config_path = root / ".codex" / "team-collaboration.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            del config["managedFiles"][".codex/scripts/validate_team_collaboration.py"]
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            self.assertIn(
                "managed file set mismatch: missing .codex/scripts/validate_team_collaboration.py",
                validate_project(root),
            )

    def test_agents_text_outside_managed_block_does_not_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            (root / "AGENTS.md").write_text("project rule\n", encoding="utf-8")
            initialize_project(root, PLUGIN_ROOT, apply=True, allow_dirty=True)
            agents = root / "AGENTS.md"
            agents.write_text("updated project rule\n" + agents.read_text(encoding="utf-8")[len("project rule\n"):], encoding="utf-8")
            self.assertNotIn("managed file drift: AGENTS.md#TEAM-COLLABORATION", validate_project(root))

    def test_agents_managed_block_drift_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            agents = root / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8").replace("Goal", "Changed Goal", 1), encoding="utf-8")
            self.assertIn("managed file drift: AGENTS.md#TEAM-COLLABORATION", validate_project(root))


if __name__ == "__main__":
    unittest.main()
