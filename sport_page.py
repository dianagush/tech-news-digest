"""Template halaman Sport Digest — SATU sumber untuk preview dan halaman live.

Dipakai oleh:
  - make_sport_preview.py  -> sport-preview.html  (untuk sign-off)
  - apply_sport_page.py    -> sport.html          (halaman live yang di-publish)

Menyimpan template di sini mencegah preview dan produksi berbeda diam-diam
(pelajaran lama: CSS/JS tersalin di beberapa tempat lalu saling basi).

Kartu berita: `apply_sport_page.py` mempertahankan kartu yang sudah ada di
sport.html; hanya kalau file belum ada, kartu contoh di bawah dipakai sebagai
benih. Cron 11:00 yang mengisi kartu sebenarnya.
"""
import json
import re
from datetime import datetime

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
         "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

CATS = [("sepakbola", "Sepakbola"), ("motorsport", "Motorsport"),
        ("basket", "Basket"), ("tenis", "Tenis"),
        ("badminton", "Bulutangkis"), ("mma", "MMA"), ("lainnya", "Lain-lain")]

SPORT_FILTERS = [("all", "Semua"), ("sepakbola", "Sepakbola"),
                 ("motorsport", "Motorsport"), ("basket", "Basket"),
                 ("tenis", "Tenis"), ("mma", "MMA")]

