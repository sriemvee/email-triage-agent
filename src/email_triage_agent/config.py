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


def _parse_bool(name: str, value: str | None, default: bool) -> bool:
    if value in (None, ""):
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value.")


@dataclass(frozen=True)
class EmailTriageConfig:
    gmail_client_id: str
    gmail_client_secret: str
    gmail_refresh_token: str
    mailbox: str = "INBOX"
    max_messages: int = 50
    allowlist_senders: tuple[str, ...] = ()
    allowlist_domains: tuple[str, ...] = ()
    protect_unread: bool = True
    irrelevant_senders: tuple[str, ...] = ()
    irrelevant_keywords: tuple[str, ...] = ()

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        require_refresh_token: bool = True,
    ) -> "EmailTriageConfig":
        env = environ or os.environ
        required = [
            "EMAIL_TRIAGE_GMAIL_CLIENT_ID",
            "EMAIL_TRIAGE_GMAIL_CLIENT_SECRET",
        ]
        if require_refresh_token:
            required.append("EMAIL_TRIAGE_GMAIL_REFRESH_TOKEN")
        missing = [name for name in required if not env.get(name)]
        if missing:
            raise ValueError(
                "Missing required environment variables: " + ", ".join(sorted(missing))
            )

        mailbox = env.get("EMAIL_TRIAGE_MAILBOX", "INBOX").strip() or "INBOX"
        return cls(
            gmail_client_id=env["EMAIL_TRIAGE_GMAIL_CLIENT_ID"].strip(),
            gmail_client_secret=env["EMAIL_TRIAGE_GMAIL_CLIENT_SECRET"].strip(),
            gmail_refresh_token=env.get("EMAIL_TRIAGE_GMAIL_REFRESH_TOKEN", "").strip(),
            mailbox=mailbox,
            max_messages=_parse_positive_int(
                "EMAIL_TRIAGE_MAX_MESSAGES", env.get("EMAIL_TRIAGE_MAX_MESSAGES"), 50
            ),
            allowlist_senders=_parse_csv(env.get("EMAIL_TRIAGE_ALLOWLIST_SENDERS")),
            allowlist_domains=_parse_csv(env.get("EMAIL_TRIAGE_ALLOWLIST_DOMAINS")),
            protect_unread=_parse_bool(
                "EMAIL_TRIAGE_PROTECT_UNREAD",
                env.get("EMAIL_TRIAGE_PROTECT_UNREAD"),
                True,
            ),
            irrelevant_senders=_parse_csv(env.get("EMAIL_TRIAGE_IRRELEVANT_SENDERS")),
            irrelevant_keywords=_parse_csv(env.get("EMAIL_TRIAGE_IRRELEVANT_KEYWORDS")),
        )
