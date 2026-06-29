import json
import subprocess
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_initialize_and_validate_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            initialize = subprocess.run(
                ["python3", str(PLUGIN_ROOT / "scripts" / "initialize_project.py"), str(root), "--apply"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(initialize.returncode, 0, initialize.stderr)
            self.assertEqual(json.loads(initialize.stdout)["status"], "applied")
            validate = subprocess.run(
                ["python3", str(PLUGIN_ROOT / "scripts" / "validate_project.py"), str(root)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)
            self.assertIn("valid", validate.stdout)

    def test_generated_validator_detects_managed_file_drift_without_plugin(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            subprocess.run(
                ["python3", str(PLUGIN_ROOT / "scripts" / "initialize_project.py"), str(root), "--apply"],
                text=True,
                capture_output=True,
                check=True,
            )
            target = root / ".github/ISSUE_TEMPLATE/team-goal.yml"
            target.write_text(target.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(root / ".codex/scripts/validate_team_collaboration.py"), str(root)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("managed file drift", result.stdout)


if __name__ == "__main__":
    unittest.main()
