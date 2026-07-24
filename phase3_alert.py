"""
Phase 3 — Activation
Reads the enriched table exported from Clay (CSV), filters to top-scoring
accounts, and posts a formatted SDR alert to Slack via incoming webhook.

Usage:
  export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
  python phase3_alert.py --csv clay_export.csv --min-score 8

Requires: pip install requests tenacity
"""

import argparse
import csv
import os
import sys

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, max=20))
def post_to_slack(webhook: str, text: str) -> None:
    r = requests.post(webhook, json={"text": text}, timeout=15)
    r.raise_for_status()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True, help="CSV exported from the Clay table")
    p.add_argument("--min-score", type=int, default=8)
    args = p.parse_args()

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        sys.exit("Set SLACK_WEBHOOK_URL environment variable first.")

    with open(args.csv, newline="") as f:
        rows = list(csv.DictReader(f))

    qualified = [
        r for r in rows
        if r.get("Lead Score") and int(float(r["Lead Score"])) >= args.min_score
    ]
    qualified.sort(key=lambda r: -int(float(r["Lead Score"])))

    if not qualified:
        print("No accounts above threshold — nothing to send.")
        return

    lines = [f"🎯 *GTM Pipeline — {len(qualified)} qualified accounts* "
             f"(score ≥ {args.min_score}, from {len(rows)} scanned)\n"]
    for r in qualified:
        pms = r.get("Rolecount") or "0"
        lines.append(
            f"*{r['company_name']}* — {int(float(r['Lead Score']))} pts · "
            f"{pms} PM(s) · {r['website_url']}"
        )
    lines.append("\n_Non-qualified rows filtered automatically — no rep time wasted._")

    post_to_slack(webhook, "\n".join(lines))
    print(f"Sent {len(qualified)} accounts to Slack.")


if __name__ == "__main__":
    main()
