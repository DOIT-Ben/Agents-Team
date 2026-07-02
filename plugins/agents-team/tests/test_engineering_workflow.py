import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.initialize import initialize_project  # noqa: E402
from team_collaboration.workflow import evaluate_goal_workflow  # noqa: E402


VALID_GATE = {
    "gate": "test:unit",
    "command": "python3 -m unittest",
    "exitCode": 0,
    "passed": 12,
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


class EngineeringWorkflowTests(unittest.TestCase):
    def test_initialized_l2_goal_blocks_bad_evidence_then_accepts_current_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            initialize_project(root, PLUGIN_ROOT, apply=True)
            config = json.loads((root / ".codex/team-collaboration.json").read_text(encoding="utf-8"))
            self.assertEqual(config["mechanism"]["protocolVersion"], "2.0.0")

            blocked = evaluate_goal_workflow(
                intent="implement upload",
                status="ready",
                risk="L2",
                available_skills=set(),
                gate_records=[{"gate": "test:unit"}],
                qa_evidence=VALID_QA,
                current_sha="abc123",
            )
            self.assertEqual(blocked["route"]["skill"], "plan-team-goal")
            self.assertEqual(blocked["status"], "blocked")

            healthy = evaluate_goal_workflow(
                intent="implement upload",
                status="ready",
                risk="L2",
                available_skills=set(),
                gate_records=[VALID_GATE],
                qa_evidence=VALID_QA,
                current_sha="abc123",
            )
            self.assertEqual(healthy["provider"]["provider"], "builtin")
            self.assertEqual(healthy["status"], "healthy")
            self.assertEqual(healthy["findings"], [])


if __name__ == "__main__":
    unittest.main()
