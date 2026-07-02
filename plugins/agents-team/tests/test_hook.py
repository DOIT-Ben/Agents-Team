import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HOOK = PLUGIN_ROOT / "hooks" / "session_start.py"


def snapshot(root: Path):
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}


class HookTests(unittest.TestCase):
    def test_hook_reports_missing_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before = snapshot(root)
            result = subprocess.run([sys.executable, str(HOOK), str(root)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("尚未初始化团队协作机制", result.stdout)
            self.assertEqual(snapshot(root), before)


if __name__ == "__main__":
    unittest.main()
