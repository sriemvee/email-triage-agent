# Email Triage Agent

A practical Gmail-focused triage agent for reviewing potentially irrelevant emails before any destructive action is taken.

## Features

- Connects to Gmail using OAuth environment variables only
- Fetches the latest N messages and normalizes sender, subject, snippet, labels, unread state, and date
- Classifies each message as `keep`, `review`, or `trash_candidate` with explicit reasons
- Protects unread mail and sender/domain allowlists by default
- Generates a local review plan before any mailbox changes
- Uses dry-run by default and moves messages to Gmail trash instead of permanently deleting them

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

## Gmail OAuth setup

Copy `.env.example` to `.env` or export the variables in your shell.

1. In Google Cloud, create or reuse a project and enable the **Gmail API**.
2. Configure an OAuth consent screen for your account.
3. Create an **OAuth client ID** for a desktop app.
4. Export the client ID and client secret:

   ```bash
   export EMAIL_TRIAGE_GMAIL_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
   export EMAIL_TRIAGE_GMAIL_CLIENT_SECRET=your-google-oauth-client-secret
   ```

5. Run the local OAuth helper to generate a refresh token:

   ```bash
   PYTHONPATH=src python -m email_triage_agent gmail-auth
   ```

   By default, the command updates `.env` in place. You can target a different file with `--env-path /path/to/.env`.

6. Confirm that your env file now includes the refresh token:

   ```bash
   EMAIL_TRIAGE_GMAIL_REFRESH_TOKEN=your-refresh-token
   ```

All OAuth values are supplied through environment variables only. Do not hardcode credentials into the repository.

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `EMAIL_TRIAGE_GMAIL_CLIENT_ID` | Yes | Google OAuth client ID for a desktop app |
| `EMAIL_TRIAGE_GMAIL_CLIENT_SECRET` | Yes | Google OAuth client secret |
| `EMAIL_TRIAGE_GMAIL_REFRESH_TOKEN` | Yes for `triage`/`apply-review` | Refresh token returned by `gmail-auth` |
| `EMAIL_TRIAGE_MAILBOX` | No | Gmail label to scan, defaults to `INBOX` |
| `EMAIL_TRIAGE_MAX_MESSAGES` | No | Maximum number of recent messages to inspect, defaults to `50` |
| `EMAIL_TRIAGE_ALLOWLIST_SENDERS` | No | Comma-separated sender email addresses that should always be kept |
| `EMAIL_TRIAGE_ALLOWLIST_DOMAINS` | No | Comma-separated sender domains that should always be kept |
| `EMAIL_TRIAGE_PROTECT_UNREAD` | No | Protect unread messages from cleanup, defaults to `true` |
| `EMAIL_TRIAGE_IRRELEVANT_SENDERS` | No | Comma-separated sender rules to strongly down-rank |
| `EMAIL_TRIAGE_IRRELEVANT_KEYWORDS` | No | Comma-separated subject/snippet keywords to down-rank |

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

That command fetches the latest Gmail messages for the configured label and creates a JSON review plan under `review-plans/`. Each decision includes a reason and is classified as `keep`, `review`, or `trash_candidate`.

Review it locally:

```bash
PYTHONPATH=src python -m email_triage_agent show-plan --plan-path review-plans/review-plan-YYYYMMDDTHHMMSSZ.json
```

Only after reviewing the plan should you apply it. `apply-review` is a dry-run unless you also pass `--apply`:

```bash
PYTHONPATH=src python -m email_triage_agent apply-review \
  --plan-path review-plans/review-plan-YYYYMMDDTHHMMSSZ.json \
  --confirm-token <token-from-reviewed-plan> \
  --confirm-trash \
  --apply
```

## Safety model

- No hardcoded credentials or secrets
- Triaging only reads Gmail metadata and snippets
- Unread messages are protected by default
- Allowlisted senders and domains are protected by default
- Cleanup is a separate command and defaults to dry-run
- Cleanup requires both the saved review plan and its confirmation token
- The review token is recomputed from plan contents to detect tampering
- Cleanup moves messages to Gmail trash and never permanently deletes them

## Running tests

```bash
cd email-triage-agent
PYTHONPATH=src python -m unittest discover -s tests -p 'test*.py'
```
