#!/usr/bin/env python3
"""
Apple Deal Tracker — Daily Price Scraper
Uses SerpApi to fetch real live Amazon prices by ASIN.
Runs via GitHub Actions every day at 9am UTC.
Updates index.html with fresh prices and today's date.
"""

import re
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

# ── Products to track ─────────────────────────────────────────────────────────

PRODUCTS = {
    "mb13": {
        "asin": "B0DYHPGPFS",
        "name": "MacBook Air 13\" M5 16GB/512GB",
        "msrp": 1099,
        "shop_url": "https://www.amazon.com/s?k=macbook+air+m5+13+512gb",
    },
    "mb15": {
        "asin": "B0DYHQ3TTW",
        "name": "MacBook Air 15\" M5 16GB/512GB",
        "msrp": 1299,
        "shop_url": "https://www.amazon.com/s?k=macbook+air+m5+15+512gb",
    },
    "air11": {
        "asin": "B0DYPQL5X4",
        "name": "iPad Air 11\" M4 128GB",
        "msrp": 599,
        "shop_url": "https://www.amazon.com/s?k=ipad+air+m4+11+inch+128gb",
    },
    "air13": {
        "asin": "B0DYPQM7ZK",
        "name": "iPad Air 13\" M4 128GB",
        "msrp": 799,
        "shop_url": "https://www.amazon.com/s?k=ipad+air+m4+13+inch+128gb",
    },
    "mini128": {
        "asin": "B0CHX2HFZN",
        "name": "iPad mini 7 128GB",
        "msrp": 499,
        "shop_url": "https://www.amazon.com/s?k=ipad+mini+7+128gb",
    },
    "mini256": {
        "asin": "B0CHX3HHWJ",
        "name": "iPad mini 7 256GB",
        "msrp": 599,
        "shop_url": "https://www.amazon.com/s?k=ipad+mini+7+256gb",
    },
    "mini512": {
        "asin": "B0CHX4LLKQ",
        "name": "iPad mini 7 512GB",
        "msrp": 779,
        "shop_url": "https://www.amazon.com/s?k=ipad+mini+7+512gb",
    },
    "ipad128": {
        "asin": "B0D3J6KPKF",
        "name": "iPad 11th Gen 128GB",
        "msrp": 349,
        "shop_url": "https://www.amazon.com/s?k=ipad+11th+generation+128gb",
    },
    "ipad256": {
        "asin": "B0D3J7MPQR",
        "name": "iPad 11th Gen 256GB",
        "msrp": 449,
        "shop_url": "https://www.amazon.com/s?k=ipad+11th+generation+256gb",
    },
}

# Fallback prices used when SerpApi fetch fails
BASELINE = {
    "mb13":    1049,
    "mb15":    1249,
    "air11":   559,
    "air13":   749,
    "mini128": 399,
    "mini256": 499,
    "mini512": 679,
    "ipad128": 299,
    "ipad256": 399,
}

# ── SerpApi fetch ─────────────────────────────────────────────────────────────

def fetch_price(asin):
    """Fetch current Amazon price for an ASIN via SerpApi. Returns float or None."""
    if not SERPAPI_KEY:
        return None

    params = urllib.parse.urlencode({
        "engine": "amazon_product",
        "asin": asin,
        "api_key": SERPAPI_KEY,
        "country": "us",
    })

    try:
        req = urllib.request.Request(f"https://serpapi.com/search.json?{params}")
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))

        pr = data.get("product_results", {})

        # Try multiple price fields SerpApi may return
        for field in ["price", "list_price"]:
            val = pr.get(field)
            if val:
                clean = re.sub(r"[^\d.]", "", str(val))
                if clean:
                    return float(clean)

        # Try offers summary
        for offer in pr.get("offers_summary", []):
            val = offer.get("price", "")
            clean = re.sub(r"[^\d.]", "", str(val))
            if clean:
                return float(clean)

    except Exception as e:
        print(f"  error: {e}")

    return None

# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt(n):
    return f"${n:,.0f}"

def get_savings(current, msrp):
    diff = msrp - current
    return f"–{fmt(diff)}" if diff > 0 else ""

# ── HTML update ───────────────────────────────────────────────────────────────

def update_html(prices, date_str):
    html_path = Path(__file__).parent / "index.html"
    html = html_path.read_text(encoding="utf-8")

    # Build output price dict
    out = {}
    for key, product in PRODUCTS.items():
        msrp = product["msrp"]
        current = prices.get(key, BASELINE.get(key, msrp))
        out[key] = {
            "current": fmt(current),
            "msrp": fmt(msrp),
            "savings": get_savings(current, msrp),
            "raw": current,
        }

    block = f"""<script id="apd" type="application/json">{json.dumps({"updated": date_str, "prices": out})}</script>
<script>
(function(){{
  try {{
    var d = JSON.parse(document.getElementById('apd').textContent);
    var p = d.prices;
    document.querySelectorAll('[data-p]').forEach(function(el){{
      var k=el.getAttribute('data-p'), f=el.getAttribute('data-f')||'current';
      if(p[k] && p[k][f] !== undefined) el.textContent = p[k][f];
    }});
    document.querySelectorAll('.js-date').forEach(function(el){{ el.textContent = d.updated; }});
  }} catch(e){{}}
}})();
</script>"""

    # Remove old block
    html = re.sub(r'<script id="apd".*?</script>\s*<script>.*?</script>', "", html, flags=re.DOTALL)
    html = html.replace("</body>", block + "\n</body>")
    html_path.write_text(html, encoding="utf-8")
    print(f"✓ index.html updated — {date_str}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %-d, %Y")
    print(f"\nApple Deal Tracker Scraper — {date_str}")
    print("=" * 50)

    if not SERPAPI_KEY:
        print("⚠️  SERPAPI_KEY not found in environment. Using baseline prices.")

    prices = {}
    for key, product in PRODUCTS.items():
        print(f"{product['name']} ({product['asin']})... ", end="", flush=True)
        live = fetch_price(product["asin"])
        if live:
            prices[key] = live
            saved = product["msrp"] - live
            note = f"saving {fmt(saved)}" if saved > 0 else "at MSRP"
            print(f"✓ {fmt(live)} ({note})")
        else:
            prices[key] = BASELINE.get(key, product["msrp"])
            print(f"→ fallback {fmt(prices[key])}")

    update_html(prices, date_str)
    print("\nDone ✓")

if __name__ == "__main__":
    main()
