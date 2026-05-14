from __future__ import annotations

import argparse
from pathlib import Path

from email_triage_agent.config import EmailTriageConfig
from email_triage_agent.email_client import GmailEmailClient, run_gmail_oauth_flow
from email_triage_agent.review import (
    format_review_plan,
    load_review_plan,
    save_review_plan,
    validate_review_plan,
)
from email_triage_agent.triage import build_review_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review-first email triage starter.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth_parser = subparsers.add_parser(
        "gmail-auth", help="Run a local Gmail OAuth flow and save a refresh token to an env file."
    )
    auth_parser.add_argument(
        "--env-path",
        type=Path,
        default=Path(".env"),
        help="Path to the env file to update with EMAIL_TRIAGE_GMAIL_REFRESH_TOKEN.",
    )
    auth_parser.set_defaults(handler=handle_gmail_auth)

    triage_parser = subparsers.add_parser(
        "triage", help="Fetch recent Gmail messages and generate a local review plan."
    )
    triage_parser.add_argument("--plan-path", type=Path, help="Optional output path for the review plan.")
    triage_parser.set_defaults(handler=handle_triage)

    show_plan_parser = subparsers.add_parser("show-plan", help="Print a saved review plan.")
    show_plan_parser.add_argument("--plan-path", type=Path, required=True, help="Path to a saved review plan.")
    show_plan_parser.set_defaults(handler=handle_show_plan)

    apply_parser = subparsers.add_parser(
        "apply-review", help="Apply a reviewed deletion plan to the mailbox."
    )
    apply_parser.add_argument("--plan-path", type=Path, required=True, help="Path to a reviewed plan.")
    apply_parser.add_argument(
        "--confirm-token",
        required=True,
        help="Confirmation token copied from the reviewed plan file.",
    )
    apply_parser.add_argument(
        "--confirm-trash",
        "--confirm-delete",
        dest="confirm_trash",
        action="store_true",
        help="Required safety flag before any message is moved to trash.",
    )
    apply_parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move trash candidates to Gmail trash. Defaults to dry-run mode.",
    )
    apply_parser.set_defaults(handler=handle_apply_review)

    return parser


def handle_gmail_auth(args: argparse.Namespace) -> int:
    config = EmailTriageConfig.from_env(require_refresh_token=False)
    refresh_token = run_gmail_oauth_flow(config)
    _upsert_env_value(args.env_path, "EMAIL_TRIAGE_GMAIL_REFRESH_TOKEN", refresh_token)
    print("Gmail OAuth completed.")
    print(f"Saved EMAIL_TRIAGE_GMAIL_REFRESH_TOKEN to {args.env_path}.")
    return 0


def handle_triage(args: argparse.Namespace) -> int:
    config = EmailTriageConfig.from_env()
    client = GmailEmailClient(config)
    messages = client.fetch_recent_messages()
    plan_path = args.plan_path or _default_plan_path()
    saved_plan = save_review_plan(build_review_plan(messages, config), plan_path)
    print(format_review_plan(saved_plan))
    print("")
    print("Review the saved plan before deleting anything:")
    print(f"  PYTHONPATH=src python -m email_triage_agent show-plan --plan-path {plan_path}")
    print("When ready, re-run apply-review with --confirm-token, --confirm-trash, and --apply.")
    return 0


def handle_show_plan(args: argparse.Namespace) -> int:
    plan = load_review_plan(args.plan_path)
    print(format_review_plan(plan))
    return 0


def handle_apply_review(args: argparse.Namespace) -> int:
    if not args.confirm_trash:
        raise SystemExit("Trashing requires --confirm-trash after reviewing the plan.")

    plan = load_review_plan(args.plan_path)
    if not validate_review_plan(plan):
        raise SystemExit("The review plan token is invalid. Re-run triage and review a fresh plan.")
    if args.confirm_token != plan.confirmation_token:
        raise SystemExit("The supplied confirmation token does not match the reviewed plan.")
    if not plan.trash_candidates:
        print("No trash candidates found in the review plan. Nothing to do.")
        return 0

    if not args.apply:
        print(
            f"Dry-run: would move {_format_message_count(len(plan.trash_candidates))} to Gmail trash."
        )
        for candidate in plan.trash_candidates:
            print(f"  - UID {candidate.uid}: {candidate.subject} | {candidate.sender}")
        print("Re-run with --apply once you are ready to move these messages to trash.")
        return 0

    config = EmailTriageConfig.from_env()
    client = GmailEmailClient(config)
    trashed = client.trash_messages([candidate.uid for candidate in plan.trash_candidates])
    print(f"Moved {_format_message_count(trashed)} to Gmail trash from {config.mailbox}.")
    return 0


def _default_plan_path() -> Path:
    from datetime import UTC, datetime

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path("review-plans") / f"review-plan-{timestamp}.json"


def _format_message_count(count: int) -> str:
    suffix = "message" if count == 1 else "messages"
    return f"{count} {suffix}"


def _upsert_env_value(path: Path, key: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_lines: list[str] = []
    if path.exists():
        existing_lines = path.read_text(encoding="utf-8").splitlines()

    updated_lines: list[str] = []
    replaced = False
    for line in existing_lines:
        if line.startswith(f"{key}="):
            updated_lines.append(f"{key}={value}")
            replaced = True
        else:
            updated_lines.append(line)
    if not replaced:
        updated_lines.append(f"{key}={value}")

    path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)
