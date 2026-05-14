from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class EmailMessageSummary:
    uid: str
    subject: str
    sender: str
    date: str
    preview: str


@dataclass(frozen=True)
class TriageDecision:
    uid: str
    subject: str
    sender: str
    date: str
    preview: str
    score: int
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "TriageDecision":
        return cls(
            uid=str(payload["uid"]),
            subject=str(payload["subject"]),
            sender=str(payload["sender"]),
            date=str(payload["date"]),
            preview=str(payload["preview"]),
            score=int(payload["score"]),
            reasons=tuple(str(item) for item in payload["reasons"]),
        )


@dataclass(frozen=True)
class ReviewPlan:
    generated_at: str
    mailbox: str
    scanned_count: int
    delete_candidates: tuple[TriageDecision, ...]
    confirmation_token: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "mailbox": self.mailbox,
            "scanned_count": self.scanned_count,
            "delete_candidates": [candidate.to_dict() for candidate in self.delete_candidates],
            "confirmation_token": self.confirmation_token,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ReviewPlan":
        raw_candidates = payload.get("delete_candidates", [])
        return cls(
            generated_at=str(payload["generated_at"]),
            mailbox=str(payload["mailbox"]),
            scanned_count=int(payload["scanned_count"]),
            delete_candidates=tuple(
                TriageDecision.from_dict(candidate) for candidate in raw_candidates
            ),
            confirmation_token=str(payload.get("confirmation_token", "")),
        )

