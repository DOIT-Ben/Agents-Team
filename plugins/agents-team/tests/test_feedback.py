import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.feedback import export_feedback, preview_feedback_export, redact_feedback  # noqa: E402


class FeedbackExportTests(unittest.TestCase):
    def test_redacts_likely_secrets_in_nested_payload(self):
        payload = {
            "title": "Beta note",
            "apiToken": "sk-live-1234567890abcdef",
            "nested": {
                "Authorization": "Bearer ghp_abcdefghijklmnopqrstuvwxyz123456",
                "notes": "keep this text",
            },
            "items": [{"password": "plain-secret"}, "github_pat_1234567890abcdefghijklmnopqrstuvwxyz"],
        }

        redacted = redact_feedback(payload)

        encoded = json.dumps(redacted, ensure_ascii=False)
        self.assertNotIn("sk-live-1234567890abcdef", encoded)
        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz123456", encoded)
        self.assertNotIn("plain-secret", encoded)
        self.assertNotIn("github_pat_1234567890abcdefghijklmnopqrstuvwxyz", encoded)
        self.assertIn("keep this text", encoded)

    def test_preview_does_not_write_output_file(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "feedback.json"

            preview = preview_feedback_export({"token": "secret-value"}, output_path=output)

            self.assertFalse(output.exists())
            self.assertIn("[REDACTED]", preview)
            self.assertNotIn("secret-value", preview)

    def test_confirmed_export_writes_only_redacted_data(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "feedback.json"

            result = export_feedback({"message": "works", "password": "secret-value"}, output, apply=True)

            self.assertEqual(result["status"], "written")
            written = output.read_text(encoding="utf-8")
            self.assertIn("works", written)
            self.assertIn("[REDACTED]", written)
            self.assertNotIn("secret-value", written)

    def test_export_without_apply_returns_preview_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "feedback.json"

            result = export_feedback({"password": "secret-value"}, output, apply=False)

            self.assertEqual(result["status"], "preview")
            self.assertFalse(output.exists())
            self.assertIn("[REDACTED]", result["preview"])

    def test_cli_preview_does_not_write_output_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "feedback-input.json"
            output = root / "feedback-export.json"
            source.write_text(json.dumps({"token": "secret-value"}), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(PLUGIN_ROOT / "scripts" / "export_feedback.py"), str(source), "--output", str(output)],
                text=True,
                encoding="utf-8",
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(output.exists())
            self.assertIn("[REDACTED]", result.stdout)
            self.assertNotIn("secret-value", result.stdout)

    def test_cli_apply_writes_redacted_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "feedback-input.json"
            output = root / "feedback-export.json"
            source.write_text(json.dumps({"password": "secret-value"}), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(PLUGIN_ROOT / "scripts" / "export_feedback.py"),
                    str(source),
                    "--output",
                    str(output),
                    "--apply",
                ],
                text=True,
                encoding="utf-8",
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(output.exists())
            self.assertIn("[REDACTED]", output.read_text(encoding="utf-8"))
            self.assertNotIn("secret-value", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
