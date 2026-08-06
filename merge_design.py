#!/usr/bin/env python3
"""Merge editorial design (design-preview.html) with live digest data (index.html).

Output: new index.html — editorial CSS/structure + real news cards + full JS
(live data, refresh, ticker US/Indo, theme localStorage, category slicers,
daily background).
"""
import re, sys

MAIN = r"C:\Users\DianAgusHermawan\OneDrive - PLN\Hermes\main"
PREVIEW = r"C:\Users\DianAgusHermawan\OneDrive - PLN\Hermes\main\design-preview.html"

old_html = open(f"{MAIN}\\index.html.bak-20260806", encoding="utf-8").read()
preview = open(PREVIEW, encoding="utf-8").read()

# ---------- 1. extract CSS dari preview ----------
m_style = re.search(r"<style>(.*?)</style>", preview, re.S)
css = m_style.group(1)

# ---------- 2. extract data dari index.html asli ----------
def extract_cards(section_html):
    cards = []
    for m in re.finditer(
        r'<div class="news-card( featured)?[^"]*" data-cat="([^"]+)">(.*?)</div>(?=\s*(?:<div class="news-card|</div>))',
        section_html, re.S):
        featured, cat, inner = m.group(1), m.group(2), m.group(3)
        stripe = re.search(r'class="stripe ([^"]+)"', inner)
        tag = re.search(r'class="tag [^"]*">([^<]+)</span>', inner)
        title = re.search(r"<h3>(.*?)</h3>", inner, re.S)
        desc = re.search(r"<p>(.*?)</p>", inner, re.S)
        src = re.search(r'<div class="source">(.*?)</div>', inner, re.S)
        link = re.search(r'<a class="read-more" href="([^"]+)"[^>]*>', inner)
        cards.append({
            "featured": bool(featured),
            "cat": cat,
            "stripe": stripe.group(1) if stripe else "stripe-neutral",
            "tag": tag.group(1) if tag else cat,
            "title": title.group(1) if title else "",
            "desc": desc.group(1) if desc else "",
            "source": src.group(1) if src else "",
            "href": link.group(1) if link else "#",
        })
    return cards

def extract_sections(html):
    sections = []
    for m in re.finditer(
        r'<section data-section="([^"]+)">.*?<div class="section-title">[^<]*?</div>(.*?)</section>',
        html, re.S):
        name, body = m.group(1), m.group(2)
        sections.append({"name": name, "cards": extract_cards(body)})
    return sections

sections = extract_sections(old_html)
total = sum(len(s["cards"]) for s in sections)
print(f"extracted sections={len(sections)} cards={total}")
for s in sections:
    print(f"  {s['name']}: {len(s['cards'])}")

# ---------- 3. data ticker (parse per item, rebuild bersih) ----------
def extract_ticker(html, tid):
    # ambil dari <div class="ticker" id="X"> sampai <div class="ticker" berikutnya ATAU akhir blok
    start = html.find(f'<div class="ticker" id="{tid}">')
    if start == -1:
        return ""
    rest = html[start:]
    nxt = rest.find('<div class="ticker"', len(f'<div class="ticker" id="{tid}">'))
    if nxt == -1:
        # blok terakhir: sampai </div>\n</div> (tutup ticker + tutup ticker-section)
        end = rest.find('\n</div>')
        body = rest[len(f'<div class="ticker" id="{tid}">'):end]
    else:
        body = rest[len(f'<div class="ticker" id="{tid}">'):nxt]
    items = re.findall(r'<div class="ticker-item">(.*?)</div>', body, re.S)
    return "\n".join(f'    <div class="ticker-item">{it.strip()}</div>' for it in items)

ticker_us = extract_ticker(old_html, "ticker-us")
ticker_id = extract_ticker(old_html, "ticker-id")

