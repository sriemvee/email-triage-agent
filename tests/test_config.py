import unittest

from email_triage_agent.config import EmailTriageConfig


class EmailTriageConfigTests(unittest.TestCase):
    def test_from_env_parses_values(self) -> None:
        config = EmailTriageConfig.from_env(
            {
                "EMAIL_TRIAGE_IMAP_HOST": "imap.example.com",
                "EMAIL_TRIAGE_IMAP_PORT": "993",
                "EMAIL_TRIAGE_EMAIL_ADDRESS": "user@example.com",
                "EMAIL_TRIAGE_EMAIL_PASSWORD": "secret",
                "EMAIL_TRIAGE_MAILBOX": "Archive",
                "EMAIL_TRIAGE_MAX_MESSAGES": "25",
                "EMAIL_TRIAGE_IRRELEVANT_SENDERS": "newsletter@example.com, deals@example.com ",
                "EMAIL_TRIAGE_IRRELEVANT_KEYWORDS": "promo, offer ",
                "EMAIL_TRIAGE_PROTECTED_SENDERS": "boss@example.com, ceo@example.com ",
                "EMAIL_TRIAGE_PROTECTED_DOMAINS": "important.com, internal.example.com ",
            }
        )

        self.assertEqual(config.imap_host, "imap.example.com")
        self.assertEqual(config.max_messages, 25)
        self.assertEqual(config.mailbox, "Archive")
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


if __name__ == "__main__":
    unittest.main()
