import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.routing import ParallelFacts, route_work  # noqa: E402


class RoutingTests(unittest.TestCase):
    def test_ready_goal_routes_to_planning(self):
        decision = route_work(intent="implement upload", status="ready", risk="L2")
        self.assertEqual(decision.phase, "plan")
        self.assertEqual(decision.skill, "plan-team-goal")
        self.assertEqual(decision.role, "goal-planner")

    def test_failure_intent_routes_to_debugging(self):
        decision = route_work(intent="tests fail with timeout", status="in-progress", risk="L2")
        self.assertEqual(decision.phase, "debug")
        self.assertEqual(decision.skill, "debug-team-goal")
        self.assertEqual(decision.role, "test-engineer")

    def test_implemented_goal_routes_to_review(self):
        decision = route_work(intent="check the completed change", status="implemented", risk="L2")
        self.assertEqual(decision.skill, "review-team-goal")
        self.assertEqual(decision.role, "code-reviewer")

    def test_passed_goal_routes_to_shipping(self):
        decision = route_work(intent="prepare delivery", status="pass", risk="L3")
        self.assertEqual(decision.skill, "ship-team-goal")
        self.assertEqual(decision.role, "independent-verifier")

    def test_parallelism_requires_every_fact(self):
        facts = ParallelFacts(True, True, True, False)
        decision = route_work(intent="implement", status="in-progress", risk="L2", parallel=facts)
        self.assertFalse(decision.can_parallel)

    def test_parallelism_is_allowed_when_all_facts_hold(self):
        facts = ParallelFacts(True, True, True, True)
        decision = route_work(intent="implement", status="in-progress", risk="L2", parallel=facts)
        self.assertTrue(decision.can_parallel)

    def test_unknown_risk_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown risk"):
            route_work(intent="implement", status="ready", risk="L4")

    def test_unknown_status_without_explicit_intent_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot route"):
            route_work(intent="continue", status="mystery", risk="L2")


if __name__ == "__main__":
    unittest.main()
