#!/usr/bin/env bash
# Refresh skor sore/malam — dipanggil cron no_agent pukul 18:00 & 22:00 WIB.
# Jendela: kemarin 11:00 → hari ini 11:00 WIB (sama dengan edisi pagi, header
# halaman tidak berubah). Hasil = laga selesai sejak `since` — jadi laga malam
# Eropa/NBA yang selesai setelah jam 11:00 tetap muncul sebagai hasil.
# stdout non-kosong = laporan dikirim; exit non-zero = alert cron.
set -euo pipefail
REPO="C:/Users/DianAgusHermawan/OneDrive - PLN/Hermes/main"
SINCE=$(date -d "yesterday 11:00" +"%Y-%m-%d %H:%M")
UNTIL=$(date +"%Y-%m-%d")" 11:00"
cd "$REPO"
python fetch_scores.py --since "$SINCE" --until "$UNTIL"
# rebuild halaman supaya masthead + konstanta SCORES ikut window/cache terbaru
# (kartu berita dipertahankan — apply_sport_page hanya menormalkan struktur)
python apply_sport_page.py
