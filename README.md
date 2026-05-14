# Email Triage Agent

A practical MVP for reviewing potentially irrelevant emails before any destructive action is taken.

## Features

- Connects to an IMAP mailbox using environment variables
- Scores likely low-value email (newsletters, promos, automated mail)
- Generates a review plan instead of deleting immediately
- Requires an explicit confirmation token before deletion
- Uses only the Python standard library

## Project structure

```text
.
├── .env.example
├── pyproject.toml
├── src/email_triage_agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── email_client.py
│   ├── models.py
│   ├── review.py
│   └── triage.py
└── tests/
```

## Configuration

Copy `.env.example` to `.env` or export the variables in your shell.

| Variable | Required | Description |
| --- | --- | --- |
| `EMAIL_TRIAGE_IMAP_HOST` | Yes | IMAP server hostname |
| `EMAIL_TRIAGE_IMAP_PORT` | No | IMAP SSL port, defaults to `993` |
| `EMAIL_TRIAGE_EMAIL_ADDRESS` | Yes | Mailbox username/login |
| `EMAIL_TRIAGE_EMAIL_PASSWORD` | Yes | App password or mailbox token |
| `EMAIL_TRIAGE_MAILBOX` | No | Mailbox/folder to scan, defaults to `INBOX` |
| `EMAIL_TRIAGE_MAX_MESSAGES` | No | Number of recent messages to inspect, defaults to `50` |
| `EMAIL_TRIAGE_IRRELEVANT_SENDERS` | No | Comma-separated sender rules to strongly down-rank |
| `EMAIL_TRIAGE_IRRELEVANT_KEYWORDS` | No | Comma-separated subject/body keywords to down-rank |
| `EMAIL_TRIAGE_PROTECTED_SENDERS` | No | Comma-separated exact sender email allowlist (never triaged/deleted) |
| `EMAIL_TRIAGE_PROTECTED_DOMAINS` | No | Comma-separated sender domain allowlist (never triaged/deleted) |

## Quick start

```bash
cd email-triage-agent
python -m venv .venv
. .venv/bin/activate
pip install -e .
cp .env.example .env
```

Export the variables from `.env` in your shell, then run:

```bash
PYTHONPATH=src python -m email_triage_agent triage
```

That command creates a JSON review plan under `review-plans/`. Review it locally:

```bash
PYTHONPATH=src python -m email_triage_agent show-plan --plan-path review-plans/review-plan-YYYYMMDDTHHMMSSZ.json
```

Only after reviewing the plan should you apply it:

```bash
PYTHONPATH=src python -m email_triage_agent apply-review \
  --plan-path review-plans/review-plan-YYYYMMDDTHHMMSSZ.json \
  --confirm-token <token-from-reviewed-plan> \
  --confirm-delete
```

## Safety model

- No hardcoded credentials or secrets
- IMAP access is read-only during triage
- Deletion is a separate command
- Deletion requires both the saved review plan and its confirmation token
- The review token is recomputed from plan contents to detect tampering
- Protected senders/domains are always skipped during triage and apply-review

## Running tests

```bash
cd email-triage-agent
PYTHONPATH=src python -m unittest discover -s tests -p 'test*.py'
```
