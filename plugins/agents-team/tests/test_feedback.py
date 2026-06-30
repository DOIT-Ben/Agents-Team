import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.feedback import FeedbackError, export_feedback, prepare_github_issue  # noqa: E402
from team_collaboration.telemetry import record_event  # noqa: E402


class FeedbackTests(unittest.TestCase):
    def _record_run(self, root: Path) -> None:
        record_event(
            "run-feedback",
            "goal_created",
            state_dir=root,
            trace_id="trace-feedback",
            cohort_id="B1-02",
            metadata={"reasonCode": "READY"},
        )
        record_event(
            "run-feedback",
            "qa_verdict",
            state_dir=root,
            trace_id="trace-feedback",
            metadata={"status": "FAIL", "reasonCode": "AT-GATE-004"},
        )

    def test_preview_does_not_write_feedback_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._record_run(root)
            result = export_feedback(
                run_id="run-feedback",
                feedback_type="missed_defect",
                severity="P1",
                expected_result="Reviewer catches the defect",
                actual_result="Reviewer passed the change",
                reproduction_steps="Run the supplied acceptance test",
                state_dir=root,
                confirmed=False,
            )
            self.assertEqual(result["status"], "preview")
            self.assertFalse((root / "feedback").exists())
            self.assertFalse(result["uploadPerformed"])

    def test_confirmed_export_writes_schema_compliant_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._record_run(root)
            result = export_feedback(
                run_id="run-feedback",
                feedback_type="missed_defect",
                severity="P1",
                expected_result="No token=secret-value in output",
                actual_result="Contact user@example.com at C:\\Users\\Alice\\repo",
                reproduction_steps="Repeat once",
                state_dir=root,
                confirmed=True,
                user_rating=2,
                would_use_again=False,
            )
            self.assertEqual(result["status"], "exported")
            bundle = Path(result["directory"])
            payload = json.loads((bundle / "diagnostics.json").read_text(encoding="utf-8"))
            markdown = (bundle / "feedback.md").read_text(encoding="utf-8")
            serialized = json.dumps(payload, ensure_ascii=False) + markdown
            self.assertEqual(payload["feedbackSchemaVersion"], 1)
            self.assertEqual(payload["runId"], "run-feedback")
            self.assertEqual(payload["traceId"], "trace-feedback")
            self.assertNotIn("secret-value", serialized)
            self.assertNotIn("user@example.com", serialized)
            self.assertNotIn("Alice", serialized)
            self.assertFalse(result["uploadPerformed"])

    def test_repeat_feedback_for_same_run_preserves_relationship(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._record_run(root)
            first = export_feedback(
                run_id="run-feedback",
                feedback_type="bug",
                severity="P2",
                expected_result="Pass",
                actual_result="Fail",
                reproduction_steps="Run it",
                state_dir=root,
                confirmed=True,
            )
            second = export_feedback(
                run_id="run-feedback",
                feedback_type="bug",
                severity="P2",
                expected_result="Pass",
                actual_result="Fail again",
                reproduction_steps="Run it again",
                state_dir=root,
                confirmed=True,
            )
            payload = json.loads((Path(second["directory"]) / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertIn(first["feedbackId"], payload["relatedFeedbackIds"])

    def test_unknown_feedback_type_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FeedbackError):
                export_feedback(
                    run_id="missing",
                    feedback_type="anything",
                    severity="P2",
                    expected_result="x",
                    actual_result="y",
                    reproduction_steps="z",
                    state_dir=Path(temp),
                    confirmed=False,
                )

    def test_export_drops_tampered_unknown_or_freeform_event_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._record_run(root)
            event_path = root / "runs" / "run-feedback" / "events.jsonl"
            events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
            events[0]["prompt"] = "PRIVATE_SOURCE_MARKER"
            events[0]["metadata"]["reasonCode"] = "READY\nPRIVATE_SOURCE_MARKER"
            event_path.write_text(
                "\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8"
            )
            result = export_feedback(
                run_id="run-feedback",
                feedback_type="privacy",
                severity="P1",
                expected_result="Safe export",
                actual_result="Tampered local event",
                reproduction_steps="Export the run",
                state_dir=root,
                confirmed=True,
            )
            serialized = (Path(result["directory"]) / "diagnostics.json").read_text(encoding="utf-8")
            self.assertNotIn("PRIVATE_SOURCE_MARKER", serialized)
            self.assertNotIn('"prompt"', serialized)

    def test_issue_preparation_only_opens_a_user_confirmed_draft(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._record_run(root)
            exported = export_feedback(
                run_id="run-feedback",
                feedback_type="bug",
                severity="P2",
                expected_result="Pass",
                actual_result="Fail",
                reproduction_steps="Run it",
                state_dir=root,
                confirmed=True,
            )
            with patch("team_collaboration.feedback.shutil.which", return_value=None), patch(
                "team_collaboration.feedback._copy_to_clipboard", return_value=False
            ), patch("team_collaboration.feedback.webbrowser.open", return_value=False):
                result = prepare_github_issue(Path(exported["directory"]), "bug")
            self.assertEqual(result["status"], "form_ready")
            self.assertFalse(result["submissionConfirmed"])

    def test_manage_cli_previews_before_local_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._record_run(root)
            command = [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "manage_project.py"),
                "feedback",
                str(root),
                "--state-dir",
                str(root),
                "--run-id",
                "run-feedback",
                "--feedback-type",
                "bug",
                "--expected-result",
                "Pass",
                "--actual-result",
                "Fail",
                "--reproduction-steps",
                "Run it",
            ]
            preview = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(json.loads(preview.stdout)["status"], "preview")
            self.assertFalse((root / "feedback").exists())
            exported = subprocess.run(command + ["--confirm"], text=True, capture_output=True)
            self.assertEqual(exported.returncode, 0, exported.stderr)
            self.assertEqual(json.loads(exported.stdout)["status"], "exported")


if __name__ == "__main__":
    unittest.main()
