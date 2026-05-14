from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from email_triage_agent.models import ReviewPlan


def build_confirmation_token(plan: ReviewPlan) -> str:
    payload = plan.to_dict()
    payload["confirmation_token"] = ""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()[:12]


def save_review_plan(plan: ReviewPlan, path: Path) -> ReviewPlan:
    path.parent.mkdir(parents=True, exist_ok=True)
    finalized = replace(plan, confirmation_token=build_confirmation_token(plan))
    path.write_text(json.dumps(finalized.to_dict(), indent=2), encoding="utf-8")
    return finalized


def load_review_plan(path: Path) -> ReviewPlan:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ReviewPlan.from_dict(payload)


def validate_review_plan(plan: ReviewPlan) -> bool:
    return bool(plan.confirmation_token) and plan.confirmation_token == build_confirmation_token(plan)


def format_review_plan(plan: ReviewPlan) -> str:
    keep_count = sum(1 for decision in plan.decisions if decision.decision == "keep")
    review_count = sum(1 for decision in plan.decisions if decision.decision == "review")
    lines = [
        f"Generated: {plan.generated_at}",
        f"Mailbox: {plan.mailbox}",
        f"Scanned messages: {plan.scanned_count}",
        f"Keep decisions: {keep_count}",
        f"Review decisions: {review_count}",
        f"Trash candidates: {len(plan.trash_candidates)}",
        f"Confirmation token: {plan.confirmation_token or '(missing)'}",
    ]
    if plan.decisions:
        lines.append("")
        lines.append("Decisions:")
        for candidate in plan.decisions:
            labels = ", ".join(candidate.labels) if candidate.labels else "(none)"
            lines.append(
                f"- [{candidate.decision}] UID {candidate.uid}: {candidate.subject} "
                f"| {candidate.sender} | unread={'yes' if candidate.is_unread else 'no'} "
                f"| labels={labels} | reasons={', '.join(candidate.reasons)}"
            )
    return "\n".join(lines)