# Benih kartu — hanya dipakai saat sport.html belum ada / preview.
SAMPLE = [
    ("sepakbola", "Persib", "Persib Tahan Imbang Bali United di Kandang",
     "Laga pekan ketiga Liga 1 berakhir 1-1 setelah gol penyeimbang di menit akhir. "
     "Persib tetap di puncak klasemen sementara dengan selisih dua poin.",
     "10 Agu", "Bola.net", "up"),
    ("sepakbola", "Timnas", "Timnas Indonesia Panggil 26 Pemain untuk Kualifikasi",
     "Pelatih mengumumkan skuad untuk dua laga kualifikasi bulan depan, termasuk "
     "tiga pemain debutan dari klub Liga 1.",
     "10 Agu", "Detik Sport", "neutral"),
    ("sepakbola", "Pramusim", "Juventus Jamu Palermo di Laga Uji Coba Terakhir",
     "Pertandingan persahabatan menjadi gladi resik sebelum Serie A bergulir, "
     "dengan dua rekrutan anyar diperkirakan tampil sejak menit pertama.",
     "11 Agu", "Football Italia", "neutral"),
    ("sepakbola", "Transfer", "Bursa Transfer Eropa Tembus Rekor Musim Panas",
     "Total belanja klub lima liga top melewati angka musim lalu sebulan sebelum "
     "jendela transfer ditutup.",
     "10 Agu", "Sky Sports", "up"),
    ("motorsport", "Formula 1", "Dutch GP Jadi Penentu Perebutan Gelar",
     "Selisih poin di klasemen menyempit menjelang balapan kandang tim papan atas.",
     "10 Agu", "Autosport", "neutral"),
    ("basket", "NBA", "Jadwal NBA 2026-27 Dirilis, Musim Dibuka Awal Oktober",
     "Liga mengumumkan kalender lengkap; laga pembuka mempertemukan finalis musim lalu.",
     "10 Agu", "ESPN", "neutral"),
    ("tenis", "ATP", "Cincinnati Open Dimulai, Unggulan Teratas Dapat Bye",
     "Turnamen Masters 1000 terakhir sebelum US Open menghadirkan hampir seluruh "
     "pemain sepuluh besar dunia.",
     "11 Agu", "ATP Tour", "neutral"),
    ("badminton", "BWF", "Indonesia Kirim 12 Wakil ke Kejuaraan Dunia",
     "Skuad terdiri dari lima sektor dengan tunggal putra sebagai andalan medali.",
     "10 Agu", "Antara", "up"),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card_html(i, cat, tag, judul, desc, tgl, sumber, sent):
    stripe = {"up": "stripe-up", "down": "stripe-down"}.get(sent, "stripe-flat")
    return f'''    <div class="news-card" id="card-{i}" data-cat="{cat}">
      <div class="stripe {stripe}"></div>
      <span class="tag">{esc(tag)}</span>
      <h4>{esc(judul)}</h4>
      <p>{esc(desc)}</p>
      <div class="foot"><span><span class="date-main">{tgl}</span> · <span class="source">{esc(sumber)}</span></span><a class="read-more" href="#" target="_blank" rel="noopener">Baca</a></div>
    </div>'''


def build_news_from_sample():
    """-> (html seksi, hitungan per kategori, total kartu)."""
    by_cat = {}
    for row in SAMPLE:
        by_cat.setdefault(row[0], []).append(row)
    parts, counts, idx = [], {}, 0
    for cat, label in CATS:
        rows = by_cat.get(cat)
        if not rows:
            continue
        counts[cat] = len(rows)
        cards = []
        for r in rows:
            idx += 1
            cards.append(card_html(idx, *r))
        parts.append(
            f'    <section data-section="{cat}">\n'
            f'    <div class="section"><div class="rule-thick"></div><h3>{label}</h3>'
            f'<div class="rule-thin"></div></div>\n'
            f'    <div class="news-grid">\n' + "\n".join(cards) + "\n    </div>\n    </section>")
    return "\n".join(parts), counts, idx


def extract_news(html):
    """Ambil blok berita dari halaman lama supaya kartu cron tidak hilang.

    -> (html seksi, hitungan per kategori, total) atau None kalau tidak ketemu.
    """
    m = re.search(r'<div id="news-container">\n(.*?)\n  </div>', html, re.S)
    if not m:
        return None
    blok = m.group(1)
    counts = {}
    for cat in re.findall(r'class="news-card"[^>]*data-cat="([\w-]+)"', blok):
        counts[cat] = counts.get(cat, 0) + 1
    total = sum(counts.values())
    if total == 0:
        return None
    return blok, counts, total


def slicers(counts, total):
    btns = [f'    <button class="slicer-btn active" data-cat="all">Semua '
            f'<span class="count">({total})</span></button>']
    for cat, label in CATS:
        if cat in counts:
            btns.append(f'    <button class="slicer-btn" data-cat="{cat}">{label} '
                        f'<span class="count">({counts[cat]})</span></button>')
    return "\n".join(btns)


def sport_filter_btns(present):
    out = []
    for key, label in SPORT_FILTERS:
        if key != "all" and key not in present:
            continue
        cls = "slicer-btn active" if key == "all" else "slicer-btn"
        out.append(f'      <button class="{cls}" data-sport="{key}" '
                   f'onclick="filterSport(\'{key}\')">{label}</button>')
    return "\n".join(out)


def durasi(scores):
    """Durasi jendela dalam jam, dibaca dari since/until."""
    try:
        a = datetime.fromisoformat(scores["since"])
        b = datetime.fromisoformat(scores["until"])
        return f"{round((b - a).total_seconds() / 3600)} jam"
    except (KeyError, ValueError):
        return "24 jam"


def render(scores, css, news=None, preview=False):
    """Rakit halaman lengkap.

    scores  : dict hasil fetch_scores.py (scores-cache.json)
    css     : gabungan tjp-design.css + sport-design.css
    news    : (html, counts, total) — None berarti pakai kartu benih
    preview : True menambah penanda [PREVIEW] di judul
    """
    news_html, counts, total = news if news else build_news_from_sample()
    present = {g["sport"] for g in scores["results"] + scores["fixtures"]}
    until = datetime.fromisoformat(scores["until"])
    tgl = f"{until.day} {BULAN[until.month - 1]} {until.year}"
    judul = f"{'[PREVIEW] ' if preview else ''}Sport Digest — {tgl} 11:00 WIB"
    scores_js = "const SCORES = " + json.dumps(scores, ensure_ascii=False) + ";"

    return f'''<!DOCTYPE html>
<html lang="id" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{judul}</title>
<meta name="description" content="Ringkasan berita olahraga harian dalam Bahasa Indonesia: sepakbola, motorsport, basket, tenis, bulutangkis, MMA. Dilengkapi papan skor dan jadwal klub besar Eropa.">
<meta name="theme-color" content="#121212">
<meta name="author" content="Sport Digest">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%23121212'/%3E%3Crect x='4' y='4' width='56' height='56' fill='none' stroke='%2312a150' stroke-width='3'/%3E%3Ctext x='32' y='44' font-family='Lora,Georgia,serif' font-size='30' font-weight='bold' fill='%23ffffff' text-anchor='middle'%3ESD%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sport Digest">
<meta property="og:title" content="Sport Digest — {tgl} 11:00 WIB">
<meta property="og:description" content="Ringkasan berita olahraga harian: sepakbola, motorsport, basket, tenis, bulutangkis, MMA. Plus skor dan jadwal klub besar Eropa.">
<meta property="og:url" content="https://dianagush.github.io/tech-news-digest/sport.html">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Sport Digest — {tgl} 11:00 WIB">
<meta name="twitter:description" content="Ringkasan berita olahraga harian plus skor dan jadwal klub besar Eropa.">
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
    <nav class="site-nav" aria-label="Navigasi halaman">
      <a href="index.html">Tech</a>
      <a href="sport.html" class="active" aria-current="page">Sport</a>
    </nav>
    <button class="theme-toggle" onclick="toggleTheme()" title="Ganti tema gelap/terang" aria-label="Ganti tema gelap atau terang">
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
    </button>
  </div>

  <!-- MASTHEAD -->
  <header class="masthead">
    <div class="kicker">Ringkasan Olahraga Harian</div>
    <h1>Sport Digest</h1>
    <div class="window">Jendela berita <strong>{scores["window"]}</strong> · <span id="win-dur">{durasi(scores)}</span> terakhir</div>
    <div class="rules"><div class="thick"></div><div class="thin"></div></div>
  </header>

  <!-- PAPAN SKOR -->
  <div class="scoreboard">
    <div class="scoreboard-head">
      <h3>Skor &amp; Jadwal</h3>
      <span class="stamp">Snapshot <b id="score-stamp">—</b></span>
    </div>
    <div class="sport-slicers" role="group" aria-label="Filter cabang olahraga">
{sport_filter_btns(present)}
    </div>
    <div id="scoreboard-body"></div>
    <div class="score-note">Sepakbola dibatasi pada klub besar Eropa; hasil memakai jendela waktu yang sama dengan berita. Sumber: ESPN &amp; TheSportsDB · snapshot diperbarui otomatis setiap hari kerja pukul 11:00 WIB.</div>
  </div>

  <!-- NEWS SLICERS -->
  <div class="slicers-row sticky" id="categorySlicers" role="group" aria-label="Filter kategori berita">
{slicers(counts, total)}
  </div>

  <div id="news-container">
{news_html}
  </div>

  <footer>Sport Digest · Disusun otomatis oleh Hermes Agent · Skor: ESPN &amp; TheSportsDB</footer>
</div>

<script>
// === SKOR (snapshot di-embed server-side oleh fetch_scores.py) ===
{scores_js}

function crest(url, nama) {{
  if (url) {{
    return '<img class="crest" src="' + url + '" alt="" loading="lazy" ' +
           'onerror="this.outerHTML=\\'<span class=&quot;crest-fb&quot;>' +
           nama.slice(0, 2).toUpperCase() + '</span>\\'">';
  }}
  return '<span class="crest-fb">' + nama.slice(0, 2).toUpperCase() + '</span>';
}}

function statusClass(state) {{
  if (state === 'in') return 'score-status live';
  if (state === 'post') return 'score-status post';
  return 'score-status';
}}

function rowMatch(g) {{
  const skor = (g.hs !== null && g.hs !== undefined)
    ? '<span class="score-num">' + g.hs + ' &ndash; ' + g.as + '</span>'
    : '<span class="score-num vs">vs</span>';
  return '<div class="score-row">' +
    '<div class="score-team">' + crest(g.hl, g.h) + '<span class="nm">' + g.h + '</span></div>' +
    skor +
    '<div class="score-team away">' + crest(g.al, g.a) + '<span class="nm">' + g.a + '</span></div>' +
    '<div class="' + statusClass(g.state) + '">' + g.st + '</div>' +
    '</div>';
}}

function rowSingle(g) {{
  return '<div class="score-single">' +
    '<div><span class="nm">' + (g.n || '') + '</span>' +
    (g.venue ? '<div class="venue">' + g.venue + '</div>' : '') + '</div>' +
    '<div class="' + statusClass(g.state) + '">' + g.st + '</div>' +
    '</div>';
}}

function renderGroups(groups) {{
  return groups.map(function (grp) {{
    const rows = grp.games.map(function (g) {{
      return (g.n !== undefined) ? rowSingle(g) : rowMatch(g);
    }}).join('');
    return '<div class="score-group" data-sport="' + grp.sport + '">' +
      '<div class="score-group-label">' + grp.label + '</div>' + rows + '</div>';
  }}).join('');
}}

function renderScores() {{
  const box = document.getElementById('scoreboard-body');
  document.getElementById('score-stamp').textContent = SCORES.updated;
  let html = '<div class="score-block-label">Hasil Terkini</div>';
  html += SCORES.results.length
    ? renderGroups(SCORES.results)
    : '<div class="score-empty">Tidak ada pertandingan klub besar yang selesai dalam jendela ini.</div>';
  if (SCORES.fixtures.length) {{
    html += '<div class="score-block-label">Jadwal Berikutnya</div>' + renderGroups(SCORES.fixtures);
  }}
  box.innerHTML = html;
}}
renderScores();

function filterSport(sport) {{
  document.querySelectorAll('.slicer-btn[data-sport]').forEach(function (b) {{
    b.classList.remove('active');
  }});
  const btn = document.querySelector('.slicer-btn[data-sport="' + sport + '"]');
  if (btn) btn.classList.add('active');
  document.querySelectorAll('.score-group').forEach(function (grp) {{
    grp.classList.toggle('hidden', sport !== 'all' && grp.dataset.sport !== sport);
  }});
}}

// === THEME TOGGLE ===
function toggleTheme() {{
  const root = document.documentElement;
  const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
  root.dataset.theme = next;
  localStorage.setItem('hermes-news-theme', next);
}}
(function () {{
  const saved = localStorage.getItem('hermes-news-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
}})();

// === CATEGORY SLICERS ===
const cards = document.querySelectorAll('.news-card, .lead');
const sections = document.querySelectorAll('section[data-section]');

function applyFilters(cat) {{
  cards.forEach(function (card) {{
    const cardCats = card.dataset.cat.split(' ');
    const catMatch = cat === 'all' || cardCats.includes(cat);
    card.classList.toggle('hidden', !catMatch);
  }});
  sections.forEach(function (section) {{
    const visible = section.querySelectorAll('.news-card:not(.hidden)');
    section.style.display = visible.length === 0 ? 'none' : '';
  }});
}}

const newsSlicers = document.querySelectorAll('#categorySlicers .slicer-btn');
newsSlicers.forEach(function (btn) {{
  btn.addEventListener('click', function () {{
    newsSlicers.forEach(function (b) {{ b.classList.remove('active'); }});
    btn.classList.add('active');
    applyFilters(btn.dataset.cat);
  }});
}});

// === DAILY BACKGROUND ===
(function () {{
  const variants = ['bg-circuit', 'bg-dots', 'bg-hex', 'bg-scan', 'bg-blueprint', 'bg-signal', 'bg-chip'];
  const d = new Date();
  const seed = d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
  document.body.classList.add(variants[seed % variants.length]);
}})();
</script>
</body>
</html>
'''
