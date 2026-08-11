#!/usr/bin/env python3
"""Merge editorial design (design-preview.html) with live digest data (index.html).

Output: new index.html — editorial CSS/structure + real news cards + full JS
(live data, refresh, ticker US/Indo, theme localStorage, category slicers,
daily background).
"""
import re, sys

MAIN = r"C:\Users\DianAgusHermawan\OneDrive - PLN\Hermes\main"
CSS_FILE = r"C:\Users\DianAgusHermawan\OneDrive - PLN\Hermes\main\tjp-design.css"

old_html = open(f"{MAIN}\\index.html", encoding="utf-8").read()

# ---------- 1. CSS dari sumber tunggal ----------
# dulu diambil dari design-preview.html; sekarang tjp-design.css supaya tidak
# ada salinan CSS yang bisa saling basi.
css = open(CSS_FILE, encoding="utf-8").read()

# ---------- 2. extract data dari index.html asli ----------
def extract_cards(section_html):
    cards = []
    for m in re.finditer(
        r'<div class="news-card( featured)?[^"]*"[^>]*data-cat="([^"]+)">(.*?)</div>(?=\s*(?:<div class="news-card|</div>))',
        section_html, re.S):
        featured, cat, inner = m.group(1), m.group(2), m.group(3)
        stripe = re.search(r'class="stripe ([^"]+)"', inner)
        tag = re.search(r'class="tag[^"]*">([^<]+)</span>', inner)
        title = re.search(r"<h[34]>(.*?)</h[34]>", inner, re.S)
        desc = re.search(r"<p>(.*?)</p>", inner, re.S)
        # footer: bentuk lengkap dibungkus <span> luar —
        #   <span><span class="date-main">07 Agu</span> · <span class="source">TechCrunch</span></span>
        # regex lama hanya mencocokkan <span class="source"> polos, jadi tanggal+outlet
        # hilang tiap rebuild (regresi 76982f8). Rekonstruksi dari kedua bagian.
        date_m = re.search(r'<span class="date-main">(.*?)</span>', inner, re.S)
        src_m = re.search(r'<span class="source">(.*?)</span>', inner, re.S)
        if date_m and src_m:
            source = f"{date_m.group(1).strip()} · {src_m.group(1).strip()}"
        elif src_m:
            source = src_m.group(1).strip()
        else:
            # fallback: teks polos di <span> pertama dalam .foot (mis. "07 Agu · TechCrunch")
            foot_m = re.search(r'<div class="foot"><span>(.*?)</span>\s*<a', inner, re.S)
            source = re.sub(r"<[^>]+>", "", foot_m.group(1)).strip() if foot_m else ""
        link = re.search(r'<a class="read-more" href="([^"]+)"[^>]*>', inner)
        cards.append({
            "featured": bool(featured),
            "cat": cat,
            "stripe": stripe.group(1) if stripe else "stripe-neutral",
            "tag": tag.group(1) if tag else cat,
            "title": title.group(1) if title else "",
            "desc": desc.group(1) if desc else "",
            "source": source,
            "href": link.group(1) if link else "#",
        })
    return cards

def extract_sections(html):
    sections = []
    # cari pembuka section; header bisa 2 bentuk lama (section-title) / baru (section)
    for m in re.finditer(r'<section data-section="([^"]+)">', html):
        name = m.group(1)
        body_start = m.end()
        nxt = html.find('<section data-section=', body_start)
        body_end = html.rfind('</section>', body_start, nxt if nxt != -1 else len(html))
        body = html[body_start:body_end]
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
    # buang simbol ▲/▼ inline — panah kini dari CSS ::before (.change.up/.down)
    cleaned = []
    for it in items:
        it = re.sub(r'(<span class="change (?:up|down)">)\s*[▲▼]\s*', r'\1', it)
        cleaned.append(it.strip())
    return "\n".join(f'    <div class="ticker-item">{it}</div>' for it in cleaned)

ticker_us = extract_ticker(old_html, "ticker-us")
ticker_id = extract_ticker(old_html, "ticker-id")

m_window = re.search(r'<div class="window">(.*?)</div>', old_html, re.S)
window_text = None
if m_window:
    wt = re.search(r"<strong>(.*?)</strong>\s*→\s*<strong>(.*?)</strong>", m_window.group(1), re.S)
    if wt:
        window_text = wt
    else:
        # bentuk baru: satu <strong> berisi "09 Agu 11:00 → 10 Agu 2026 11:00 WIB"
        wt2 = re.search(r"<strong>(.*?)\s*→\s*(.*?)</strong>", m_window.group(1), re.S)
        if wt2:
            window_text = wt2
