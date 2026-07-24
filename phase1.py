"""
Phase 1 — Data Foundation
Pulls one YC batch (noisy, uncategorized tech companies), filters out dead
companies for free, and sends {company_name, website_url} to a Clay webhook.

Usage:
  python phase1.py --csv companies.csv                                     # free path: CSV for Clay import
  python phase1.py --webhook https://api.clay.com/v3/sources/webhook/...   # paid path: Clay webhook
  python phase1.py --dry-run --limit 5                                     # test on 5 rows, no output

Requires: pip install requests tenacity
"""

import argparse
import csv
import logging
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

BATCH_URL = "https://yc-oss.github.io/api/batches/{batch}.json"
SENT_LOG = Path("sent_domains.txt")  # dedupe across re-runs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("phase1.log")],
)
log = logging.getLogger("phase1")


def fetch_batch(batch: str) -> list[dict]:
    url = BATCH_URL.format(batch=batch)
    log.info("Fetching %s", url)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def is_live(url: str) -> bool:
    """Free liveness check: don't pay Clay credits to analyze dead websites."""
    try:
        r = requests.head(url, timeout=8, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 405:  # some servers reject HEAD; try GET
            r = requests.get(url, timeout=8, allow_redirects=True, stream=True,
                             headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code < 400
    except requests.RequestException:
        return False


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, max=20))
def send_to_clay(webhook: str, payload: dict) -> None:
    r = requests.post(webhook, json=payload, timeout=15)
    r.raise_for_status()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="winter-2026", help="YC batch slug, e.g. winter-2026")
    p.add_argument("--limit", type=int, default=0, help="max companies to send (0 = all)")
    p.add_argument("--webhook", default="", help="Clay inbound webhook URL (paid plans)")
    p.add_argument("--csv", default="", help="write results to this CSV file (free plan path)")
    p.add_argument("--dry-run", action="store_true", help="print instead of sending/writing")
    args = p.parse_args()

    if not args.dry_run and not args.webhook and not args.csv:
        sys.exit("Provide --webhook URL or --csv file, or use --dry-run.")

    already_sent = set(SENT_LOG.read_text().split()) if SENT_LOG.exists() else set()

    companies = fetch_batch(args.batch)
    raw = len(companies)

    # Free filters: active companies with a real website only
    companies = [c for c in companies if c.get("status") == "Active" and c.get("website")]
    active = len(companies)

    rows_for_csv: list[dict] = []
    sent = skipped_dead = skipped_dupe = 0
    for c in companies:
        if args.limit and sent >= args.limit:
            break
        name, website = c["name"], c["website"]
        dom = domain_of(website)

        if dom in already_sent:
            skipped_dupe += 1
            continue
        if not is_live(website):
            log.info("DEAD  %-25s %s", name, website)
            skipped_dead += 1
            continue

        payload = {"company_name": name, "website_url": website}
        if args.dry_run:
            log.info("DRY   %s", payload)
        elif args.csv:
            rows_for_csv.append(payload)
            log.info("CSV   %-25s %s", name, website)
        else:
            try:
                send_to_clay(args.webhook, payload)
                log.info("SENT  %-25s %s", name, website)
            except Exception as e:
                log.error("FAIL  %-25s %s (%s)", name, website, e)
                continue
        with SENT_LOG.open("a") as f:
            f.write(dom + "\n")
        already_sent.add(dom)
        sent += 1
        time.sleep(0.3)  # be polite

    if args.csv and rows_for_csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["company_name", "website_url"])
            w.writeheader()
            w.writerows(rows_for_csv)
        log.info("Wrote %d rows to %s", len(rows_for_csv), args.csv)

    log.info("=" * 50)
    log.info("FUNNEL: %d raw -> %d active -> %d live & sent "
             "(%d dead skipped, %d duplicates skipped)",
             raw, active, sent, skipped_dead, skipped_dupe)


if __name__ == "__main__":
    main()
