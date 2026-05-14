from __future__ import annotations

import imaplib
import re
from email import message_from_bytes, policy
from email.header import decode_header, make_header
from html import unescape

from email_triage_agent.config import EmailTriageConfig
from email_triage_agent.models import EmailMessageSummary


class EmailClientError(RuntimeError):
    """Raised when mailbox operations fail."""


class ImapEmailClient:
    def __init__(self, config: EmailTriageConfig) -> None:
        self._config = config

    def fetch_recent_messages(self) -> list[EmailMessageSummary]:
        with self._connect() as client:
            self._select_mailbox(client, readonly=True)
            status, data = client.uid("SEARCH", None, "ALL")
            self._ensure_ok(status, "search mailbox")
            uids = data[0].decode("utf-8").split()
            recent_uids = uids[-self._config.max_messages :]
            messages: list[EmailMessageSummary] = []
            for uid in recent_uids:
                status, payload = client.uid("FETCH", uid, "(RFC822)")
                self._ensure_ok(status, f"fetch message {uid}")
                raw_message = self._extract_raw_message(payload)
                parsed = message_from_bytes(raw_message, policy=policy.default)
                messages.append(
                    EmailMessageSummary(
                        uid=uid,
                        subject=self._decode_header(parsed.get("Subject", "(no subject)")),
                        sender=self._decode_header(parsed.get("From", "(unknown sender)")),
                        date=self._decode_header(parsed.get("Date", "")),
                        preview=self._extract_preview(parsed),
                    )
                )
            return messages

    def delete_messages(self, uids: list[str]) -> int:
        if not uids:
            return 0
        with self._connect() as client:
            self._select_mailbox(client, readonly=False)
            for uid in uids:
                status, _ = client.uid("STORE", uid, "+FLAGS.SILENT", r"(\Deleted)")
                self._ensure_ok(status, f"mark message {uid} as deleted")
            status, _ = client.expunge()
            self._ensure_ok(status, "expunge mailbox")
        return len(uids)

    def _connect(self) -> imaplib.IMAP4_SSL:
        try:
            client = imaplib.IMAP4_SSL(self._config.imap_host, self._config.imap_port)
            client.login(self._config.email_address, self._config.email_password)
            return client
        except imaplib.IMAP4.error as exc:
            raise EmailClientError(f"Unable to connect to mailbox: {exc}") from exc

    def _select_mailbox(self, client: imaplib.IMAP4_SSL, readonly: bool) -> None:
        status, _ = client.select(self._config.mailbox, readonly=readonly)
        self._ensure_ok(status, f"select mailbox {self._config.mailbox}")

    @staticmethod
    def _ensure_ok(status: str, action: str) -> None:
        if status != "OK":
            raise EmailClientError(f"Failed to {action}.")

    @staticmethod
    def _extract_raw_message(payload: list[object]) -> bytes:
        for item in payload:
            if isinstance(item, tuple) and len(item) > 1 and isinstance(item[1], bytes):
                return item[1]
        raise EmailClientError("Unable to parse message payload from IMAP response.")

    @staticmethod
    def _decode_header(value: str) -> str:
        return str(make_header(decode_header(value))).strip()

    @staticmethod
    def _extract_preview(message) -> str:
        part = message.get_body(preferencelist=("plain", "html")) if message.is_multipart() else message
        if part is None:
            return ""
        try:
            content = part.get_content()
        except (LookupError, AttributeError):
            payload = part.get_payload(decode=True)
            if isinstance(payload, bytes):
                charset = part.get_content_charset() or "utf-8"
                content = payload.decode(charset, errors="replace")
            else:
                content = str(payload or "")
        if part.get_content_subtype() == "html":
            content = re.sub(r"<[^>]+>", " ", content)
            content = unescape(content)
        normalized = " ".join(content.split())
        return normalized[:200]

