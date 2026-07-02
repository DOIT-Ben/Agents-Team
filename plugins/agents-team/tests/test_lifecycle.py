import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.lifecycle import status_from_labels, validate_transition  # noqa: E402


class LifecycleTests(unittest.TestCase):
    def test_exactly_one_status_label_is_required(self):
        status, findings = status_from_labels(["status:ready", "status:in-progress"])
        self.assertIsNone(status)
        self.assertIn("AT-STATE-001", [finding.code for finding in findings])

    def test_legal_transition_passes(self):
        self.assertEqual(validate_transition("ready", "in-progress", risk="L2"), [])

    def test_skipping_qa_is_blocked(self):
        findings = validate_transition("implemented", "mergeable", risk="L2")
        self.assertIn("AT-STATE-002", [finding.code for finding in findings])

    def test_pass_requires_explicit_verifying_state(self):
        self.assertEqual(validate_transition("implemented", "verifying", risk="L2"), [])
        self.assertEqual(validate_transition("verifying", "pass", risk="L2"), [])
        findings = validate_transition("implemented", "pass", risk="L2")
        self.assertIn("AT-STATE-002", [finding.code for finding in findings])

    def test_l3_cannot_start_without_decision(self):
        findings = validate_transition("ready", "in-progress", risk="L3", decision_approved=False)
        self.assertIn("AT-STATE-003", [finding.code for finding in findings])

    def test_fail_can_only_return_to_in_progress(self):
        self.assertEqual(validate_transition("fail", "in-progress", risk="L2"), [])
        self.assertTrue(validate_transition("fail", "verifying", risk="L2"))


if __name__ == "__main__":
    unittest.main()
