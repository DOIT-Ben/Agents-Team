import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.initialize import InitializationError, initialize_project  # noqa: E402


def init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)


def commit_all(root: Path) -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=root, check=True)


class InitializeProjectTests(unittest.TestCase):
    def test_dry_run_does_not_write_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            result = initialize_project(root, PLUGIN_ROOT, apply=False)
            self.assertFalse((root / "AGENTS.md").exists())
            self.assertIn("AGENTS.md", result["create"])

    def test_apply_preserves_existing_agents_and_writes_adapter(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            (root / "AGENTS.md").write_text("# Existing\n\nKeep me.\n", encoding="utf-8")
            commit_all(root)
            result = initialize_project(root, PLUGIN_ROOT, apply=True)
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertTrue(agents.startswith("# Existing\n\nKeep me.\n"))
            self.assertIn("TEAM-COLLABORATION:START", agents)
            self.assertTrue((root / ".codex" / "team-collaboration.json").is_file())
            self.assertEqual(result["status"], "applied")

    def test_repeated_apply_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            first = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file() and ".git" not in path.parts}
            initialize_project(root, PLUGIN_ROOT, apply=True, allow_dirty=True)
            second = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file() and ".git" not in path.parts}
            self.assertEqual(first, second)

    def test_dirty_repository_requires_explicit_override(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            (root / "uncommitted.txt").write_text("change", encoding="utf-8")
            with self.assertRaises(InitializationError):
                initialize_project(root, PLUGIN_ROOT, apply=True)

    def test_existing_unmanaged_target_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_git(root)
            target = root / ".github" / "pull_request_template.md"
            target.parent.mkdir(parents=True)
            target.write_text("custom template", encoding="utf-8")
            with self.assertRaises(InitializationError):
                initialize_project(root, PLUGIN_ROOT, apply=True, allow_dirty=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "custom template")


if __name__ == "__main__":
    unittest.main()
