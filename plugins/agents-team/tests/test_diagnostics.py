import json
import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.diagnostics import Finding, summarize_findings  # noqa: E402


class DiagnosticsTests(unittest.TestCase):
    def test_finding_has_stable_machine_readable_shape(self):
        finding = Finding(
            code="AT-GATE-003",
            severity="error",
            location="PR#45/测试门禁",
            message="required command has no exit code",
            remediation="record command and exit code",
            evidence="测试门禁",
        )
        payload = finding.to_dict()
        self.assertEqual(payload["code"], "AT-GATE-003")
        self.assertEqual(json.loads(json.dumps(payload, ensure_ascii=False))["location"], "PR#45/测试门禁")

    def test_summary_distinguishes_blocked_warning_and_healthy(self):
        error = Finding("AT-SYSTEM-001", "error", "config", "broken", "repair")
        warning = Finding("AT-SYSTEM-002", "warning", "config", "unknown", "review")
        self.assertEqual(summarize_findings([error, warning])["status"], "blocked")
        self.assertEqual(summarize_findings([warning])["status"], "warning")
        self.assertEqual(summarize_findings([])["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
