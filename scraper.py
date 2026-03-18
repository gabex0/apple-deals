#!/usr/bin/env python3
"""
Apple Deal Tracker — Daily Price Scraper
Fetches current prices from Amazon, Best Buy, and Apple.
Runs via GitHub Actions every day at 9am UTC.
Updates index.html with fresh prices and today's date.
"""

import re
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Price definitions ──────────────────────────────────────────────────────────
# Structure: { product_key: { retailer: price_string } }
# These are the MSRP / known prices loaded as baseline.
# The scraper will attempt live fetches and overwrite if successful.

BASELINE = {
    "mb13": {
        "amazon": "$1,049",
        "costco": "$1,049",
        "bestbuy": "$1,099",
        "apple": "$1,099",
        "edu": "$999",
        "bh": "$1,099",
        "refurb": "N/A",
        "openbox": "~$850–950",
    },
    "mb15": {
        "amazon": "$1,249",
        "bestbuy": "$1,299",
        "edu": "$1,199",
        "refurb": "N/A",
    },
    "air11": {
        "amazon": "$559",
        "bestbuy": "$559",
        "edu": "$549",
        "msrp": "$599",
    },
    "air13": {
        "amazon": "$749",
        "bestbuy": "$749",
        "edu": "$749",
        "msrp": "$799",
    },
    "mini128": {
        "amazon": "$399",
        "bestbuy": "$399",
        "edu": "$449",
        "msrp": "$499",
        "atl": "$349",
    },
    "mini256": {
        "amazon": "$499",
        "bestbuy": "$499",
        "edu": "$549",
        "msrp": "$599",
    },
    "mini512": {
        "amazon": "$679",
        "bestbuy": "$679",
        "edu": "$729",
        "msrp": "$779",
    },
    "ipad128": {
        "amazon": "$299",
        "bestbuy": "$299",
        "edu": "$329",
        "msrp": "$349",
        "atl": "$278",
    },
    "ipad256": {
        "amazon": "$399",
        "bestbuy": "$449",
        "edu": "$429",
        "msrp": "$449",
    },
}

# ── Live fetch helpers ─────────────────────────────────────────────────────────

def fetch(url, timeout=12):
    """Fetch a URL and return text, or None on failure."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  fetch failed {url[:60]}…  ({e})")
        return None


def extract_price(html, patterns):
    """Try a list of regex patterns against html, return first match or None."""
    if not html:
        return None
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            raw = m.group(1).replace(",", "").strip()
            try:
                val = float(raw)
                return f"${val:,.0f}" if val == int(val) else f"${val:,.2f}"
            except ValueError:
                pass
    return None


def fetch_amazon_price(asin):
    """Attempt to get price from Amazon product page."""
    url = f"https://www.amazon.com/dp/{asin}"
    html = fetch(url)
    patterns = [
        r'"priceAmount":\s*([\d.]+)',
        r'<span[^>]+class="[^"]*a-price-whole[^"]*"[^>]*>([\d,]+)',
        r'"price":\s*\{"value":\s*([\d.]+)',
    ]
    return extract_price(html, patterns)


def fetch_bestbuy_price(sku):
    """Attempt to get price from Best Buy API."""
    url = (
        f"https://www.bestbuy.com/api/tcfb/model.json?paths=%5B%5B%22shop%22%2C%22"
        f"buttonstate%22%2C%22v5%22%2C%22item%22%2C%22skus%22%2C{sku}%2C%22conditions%22"
        f"%2C%22NONE%22%2C%22destinationZipCode%22%2C%2290035%22%2C%22storeId%22%2C%22"
        f"058%22%2C%22context%22%2C%22cyp%22%2C%22addAll%22%2C%22false%22%5D%5D&"
        f"method=get"
    )
    html = fetch(url)
    patterns = [r'"currentPrice":\s*([\d.]+)', r'"salePrice":\s*([\d.]+)']
    return extract_price(html, patterns)


# ── Product → ASIN / SKU map ───────────────────────────────────────────────────
# ASINs and BB SKUs for the exact configs we track.
# If Amazon/BB blocks the request, baseline prices are used as fallback.

AMAZON_ASINS = {
    "mb13":    "B0DYHPGPFS",   # MacBook Air 13" M5 16GB 512GB Midnight
    "mb15":    "B0DYHQ3TTW",   # MacBook Air 15" M5 16GB 512GB Midnight
    "air11":   "B0DYPQL5X4",   # iPad Air 11" M4 128GB Wi-Fi Blue
    "air13":   "B0DYPQM7ZK",   # iPad Air 13" M4 128GB Wi-Fi Blue
    "mini128": "B0CHX2HFZN",   # iPad mini 7 128GB Wi-Fi Starlight
    "mini256": "B0CHX3HHWJ",   # iPad mini 7 256GB Wi-Fi Starlight
    "mini512": "B0CHX4LLKQ",   # iPad mini 7 512GB Wi-Fi Starlight
    "ipad128": "B0D3J6KPKF",   # iPad 11th gen 128GB Wi-Fi Blue
    "ipad256": "B0D3J7MPQR",   # iPad 11th gen 256GB Wi-Fi Blue
}

BB_SKUS = {
    "mb13":    "9609849",
    "mb15":    "9609850",
    "mini128": "5082982",
    "ipad128": "5082983",
}


# ── Main update logic ──────────────────────────────────────────────────────────

def scrape_prices():
    """Try to fetch live prices; fall back to baseline."""
    prices = {k: dict(v) for k, v in BASELINE.items()}

    print("Fetching live prices…")

    for key, asin in AMAZON_ASINS.items():
        print(f"  Amazon {key} ({asin})…", end=" ")
        live = fetch_amazon_price(asin)
        if live:
            prices[key]["amazon"] = live
            print(f"✓ {live}")
        else:
            print(f"→ using baseline {prices[key].get('amazon','?')}")

    for key, sku in BB_SKUS.items():
        print(f"  Best Buy {key} ({sku})…", end=" ")
        live = fetch_bestbuy_price(sku)
        if live:
            prices[key]["bestbuy"] = live
            print(f"✓ {live}")
        else:
            print(f"→ using baseline {prices[key].get('bestbuy','?')}")

    return prices


def update_html(prices):
    """Read index.html, substitute price placeholders, write back."""
    html_path = Path(__file__).parent / "index.html"
    html = html_path.read_text(encoding="utf-8")

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %-d, %Y")   # e.g. "March 17, 2026"

    # Inject a data block just before </body> so JS can read live prices
    data_block = f"""
<script id="live-prices" type="application/json">
{json.dumps({"updated": date_str, "prices": prices}, indent=2)}
</script>
"""

    # Remove old block if present
    html = re.sub(
        r'<script id="live-prices".*?</script>\s*',
        "",
        html,
        flags=re.DOTALL,
    )

    html = html.replace("</body>", data_block + "\n</body>")
    html_path.write_text(html, encoding="utf-8")
    print(f"\n✓ index.html updated — {date_str}")


if __name__ == "__main__":
    prices = scrape_prices()
    update_html(prices)
    print("Done.")
