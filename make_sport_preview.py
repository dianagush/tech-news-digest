"""Bangun sport-preview.html untuk sign-off — TIDAK pernah menulis file live.

Template ada di sport_page.py (dipakai bersama apply_sport_page.py) sehingga
preview dan halaman produksi tidak bisa berbeda diam-diam.

Jalankan: python make_sport_preview.py
"""
import json
import pathlib
import sys

import sport_page

REPO = pathlib.Path(__file__).resolve().parent
CSS_BASE = REPO / "tjp-design.css"
CSS_SPORT = REPO / "sport-design.css"
CACHE = REPO / "scores-cache.json"
OUT = REPO / "sport-preview.html"


def main():
    if not CACHE.exists():
        sys.exit("FATAL: scores-cache.json belum ada — jalankan `python fetch_scores.py --dump`")
    css = CSS_BASE.read_text(encoding="utf-8") + "\n" + CSS_SPORT.read_text(encoding="utf-8")
    scores = json.loads(CACHE.read_text(encoding="utf-8"))

    html = sport_page.render(scores, css, news=None, preview=True)
    OUT.write_text(html, encoding="utf-8")

    nr = sum(len(g["games"]) for g in scores["results"])
    nf = sum(len(g["games"]) for g in scores["fixtures"])
    print(f"CSS     : {CSS_BASE.name} + {CSS_SPORT.name} ({len(css):,} bytes)")
    print(f"tulis   : {OUT.name} ({len(html):,} bytes)")
    print(f"jendela : {scores['window']} ({sport_page.durasi(scores)})")
    print(f"hasil   : {nr} laga / {len(scores['results'])} grup")
    print(f"jadwal  : {nf} laga / {len(scores['fixtures'])} grup")


if __name__ == "__main__":
    main()
