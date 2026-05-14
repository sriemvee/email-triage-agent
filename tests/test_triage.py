import unittest

from email_triage_agent.config import EmailTriageConfig
from email_triage_agent.models import EmailMessageSummary
from email_triage_agent.triage import build_review_plan, classify_message, score_message


class TriageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = EmailTriageConfig(
            gmail_client_id="client-id",
            gmail_client_secret="client-secret",
            gmail_refresh_token="refresh-token",
            allowlist_senders=("vip@example.com",),
            allowlist_domains=("trusted.com",),
            irrelevant_senders=("deals@example.com",),
            irrelevant_keywords=("coupon",),
        )

    def test_score_message_flags_irrelevant_email(self) -> None:
        message = EmailMessageSummary(
            uid="42",
            subject="Exclusive coupon offer",
            sender="deals@example.com",
            date="Thu, 14 May 2026 10:00:00 +0000",
            snippet="Unsubscribe from more promo email",
            labels=("CATEGORY_PROMOTIONS",),
        )

        score, reasons = score_message(message, self.config)

        self.assertGreaterEqual(score, 2)
        self.assertTrue(reasons)

    def test_classify_message_protects_allowlisted_and_unread_messages(self) -> None:
        allowlisted = EmailMessageSummary(
            uid="50",
            subject="Invoice available",
            sender="vip@example.com",
            date="Thu, 14 May 2026 09:00:00 +0000",
            snippet="Monthly invoice",
            labels=("INBOX",),
            is_unread=False,
        )
        unread = EmailMessageSummary(
            uid="51",
            subject="Big promo sale",
            sender="deals@example.com",
            date="Thu, 14 May 2026 09:05:00 +0000",
            snippet="unsubscribe now",
            labels=("CATEGORY_PROMOTIONS", "UNREAD"),
            is_unread=True,
        )

        allowlisted_decision = classify_message(allowlisted, self.config)
        unread_decision = classify_message(unread, self.config)

        self.assertEqual(allowlisted_decision.decision, "keep")
        self.assertEqual(allowlisted_decision.reasons, ("Sender is allowlisted",))
        self.assertEqual(unread_decision.decision, "keep")
        self.assertEqual(unread_decision.reasons, ("Unread protection is enabled",))

    def test_build_review_plan_assigns_review_and_trash_candidates(self) -> None:
        messages = [
            EmailMessageSummary(
                uid="42",
                subject="Exclusive coupon offer",
                sender="deals@example.com",
                date="Thu, 14 May 2026 10:00:00 +0000",
                snippet="Unsubscribe from more promo email",
                labels=("CATEGORY_PROMOTIONS",),
            ),
            EmailMessageSummary(
                uid="43",
                subject="Forum digest",
                sender="updates@community.example.com",
                date="Thu, 14 May 2026 11:00:00 +0000",
                snippet="Latest topics from the community",
                labels=("CATEGORY_FORUMS",),
            ),
            EmailMessageSummary(
                uid="44",
                subject="Project update",
                sender="teammate@example.com",
                date="Thu, 14 May 2026 11:05:00 +0000",
                snippet="Can you review the latest proposal?",
                labels=("INBOX",),
            ),
        ]

        plan = build_review_plan(messages, self.config)

        self.assertEqual(plan.scanned_count, 3)
        self.assertEqual(
            {decision.uid: decision.decision for decision in plan.decisions},
            {"42": "trash_candidate", "43": "review", "44": "keep"},
        )


if __name__ == "__main__":
    unittest.main()
