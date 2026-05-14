import unittest

from email_triage_agent.config import EmailTriageConfig
from email_triage_agent.models import EmailMessageSummary
from email_triage_agent.triage import build_review_plan, score_message


class TriageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = EmailTriageConfig(
            imap_host="imap.example.com",
            imap_port=993,
            email_address="user@example.com",
            email_password="secret",
            irrelevant_senders=("deals@example.com",),
            irrelevant_keywords=("coupon",),
        )

    def test_score_message_flags_irrelevant_email(self) -> None:
        message = EmailMessageSummary(
            uid="42",
            subject="Exclusive coupon offer",
            sender="deals@example.com",
            date="Thu, 14 May 2026 10:00:00 +0000",
            preview="Unsubscribe for more promo email",
        )

        score, reasons = score_message(message, self.config)

        self.assertGreaterEqual(score, 2)
        self.assertTrue(reasons)

    def test_build_review_plan_keeps_legitimate_email_out(self) -> None:
        messages = [
            EmailMessageSummary(
                uid="42",
                subject="Exclusive coupon offer",
                sender="deals@example.com",
                date="Thu, 14 May 2026 10:00:00 +0000",
                preview="Unsubscribe for more promo email",
            ),
            EmailMessageSummary(
                uid="43",
                subject="Project update",
                sender="teammate@example.com",
                date="Thu, 14 May 2026 11:00:00 +0000",
                preview="Can you review the latest proposal?",
            ),
        ]

        plan = build_review_plan(messages, self.config)

        self.assertEqual(plan.scanned_count, 2)
        self.assertEqual([candidate.uid for candidate in plan.delete_candidates], ["42"])


if __name__ == "__main__":
    unittest.main()
