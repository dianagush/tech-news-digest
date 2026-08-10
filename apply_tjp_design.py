"""Terapkan CSS desain TJP dari design-preview.html ke index.html.

Hanya menyentuh: blok <style>, <link> Google Fonts, palet favicon.
Struktur HTML, kartu berita, JS (LIVE_IHSG/LIVE_USDIDR, slicer, theme,
win-dur) tidak disentuh sama sekali.

Idempoten: menjalankan dua kali menghasilkan file yang sama.
Default tema TETAP dark (perilaku lama) — desain jalan di dua tema.

Jalankan: python apply_tjp_design.py
"""
import re, pathlib, shutil, sys

REPO = pathlib.Path(__file__).resolve().parent
PREVIEW, TARGET = REPO / "design-preview.html", REPO / "index.html"

preview = PREVIEW.read_text(encoding="utf-8")
target = TARGET.read_text(encoding="utf-8")
before = target

# ---------- 1. ambil CSS + blok font dari preview ----------
m_css = re.search(r"<style>(.*?)</style>", preview, re.S)
if not m_css:
    sys.exit("FATAL: <style> tidak ditemukan di design-preview.html")
css = m_css.group(1)

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700'
         '&family=Lato:wght@400;700;900&display=swap" rel="stylesheet">\n')

# ---------- 2. ganti blok <style> di index.html ----------
m_t = re.search(r"<style>.*?</style>", target, re.S)
if not m_t:
    sys.exit("FATAL: <style> tidak ditemukan di index.html")
target = target[:m_t.start()] + "<style>" + css + "</style>" + target[m_t.end():]

# ---------- 3. sisipkan font sekali saja (idempoten) ----------
if "fonts.googleapis" not in target:
    target = target.replace("<style>", FONTS + "<style>", 1)

# ---------- 4. favicon ikut palet TJP ----------
target = (target.replace("%23e0483e", "%23dc2027")
                .replace("%23f0ece4", "%23ffffff")
                .replace("font-family='Georgia,serif'", "font-family='Lora,Georgia,serif'"))

TARGET.write_text(target, encoding="utf-8")

# ---------- 5. lapor ----------
def n(pat, s): return len(re.findall(pat, s))
print(f"index.html : {len(before):,} -> {len(target):,} bytes")
print(f"kartu      : {n(r'class=.news-card', target)}")
print(f"fonts      : {'OK' if 'fonts.googleapis' in target else 'HILANG'}")
print(f"Lora/Lato  : {target.count('Lora')}/{target.count('Lato')} rujukan")
print(f"aksen TJP  : {'OK' if '--accent: #dc2027' in target else 'HILANG'}")
print(f"palet lama : {'BERSIH' if not re.search(r'e0483e|f0ece4|f4f1ea', target) else 'MASIH ADA'}")
has_windur = 'id="win-dur"' in target
print(f"win-dur    : {'OK' if has_windur else 'HILANG'}")
print(f"LIVE data  : {'OK' if 'const LIVE_IHSG' in target else 'HILANG'}")
