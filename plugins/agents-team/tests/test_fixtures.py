import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.initialize import initialize_project  # noqa: E402
from team_collaboration.validate import validate_project  # noqa: E402


class FixtureTests(unittest.TestCase):
    def test_all_fixture_types_initialize_and_validate(self):
        expected = {
            "python-fastapi": "python",
            "node-nextjs": "nextjs",
            "dotnet-winforms": "dotnet",
            "fullstack-monorepo": "monorepo",
            "existing-agents": "generic",
            "existing-ci": "python",
        }
        for fixture, project_type in expected.items():
            with self.subTest(fixture=fixture), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / fixture
                shutil.copytree(FIXTURES / fixture, root)
                subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
                result = initialize_project(root, PLUGIN_ROOT, apply=True, allow_dirty=True)
                self.assertEqual(result["profile"]["projectType"], project_type)
                self.assertEqual(validate_project(root), [])
                if fixture == "existing-agents":
                    self.assertTrue((root / "AGENTS.md").read_text(encoding="utf-8").startswith("# Existing Project Rules"))
                if fixture == "existing-ci":
                    self.assertTrue((root / ".github/workflows/ci.yml").is_file())


if __name__ == "__main__":
    unittest.main()