m_window = re.search(r'<div class="window">(.*?)</div>', old_html, re.S)
window_text = re.search(r"<strong>(.*?)</strong>.*?<strong>(.*?)</strong>", m_window.group(1), re.S) if m_window else None
window_html = (f"{window_text.group(1)} → {window_text.group(2)}" if window_text else old_html)

m_live_ihsg = re.search(r"const LIVE_IHSG = \{([^}]+)\};", old_html)
m_live_usd = re.search(r"const LIVE_USDIDR = \{([^}]+)\};", old_html)
live_ihsg = m_live_ihsg.group(1) if m_live_ihsg else "price: 0, change: 0, pct: 0"
live_usd = m_live_usd.group(1) if m_live_usd else "rate: 0, updated: ''"

# ---------- 4. build sections HTML (editorial) ----------
# LEAD STORY dulu (dipakai loop di bawah)
all_cards = [c for s in sections for c in s["cards"]]
lead = next((c for c in all_cards if c["featured"]), all_cards[0] if all_cards else None)

section_titles = {
    "ai": "AI & Large Language Models",
    "earnings": "Earnings & Big Tech",
    "chip": "Semiconductor & Chip Industry",
    "gadget": "Gadget & Consumer Tech",
    "quantum": "Quantum Computing",
    "policy": "Policy, Regulasi & Security",
    "other": "Lain-lain — Pasar & Teknologi Terkait",
}

def card_html(c):
    feat = " featured" if c["featured"] else ""
    return f'''    <div class="news-card{feat}" data-cat="{c['cat']}">
      <div class="stripe {c['stripe']}"></div>
      <span class="tag">{c['tag']}</span>
      <h4>{c['title']}</h4>
      <p>{c['desc']}</p>
      <div class="foot"><span>{c['source']}</span><a class="read-more" href="{c['href']}" target="_blank">Baca</a></div>
    </div>'''

sections_html = []
for s in sections:
    title = section_titles.get(s["name"], s["name"])
    # kartu lead tidak diulang di grid (sudah tampil sebagai headline)
    grid_cards = [c for c in s["cards"] if c is not lead]
    grid = "\n".join(card_html(c) for c in grid_cards)
    sections_html.append(f'''    <section data-section="{s['name']}">
    <div class="section"><div class="rule-thick"></div><h3>{title}</h3><div class="rule-thin"></div></div>
    <div class="news-grid">
{grid}
    </div>
    </section>''')
sections_html = "\n".join(sections_html)

# ---------- 4b. LEAD STORY HTML ----------
lead_html = ""
if lead:
    sent = "neutral"
    if "up" in lead["stripe"]: sent = "up"
    elif "down" in lead["stripe"]: sent = "down"
    sent_label = {"up": "Sentimen: Naik", "down": "Sentimen: Turun", "neutral": "Sentimen: Netral"}[sent]
    lead_html = f'''  <!-- LEAD STORY -->
  <div class="lead" data-cat="{lead['cat']}">
    <div class="tag-row"><span class="tag">{lead['tag']}</span></div>
    <h2>{lead['title']}</h2>
    <p>{lead['desc']}</p>
    <div class="meta">
      <span class="src">{lead['source']}</span>
      <span class="sent {sent}">{sent_label}</span>
      <a class="read-more" href="{lead['href']}" target="_blank">Baca selengkapnya</a>
    </div>
  </div>
'''

# ---------- 5. slicer counts ----------
counts = {s["name"]: len(s["cards"]) for s in sections}
total_cards = sum(counts.values())
def slicer_btn(cat, label):
    n = counts.get(cat, total_cards) if cat == "all" else counts.get(cat, 0)
    active = ' active' if cat == 'all' else ''
    return f'    <button class="slicer-btn{active}" data-cat="{cat}">{label} <span class="count">({n})</span></button>'

