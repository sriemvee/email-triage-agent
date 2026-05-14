from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from email_triage_agent.models import ReviewPlan, TriageDecision
from email_triage_agent.review import load_review_plan, save_review_plan, validate_review_plan


class ReviewPlanTests(unittest.TestCase):
    def test_save_and_load_round_trip(self) -> None:
        plan = ReviewPlan(
            generated_at="2026-05-14T10:00:00Z",
            mailbox="INBOX",
            scanned_count=3,
            delete_candidates=(
                TriageDecision(
                    uid="101",
                    subject="Weekend sale",
                    sender="deals@example.com",
                    date="Thu, 14 May 2026 10:00:00 +0000",
                    preview="Huge discount inside",
                    score=3,
                    reasons=("Matched keywords: sale",),
                ),
            ),
        )

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "plan.json"
            saved = save_review_plan(plan, path)
            reloaded = load_review_plan(path)

        self.assertTrue(validate_review_plan(saved))
        self.assertEqual(reloaded.confirmation_token, saved.confirmation_token)
        self.assertEqual(reloaded.delete_candidates[0].uid, "101")

    def test_validate_review_plan_rejects_tampering(self) -> None:
        plan = ReviewPlan(
            generated_at="2026-05-14T10:00:00Z",
            mailbox="INBOX",
            scanned_count=1,
            delete_candidates=(),
            confirmation_token="abc123",
        )

        self.assertFalse(validate_review_plan(plan))
        self.assertFalse(validate_review_plan(replace(plan, confirmation_token="")))


if __name__ == "__main__":
    unittest.main()

