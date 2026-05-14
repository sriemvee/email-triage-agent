from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class EmailMessageSummary:
    uid: str
    subject: str
    sender: str
    date: str
    snippet: str
    labels: tuple[str, ...] = ()
    is_unread: bool = False

    @property
    def preview(self) -> str:
        return self.snippet


@dataclass(frozen=True)
class TriageDecision:
    uid: str
    subject: str
    sender: str
    date: str
    snippet: str
    labels: tuple[str, ...]
    is_unread: bool
    decision: str
    reasons: tuple[str, ...]

    @property
    def preview(self) -> str:
        return self.snippet

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "TriageDecision":
        return cls(
            uid=str(payload["uid"]),
            subject=str(payload["subject"]),
            sender=str(payload["sender"]),
            date=str(payload["date"]),
            snippet=str(payload.get("snippet", payload.get("preview", ""))),
            labels=tuple(str(item) for item in payload.get("labels", [])),
            is_unread=bool(payload.get("is_unread", False)),
            decision=str(payload.get("decision", "trash_candidate")),
            reasons=tuple(str(item) for item in payload["reasons"]),
        )


@dataclass(frozen=True)
class ReviewPlan:
    generated_at: str
    mailbox: str
    scanned_count: int
    decisions: tuple[TriageDecision, ...]
    confirmation_token: str = ""

    @property
    def delete_candidates(self) -> tuple[TriageDecision, ...]:
        return self.trash_candidates

    @property
    def trash_candidates(self) -> tuple[TriageDecision, ...]:
        return tuple(
            decision for decision in self.decisions if decision.decision == "trash_candidate"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "mailbox": self.mailbox,
            "scanned_count": self.scanned_count,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "confirmation_token": self.confirmation_token,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ReviewPlan":
        raw_candidates = payload.get("decisions", payload.get("delete_candidates", []))
        return cls(
            generated_at=str(payload["generated_at"]),
            mailbox=str(payload["mailbox"]),
            scanned_count=int(payload["scanned_count"]),
            decisions=tuple(
                TriageDecision.from_dict(candidate) for candidate in raw_candidates
            ),
            confirmation_token=str(payload.get("confirmation_token", "")),
        )
