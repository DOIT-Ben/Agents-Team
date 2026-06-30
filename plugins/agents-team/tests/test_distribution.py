import subprocess
import sys
import tempfile
import unittest
import zipfile
import json
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]


class DistributionTests(unittest.TestCase):
    def test_build_distribution_contains_installable_marketplace(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "plugin.zip"
            evidence = Path(temp) / "test-results.json"
            evidence.write_text(json.dumps({
                "status": "passed",
                "command": "python -m unittest discover -s plugins/agents-team/tests -v",
                "passed": 100,
                "failed": 0,
                "errors": 0,
                "skipped": 1,
            }), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools/build_distribution.py"),
                    "--output",
                    str(output),
                    "--channel",
                    "beta",
                    "--tag",
                    "v0.4.0-beta.1",
                    "--test-evidence",
                    str(evidence),
                ],
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
            self.assertIn("tools/verify_distribution.py", names)
            self.assertIn("NOTICE.md", names)
            self.assertIn("SECURITY.md", names)
            self.assertIn("release/channels.json", names)
            self.assertIn(".github/ISSUE_TEMPLATE/bug.yml", names)
            self.assertIn("plugins/agents-team/references/feedback.schema.json", names)
            self.assertNotIn("plugins/agents-team/tests/__pycache__", "\n".join(names))
            checksum = Path(str(output) + ".sha256")
            sbom = output.with_suffix(".spdx.json")
            report = output.with_suffix(".build.json")
            self.assertTrue(checksum.is_file())
            self.assertTrue(sbom.is_file())
            self.assertTrue(report.is_file())
            metadata = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(metadata["version"], "0.4.0-beta.1")
            self.assertEqual(metadata["feedbackSchemaVersion"], 1)
            self.assertEqual(metadata["testEvidence"]["status"], "passed")
            self.assertNotIn(str(Path.home()), json.dumps(metadata))
            self.assertIn(output.name, metadata["verificationCommands"][1])

    def test_build_rejects_tag_that_does_not_match_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools/build_distribution.py"),
                    "--output",
                    str(Path(temp) / "plugin.zip"),
                    "--channel",
                    "beta",
                    "--tag",
                    "v0.4.0-beta.2",
                    "--test-evidence",
                    str(Path(temp) / "missing.json"),
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match plugin version", result.stderr)


if __name__ == "__main__":
    unittest.main()
