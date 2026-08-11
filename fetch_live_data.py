"""
fetch_live_data.py — Fetch IHSG & USD/IDR, embed ke HTML sebagai JS constants.
Dipanggil oleh cron job SEBELUM push ke GitHub.
"""
import urllib.request
import json
import re
import sys
import os

# index.html berada di folder yang sama dengan script ini (repo main/).
# Dulu memakai path absolut BASE + "main" — script hidup di luar repo sehingga
# tidak ter-backup git. Sekarang relatif terhadap lokasi file ini.
HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def fetch_ihsg():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EJKSE?interval=1d&range=1d"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    meta = data["chart"]["result"][0]["meta"]
    price = meta["regularMarketPrice"]
    prev = meta.get("chartPreviousClose", meta.get("previousClose", price))
    change = round(price - prev, 2)
    pct = round((change / prev) * 100, 2) if prev else 0
    return {"price": price, "change": change, "pct": pct}

def fetch_usdidr():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    rate = data["rates"]["IDR"]
    from datetime import datetime
    now = datetime.now()
    updated = f"{now.strftime('%d %b %Y %H:%M')}"
    return {"rate": rate, "updated": updated}

def embed_data(ihsg, usdidr):
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    old_ihsg = r"const LIVE_IHSG = \{[^}]+\}"
    new_ihsg = f"const LIVE_IHSG = {{price: {ihsg['price']}, change: {ihsg['change']}, pct: {ihsg['pct']}}}"
    html = re.sub(old_ihsg, new_ihsg, html)

    old_usdidr = r"const LIVE_USDIDR = \{[^}]+\}"
    new_usdidr = f"const LIVE_USDIDR = {{rate: {usdidr['rate']}, updated: '{usdidr['updated']}'}}"
    html = re.sub(old_usdidr, new_usdidr, html)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"IHSG: {ihsg['price']} ({ihsg['change']:+.2f}, {ihsg['pct']:+.2f}%)")
    print(f"USD/IDR: Rp {usdidr['rate']:,.0f} ({usdidr['updated']})")

if __name__ == "__main__":
    try:
        ihsg = fetch_ihsg()
        usdidr = fetch_usdidr()
        embed_data(ihsg, usdidr)
        print("OK")
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
