from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


def _parse_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip().lower() for item in value.split(",") if item.strip())


def _parse_positive_int(name: str, value: str | None, default: int) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return parsed


@dataclass(frozen=True)
class EmailTriageConfig:
    imap_host: str
    imap_port: int
    email_address: str
    email_password: str
    mailbox: str = "INBOX"
    max_messages: int = 50
    irrelevant_senders: tuple[str, ...] = ()
    irrelevant_keywords: tuple[str, ...] = ()

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "EmailTriageConfig":
        env = environ or os.environ
        required = (
            "EMAIL_TRIAGE_IMAP_HOST",
            "EMAIL_TRIAGE_EMAIL_ADDRESS",
            "EMAIL_TRIAGE_EMAIL_PASSWORD",
        )
        missing = [name for name in required if not env.get(name)]
        if missing:
            raise ValueError(
                "Missing required environment variables: " + ", ".join(sorted(missing))
            )

        mailbox = env.get("EMAIL_TRIAGE_MAILBOX", "INBOX").strip() or "INBOX"
        return cls(
            imap_host=env["EMAIL_TRIAGE_IMAP_HOST"].strip(),
            imap_port=_parse_positive_int(
                "EMAIL_TRIAGE_IMAP_PORT", env.get("EMAIL_TRIAGE_IMAP_PORT"), 993
            ),
            email_address=env["EMAIL_TRIAGE_EMAIL_ADDRESS"].strip(),
            email_password=env["EMAIL_TRIAGE_EMAIL_PASSWORD"],
            mailbox=mailbox,
            max_messages=_parse_positive_int(
                "EMAIL_TRIAGE_MAX_MESSAGES", env.get("EMAIL_TRIAGE_MAX_MESSAGES"), 50
            ),
            irrelevant_senders=_parse_csv(env.get("EMAIL_TRIAGE_IRRELEVANT_SENDERS")),
            irrelevant_keywords=_parse_csv(env.get("EMAIL_TRIAGE_IRRELEVANT_KEYWORDS")),
        )

