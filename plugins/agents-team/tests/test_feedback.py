import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.feedback import (  # noqa: E402
    build_feedback_issue,
    export_feedback,
    preview_feedback_export,
    preview_feedback_issue,
    redact_feedback,
    submit_feedback_issue,
)


class FeedbackExportTests(unittest.TestCase):
    def test_redacts_likely_secrets_in_nested_payload(self):
        openai_like_sample = "sk-" + "live" + "-1234567890abcdef"
        github_like_sample = "ghp_" + "abcdefghijklmnopqrstuvwxyz123456"
        gh_personal_access_like_sample = "github_" + "pat_" + "1234567890abcdefghijklmnopqrstuvwxyz"
        payload = {
            "title": "Beta note",
            "apiToken": openai_like_sample,
            "nested": {
                "Authorization": "Bearer " + github_like_sample,
                "notes": "keep this text",
            },
            "items": [{"password": "plain-secret"}, gh_personal_access_like_sample],
        }

        redacted = redact_feedback(payload)

        encoded = json.dumps(redacted, ensure_ascii=False)
        self.assertNotIn(openai_like_sample, encoded)
        self.assertNotIn(github_like_sample, encoded)
        self.assertNotIn("plain-secret", encoded)
        self.assertNotIn(gh_personal_access_like_sample, encoded)
        self.assertIn("keep this text", encoded)

    def test_redacts_remote_urls_and_common_local_paths(self):
        payload = {
            "remotes": [
                "git@github.com:private-org/private-repo.git",
                "ssh://git@github.com/private-org/private-repo.git",
                "https://token123@github.com/private-org/private-repo.git",
                "https://github.com/private-org/private-repo/issues/12",
            ],
            "paths": [
                r"C:\Users\alice\secret-project",
                r"E:\customer\secret-project",
                "/Users/alice/secret-project",
                "/home/alice/secret-project",
            ],
        }

        encoded = json.dumps(redact_feedback(payload), ensure_ascii=False)

        for leaked in ["private-org", "private-repo", "alice", "customer", "secret-project", "token123"]:
            self.assertNotIn(leaked, encoded)
        self.assertIn("[REDACTED]", encoded)

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

    def test_issue_body_uses_feedback_template_and_redacts_payload(self):
        issue = build_feedback_issue(
            {
                "pluginVersion": "0.3.0",
                "stage": "Initialization dry-run",
                "environment": "Codex Plugin, Windows",
                "projectType": "Python",
                "summary": "Dry-run picked the wrong test command",
                "expected": "Use pytest for the smoke test.",
                "actual": "Selected npm test.",
                "steps": ["Initialize the project", "Inspect detected commands"],
                "evidence": "token sk-test12345 should be removed",
            }
        )

        self.assertEqual(issue["title"], "[Beta feedback]: Dry-run picked the wrong test command")
        self.assertIn("### Plugin version", issue["body"])
        self.assertIn("### Redacted evidence", issue["body"])
        self.assertIn("[REDACTED]", issue["body"])
        self.assertNotIn("sk-test12345", issue["body"])
        self.assertIn("- [ ] I reviewed this draft", issue["body"])

    def test_issue_preview_does_not_call_github(self):
        preview = preview_feedback_issue({"summary": "Preview only", "token": "secret-value"}, repo="DOIT-Ben/Agents-Team")

        self.assertIn('"status": "preview"', preview)
        self.assertIn('"repo": "DOIT-Ben/Agents-Team"', preview)
        self.assertIn("[REDACTED]", preview)
        self.assertNotIn("secret-value", preview)

    def test_issue_submit_requires_apply_before_calling_gh(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))

            class Result:
                returncode = 0
                stdout = "https://github.com/DOIT-Ben/Agents-Team/issues/123\n"
                stderr = ""

            return Result()

        preview = submit_feedback_issue({"summary": "Preview only"}, repo="DOIT-Ben/Agents-Team", apply=False, runner=runner)
        self.assertEqual(preview["status"], "preview")
        self.assertEqual(calls, [])

        submitted = submit_feedback_issue({"summary": "Create issue"}, repo="DOIT-Ben/Agents-Team", apply=True, runner=runner)
        self.assertEqual(submitted["status"], "submitted")
        self.assertEqual(submitted["issueUrl"], "https://github.com/DOIT-Ben/Agents-Team/issues/123")
        self.assertEqual(calls[0][0][:5], ["gh", "issue", "create", "--repo", "DOIT-Ben/Agents-Team"])
        self.assertIn("--body-file", calls[0][0])
        self.assertNotIn("### Plugin version", calls[0][0])

    def test_issue_submit_failure_returns_redacted_preview(self):
        def runner(command, **kwargs):
            raise FileNotFoundError("gh missing for C:\\Users\\alice\\repo")

        result = submit_feedback_issue(
            {"summary": "Create issue", "evidence": "remote git@github.com:private-org/private-repo.git"},
            repo="DOIT-Ben/Agents-Team",
            apply=True,
            runner=runner,
        )

        self.assertEqual(result["status"], "failed")
        self.assertIn("title", result)
        self.assertIn("body", result)
        self.assertIn("[REDACTED]", result["body"])
        self.assertNotIn("private-org", json.dumps(result, ensure_ascii=False))
        self.assertNotIn("alice", json.dumps(result, ensure_ascii=False))

    def test_submit_feedback_cli_preview_does_not_create_issue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "feedback-input.json"
            source.write_text(json.dumps({"summary": "CLI preview", "token": "secret-value"}), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(PLUGIN_ROOT / "scripts" / "submit_feedback.py"), str(source)],
                text=True,
                encoding="utf-8",
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('"status": "preview"', result.stdout)
            self.assertIn("[REDACTED]", result.stdout)
            self.assertNotIn("secret-value", result.stdout)


if __name__ == "__main__":
    unittest.main()
