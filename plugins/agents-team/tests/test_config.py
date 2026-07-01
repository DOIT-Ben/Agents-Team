import json
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.config import ConfigError, load_config, validate_config  # noqa: E402


def valid_config():
    return {
        "mechanism": {
            "id": "agents-team",
            "pluginVersion": "0.3.0",
            "protocolVersion": "2.0.0",
            "configSchemaVersion": 2,
            "initializedAt": "2026-06-29T00:00:00Z",
            "lastUpgradedAt": None,
        },
        "project": {
            "name": "sample",
            "type": "python",
            "repository": "owner/sample",
            "defaultBranch": "main",
        },
        "commands": {"test": "python -m unittest", "build": "", "lint": "", "typecheck": "", "e2e": ""},
        "paths": {"frontend": [], "backend": ["src"], "database": [], "deployment": [], "tests": ["tests"]},
        "risk": {"criticalPaths": [], "protectedFiles": [], "productionPaths": [], "realProviderPaths": []},
        "overrides": {"requireIssueForL1": False, "requireRealSmokeForRelease": True},
        "enforcement": {
            "mode": "strict",
            "failClosedRisks": ["L2", "L3"],
            "requireLinkedIssue": {"L1": False, "L2": True, "L3": True},
            "requireIndependentQA": {"L1": False, "L2": True, "L3": True},
            "requireFailureRecord": True,
        },
        "managedFiles": {},
    }


class ConfigTests(unittest.TestCase):
    def test_valid_config_has_no_errors(self):
        self.assertEqual(validate_config(valid_config()), [])

    def test_missing_goal_mechanism_identifier_is_rejected(self):
        config = valid_config()
        del config["mechanism"]["id"]
        self.assertIn("mechanism.id is required", validate_config(config))

    def test_invalid_semantic_version_is_rejected(self):
        config = valid_config()
        config["mechanism"]["protocolVersion"] = "latest"
        self.assertIn("mechanism.protocolVersion must be semantic version", validate_config(config))

    def test_path_escape_is_rejected(self):
        config = valid_config()
        config["risk"]["criticalPaths"] = ["../outside"]
        self.assertIn("risk.criticalPaths contains unsafe path: ../outside", validate_config(config))

    def test_enforcement_section_is_required(self):
        config = valid_config()
        del config["enforcement"]
        self.assertIn("enforcement is required", validate_config(config))

    def test_fail_closed_risks_reject_unknown_values(self):
        config = valid_config()
        config["enforcement"]["failClosedRisks"] = ["L4"]
        self.assertIn("enforcement.failClosedRisks must contain only L1, L2, L3", validate_config(config))

    def test_enforcement_mode_must_be_strict_or_advisory(self):
        config = valid_config()
        config["enforcement"]["mode"] = "sometimes"
        self.assertIn("enforcement.mode must be strict or advisory", validate_config(config))

    def test_linked_issue_rules_must_cover_all_risks_with_booleans(self):
        config = valid_config()
        config["enforcement"]["requireLinkedIssue"] = {"L1": False, "L2": True}
        self.assertIn(
            "enforcement.requireLinkedIssue must map L1, L2 and L3 to booleans",
            validate_config(config),
        )
        config = valid_config()
        config["enforcement"]["requireLinkedIssue"] = {"L1": False, "L2": True, "L3": "yes"}
        self.assertIn(
            "enforcement.requireLinkedIssue must map L1, L2 and L3 to booleans",
            validate_config(config),
        )

    def test_independent_qa_rules_must_cover_all_risks_with_booleans(self):
        config = valid_config()
        config["enforcement"]["requireIndependentQA"] = {"L1": False, "L2": True, "L3": "yes"}
        self.assertIn(
            "enforcement.requireIndependentQA must map L1, L2 and L3 to booleans",
            validate_config(config),
        )

    def test_failure_record_requirement_must_be_boolean(self):
        config = valid_config()
        config["enforcement"]["requireFailureRecord"] = "required"
        self.assertIn("enforcement.requireFailureRecord must be boolean", validate_config(config))

    def test_load_config_raises_with_all_validation_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps({}), encoding="utf-8")
            with self.assertRaises(ConfigError) as context:
                load_config(path)
            self.assertIn("mechanism is required", str(context.exception))


if __name__ == "__main__":
    unittest.main()
