import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.evidence import validate_gate_evidence, validate_qa_evidence  # noqa: E402


VALID_GATE = {
    "gate": "test:unit",
    "command": "python3 -m unittest",
    "exitCode": 0,
    "passed": 44,
    "failed": 0,
    "skipped": 0,
    "artifact": "https://github.com/example/actions/runs/1",
    "timestamp": "2026-06-30T12:00:00Z",
    "commitSha": "abc123",
}

VALID_QA = {
    "independent": True,
    "verdict": "PASS",
    "verifier": "independent-verifier",
    "implementationContext": "implement-session-1",
    "qaContext": "qa-session-1",
    "commitSha": "abc123",
    "artifact": "https://github.com/example/actions/runs/1",
}


class EvidenceTests(unittest.TestCase):
    def test_valid_gate_evidence_passes(self):
        self.assertEqual(validate_gate_evidence([VALID_GATE]), [])

    def test_nonzero_exit_code_is_blocked(self):
        evidence = {**VALID_GATE, "exitCode": 1}
        self.assertIn("AT-GATE-001", [finding.code for finding in validate_gate_evidence([evidence])])

    def test_failed_test_count_is_blocked(self):
        evidence = {**VALID_GATE, "failed": 1}
        self.assertIn("AT-GATE-002", [finding.code for finding in validate_gate_evidence([evidence])])

    def test_unexplained_skips_are_blocked(self):
        evidence = {**VALID_GATE, "skipped": 2}
        self.assertIn("AT-GATE-003", [finding.code for finding in validate_gate_evidence([evidence])])

    def test_skips_with_reason_are_allowed(self):
        evidence = {**VALID_GATE, "skipped": 2, "skipReason": "Windows-only tests on Linux"}
        self.assertEqual(validate_gate_evidence([evidence]), [])

    def test_timestamp_and_commit_sha_are_required(self):
        evidence = {key: value for key, value in VALID_GATE.items() if key not in {"timestamp", "commitSha"}}
        findings = validate_gate_evidence([evidence])
        self.assertIn("AT-GATE-004", [finding.code for finding in findings])

    def test_invalid_timestamp_is_blocked(self):
        evidence = {**VALID_GATE, "timestamp": "sometime yesterday"}
        self.assertIn("AT-GATE-004", [finding.code for finding in validate_gate_evidence([evidence])])

    def test_evidence_from_another_commit_is_blocked(self):
        findings = validate_gate_evidence([VALID_GATE], current_sha="def456")
        self.assertIn("AT-GATE-005", [finding.code for finding in findings])

    def test_current_commit_evidence_passes(self):
        self.assertEqual(validate_gate_evidence([VALID_GATE], current_sha="abc123"), [])

    def test_l2_qa_requires_independent_pass(self):
        findings = validate_qa_evidence({**VALID_QA, "independent": False}, risk="L2")
        self.assertIn("AT-QA-001", [finding.code for finding in findings])
        findings = validate_qa_evidence({**VALID_QA, "verdict": "FAIL"}, risk="L2")
        self.assertIn("AT-QA-002", [finding.code for finding in findings])

    def test_l2_qa_requires_verifiable_context_fields(self):
        evidence = {key: value for key, value in VALID_QA.items() if key not in {"verifier", "qaContext"}}
        findings = validate_qa_evidence(evidence, risk="L2", current_sha="abc123")
        self.assertIn("AT-QA-003", [finding.code for finding in findings])

    def test_qa_evidence_from_another_commit_is_blocked(self):
        findings = validate_qa_evidence(VALID_QA, risk="L2", current_sha="def456")
        self.assertIn("AT-QA-004", [finding.code for finding in findings])

    def test_qa_context_must_differ_from_implementation_context(self):
        evidence = {**VALID_QA, "qaContext": "implement-session-1"}
        findings = validate_qa_evidence(evidence, risk="L2", current_sha="abc123")
        self.assertIn("AT-QA-005", [finding.code for finding in findings])

    def test_current_commit_qa_evidence_passes(self):
        self.assertEqual(validate_qa_evidence(VALID_QA, risk="L2", current_sha="abc123"), [])


if __name__ == "__main__":
    unittest.main()
