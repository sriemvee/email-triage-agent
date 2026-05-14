from __future__ import annotations

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


def build_review_plan(
    messages: list[EmailMessageSummary], config: EmailTriageConfig
) -> ReviewPlan:
    candidates: list[TriageDecision] = []
    for message in messages:
        score, reasons = score_message(message, config)
        if score < 2:
            continue
        candidates.append(
            TriageDecision(
                uid=message.uid,
                subject=message.subject,
                sender=message.sender,
                date=message.date,
                preview=message.preview,
                score=score,
                reasons=reasons,
            )
        )

    return ReviewPlan(
        generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        mailbox=config.mailbox,
        scanned_count=len(messages),
        delete_candidates=tuple(candidates),
    )

