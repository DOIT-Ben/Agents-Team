import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]


class BetaDeliveryTests(unittest.TestCase):
    def test_feedback_schemas_are_packaged_and_versioned(self):
        for name in ["event.schema.json", "feedback.schema.json", "beta-evaluation.schema.json"]:
            path = PLUGIN_ROOT / "references" / name
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["type"], "object")

    def test_repository_has_each_structured_feedback_form(self):
        forms = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
        expected = {
            "bug.yml",
            "missed-defect.yml",
            "false-block.yml",
            "context-isolation.yml",
            "compatibility.yml",
            "privacy.yml",
            "feature-request.yml",
        }
        self.assertEqual({path.name for path in forms.glob("*.yml")} & expected, expected)
        for name in expected:
            text = (forms / name).read_text(encoding="utf-8")
            self.assertIn("run_id", text, name)
            self.assertIn("agents_team_version", text, name)
            self.assertIn("reproduction", text, name)

    def test_beta_channel_is_version_pinned_and_stable_is_closed(self):
        channels = json.loads((REPO_ROOT / "release" / "channels.json").read_text(encoding="utf-8"))
        self.assertEqual(channels["beta"]["version"], "0.4.0-beta.1")
        self.assertEqual(channels["beta"]["ref"], "v0.4.0-beta.1")
        self.assertFalse(channels["stable"]["open"])

    def test_beta_workflow_builds_sidecars_and_prerelease(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "beta-release.yml").read_text(encoding="utf-8")
        for phrase in [
            "v*-beta.*", "ubuntu-latest", "windows-latest", "macos-latest",
            "run_tests.py", "build_distribution.py", "verify_distribution.py", "prerelease: true",
        ]:
            self.assertIn(phrase, workflow)

    def test_public_beta_docs_cover_onboarding_privacy_evaluation_and_recall(self):
        required = {
            "docs/beta-guide.md": ["第 1 天", "第 7 天", "第 14 天", "cohort_id"],
            "docs/privacy.md": ["本地", "14 天", "明确确认", "删除"],
            "docs/evaluation.md": ["配对", "独立", "15 个百分点", "30%"],
            "docs/release-and-recall.md": ["Withdrawn", "回滚", "召回", "不支持远程强制卸载"],
        }
        for relative, phrases in required.items():
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, relative)


if __name__ == "__main__":
    unittest.main()
