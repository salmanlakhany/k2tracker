#!/usr/bin/env python3
"""
Chrono24 Patek Philippe Nautilus tracker.

Fetches the "newest" listings for the Nautilus family (all references)
from Chrono24 and writes them to docs/data.json for the static dashboard.

Runs once per hour via GitHub Actions (see .github/workflows/scrape.yml).

Notes:
- Chrono24 has no public API, so this parses their listing page HTML.
  Their markup can change without notice; if listings stop appearing,
  the SELECTORS/PATTERNS below are the first thing to check.
- Kept to a single request per run (a couple of pages at most) to be a
  polite, low-volume, low-frequency client.
"""

import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from html import unescape

BASE_URL = "https://www.chrono24.com/patekphilippe/nautilus--mod106.htm"
# sortorder=5 = "Newest" on Chrono24's own site as of July 2026.
# If listings look stale/wrong after Chrono24 changes their site,
# open the Nautilus page in a browser, click "Newest", and copy the
# sortorder value from the resulting URL here.
PAGES = [
    f"{BASE_URL}?sortorder=5&pageSize=120&showpage=1",
    f"{BASE_URL}?sortorder=5&pageSize=120&showpage=2",
]

OUTPUT_PATH = "docs/data.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Matches a Chrono24 listing detail link, e.g.:
#   /patekphilippe/nautilus-2025-new-...--id39248826.htm
LISTING_LINK_RE = re.compile(
    r'href="(/patekphilippe/[a-z0-9\-]+--id(\d+)\.htm)"', re.IGNORECASE
)

# Matches a price like $275,000 or $1,550,000 (USD only, simplest case)
PRICE_RE = re.compile(r"\$[\d,]{3,}")

TITLE_HINT_RE = re.compile(r">([^<>]{5,120})</a>")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_listings(html: str):
    """
    Best-effort parse of listing cards. Chrono24 repeats each listing's
    link/title several times per card (thumbnail + title + price block),
    so we de-duplicate by listing id and keep the richest text we saw
    for title/price.
    """
    listings = {}

    for match in LISTING_LINK_RE.finditer(html):
        path, listing_id = match.group(1), match.group(2)
        url = "https://www.chrono24.com" + path

        # Look at a window of text after this link to find a title and price
        window = html[match.end(): match.end() + 800]

        price_match = PRICE_RE.search(window)
        price = price_match.group(0) if price_match else None

        title_match = TITLE_HINT_RE.search(html[max(0, match.start() - 400): match.start()])
        title = None
        if title_match:
            title = unescape(re.sub(r"\s+", " ", title_match.group(1))).strip()

        existing = listings.get(listing_id)
        if existing is None:
            listings[listing_id] = {
                "id": listing_id,
                "url": url,
                "title": title,
                "price": price,
            }
        else:
            if not existing.get("title") and title:
                existing["title"] = title
            if not existing.get("price") and price:
                existing["price"] = price

    # Drop entries where we never found a usable title (likely noise, e.g.
    # nav links that happen to match the URL pattern)
    return [v for v in listings.values() if v["title"]]


def main():
    all_listings = {}
    for page_url in PAGES:
        try:
            html = fetch(page_url)
        except Exception as exc:
            print(f"WARNING: failed to fetch {page_url}: {exc}", file=sys.stderr)
            continue

        for item in parse_listings(html):
            all_listings[item["id"]] = item

        time.sleep(2)  # small courtesy delay between the (at most 2) requests

    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "count": len(all_listings),
        "listings": list(all_listings.values()),
    }

    if not all_listings:
        print(
            "WARNING: parsed 0 listings — Chrono24's markup may have changed, "
            "or the request was blocked. Leaving previous data.json in place if present.",
            file=sys.stderr,
        )
        try:
            with open(OUTPUT_PATH) as f:
                json.load(f)  # previous file exists and is valid, just leave it
            return
        except Exception:
            pass  # no previous file — fall through and write the (empty) result anyway

    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Wrote {len(all_listings)} listings to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
