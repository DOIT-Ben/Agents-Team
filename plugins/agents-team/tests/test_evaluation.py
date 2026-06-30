import unittest
from pathlib import Path
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.evaluation import EvaluationError, evaluate_beta  # noqa: E402


def successful_dataset():
    runs = []
    for index in range(50):
        pair_id = f"pair-{index:02d}"
        runs.extend([
            {
                "runId": f"base-{index}", "pairId": pair_id, "mode": "baseline",
                "verifiedSuccess": index < 35, "defectEscaped": index < 13,
                "firstPass": index < 30, "criticalMiss": False, "falseGate": False,
                "durationSeconds": 100, "cost": 1.0,
            },
            {
                "runId": f"team-{index}", "pairId": pair_id, "mode": "agents-team",
                "verifiedSuccess": index < 45, "defectEscaped": index < 5,
                "firstPass": index < 40, "criticalMiss": False, "falseGate": index == 0,
                "durationSeconds": 130, "cost": 1.3, "contextIsolationViolation": False,
                "userRating": 4, "wouldUseAgain": index < 42,
            },
        ])
    return {
        "invitedTesters": 24,
        "effectiveTesters": 20,
        "installAttempts": 21,
        "installSuccesses": 20,
        "upgradeAttempts": 20,
        "upgradeSuccesses": 20,
        "rollbackAttempts": 20,
        "rollbackSuccesses": 19,
        "diagnosticReports": 20,
        "reproducibleReports": 18,
        "openP0P1PrivacyOrDataLoss": 0,
        "testerFeedback": [
            {"cohortId": f"B1-{index:02d}", "userRating": 4, "wouldUseAgain": index < 15}
            for index in range(20)
        ],
        "runs": runs,
    }


class EvaluationTests(unittest.TestCase):
    def test_evaluates_beta_exit_gate_from_paired_runs(self):
        report = evaluate_beta(successful_dataset())
        self.assertEqual(report["decision"], "stable_candidate")
        self.assertGreaterEqual(report["metrics"]["verifiedSuccessLiftPoints"], 15)
        self.assertGreaterEqual(report["metrics"]["diagnosticReproductionRate"], 0.85)
        self.assertEqual(report["failedGates"], [])

    def test_context_isolation_violation_blocks_stable(self):
        data = successful_dataset()
        data["runs"][1]["contextIsolationViolation"] = True
        report = evaluate_beta(data)
        self.assertEqual(report["decision"], "continue_beta")
        self.assertIn("context_isolation", report["failedGates"])

    def test_requires_complete_pairs(self):
        data = successful_dataset()
        data["runs"].pop()
        with self.assertRaises(EvaluationError):
            evaluate_beta(data)

    def test_rejects_missing_outcome_fields(self):
        data = successful_dataset()
        del data["runs"][0]["verifiedSuccess"]
        with self.assertRaises(EvaluationError):
            evaluate_beta(data)


if __name__ == "__main__":
    unittest.main()
