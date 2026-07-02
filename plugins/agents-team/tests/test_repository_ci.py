import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


class RepositoryCiTests(unittest.TestCase):
    def setUp(self):
        if not CI_WORKFLOW.is_file():
            self.skipTest("repository CI workflow is not packaged in marketplace archives")

    def test_ci_runs_on_linux_and_windows(self):
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("windows-latest", workflow)
        self.assertIn("matrix.os", workflow)

    def test_ci_uses_cross_platform_python_invocation(self):
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("python -m unittest discover -s plugins/agents-team/tests -v", workflow)
        self.assertNotIn("python3 -m unittest", workflow)


if __name__ == "__main__":
    unittest.main()
