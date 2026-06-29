import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.doctor import doctor_project  # noqa: E402
from team_collaboration.initialize import initialize_project  # noqa: E402


class DoctorTests(unittest.TestCase):
    def _root(self, temp: str) -> Path:
        root = Path(temp)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
        return root

    def test_uninitialized_project_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            result = doctor_project(self._root(temp))
            self.assertEqual(result["status"], "blocked")
            self.assertIn("AT-DRIFT-001", [item["code"] for item in result["findings"]])

    def test_initialized_but_unclassified_project_warns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            result = doctor_project(root)
            self.assertEqual(result["status"], "warning")
            codes = [item["code"] for item in result["findings"]]
            self.assertIn("AT-CONTRACT-010", codes)

    def test_fully_classified_project_is_healthy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            path = root / ".codex/team-collaboration.json"
            config = json.loads(path.read_text(encoding="utf-8"))
            config["project"]["repository"] = "owner/repo"
            config["risk"]["criticalPaths"] = ["src/core"]
            config["risk"]["protectedFiles"] = ["pyproject.toml"]
            config["commands"]["test"] = "python3 -m unittest"
            path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = doctor_project(root)
            self.assertEqual(result["status"], "healthy")

    def test_doctor_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if ".git" not in path.parts)
            doctor_project(root)
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if ".git" not in path.parts)
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
