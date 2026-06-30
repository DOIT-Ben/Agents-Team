import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.telemetry import (  # noqa: E402
    TelemetryError,
    delete_logs,
    list_runs,
    record_event,
)


class TelemetryTests(unittest.TestCase):
    def test_records_only_redacted_structured_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            result = record_event(
                "run-001",
                "goal_created",
                state_dir=Path(temp),
                trace_id="trace-001",
                cohort_id="B1-07",
                provider="example",
                model="token=secret-value;user@example.com;C:\\Users\\Alice\\private\\repo",
                task_category="feature",
                risk_level="L2",
                metadata={
                    "reasonCode": "READY",
                },
            )
            event_path = Path(result["path"])
            event = json.loads(event_path.read_text(encoding="utf-8").splitlines()[0])
            serialized = json.dumps(event, ensure_ascii=False)
            self.assertNotIn("secret-value", serialized)
            self.assertNotIn("user@example.com", serialized)
            self.assertNotIn("Alice", serialized)
            self.assertIn("[REDACTED_SECRET]", serialized)
            self.assertIn("[REDACTED_EMAIL]", serialized)
            self.assertIn("[REDACTED_PATH]", serialized)
            self.assertEqual(event["runId"], "run-001")
            self.assertEqual(event["eventType"], "goal_created")

    def test_rejects_prompt_source_and_environment_payloads(self):
        with tempfile.TemporaryDirectory() as temp:
            for key in ("prompt", "output", "source", "environment"):
                with self.subTest(key=key), self.assertRaises(TelemetryError):
                    record_event(
                        "run-001",
                        "work_dispatched",
                        state_dir=Path(temp),
                        metadata={key: "must not be recorded"},
                    )

    def test_rejects_freeform_or_multiline_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(TelemetryError):
                record_event(
                    "run-001",
                    "work_dispatched",
                    state_dir=Path(temp),
                    metadata={"reasonCode": "READY\nsource code follows"},
                )

    def test_lists_and_deletes_local_runs_without_touching_other_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            keep = root / "keep.txt"
            keep.write_text("keep", encoding="utf-8")
            record_event("run-a", "goal_created", state_dir=root)
            record_event("run-b", "goal_created", state_dir=root)
            self.assertEqual([item["runId"] for item in list_runs(state_dir=root)], ["run-b", "run-a"])
            deleted = delete_logs("run-a", state_dir=root)
            self.assertEqual(deleted["deletedRuns"], ["run-a"])
            self.assertTrue(keep.is_file())
            self.assertEqual([item["runId"] for item in list_runs(state_dir=root)], ["run-b"])

    def test_expired_runs_are_purged_before_recording(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old = datetime.now(timezone.utc) - timedelta(days=20)
            record_event("old-run", "goal_created", state_dir=root, timestamp=old)
            record_event("new-run", "goal_created", state_dir=root)
            self.assertFalse((root / "runs" / "old-run").exists())
            self.assertTrue((root / "runs" / "new-run").exists())

    def test_log_rotation_is_bounded(self):
        with tempfile.TemporaryDirectory() as temp, patch(
            "team_collaboration.telemetry.MAX_LOG_BYTES", 500
        ), patch("team_collaboration.telemetry.MAX_ROTATED_FILES", 2):
            root = Path(temp)
            for _ in range(6):
                record_event("run-rotate", "goal_created", state_dir=root)
            run_dir = root / "runs" / "run-rotate"
            self.assertTrue((run_dir / "events.jsonl.1").is_file())
            self.assertTrue((run_dir / "events.jsonl.2").is_file())
            self.assertFalse((run_dir / "events.jsonl.3").exists())


if __name__ == "__main__":
    unittest.main()
