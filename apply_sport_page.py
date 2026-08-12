"""Tulis/rebuild sport.html (halaman live).

Idempoten: menjalankan berulang menghasilkan file byte-identical selama data
tidak berubah. Kartu berita yang sudah ada di sport.html DIPERTAHANKAN — hanya
saat file belum ada, kartu benih dari sport_page.SAMPLE yang dipakai.

CATATAN (audit P2 2026-08-11): skrip ini TIDAK menyentuh index.html. Topbar dan
CSS nav index.html dimiliki merge_design.py; templatenya sudah memuat
`<nav class="site-nav">` dan CSS nav ada di tjp-design.css (base bersama).
Menulis index.html dari dua skrip = multi-writer seam yang berosilasi.

Jalankan: python apply_sport_page.py
"""
import json
import pathlib
import sys

import sport_page

REPO = pathlib.Path(__file__).resolve().parent
CSS_BASE = REPO / "tjp-design.css"
CSS_SPORT = REPO / "sport-design.css"
CACHE = REPO / "scores-cache.json"
PAGE = REPO / "sport.html"


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


if __name__ == "__main__":
    main()