slicers = "\n".join([
    slicer_btn("all", "Semua"),
    slicer_btn("ai", "AI"),
    slicer_btn("earnings", "Earnings"),
    slicer_btn("chip", "Chip"),
    slicer_btn("gadget", "Gadget"),
    slicer_btn("quantum", "Quantum"),
    slicer_btn("policy", "Policy"),
    slicer_btn("other", "Lain-lain"),
])

# ---------- 6. JS gabungan ----------
js = f'''// === LIVE DATA: IHSG + USD/IDR (di-embed cron server-side) ===
const LIVE_IHSG = {{{live_ihsg}}};
const LIVE_USDIDR = {{{live_usd}}};

function applyIHSG() {{
  const el = document.getElementById('ihsg-value');
  const ch = document.getElementById('ihsg-change');
  const price = LIVE_IHSG.price.toLocaleString('id-ID');
  const sign = LIVE_IHSG.change >= 0 ? '+' : '';
  el.textContent = price;
  ch.textContent = `${{sign}}${{LIVE_IHSG.change.toLocaleString('id-ID')}} (${{sign}}${{LIVE_IHSG.pct}}%)`;
  ch.className = 'chg ' + (LIVE_IHSG.change >= 0 ? 'up' : 'down');
}}

function applyUSDIDR() {{
  const el = document.getElementById('usdidr-value');
  const tm = document.getElementById('usdidr-time');
  el.textContent = 'Rp ' + LIVE_USDIDR.rate.toLocaleString('id-ID');
  tm.textContent = LIVE_USDIDR.updated;
}}

applyIHSG();
applyUSDIDR();

function refreshLiveData() {{
  const ihsgEl = document.getElementById('ihsg-value');
  const ihsgCh = document.getElementById('ihsg-change');
  const usdEl = document.getElementById('usdidr-value');
  const usdTm = document.getElementById('usdidr-time');
  ihsgEl.innerHTML = '…';
  ihsgCh.textContent = '';
  usdEl.innerHTML = '…';
  usdTm.textContent = '';

  Promise.all([
    fetch('https://query1.finance.yahoo.com/v8/finance/chart/%5EJKSE?interval=1d&range=1d')
      .then(r => r.json())
      .then(d => {{
        const m = d.chart.result[0].meta;
        const price = m.regularMarketPrice;
        const prev = m.chartPreviousClose || m.previousClose || price;
        const change = price - prev;
        const pct = ((change / prev) * 100).toFixed(2);
        LIVE_IHSG.price = price;
        LIVE_IHSG.change = parseFloat(change.toFixed(2));
        LIVE_IHSG.pct = parseFloat(pct);
        applyIHSG();
      }}),
    fetch('https://api.exchangerate-api.com/v4/latest/USD')
      .then(r => r.json())
      .then(d => {{
        LIVE_USDIDR.rate = d.rates.IDR;
        LIVE_USDIDR.updated = 'live · ' + new Date().toLocaleTimeString('id-ID', {{hour:'2-digit',minute:'2-digit'}});
        applyUSDIDR();
      }})
  ]).catch(() => {{
    applyIHSG();
    applyUSDIDR();
  }});
}}

// === THEME TOGGLE (ikon matahari/bulan via CSS, simpan preferensi) ===
function toggleTheme() {{
  const root = document.documentElement;
  const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
  root.dataset.theme = next;
  localStorage.setItem('hermes-news-theme', next);
}}
(function() {{
  const saved = localStorage.getItem('hermes-news-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
}})();

// === TICKER FILTER (US / Indo) ===
function filterTicker(region) {{
  document.querySelectorAll('[data-ticker]').forEach(b => b.classList.remove('active'));
  document.querySelector(`[data-ticker="${{region}}"]`).classList.add('active');
  const us = document.getElementById('ticker-us');
  const id = document.getElementById('ticker-id');
  if (region === 'all') {{ us.classList.remove('hidden'); id.classList.remove('hidden'); }}
  else if (region === 'us') {{ us.classList.remove('hidden'); id.classList.add('hidden'); }}
  else {{ us.classList.add('hidden'); id.classList.remove('hidden'); }}
}}

// === CATEGORY SLICERS ===
// lead story ikut terfilter (dia punya data-cat juga)
const cards = document.querySelectorAll('.news-card, .lead');
const sections = document.querySelectorAll('section[data-section]');

function applyFilters(cat) {{
  cards.forEach(card => {{
    const cardCats = card.dataset.cat.split(' ');
    const catMatch = cat === 'all' || cardCats.includes(cat);
    card.classList.toggle('hidden', !catMatch);
  }});
  sections.forEach(section => {{
    const visible = section.querySelectorAll('.news-card:not(.hidden)');
    section.style.display = visible.length === 0 ? 'none' : '';
  }});
}}

const newsSlicers = document.querySelectorAll('#categorySlicers .slicer-btn');
newsSlicers.forEach(btn => {{
  btn.addEventListener('click', () => {{
    newsSlicers.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    applyFilters(btn.dataset.cat);
  }});
}});

// === DAILY BACKGROUND (ganti tiap hari) ===
(function () {{
  const variants = ['bg-circuit', 'bg-dots', 'bg-hex', 'bg-scan', 'bg-blueprint', 'bg-signal', 'bg-chip'];
  const d = new Date();
  const seed = d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
  document.body.classList.add(variants[seed % variants.length]);
}})();'''

