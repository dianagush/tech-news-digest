"""Tulis/rebuild sport.html (halaman live) + sisipkan nav ke index.html.

Idempoten: menjalankan berulang menghasilkan file byte-identical selama data
tidak berubah. Kartu berita yang sudah ada di sport.html DIPERTAHANKAN — hanya
saat file belum ada, kartu benih dari sport_page.SAMPLE yang dipakai.

Jalankan: python apply_sport_page.py
"""
import json
import pathlib
import re
import sys

import sport_page

REPO = pathlib.Path(__file__).resolve().parent
CSS_BASE = REPO / "tjp-design.css"
CSS_SPORT = REPO / "sport-design.css"
CACHE = REPO / "scores-cache.json"
PAGE = REPO / "sport.html"
INDEX = REPO / "index.html"

NAV = '''    <nav class="site-nav" aria-label="Navigasi halaman">
      <a href="index.html" class="active" aria-current="page">Tech</a>
      <a href="sport.html">Sport</a>
    </nav>'''

# index.html tidak memuat sport-design.css, jadi aturan nav ditulis eksplisit di
# sini. (Percobaan sebelumnya menyaring baris ber-awalan ".site-nav" dari
# sport-design.css — hasilnya rule terpotong di tengah dan baris dari media
# query ikut terseret. Blok utuh, jangan ekstraksi per-baris.)
CSS_NAV = """
  .site-nav { display: flex; gap: 1.1rem; align-items: center; }
  .site-nav a {
    font-family: 'Lato', sans-serif;
    font-size: 0.68rem; letter-spacing: 0.14em; text-transform: uppercase;
    font-weight: 700; color: var(--text2);
    padding-bottom: 0.2rem; border-bottom: 2px solid transparent;
  }
  .site-nav a:hover { color: var(--text); text-decoration: none; }
  .site-nav a.active { color: var(--accent); border-bottom-color: var(--accent); }
  @media (max-width: 768px) {
    .site-nav { gap: 0.8rem; }
    .site-nav a { font-size: 0.6rem; letter-spacing: 0.1em; }
  }
  @media print {
    .site-nav { display: none; }
  }
"""


def sync_index():
    """Ganti `.edition` di index.html dengan nav dua halaman + tempel CSS nav.

    Hanya menyentuh dua hal itu; CSS/JS/kartu index.html lain tidak diubah.
    """
    if not INDEX.exists():
        return "index.html tidak ada — dilewati"
    html = INDEX.read_text(encoding="utf-8")
    asli = html

    if 'class="site-nav"' not in html:
        html, n = re.subn(r'    <div class="edition">.*?</div>\n', NAV + "\n",
                          html, count=1, flags=re.S)
        if not n:
            return "GAGAL: blok .edition tidak ditemukan"

    style = re.search(r"<style>(.*?)</style>", html, re.S)
    if not style:
        return "GAGAL: blok <style> tidak ditemukan"
    if ".site-nav" not in style.group(1):
        html = html.replace("</style>", CSS_NAV + "</style>", 1)

    if html != asli:
        INDEX.write_text(html, encoding="utf-8")
        return "nav disisipkan"
    return "sudah sinkron"


def main():
    if not CACHE.exists():
        sys.exit("FATAL: scores-cache.json belum ada — jalankan `python fetch_scores.py` dulu")
    css = CSS_BASE.read_text(encoding="utf-8") + "\n" + CSS_SPORT.read_text(encoding="utf-8")
    scores = json.loads(CACHE.read_text(encoding="utf-8"))

    news = None
    if PAGE.exists():
        news = sport_page.extract_news(PAGE.read_text(encoding="utf-8"))

    html = sport_page.render(scores, css, news=news, preview=False)
    berubah = (not PAGE.exists()) or PAGE.read_text(encoding="utf-8") != html
    if berubah:
        PAGE.write_text(html, encoding="utf-8")

    nr = sum(len(g["games"]) for g in scores["results"])
    nf = sum(len(g["games"]) for g in scores["fixtures"])
    print(f"tulis   : {PAGE.name} ({len(html):,} bytes) — {'diperbarui' if berubah else 'tidak berubah'}")
    print(f"kartu   : {news[2] if news else len(sport_page.SAMPLE)} "
          f"({'dipertahankan dari halaman lama' if news else 'benih contoh'})")
    print(f"jendela : {scores['window']} ({sport_page.durasi(scores)})")
    print(f"hasil   : {nr} laga / {len(scores['results'])} grup")
    print(f"jadwal  : {nf} laga / {len(scores['fixtures'])} grup")
    print(f"index   : {sync_index()}")


if __name__ == "__main__":
    main()
