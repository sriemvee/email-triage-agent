import os
import unittest
from unittest.mock import patch

from email_triage_agent.config import EmailTriageConfig


class EmailTriageConfigTests(unittest.TestCase):
    def test_from_env_parses_values(self) -> None:
        config = EmailTriageConfig.from_env(
            {
                "EMAIL_TRIAGE_GMAIL_CLIENT_ID": "client-id",
                "EMAIL_TRIAGE_GMAIL_CLIENT_SECRET": "client-secret",
                "EMAIL_TRIAGE_GMAIL_REFRESH_TOKEN": "refresh-token",
                "EMAIL_TRIAGE_MAILBOX": "Archive",
                "EMAIL_TRIAGE_MAX_MESSAGES": "25",
                "EMAIL_TRIAGE_ALLOWLIST_SENDERS": "vip@example.com, ceo@example.com ",
                "EMAIL_TRIAGE_ALLOWLIST_DOMAINS": "trusted.com, example.org ",
                "EMAIL_TRIAGE_PROTECT_UNREAD": "false",
                "EMAIL_TRIAGE_IRRELEVANT_SENDERS": "newsletter@example.com, deals@example.com ",
                "EMAIL_TRIAGE_IRRELEVANT_KEYWORDS": "promo, offer ",
                "EMAIL_TRIAGE_PROTECTED_SENDERS": "boss@example.com, ceo@example.com ",
                "EMAIL_TRIAGE_PROTECTED_DOMAINS": "important.com, internal.example.com ",
            }
        )

        self.assertEqual(config.gmail_client_id, "client-id")
        self.assertEqual(config.max_messages, 25)
        self.assertEqual(config.mailbox, "Archive")
        self.assertEqual(config.allowlist_senders, ("vip@example.com", "ceo@example.com"))
        self.assertEqual(config.allowlist_domains, ("trusted.com", "example.org"))
        self.assertFalse(config.protect_unread)
        self.assertEqual(
            config.irrelevant_senders,
            ("newsletter@example.com", "deals@example.com"),
        )
        self.assertEqual(config.irrelevant_keywords, ("promo", "offer"))
        self.assertEqual(config.protected_senders, ("boss@example.com", "ceo@example.com"))
        self.assertEqual(config.protected_domains, ("important.com", "internal.example.com"))

    def test_from_env_requires_mandatory_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing required"):
            EmailTriageConfig.from_env({})

    def test_from_env_does_not_fall_back_when_given_empty_mapping(self) -> None:
        with patch.dict(
            os.environ,
            {
                "EMAIL_TRIAGE_IMAP_HOST": "imap.example.com",
                "EMAIL_TRIAGE_EMAIL_ADDRESS": "user@example.com",
                "EMAIL_TRIAGE_EMAIL_PASSWORD": "secret",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "Missing required"):
                EmailTriageConfig.from_env({})


if __name__ == "__main__":
    unittest.main()
