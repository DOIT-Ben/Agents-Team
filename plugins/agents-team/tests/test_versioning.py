import subprocess
import sys
import tempfile
import unittest
import json
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.initialize import InitializationError, initialize_project  # noqa: E402
from team_collaboration.manage import manage_project  # noqa: E402
from team_collaboration.versioning import compare_versions  # noqa: E402


class VersioningTests(unittest.TestCase):
    def test_compares_semantic_versions(self):
        self.assertEqual(compare_versions("1.0.0", "1.0.1"), -1)
        self.assertEqual(compare_versions("1.1.0", "1.0.9"), 1)
        self.assertEqual(compare_versions("1.0.0", "1.0.0"), 0)

    def test_remove_preview_and_apply_preserve_project_agents_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            (root / "AGENTS.md").write_text("keep this\n", encoding="utf-8")
            initialize_project(root, PLUGIN_ROOT, apply=True, allow_dirty=True)
            preview = manage_project(root, PLUGIN_ROOT, "remove", apply=False)
            self.assertIn(".codex/team-collaboration.json", preview["delete"])
            self.assertIn("TEAM-COLLABORATION:START", (root / "AGENTS.md").read_text(encoding="utf-8"))
            manage_project(root, PLUGIN_ROOT, "remove", apply=True)
            self.assertEqual((root / "AGENTS.md").read_text(encoding="utf-8"), "keep this\n")
            self.assertFalse((root / ".codex/team-collaboration.json").exists())

    def test_upgrade_updates_protocol_and_records_timestamp(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            config_path = root / ".codex/team-collaboration.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["mechanism"]["protocolVersion"] = "0.9.0"
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            manage_project(root, PLUGIN_ROOT, "upgrade", apply=True)
            upgraded = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(upgraded["mechanism"]["protocolVersion"], "2.0.0")
            self.assertEqual(upgraded["mechanism"]["configSchemaVersion"], 2)
            self.assertEqual(upgraded["enforcement"]["mode"], "strict")
            self.assertIsNotNone(upgraded["mechanism"]["lastUpgradedAt"])

    def test_upgrade_migrates_v1_configuration_to_strict_v2(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            path = root / ".codex/team-collaboration.json"
            config = json.loads(path.read_text(encoding="utf-8"))
            config["mechanism"]["pluginVersion"] = "0.1.0"
            config["mechanism"]["protocolVersion"] = "1.0.0"
            config["mechanism"]["configSchemaVersion"] = 1
            config.pop("enforcement", None)
            path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            preview = manage_project(root, PLUGIN_ROOT, "upgrade", apply=False)
            self.assertEqual(preview["status"], "preview")
            manage_project(root, PLUGIN_ROOT, "upgrade", apply=True)
            migrated = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(migrated["mechanism"]["protocolVersion"], "2.0.0")
            self.assertIn("enforcement", migrated)

    def test_upgrade_refuses_locally_modified_managed_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            target = root / ".github/ISSUE_TEMPLATE/team-goal.yml"
            target.write_text(target.read_text(encoding="utf-8") + "# custom\n", encoding="utf-8")
            with self.assertRaises(InitializationError):
                manage_project(root, PLUGIN_ROOT, "upgrade", apply=True)


if __name__ == "__main__":
    unittest.main()
