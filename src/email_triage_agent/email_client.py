from __future__ import annotations

from email_triage_agent.config import EmailTriageConfig
from email_triage_agent.models import EmailMessageSummary

GMAIL_MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"


class EmailClientError(RuntimeError):
    """Raised when mailbox operations fail."""


def run_gmail_oauth_flow(config: EmailTriageConfig) -> str:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise EmailClientError(
            "Gmail OAuth dependencies are not installed. Run `pip install -e .` first."
        ) from exc

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": config.gmail_client_id,
                "client_secret": config.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        },
        scopes=[GMAIL_MODIFY_SCOPE],
    )
    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        open_browser=True,
        authorization_prompt_message=(
            "Open this URL in your browser to authorize Gmail access:\n{url}\n"
        ),
        success_message="Authorization complete. Return to the terminal.",
        access_type="offline",
        prompt="consent",
    )
    refresh_token = credentials.refresh_token or ""
    if not refresh_token:
        raise EmailClientError(
            "OAuth succeeded but no refresh token was returned. Revoke the app and try again."
        )
    return refresh_token


class GmailEmailClient:
    def __init__(self, config: EmailTriageConfig) -> None:
        self._config = config

    def fetch_recent_messages(self) -> list[EmailMessageSummary]:
        try:
            service = self._build_service()
            mailbox_label = self._resolve_label_id(service, self._config.mailbox)
            response = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=[mailbox_label],
                    maxResults=self._config.max_messages,
                )
                .execute()
            )
            messages: list[EmailMessageSummary] = []
            for message_ref in response.get("messages", []):
                payload = (
                    service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=message_ref["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    )
                    .execute()
                )
                messages.append(self._normalize_message(payload))
            return messages
        except Exception as exc:
            raise EmailClientError(f"Unable to fetch Gmail messages: {exc}") from exc

    def trash_messages(self, uids: list[str]) -> int:
        if not uids:
            return 0
        try:
            service = self._build_service()
            for uid in uids:
                service.users().messages().trash(userId="me", id=uid).execute()
        except Exception as exc:
            raise EmailClientError(f"Unable to move Gmail messages to trash: {exc}") from exc
        return len(uids)

    def _build_service(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise EmailClientError(
                "Gmail dependencies are not installed. Run `pip install -e .` first."
            ) from exc

        credentials = Credentials(
            token=None,
            refresh_token=self._config.gmail_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self._config.gmail_client_id,
            client_secret=self._config.gmail_client_secret,
            scopes=[GMAIL_MODIFY_SCOPE],
        )
        credentials.refresh(Request())
        return build("gmail", "v1", credentials=credentials, cache_discovery=False)

    @staticmethod
    def _resolve_label_id(service, mailbox: str) -> str:
        labels = (
            service.users()
            .labels()
            .list(userId="me")
            .execute()
            .get("labels", [])
        )
        normalized_mailbox = mailbox.strip().lower()
        for label in labels:
            label_id = str(label.get("id", ""))
            label_name = str(label.get("name", ""))
            if normalized_mailbox in {label_id.lower(), label_name.lower()}:
                return label_id
        raise EmailClientError(f"Unable to find Gmail label `{mailbox}`.")

    @staticmethod
    def _normalize_message(payload: dict[str, object]) -> EmailMessageSummary:
        headers = {
            str(header["name"]).lower(): str(header["value"])
            for header in payload.get("payload", {}).get("headers", [])
        }
        labels = tuple(sorted(str(label) for label in payload.get("labelIds", [])))
        return EmailMessageSummary(
            uid=str(payload["id"]),
            subject=headers.get("subject", "(no subject)"),
            sender=headers.get("from", "(unknown sender)"),
            date=headers.get("date", ""),
            snippet=str(payload.get("snippet", "")),
            labels=labels,
            is_unread="UNREAD" in labels,
        )
