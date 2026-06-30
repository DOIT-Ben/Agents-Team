import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.initialize import InitializationError, initialize_project  # noqa: E402


class SecurityTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_refuses_to_write_through_symlinked_management_directory(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            try:
                os.symlink(outside, root / ".codex", target_is_directory=True)
            except OSError as exc:
                if getattr(exc, "winerror", None) == 1314:
                    self.skipTest("Windows developer mode or symlink privilege is required")
                raise
            with self.assertRaises(InitializationError):
                initialize_project(root, PLUGIN_ROOT, apply=True, allow_dirty=True)
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_refuses_repository_path_that_is_not_git(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(InitializationError):
                initialize_project(Path(temp), PLUGIN_ROOT, apply=True)


if __name__ == "__main__":
    unittest.main()
