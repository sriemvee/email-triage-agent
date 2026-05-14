import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from email_triage_agent.cli import build_parser, handle_apply_review, handle_gmail_auth
from email_triage_agent.config import EmailTriageConfig
from email_triage_agent.models import ReviewPlan, TriageDecision
from email_triage_agent.review import save_review_plan


class CliApplyReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = EmailTriageConfig(
            gmail_client_id="client-id",
            gmail_client_secret="client-secret",
            gmail_refresh_token="refresh-token",
        )

    def _write_plan(self, path: Path) -> ReviewPlan:
        return save_review_plan(
            ReviewPlan(
                generated_at="2026-05-14T10:00:00Z",
                mailbox="INBOX",
                scanned_count=1,
                decisions=(
                    TriageDecision(
                        uid="101",
                        subject="Weekend sale",
                        sender="deals@example.com",
                        date="Thu, 14 May 2026 10:00:00 +0000",
                        snippet="Huge discount inside",
                        labels=("CATEGORY_PROMOTIONS",),
                        is_unread=False,
                        decision="trash_candidate",
                        reasons=("Matched keywords: sale",),
                    ),
                ),
            ),
            path,
        )

    def test_apply_review_defaults_to_dry_run(self) -> None:
        with TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "plan.json"
            plan = self._write_plan(plan_path)
            args = build_parser().parse_args(
                [
                    "apply-review",
                    "--plan-path",
                    str(plan_path),
                    "--confirm-token",
                    plan.confirmation_token,
                    "--confirm-trash",
                ]
            )

            with patch("email_triage_agent.cli.EmailTriageConfig.from_env", return_value=self.config), patch(
                "email_triage_agent.cli.GmailEmailClient"
            ) as client_class, patch("sys.stdout", new_callable=io.StringIO) as stdout:
                result = handle_apply_review(args)

        self.assertEqual(result, 0)
        client_class.return_value.trash_messages.assert_not_called()
        self.assertIn("Dry-run: would move 1 message", stdout.getvalue())

    def test_apply_review_requires_apply_flag_to_trash(self) -> None:
        with TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "plan.json"
            plan = self._write_plan(plan_path)
            args = build_parser().parse_args(
                [
                    "apply-review",
                    "--plan-path",
                    str(plan_path),
                    "--confirm-token",
                    plan.confirmation_token,
                    "--confirm-trash",
                    "--apply",
                ]
            )

            with patch("email_triage_agent.cli.EmailTriageConfig.from_env", return_value=self.config), patch(
                "email_triage_agent.cli.GmailEmailClient"
            ) as client_class, patch("sys.stdout", new_callable=io.StringIO) as stdout:
                client_class.return_value.trash_messages.return_value = 1
                result = handle_apply_review(args)

        self.assertEqual(result, 0)
        client_class.return_value.trash_messages.assert_called_once_with(["101"])
        self.assertIn("Moved 1 message to Gmail trash", stdout.getvalue())

    def test_gmail_auth_saves_refresh_token_without_printing_it(self) -> None:
        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            args = build_parser().parse_args(["gmail-auth", "--env-path", str(env_path)])

            with patch("email_triage_agent.cli.EmailTriageConfig.from_env", return_value=self.config), patch(
                "email_triage_agent.cli.run_gmail_oauth_flow", return_value="refresh-token-value"
            ), patch("sys.stdout", new_callable=io.StringIO) as stdout:
                result = handle_gmail_auth(args)

            self.assertEqual(result, 0)
            self.assertIn(
                "EMAIL_TRIAGE_GMAIL_REFRESH_TOKEN=refresh-token-value",
                env_path.read_text(encoding="utf-8"),
            )
            self.assertNotIn("refresh-token-value", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
