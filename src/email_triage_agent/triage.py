from __future__ import annotations

from email.utils import parseaddr
from datetime import UTC, datetime

from email_triage_agent.config import EmailTriageConfig
from email_triage_agent.models import EmailMessageSummary, ReviewPlan, TriageDecision

DEFAULT_IRRELEVANT_KEYWORDS = (
    "unsubscribe",
    "newsletter",
    "sale",
    "discount",
    "offer",
    "promo",
    "promotion",
)
AUTOMATED_SENDER_MARKERS = ("noreply", "no-reply", "newsletter", "mailer-daemon", "donotreply")
LOW_VALUE_LABELS = ("CATEGORY_FORUMS", "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES")


def score_message(
    message: EmailMessageSummary, config: EmailTriageConfig
) -> tuple[int, tuple[str, ...]]:
    score = 0
    reasons: list[str] = []
    sender = message.sender.lower()
    text = f"{message.subject}\n{message.preview}".lower()

    if any(marker in sender for marker in AUTOMATED_SENDER_MARKERS):
        score += 1
        reasons.append("Sender looks automated")

    if any(rule in sender for rule in config.irrelevant_senders):
        score += 2
        reasons.append("Sender matched configured irrelevant sender rule")

    label_matches = sorted({label for label in message.labels if label in LOW_VALUE_LABELS})
    if label_matches:
        score += 1
        reasons.append(f"Gmail labels suggest low-value content: {', '.join(label_matches)}")

    keyword_matches = sorted(
        {
            keyword
            for keyword in (*DEFAULT_IRRELEVANT_KEYWORDS, *config.irrelevant_keywords)
            if keyword and keyword in text
        }
    )
    if keyword_matches:
        score += min(2, len(keyword_matches))
        reasons.append(f"Matched keywords: {', '.join(keyword_matches[:3])}")

    return score, tuple(reasons)


def classify_message(message: EmailMessageSummary, config: EmailTriageConfig) -> TriageDecision:
    sender_address = parseaddr(message.sender)[1].lower()
    sender_domain = sender_address.partition("@")[2]

    reasons: tuple[str, ...]
    decision = "keep"
    if sender_address and sender_address in config.allowlist_senders:
        reasons = ("Sender is allowlisted",)
    elif sender_domain and sender_domain in config.allowlist_domains:
        reasons = ("Sender domain is allowlisted",)
    elif message.is_unread and config.protect_unread:
        reasons = ("Unread protection is enabled",)
    else:
        score, reasons = score_message(message, config)
        if score >= 3:
            decision = "trash_candidate"
        elif score >= 1:
            decision = "review"
        if not reasons:
            reasons = ("No low-value signals detected",)

    return TriageDecision(
        uid=message.uid,
        subject=message.subject,
        sender=message.sender,
        date=message.date,
        snippet=message.snippet,
        labels=message.labels,
        is_unread=message.is_unread,
        decision=decision,
        reasons=reasons,
    )


def build_review_plan(
    messages: list[EmailMessageSummary], config: EmailTriageConfig
) -> ReviewPlan:
    decisions = [classify_message(message, config) for message in messages]

    return ReviewPlan(
        generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        mailbox=config.mailbox,
        scanned_count=len(messages),
        decisions=tuple(decisions),
    )
