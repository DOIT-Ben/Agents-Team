import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]


class PackageTests(unittest.TestCase):
    def test_plugin_manifest_is_release_ready(self):
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "agents-team")
        self.assertEqual(manifest["version"], "0.3.0")
        self.assertEqual(manifest["author"]["name"], "DOIT-Ben")
        self.assertIn("Engineering lifecycle", manifest["interface"]["capabilities"])
        self.assertIn("Deterministic routing", manifest["interface"]["capabilities"])
        self.assertNotIn("scaffold", json.dumps(manifest).lower())
        self.assertNotIn("local developer", json.dumps(manifest).lower())

    def test_repository_contains_upstream_attribution(self):
        notice = (REPO_ROOT / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("addyosmani/agent-skills", notice)
        self.assertIn("MIT", notice)

    def test_marketplace_points_to_plugin(self):
        marketplace = json.loads((REPO_ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "agents-team")
        self.assertEqual(entry["source"]["path"], "./plugins/agents-team")

    def test_every_skill_has_interface_metadata(self):
        for skill in (PLUGIN_ROOT / "skills").iterdir():
            if skill.is_dir():
                self.assertTrue((skill / "agents/openai.yaml").is_file(), skill.name)

    def test_role_contracts_are_packaged_as_references(self):
        roles = PLUGIN_ROOT / "references" / "roles"
        self.assertEqual(len(list(roles.glob("*.md"))), 6)


if __name__ == "__main__":
    unittest.main()
