import subprocess
import sys
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
                [sys.executable, str(REPO_ROOT / "tools/build_distribution.py"), "--output", str(output)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn(".agents/plugins/marketplace.json", names)
            self.assertIn("plugins/agents-team/.codex-plugin/plugin.json", names)
            self.assertIn("plugins/agents-team/skills/route-team-work/SKILL.md", names)
            self.assertIn("plugins/agents-team/references/roles/independent-verifier.md", names)
            self.assertIn("docs/README.md", names)
            self.assertIn("docs/beta-quickstart.md", names)
            self.assertIn("docs/feedback.md", names)
            self.assertIn("docs/privacy-feedback.md", names)
            self.assertIn("docs/assets/agents-team-hero-beta.svg", names)
            self.assertIn("tools/verify_distribution.py", names)
            self.assertIn("NOTICE.md", names)
            self.assertFalse(any(name.startswith("plugins/agents-team/tests/") for name in names))
            self.assertNotIn("plugins/agents-team/tests/__pycache__", "\n".join(names))
            self.assertNotIn("docs/assets/agents-team-hero-v2.jpg", names)
            self.assertNotIn("docs/beta-feedback-lifecycle-split-plan.md", names)
            self.assertFalse(any(name.startswith("docs/superpowers/") for name in names))
            self.assertFalse(any(name.startswith("docs/adr/") for name in names))


if __name__ == "__main__":
    unittest.main()
