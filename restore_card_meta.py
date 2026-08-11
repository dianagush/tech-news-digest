"""Pulihkan metadata footer kartu (tanggal + outlet) yang hilang akibat regresi 76982f8.

merge_design.py memakai regex yang tidak cocok dengan markup <span> bersarang,
sehingga tiap rebuild menulis <div class="foot"><span></span> — kosong. Kerusakan
mengunci diri: run berikutnya membaca file kosong itu sebagai sumber.

Script ini mengambil kembali pasangan (link -> "tanggal · outlet") dari commit
ea64217 (terakhir yang masih utuh) dan menyuntikkannya ke index.html. Kartu
dicocokkan lewat URL, bukan urutan, jadi aman kalau urutan berubah.

Idempoten: kartu yang footernya sudah terisi dilewati.
Jalankan: python restore_card_meta.py
"""
import pathlib, re, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parent
IDX = REPO / "index.html"
DONOR = "ea64217"

# ---------- 1. ambil markup donor ----------
r = subprocess.run(["git", "show", f"{DONOR}:index.html"], cwd=REPO,
                   capture_output=True, text=True, encoding="utf-8")
if r.returncode != 0:
    sys.exit(f"FATAL: gagal baca {DONOR}: {r.stderr.strip()}")
donor = r.stdout

# ---------- 2. peta href -> footer dari donor ----------
FOOT = re.compile(
    r'<div class="foot"><span>(?P<meta>.*?)</span>'
    r'<a class="read-more" href="(?P<href>[^"]+)"', re.S)

meta_by_href = {}
for m in FOOT.finditer(donor):
    meta = m.group("meta").strip()
    if meta:
        meta_by_href[m.group("href")] = meta
print(f"donor {DONOR}: {len(meta_by_href)} kartu bermetadata")

# ---------- 3. suntik ke index.html ----------
html = IDX.read_text(encoding="utf-8")
filled = skipped = missing = 0
missing_hrefs = []

def fix(m):
    global filled, skipped, missing
    if m.group("meta").strip():
        skipped += 1
        return m.group(0)
    meta = meta_by_href.get(m.group("href"))
    if not meta:
        missing += 1
        missing_hrefs.append(m.group("href"))
        return m.group(0)
    filled += 1
    return (f'<div class="foot"><span>{meta}</span>'
            f'<a class="read-more" href="{m.group("href")}"')

out = FOOT.sub(fix, html)
IDX.write_text(out, encoding="utf-8")

# ---------- 4. lapor ----------
print(f"diisi   : {filled}")
print(f"dilewati: {skipped} (sudah terisi)")
print(f"tak ada : {missing}")
for h in missing_hrefs:
    print(f"   ! {h[:80]}")
print(f"span.source : {out.count(chr(60) + 'span class=' + chr(34) + 'source' + chr(34) + chr(62))}")
print(f"date-main   : {out.count('class=' + chr(34) + 'date-main' + chr(34))}")
print(f"foot kosong : {out.count('<div class=' + chr(34) + 'foot' + chr(34) + '><span></span>')}")