window_html = (f"{window_text.group(1)} → {window_text.group(2)}" if window_text else "")
# group(2) bentuk baru sudah mengandung "WIB" — buang biar tidak dobel di template
window_html = re.sub(r"\s*WIB\s*$", "", window_html)

# durasi window (isi <span id="win-dur">), mis. "24 jam" / "72 jam"
m_windur = re.search(r'<span id="win-dur">(.*?)</span>', old_html, re.S)
win_dur = m_windur.group(1).strip() if m_windur else "24 jam"

m_live_ihsg = re.search(r"const LIVE_IHSG = \{([^}]+)\};", old_html)
m_live_usd = re.search(r"const LIVE_USDIDR = \{([^}]+)\};", old_html)
live_ihsg = m_live_ihsg.group(1) if m_live_ihsg else "price: 0, change: 0, pct: 0"
live_usd = m_live_usd.group(1) if m_live_usd else "rate: 0, updated: ''"

# tanggal data pasar untuk label ticker (dari LIVE_USDIDR.updated, mis. '06 Aug 2026 11:28')
m_upd = re.search(r"updated:\s*'([^']*)'", live_usd)
market_date = (m_upd.group(1).rsplit(" ", 1)[0] if m_upd and m_upd.group(1) else "hari ini")

# ---------- 4. build sections HTML (editorial) ----------
# LEAD STORY dulu (dipakai loop di bawah)
all_cards = [c for s in sections for c in s["cards"]]
# lead asli dari index.html (class="lead") — kalau ada, pertahankan
m_lead = re.search(r'<div class="lead" data-cat="([^"]+)">(.*?)</div>\s*</div>', old_html, re.S)
if m_lead:
    lead = {
        "cat": m_lead.group(1),
        "stripe": "stripe-up",
        "tag": re.search(r'<span class="tag">([^<]+)</span>', m_lead.group(2)).group(1)
               if re.search(r'<span class="tag">([^<]+)</span>', m_lead.group(2)) else m_lead.group(1),
        "title": re.search(r"<h2>(.*?)</h2>", m_lead.group(2), re.S).group(1)
                 if re.search(r"<h2>(.*?)</h2>", m_lead.group(2), re.S) else "",
        "desc": re.search(r"<p>(.*?)</p>", m_lead.group(2), re.S).group(1)
                if re.search(r"<p>(.*?)</p>", m_lead.group(2), re.S) else "",
        "source": re.search(r'<span class="src">(.*?)</span>', m_lead.group(2), re.S).group(1)
                  if re.search(r'<span class="src">(.*?)</span>', m_lead.group(2), re.S) else "",
        "href": re.search(r'<a class="read-more" href="([^"]+)"', m_lead.group(2)).group(1)
                if re.search(r'<a class="read-more" href="([^"]+)"', m_lead.group(2)) else "#",
    }
else:
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

def card_html(c, idx=None):
    feat = " featured" if c["featured"] else ""
    anchor = f' id="card-{idx}"' if idx is not None else ""
    # pisahkan tanggal (sebelum ·) dan sumber (sesudah ·) agar tanggal bisa ditonjolkan
    src = c["source"]
    if "·" in src:
        tgl, outlet = src.split("·", 1)
        foot_left = (f'<span class="date-main">{tgl.strip()}</span>'
                     f' · <span class="source">{outlet.strip()}</span>')
    elif src:
        foot_left = f'<span class="source">{src}</span>'
    else:
        foot_left = ""
    return f'''    <div class="news-card{feat}"{anchor} data-cat="{c['cat']}">
      <div class="stripe {c['stripe']}"></div>
      <span class="tag">{c['tag']}</span>
      <h4>{c['title']}</h4>
      <p>{c['desc']}</p>
      <div class="foot"><span>{foot_left}</span><a class="read-more" href="{c['href']}" target="_blank" rel="noopener">Baca</a></div>
    </div>'''

sections_html = []
card_index = {}  # id(card) -> nomor anchor, dipakai Top-5
_ctr = [0]
for s in sections:
    title = section_titles.get(s["name"], s["name"])
    # kartu lead tidak diulang di grid (sudah tampil sebagai headline)
    grid_cards = [c for c in s["cards"] if c is not lead]
    parts = []
    for c in grid_cards:
        _ctr[0] += 1
        card_index[id(c)] = _ctr[0]
        parts.append(card_html(c, _ctr[0]))
    grid = "\n".join(parts)
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
    sent_label = {"up": "Kabar positif", "down": "Kabar negatif", "neutral": "Netral"}[sent]
    lead_html = f'''  <!-- LEAD STORY -->
  <div class="lead" data-cat="{lead['cat']}">
    <div class="tag-row"><span class="tag">{lead['tag']}</span></div>
    <h2>{lead['title']}</h2>
    <p>{lead['desc']}</p>
    <div class="meta">
      <span class="src">{lead['source']}</span>
      <span class="sent {sent}">{sent_label}</span>
      <a class="read-more" href="{lead['href']}" target="_blank" rel="noopener">Baca selengkapnya</a>
    </div>
  </div>
'''

