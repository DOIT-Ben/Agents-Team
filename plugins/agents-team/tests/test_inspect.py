import json
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.inspect import inspect_repository  # noqa: E402


class InspectRepositoryTests(unittest.TestCase):
    def test_detects_nextjs_commands_without_reading_env(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"next": "16"}, "scripts": {"test": "vitest", "build": "next build", "lint": "eslint ."}}),
                encoding="utf-8",
            )
            (root / ".env").write_text("SECRET=do-not-read", encoding="utf-8")
            result = inspect_repository(root)
            self.assertEqual(result["projectType"], "nextjs")
            self.assertEqual(result["commands"]["build"], "npm run build")
            self.assertNotIn("do-not-read", json.dumps(result))

    def test_detects_python_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            (root / "tests").mkdir()
            result = inspect_repository(root)
            self.assertEqual(result["projectType"], "python")
            self.assertEqual(result["commands"]["test"], "python -m pytest")
            self.assertIn("tests", result["paths"]["tests"])

    def test_detects_dotnet_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Sample.sln").write_text("", encoding="utf-8")
            result = inspect_repository(root)
            self.assertEqual(result["projectType"], "dotnet")
            self.assertEqual(result["commands"]["build"], "dotnet build")
            self.assertEqual(result["commands"]["test"], "dotnet test")


if __name__ == "__main__":
    unittest.main()
