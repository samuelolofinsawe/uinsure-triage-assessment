"""
ai_triage.py — Claude API integration for ticket triage

Sends batches of tickets to Claude and returns structured triage results.
Batching reduces API round-trips (49 tickets → 5 calls at batch_size=10).

Model: claude-haiku-4-5-20251001 — fast and cost-effective for structured
classification tasks. Upgrade to claude-sonnet-4-5-20250929 for higher
accuracy if needed.
"""

import json
import os
import re
import urllib.request
import urllib.error
import pandas as pd


SYSTEM_PROMPT = """You are a support triage assistant for an AI platform company.
You will receive a batch of support tickets in JSON format.
For EACH ticket, return a JSON array where each element has:
{
  "ticket_id": "<id>",
  "suggested_priority": "Critical|High|Medium|Low",
  "suggested_category": "<category>",
  "suggested_subcategory": "<subcategory>",
  "explanation": "<2-3 sentence human-readable summary a support manager can act on immediately>"
}

Priority guidance:
- Critical: data loss, security/safety issues, legal exposure, customer threatening cancellation with legal action
- High: production blocked, recurring issue (3+ times), customer explicitly escalating
- Medium: significant inconvenience but workaround exists, second occurrence
- Low: billing queries, onboarding questions, single first-time reports

Return ONLY a valid JSON array. No preamble, no markdown fences."""


def triage_batch(tickets: list[dict]) -> list[dict]:
    """Send one batch of tickets to Claude and return structured triage results."""
    user_msg = json.dumps(tickets, default=str, indent=2)

    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_msg}],
    }).encode("utf-8")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set — create a .env file with your key. "
            "Get one at: https://console.anthropic.com/settings/keys"
        )

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"Anthropic API returned HTTP {e.code}. "
            "Check your API key is valid and your account has credits."
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Could not reach Anthropic API: {e.reason}. "
            "Check your internet connection and try again."
        ) from e
    except TimeoutError:
        raise RuntimeError(
            "Request to Anthropic API timed out after 60 seconds. "
            "Check your internet connection and try again."
        )

    raw = data["content"][0]["text"].strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"```\s*$", "", raw).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(
            "Claude returned an unexpected response format. "
            "This is rare — try running again."
        )


def triage_all(df: pd.DataFrame, batch_size: int = 10) -> list[dict]:
    """Triage all tickets in batches, printing progress."""
    records = df[[
        "ticket_id", "date_submitted", "customer_id",
        "category", "subcategory", "priority", "status",
        "ticket_description", "satisfaction_score",
    ]].to_dict(orient="records")

    results = []
    for i in range(0, len(records), batch_size):
        batch = records[i: i + batch_size]
        end = min(i + batch_size, len(records))
        print(f"  Triaging tickets {i + 1}–{end}…", flush=True)
        results.extend(triage_batch(batch))

    return results