# ---------- 4c. TOP 5 (ringkasan cepat, klik -> scroll ke kartu) ----------
cat_label = {"ai": "AI", "earnings": "Earnings", "chip": "Chip", "gadget": "Gadget",
             "quantum": "Quantum", "policy": "Policy", "other": "Lain-lain"}
top5_items = [c for c in all_cards if c["featured"] and c is not lead][:5]
if len(top5_items) < 5:
    for c in all_cards:
        if c is not lead and c not in top5_items:
            top5_items.append(c)
        if len(top5_items) == 5:
            break
top5_html = ""
if top5_items:
    lis = "\n".join(
        f'      <li><a href="#card-{card_index.get(id(c), 1)}">{c["title"]}</a>'
        f'<span class="cat-tag">{cat_label.get(c["cat"], c["cat"])}</span></li>'
        for c in top5_items
    )
    top5_html = f'''  <!-- TOP 5 -->
  <div class="top5">
    <h3>Sorotan Hari Ini</h3>
    <ol>
{lis}
    </ol>
  </div>
'''

# ---------- 5. slicer counts ----------
# count = kartu grid saja (lead/highlight TIDAK dihitung, tapi tetap ikut filter saat tampil)
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
<meta name="description" content="Ringkasan berita teknologi harian dalam Bahasa Indonesia: AI, chip, gadget, earnings, quantum, dan kebijakan. {total_cards} berita pilihan dari sumber kredibel, diperbarui setiap hari kerja pukul 11:00 WIB.">
<meta name="theme-color" content="#121212">
<meta name="author" content="Tech News Digest">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%23121212'/%3E%3Crect x='4' y='4' width='56' height='56' fill='none' stroke='%23dc2027' stroke-width='3'/%3E%3Ctext x='32' y='44' font-family='Lora,Georgia,serif' font-size='30' font-weight='bold' fill='%23ffffff' text-anchor='middle'%3ETD%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Tech News Digest">
<meta property="og:title" content="Tech News Digest — {window_text.group(2) if window_text else ''}">
<meta property="og:description" content="Ringkasan berita teknologi terkini: AI, chip, gadget, earnings, quantum, kebijakan. Diperbarui tiap hari kerja 11:00 WIB.">
<meta property="og:url" content="https://dianagush.github.io/tech-news-digest/">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Tech News Digest — {window_text.group(2) if window_text else ''}">
<meta name="twitter:description" content="Ringkasan berita teknologi harian: AI, chip, gadget, earnings, quantum, kebijakan.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Lato:wght@400;700;900&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<div class="bg-layer"></div>
<div class="container">

  <!-- TOP BAR -->
  <div class="topbar">
    <div class="edition">Edisi · Digest Harian</div>
    <button class="theme-toggle" onclick="toggleTheme()" title="Ganti tema gelap/terang" aria-label="Ganti tema gelap atau terang">
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
    </button>
  </div>

  <!-- MASTHEAD -->
  <header class="masthead">
    <div class="kicker">Ringkasan Harian</div>
    <h1>Tech News Digest</h1>
    <div class="window">Jendela berita <strong>{window_html} WIB</strong> · <span id="win-dur">{win_dur}</span> terakhir</div>
    <div class="rules"><div class="thick"></div><div class="thin"></div></div>
  </header>

  <!-- LIVE STATS -->
  <div class="ticker" role="region" aria-label="Data pasar terkini">
    <div class="item"><span class="label">IHSG</span><span class="val" id="ihsg-value">…</span><span class="chg" id="ihsg-change"></span></div>
    <div class="item"><span class="label">USD/IDR</span><span class="val" id="usdidr-value">…</span><span class="chg" id="usdidr-time"></span></div>
    <button class="refresh-btn" onclick="refreshLiveData()" aria-label="Perbarui data pasar" title="Perbarui data pasar">⟳</button>
  </div>

{top5_html}
{lead_html}

  <!-- MARKET TICKERS -->
  <div class="ticker-section">
    <div class="slicers-row" role="group" aria-label="Filter pasar saham">
      <span class="ticker-label">Pergerakan saham {market_date}:</span>
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
  <div class="slicers-row sticky" id="categorySlicers" role="group" aria-label="Filter kategori berita">
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
