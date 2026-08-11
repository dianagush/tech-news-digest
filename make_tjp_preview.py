"""Bangun design-preview.html dari index.html + tjp-design.css.

CSS TIDAK lagi disimpan di script ini (dulu ada 3 salinan: index.html,
design-preview.html, dan string di sini — ubah satu, dua lainnya basi).
Sumber tunggal sekarang: tjp-design.css.

Struktur HTML/JS tidak disentuh sama sekali — hanya blok <style>, <link> font,
dan palet favicon.

Jalankan: python make_tjp_preview.py
"""
import re, pathlib, sys

REPO = pathlib.Path(__file__).resolve().parent
SRC = REPO / "index.html"
CSS_FILE = REPO / "tjp-design.css"
OUT = REPO / "design-preview.html"

html = SRC.read_text(encoding="utf-8")
css = CSS_FILE.read_text(encoding="utf-8")

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Lato:wght@400;700;900&display=swap" rel="stylesheet">
"""

# ---------------------------------------------------------------- rakit
m = re.search(r"<style>.*?</style>", html, re.S)
if not m:
    sys.exit("FATAL: blok <style> tidak ditemukan di index.html")
out = html[:m.start()] + "<style>" + css + "</style>" + html[m.end():]

# sisipkan font sekali saja (idempoten)
if "fonts.googleapis" not in out:
    out = out.replace("<style>", FONTS + "<style>", 1)

# penanda preview
if "[PREVIEW TJP]" not in out:
    out = out.replace("<title>", "<title>[PREVIEW TJP] ", 1)
out = out.replace('data-theme="dark"', 'data-theme="light"', 1)

# favicon ikut palet TJP
out = (out.replace("%23e0483e", "%23dc2027")
          .replace("%23f0ece4", "%23ffffff")
          .replace("%23121212'/%3E%3Crect", "%23000000'/%3E%3Crect")
          .replace("font-family='Georgia,serif'", "font-family='Lora,Georgia,serif'"))
out = out.replace('<meta name="theme-color" content="#121212">',
                  '<meta name="theme-color" content="#ffffff">', 1)

OUT.write_text(out, encoding="utf-8")

# ---------------------------------------------------------------- lapor
n = lambda pat: len(re.findall(pat, out))
print(f"sumber CSS : {CSS_FILE.name} ({len(css):,} bytes)")
print(f"tulis      : {OUT.name} ({len(out):,} bytes)")
print(f"kartu      : {n(r'class=.news-card')}")
print(f"fonts      : {'OK' if 'fonts.googleapis' in out else 'HILANG'}")
print(f"Lora/Lato  : {out.count('Lora')}/{out.count('Lato')} rujukan")
print(f"badge      : {n(r'.news-card.data-cat=')} aturan")
print(f"span.source: {out.count(chr(34) + 'source' + chr(34))}")