# ---------- 7. assemble ----------
html = f'''<!DOCTYPE html>
<html lang="id" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tech News Digest — {window_text.group(2) if window_text else ''}</title>
<style>
{css}
</style>
</head>
<body>
<div class="bg-layer"></div>
<div class="container">

  <!-- TOP BAR -->
  <div class="topbar">
    <div class="edition">Edisi · Digest Harian</div>
    <button class="theme-toggle" onclick="toggleTheme()" title="Ganti tema">
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
    </button>
  </div>

  <!-- MASTHEAD -->
  <header class="masthead">
    <div class="kicker">Ringkasan Harian</div>
    <h1>Tech News Digest</h1>
    <div class="window">Jendela berita <strong>{window_html}</strong> WIB · 24 jam terakhir</div>
    <div class="rules"><div class="thick"></div><div class="thin"></div></div>
  </header>

  <!-- LIVE STATS -->
  <div class="ticker">
    <div class="item"><span class="label">IHSG</span><span class="val" id="ihsg-value">…</span><span class="chg" id="ihsg-change"></span></div>
    <div class="item"><span class="label">USD/IDR</span><span class="val" id="usdidr-value">…</span><span class="chg" id="usdidr-time"></span></div>
    <button class="refresh-btn" onclick="refreshLiveData()">⟳ Refresh</button>
  </div>

{lead_html}

  <!-- MARKET TICKERS -->
  <div class="ticker-section">
    <div class="slicers-row">
      <span class="ticker-label">Pasar:</span>
      <button class="slicer-btn active" data-ticker="all" onclick="filterTicker('all')">Semua</button>
      <button class="slicer-btn" data-ticker="us" onclick="filterTicker('us')">US</button>
      <button class="slicer-btn" data-ticker="id" onclick="filterTicker('id')">Indo</button>
    </div>
    <div class="ticker" id="ticker-us">
{ticker_us}
    </div>
    <div class="ticker" id="ticker-id">
{ticker_id}
    </div>
  </div>

  <!-- NEWS SLICERS -->
  <div class="slicers-row" id="categorySlicers">
{slicers}
  </div>

  <div id="news-container">
{sections_html}
  </div>

  <footer>Tech News Digest · Disusun otomatis oleh Hermes Agent · Data pasar: Yahoo Finance &amp; exchangerate-api</footer>
</div>

<script>
{js}
</script>
</body>
</html>'''

out = f"{MAIN}\\index.html"
open(out, "w", encoding="utf-8", newline="\n").write(html)
print(f"WROTE {out} ({len(html)} bytes)")
