from __future__ import annotations

import argparse
from pathlib import Path

from email_triage_agent.config import EmailTriageConfig
from email_triage_agent.email_client import ImapEmailClient
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

    triage_parser = subparsers.add_parser(
        "triage", help="Connect to IMAP and generate a local review plan."
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
        "--confirm-delete",
        action="store_true",
        help="Required safety flag before any message is deleted.",
    )
    apply_parser.set_defaults(handler=handle_apply_review)

    return parser


def handle_triage(args: argparse.Namespace) -> int:
    config = EmailTriageConfig.from_env()
    client = ImapEmailClient(config)
    messages = client.fetch_recent_messages()
    plan_path = args.plan_path or _default_plan_path()
    saved_plan = save_review_plan(build_review_plan(messages, config), plan_path)
    print(format_review_plan(saved_plan))
    print("")
    print("Review the saved plan before deleting anything:")
    print(f"  PYTHONPATH=src python -m email_triage_agent show-plan --plan-path {plan_path}")
    print("When ready, re-run with --confirm-token and --confirm-delete.")
    return 0


def handle_show_plan(args: argparse.Namespace) -> int:
    plan = load_review_plan(args.plan_path)
    print(format_review_plan(plan))
    return 0


def handle_apply_review(args: argparse.Namespace) -> int:
    if not args.confirm_delete:
        raise SystemExit("Deletion requires --confirm-delete after reviewing the plan.")

    plan = load_review_plan(args.plan_path)
    if not validate_review_plan(plan):
        raise SystemExit("The review plan token is invalid. Re-run triage and review a fresh plan.")
    if args.confirm_token != plan.confirmation_token:
        raise SystemExit("The supplied confirmation token does not match the reviewed plan.")
    if not plan.delete_candidates:
        print("No delete candidates found in the review plan. Nothing to do.")
        return 0

    config = EmailTriageConfig.from_env()
    client = ImapEmailClient(config)
    deleted = client.delete_messages([candidate.uid for candidate in plan.delete_candidates])
    print(f"Deleted {deleted} messages from {config.mailbox}.")
    return 0


def _default_plan_path() -> Path:
    from datetime import UTC, datetime

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path("review-plans") / f"review-plan-{timestamp}.json"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)

