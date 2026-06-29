import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]


class DistributionTests(unittest.TestCase):
    def test_build_distribution_contains_installable_marketplace(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "plugin.zip"
            result = subprocess.run(
                ["python3", str(REPO_ROOT / "tools/build_distribution.py"), "--output", str(output)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn(".agents/plugins/marketplace.json", names)
            self.assertIn("plugins/agents-team/.codex-plugin/plugin.json", names)
            self.assertNotIn("plugins/agents-team/tests/__pycache__", "\n".join(names))


if __name__ == "__main__":
    unittest.main()
