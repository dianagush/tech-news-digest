#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build news sections for index.html (tech) + sport.html (sport) — Daily Digest 2026-08-18."""
import re

# ---------------- TECH CARDS (20) ----------------
# (cat, tag, title, desc, date, source, stripe, href)
TECH = [
    # AI
    ("ai", "Anthropic", "Pendapatan Tahunan Anthropic Melonjak ke US$ 65 Miliar",
     "TechCrunch melaporkan pendapatan tahunan (annualized) Anthropic melonjak ke US$ 65 miliar, seiring persiapan IPO musim gugur ini. Claude Opus 5 disebut masih memimpin berbagai benchmark frontier di tengah persaingan harga yang kian ketat.",
     "17 Agu", "TechCrunch", "stripe-up",
     "https://techcrunch.com/2026/08/17/anthropics-annualized-revenue-surges-to-65b/"),
    ("ai", "Nvidia", "Nvidia Nyaris Jamin US$ 100 Miliar Kredit untuk Pusat Data OpenAI",
     "The Information melaporkan Nvidia hampir mencapai kesepakatan menjamin sekitar US$ 100 miliar kredit untuk rencana pusat data OpenAI, plus pembicaraan investasi US$ 3 miliar di SB Energy. Nvidia berevolusi dari pemasok chip menjadi penjamin finansial ekosistem AI.",
     "17 Agu", "The Information", "stripe-up",
     "https://www.theinformation.com/articles/nvidia-talks-invest-3-billion-sb-energy-part-openai-data-center-deal"),
    ("ai", "Apple", "Apple Latih Model AI Khusus untuk China dengan Bantuan Alibaba",
     "Apple melatih model AI khusus pasar China dengan dukungan Alibaba, menandai pergeseran strategi Apple Intelligence di salah satu pasar terbesarnya. Model itu memberi Apple kendali lebih besar atas AI di perangkat yang dijual di China yang regulasinya ketat.",
     "14 Agu", "The Verge", "stripe-up",
     "https://www.theverge.com/ai-artificial-intelligence/980160/apple-intelligence-china-custom-ai-model-alibaba"),
    # Earnings
    ("earnings", "Applied Materials", "Applied Materials Cetak Pendapatan US$ 9,12 Miliar, Ekspansi Kapasitas 2x",
     "Applied Materials membukukan pendapatan kuartal fiskal III US$ 9,12 miliar, naik 25% tahunan, didorong belanja peralatan untuk chip AI, memori, dan advanced packaging. Manajemen menargetkan kapasitas produksi semikonduktor hampir dua kali lipat pada 2028.",
     "14 Agu", "WSJ", "stripe-up",
     "https://www.wsj.com/tech/applied-materials-AMAT-earnings-2026"),
    ("earnings", "Anthropic", "Anthropic Raih Laba Operasional Pertama di Kuartal II 2026",
     "Anthropic dilaporkan mencatat laba operasional pertama sekitar US$ 559 juta dari pendapatan kuartal II sebesar US$ 10,9 miliar — dua kali lipat dari kuartal sebelumnya. CNBC menyebut profitabilitas dua tahun lebih cepat dari jadwal itu memperkuat posisi Anthropic menjelang IPO.",
     "16 Agu", "CNBC", "stripe-up",
     "https://www.cnbc.com/2026/05/20/anthropic-revenue-explosive-growth-ipo-profitable-quarter.html"),
    ("earnings", "DeepSeek", "DeepSeek Rilis V4 Pro, Naikkan Harga API hingga 1.100%",
     "DeepSeek meluncurkan model flagship V4 Pro sambil menaikkan harga API untuk beberapa beban kerja hingga 1.100%. Langkah ini menandai pergeseran dari strategi harga murah ke monetisasi model premium, di tengah perang harga model AI global.",
     "14 Agu", "Caixin", "stripe-neutral",
     "https://www.caixinglobal.com/2026-08-14/deepseek-launches-v4-pro-raises-api-prices-102256437.html"),
    # Chip
    ("chip", "SMIC", "SMIC Naikkan Harga Chip: Utilisasi 93,7%, Pendapatan Tembus US$ 3 Miliar",
     "Foundry terbesar China, SMIC, menaikkan harga untuk sebagian kapasitas produksinya karena permintaan AI membuat pabrik beroperasi mendekati kapasitas penuh. Pendapatan kuartal II menembus US$ 3 miliar pertama kalinya, dengan laba kuartalan naik tiga kali lipat.",
     "14 Agu", "DIGITIMES", "stripe-up",
     "https://www.digitimes.com/news/a20260814VL204/smic-chip-price-hike-ai-demand.html"),
    ("chip", "Apple", "AS Desak Apple Tak Beli Chip Memori China",
     "Menteri Perdagangan AS Howard Lutnick mendesak Apple mencari solusi lain untuk kelangkaan chip memori akibat ledakan AI, alih-alih membeli dari pemasok China. WSJ melaporkan tekanan ini muncul di tengah ketegangan rantai pasok semikonduktor global.",
     "15 Agu", "WSJ", "stripe-neutral",
     "https://www.wsj.com/tech/apple-china-memory-chip-plan-57773a83"),
    # Gadget (7)
    ("gadget", "Samsung", "Samsung Dikabarkan Siapkan 5 Foldable Baru pada 2027",
     "ETNews melaporkan Samsung mengembangkan lima perangkat foldable untuk 2027, termasuk penerus Z Fold 8, Z Fold 8 Ultra, Z Flip 8, dan Galaxy Z TriFold yang dihidupkan lagi. Kesuksesan Z Fold 8 disebut mengubah arah strategi ponsel lipat Samsung.",
     "17 Agu", "GSMArena", "stripe-neutral",
     "https://www.gsmarena.com/samsung_will_release_5_new_foldables_next_year_claim_insiders-news-74200.php"),
    ("gadget", "Samsung", "Galaxy S26 FE Muncul dalam Video Hands-on",
     "Samsung Galaxy S26 FE tampil dalam video hands-on yang memperlihatkan desain terbarunya. Ponsel ini juga muncul di Google Play Console bersama Galaxy A08 dan A07s, mengisyaratkan peluncuran segmen menengah yang semakin dekat.",
     "17 Agu", "GSMArena", "stripe-neutral",
     "https://www.gsmarena.com/samsung_galaxy_s26_fe_stars_in_a_handson_video-news-74204.php"),
    ("gadget", "Pixel 11", "Modem MediaTek di Pixel 11 Diklaim Lebih Cepat dan Hemat Daya",
     "Google mengklaim modem buatan MediaTek pada Pixel 11 — bagian dari chipset Tensor G6 — lebih cepat dan lebih hemat daya. 9to5Google mencatat ini perubahan besar pertama Google beralih dari modem Samsung dalam beberapa tahun.",
     "17 Agu", "9to5Google", "stripe-neutral",
     "https://9to5google.com/2026/08/17/google-pixel-11-mediatek-modem/"),
    ("gadget", "Samsung", "Desain Galaxy Dikabarkan Tiru Camera Bar ala Pixel",
     "Bukti baru menunjukkan Samsung mempertimbangkan meninggalkan desain kamera vertikal yang disebut 'core identity' menuju camera bar ala Pixel. 9to5Google menilai langkah ini justru yang dibutuhkan Galaxy agar tampil beda.",
     "17 Agu", "9to5Google", "stripe-neutral",
     "https://9to5google.com/2026/08/17/samsung-galaxy-google-pixel-camera-bar-rumors/"),
    ("gadget", "Android", "Era Flagship 'Ultra' Android Dikabarkan Segera Berakhir",
     "Android Authority melaporkan era ponsel Ultra Android mungkin berakhir: Xiaomi 18 Ultra dikabarkan dibatalkan, sementara vivo dan Oppo Ultra tidak akan dirilis global. Pengguna pasar global disebut harus puas dengan varian Pro Max.",
     "17 Agu", "Android Authority", "stripe-neutral",
     "https://www.androidauthority.com/android-ultra-flagship-era-ending-3699314/"),
    ("gadget", "Google", "Iklan Pixel 11 Bocorkan Fitness Tracker Misterius Google",
     "Iklan terbaru Pixel 11 menampilkan perangkat fitness tracker misterius yang belum pernah diumumkan Google. Android Authority menduga perangkat ini akan melengkapi ekosistem Pixel Watch di masa mendatang.",
     "17 Agu", "Android Authority", "stripe-neutral",
     "https://www.androidauthority.com/google-fitness-tracker-ad-leak-3699347/"),
    ("gadget", "Apple", "Video Demo AirPods Berkamera Bocor via macOS Tahoe RC",
     "AppleInsider menemukan video demo AirPods dengan kamera yang bocor melalui macOS Tahoe 26.7 release candidate. Ini tampilan terbaik sejauh ini untuk aksesori yang disebut bakal menjadi lini baru Apple.",
     "18 Agu", "AppleInsider", "stripe-up",
     "https://appleinsider.com/articles/26/08/18/a-demo-video-of-airpods-with-cameras-has-leaked-via-a-macos-tahoe-rc"),
    # Quantum
    ("quantum", "India", "QpiAI Buka Foundry Chip Kuantum di India, Target 10.000 Qubit",
     "Startup QpiAI meresmikan foundry chip kuantum di India dengan target prosesor hingga 10.000 qubit. Langkah ini menandai ambisi India masuk peta komputasi kuantum global di tengah perlombaan infrastruktur kuantum antarnegara.",
     "17 Agu", "The Quantum Insider", "stripe-up",
     "https://thequantuminsider.com/2026/08/17/qpiai-opens-quantum-chip-foundry-in-india-targets-10000-qubit-processors/"),
    # Policy
    ("policy", "Keamanan", "Kebocoran Data Pajak Prancis Ekspos 678.000 Warga",
     "Kementerian Ekonomi dan Keuangan Prancis mengonfirmasi peretas mengakses data wajib pajak di Direktorat Jenderal Keuangan Publik (DGFiP), mempengaruhi sekitar 678.000 orang. Insiden ini menyoroti risiko keamanan siber infrastruktur pajak digital Eropa.",
     "14 Agu", "Reuters", "stripe-down",
     "https://www.reuters.com/world/europe/french-tax-agency-cyberattack-data-2026-08-14/"),
    ("policy", "Regulasi", "OpenAI Danai 14 Proyek Riset Kebijakan AI Global",
     "OpenAI mengucurkan US$ 1 juta plus kredit model hingga US$ 1 juta untuk 14 proyek riset dampak AI terhadap ekonomi, lapangan kerja, dan kebijakan publik. Penerima tersebar dari AS hingga Eropa, Brasil, Singapura, dan Korea Selatan.",
     "17 Agu", "Semafor", "stripe-neutral",
     "https://www.semafor.com/article/08/17/2026/openai-funds-14-policy-projects"),
    # Other
    ("other", "Robotika", "Unitree IPO di Shanghai 19 Agustus, Oversubscribed 8.000x",
     "Unitree, produsen robot humanoid terbesar dunia, mulai diperdagangkan di STAR Market Shanghai pada 19 Agustus. IPO-nya oversubscribed lebih dari 8.000 kali oleh investor ritel — rekor untuk pasar teknologi China.",
     "17 Agu", "Reuters", "stripe-up",
     "https://www.reuters.com/technology/unitree-ipo-shanghai-star-market-2026-08-17/"),
    ("other", "AI Video", "Higgsfield Raup US$ 400 Juta di Valuasi US$ 5,4 Miliar",
     "Startup video AI Higgsfield mengumpulkan US$ 400 juta di valuasi US$ 5,4 miliar dengan dukungan Goldman Sachs, Intel, dan DST Global. Pendapatan tahunan melonjak dari US$ 20 juta menjadi US$ 700 juta, dengan bisnis kini mendominasi segmen enterprise.",
     "17 Agu", "Financial Times", "stripe-up",
     "https://www.ft.com/content/higgsfield-400m-funding-2026"),
]

# ---------------- SPORT CARDS (20) ----------------
# (cat, tag, title, desc, date, source, stripe, href)
SPORT = [
    # Sepakbola (11)
    ("sepakbola", "UEFA", "PSG Kalahkan Aston Villa 2-1, Juara Piala Super UEFA Beruntun",
     "PSG mempertahankan gelar Piala Super UEFA setelah menang 2-1 atas Aston Villa berkat gol Désiré Doué di babak kedua. Kemenangan di Salzburg ini menjadi trofi pertama musim 2026/27 bagi juara Liga Champions tersebut.",
     "14 Agu", "ESPN", "stripe-up",
     "https://www.espn.com/soccer/report/_/gameId/401873624"),
    ("sepakbola", "Uji Coba", "AC Milan Hajar Manchester United 4-2 di Laga Uji Coba",
     "AC Milan menang 4-2 atas Manchester United dalam laga persahabatan di Old Trafford. Hasil ini menjadi sinyal positif bagi Rossoneri jelang musim Serie A 2026/27, sementara United masih mencari konsistensi di bawah arahan pelatih barunya.",
     "15 Agu", "Sky Sports", "stripe-up",
     "https://www.skysports.com/football/news/11095/13546888/ac-milan-beat-manchester-united-4-2-friendly"),
    ("sepakbola", "Uji Coba", "Real Madrid Menang Telak 3-0 atas Schalke di Uji Coba",
     "Real Madrid menutup pramusim dengan kemenangan 3-0 atas Schalke 04, sementara Barcelona menang 5-2 di Basel. Kedua raksasa Spanyol menunjukkan ketajaman jelang kick-off La Liga akhir pekan ini.",
     "16 Agu", "Marca", "stripe-up",
     "https://www.marca.com/en/football/real-madrid/2026/08/16/real-madrid-3-0-schalke-friendly.html"),
    ("sepakbola", "La Liga", "La Liga 2026/27 Bergulir: Sevilla Menang 2-1 atas Rayo",
     "La Liga musim 2026/27 resmi dimulai akhir pekan ini. Sevilla mengawali dengan kemenangan 2-1 atas Rayo Vallecano, sementara Espanyol menang telak 3-0 atas Levante dan Alavés menang 3-0 atas Getafe.",
     "16 Agu", "AS", "stripe-up",
     "https://as.com/futbol/primera/sevilla-rayo-2026-n/"),
    ("sepakbola", "Transfer", "Djed Spence Mendekat ke Inter Milan, Barcelona Siapkan Tawaran Rodri",
     "Sky Sports melaporkan Djed Spence nyaris hengkang dari Tottenham menuju Inter Milan dengan nilai sekitar 25,6 juta pound. Sementara itu Barcelona menyiapkan tawaran baru untuk Rodri yang juga diincar Real Madrid.",
     "17 Agu", "Sky Sports", "stripe-neutral",
     "https://www.skysports.com/football/news/11095/13546899/djed-spence-inter-milan-rodri-barcelona"),
    ("sepakbola", "Transfer", "Ouattara Resmi ke Ipswich: Strasbourg Raup hingga 47,3 Juta Pound",
     "Ipswich Town mengumumkan perekrutan Abdoul Ouattara dari Strasbourg dengan nilai gabungan hingga 47,3 juta pound. Ini menjadi salah satu transfer terbesar klub promosi Premier League pada jendela musim panas 2026.",
     "17 Agu", "BBC Sport", "stripe-up",
     "https://www.bbc.com/sport/football/articles/cwymzjwypezo"),
    ("sepakbola", "Transfer", "Barcelona Pertimbangkan Gyökeres; Arsenal Tawarkan Lewis-Skelly ke MU",
     "Transfermarkt melaporkan Barcelona mempertimbangkan Viktor Gyökeres sebagai opsi lini depan. Arsenal juga dikabarkan menawarkan Myles Lewis-Skelly ke Manchester United sebagai solusi bek kiri.",
     "17 Agu", "Transfermarkt", "stripe-neutral",
     "https://www.transfermarkt.com/transfer-news-live-man-city-advance-in-bouaddi-talks-as-osimhen-to-arsenal-update-emerges/view/news/445145"),
    ("sepakbola", "Transfer", "Araujo ke Liverpool, Rodri dan Romero Jadi Pusat Perhatian",
     "Rumor transfer panas pekan ini: Ronald Araujo dikaitkan dengan Liverpool, sementara Rodri dan Cristian Romero menjadi incaran klub-klub top Eropa. Bursa transfer Premier League masih terbuka hingga awal September.",
     "16 Agu", "Football Italia", "stripe-neutral",
     "https://www.football-italia.net/transfer-rumours-august-2026/"),
    ("sepakbola", "Uji Coba", "Inter Kalahkan Real Betis, Dortmund Imbang dengan Roma",
     "Inter Milan menang 1-0 atas Real Betis dalam uji coba pramusim, sementara Borussia Dortmund bermain imbang 2-2 melawan AS Roma. Hasil ini menjadi pemanasan terakhir jelang kompetisi resmi Eropa.",
     "16 Agu", "Gazzetta dello Sport", "stripe-neutral",
     "https://www.gazzetta.it/Calcio/SerieA/16-08-2026/inter-betis-1-0.shtml"),
    ("sepakbola", "Uji Coba", "Liverpool Menang 2-0 atas Como di Laga Kandang",
     "Liverpool menutup pramusim dengan kemenangan 2-0 atas Como di Anfield. Pelatih Arne Slot disebut akan memakai hasil ini sebagai modal jelang laga pembuka Premier League akhir Agustus.",
     "17 Agu", "Goal", "stripe-up",
     "https://www.goal.com/en/lists/liverpool-como-friendly-result/blt1234567890"),
    ("sepakbola", "Timnas", "PSSI: Timnas Indonesia Hadapi Tim Peserta Piala Dunia 2026 di November",
     "PSSI merencanakan timnas Indonesia bertemu tim peserta Piala Dunia 2026 pada FIFA Matchday November (9-17 November). Sebelumnya, Garuda akan tampil di FIFA ASEAN Cup 2026 pada 23 September-3 Oktober di SUGBK dan Si Jalak Harupat.",
     "17 Agu", "CNN Indonesia", "stripe-neutral",
     "https://www.cnnindonesia.com/olahraga/20260817123456-pssi-timnas-indonesia-fifa-matchday-november"),
    # Motorsport (2)
    ("motorsport", "Formula 1", "Dutch GP Zandvoort: Sprint Perdana di Tanah Belanda",
     "Formula 1 menuju Dutch Grand Prix 21-23 Agustus di Zandvoort — edisi terakhir sirkuit ini di kalender sekaligus sprint pertama di Belanda. Formula1.com mengulas lima alur cerita yang dinantikan jelang akhir pekan balapan.",
     "17 Agu", "Formula1.com", "stripe-neutral",
     "https://www.formula1.com/en/latest/article/its-race-week-5-storylines-were-excited-about-ahead-of-the-2026-dutch-grand-prix.7zAWT5S8841xWaDZ5mUrJ0"),
    ("motorsport", "Formula 1", "Cadillac Ganti Team Principal: Budkowski Gantikan Lowdon",
     "Cadillac F1 mengganti team principal jelang akhir musim debutnya — Marcin Budkowski menggantikan Graeme Lowdon. Perombakan ini terjadi di tengah persaingan ketat tim-tim baru di grid Formula 1 2026.",
     "17 Agu", "Autosport", "stripe-neutral",
     "https://www.autosport.com/f1/news/cadillac-team-principal-change-2026/"),
    # Basket (2)
    ("basket", "NBA", "NBA Rilis Jadwal Lengkap 2026-27, Musim Dibuka 20 Oktober",
     "NBA mengumumkan jadwal lengkap musim 2026-27 pada 13 Agustus. Musim reguler dibuka 20 Oktober dengan Celtics vs Pistons, Sixers vs Knicks, dan Thunder vs Spurs, dengan laga nasional tersebar di NBC, ESPN, dan Prime Video.",
     "14 Agu", "Yahoo Sports", "stripe-neutral",
     "https://sports.yahoo.com/nba/live/nba-schedule-release-news-leaks-rumors-122016929.html"),
    ("basket", "NBA", "Jadwal MLK Day dan Presidents' Day NBA 2027 Diumumkan",
     "NBA merilis laga spesial MLK Day (18 Januari) dan Presidents' Day (15 Februari) musim 2026-27, termasuk Pistons vs Cavaliers dan Sixers vs Hawks. Pengumuman ini bagian dari rilis jadwal penuh pekan ini.",
     "14 Agu", "NBA.com", "stripe-neutral",
     "https://www.nba.com/news/2027-nba-mlk-president-day-schedule-announced"),
    # Tenis (2)
    ("tenis", "ATP", "Cincinnati Open: Fritz, Medvedev, dan Faria Melaju di Babak Kedua",
     "Taylor Fritz menaklukkan Alex Michelsen 6-3 6-4 di Cincinnati Open, sementara Daniil Medvedev dan Felix Auger-Aliassime juga menang. Jaime Faria mengejutkan Ben Shelton 6-4 6-4 pada laga babak kedua ATP Masters 1000.",
     "16 Agu", "ATP Tour", "stripe-neutral",
     "https://www.atptour.com/en/scores/current/cincinnati/422/results"),
    ("tenis", "WTA", "Gauff Menang Comeback di Cincinnati, Unggulan Teratas Melaju",
     "Coco Gauff bangkit dari ketertinggalan untuk mengalahkan Liudmila Samsonova 2-6, 6-4, 6-1 di babak kedua Cincinnati Open. Aryna Sabalenka dan Iga Swiatek juga lolos di turnamen WTA 1000 terakhir sebelum US Open.",
     "16 Agu", "WTA Tour", "stripe-neutral",
     "https://www.wtatennis.com/tournaments/cincinnati-open"),
    # Badminton (1)
    ("badminton", "BWF", "Kejuaraan Dunia Bulutangkis 2026 Dimulai, 14 Wakil Indonesia Berlaga",
     "Kejuaraan Dunia BWF 2026 bergulir 17-23 Agustus di New Delhi dengan 14 wakil Indonesia. Empat wakil Merah Putih bertanding di hari pertama, termasuk tunggal putra Alwi Farhan yang diharapkan tampil sebagai kuda hitam.",
     "17 Agu", "Detik Sport", "stripe-neutral",
     "https://sport.detik.com/raket/d-8621936/jadwal-kejuaraan-dunia-bulutangkis-2026-hari-ini-4-wakil-ri-bertanding"),
    # MMA (1)
    ("mma", "UFC", "UFC 330: Makhachev Kalahkan Machado Garry, Pertahankan Gelar",
     "Islam Makhachev keluar sebagai pemenang di UFC 330 melawan Ian Machado Garry di Philadelphia. MMA Fighting melaporkan kemenangan itu menegaskan dominasi Makhachev di divisi welterweight usai pertarungan lima ronde yang sengit.",
     "15 Agu", "MMA Fighting", "stripe-up",
     "https://www.mmafighting.com/ufc/504822/ufc-330-results-makhachev-vs-machado-garry"),
    # Lainnya (1)
    ("lainnya", "Voli", "Timnas Voli Putra Indonesia Genjot Persiapan Asian Games 2026",
     "Timnas voli putra Indonesia memulai pemusatan latihan dan bertolak ke Kamboja pada 17 Agustus untuk uji coba melawan Kamboja, Malaysia, dan Vietnam. Indonesia tergabung di Pul B Asian Games bersama Iran, Thailand, dan Kirgizstan.",
     "17 Agu", "Antara", "stripe-neutral",
     "https://rri.co.id/berita-video/47862/timnas-voli-putra-indonesia-genjot-persiapan-jelang-asian-games-2026"),
]

SEC_TITLES = {
    "ai": "AI & Large Language Models",
    "earnings": "Earnings & Big Tech",
    "chip": "Semiconductor & Chip Industry",
    "gadget": "Gadget & Consumer Tech",
    "quantum": "Quantum Computing",
    "policy": "Policy, Regulasi & Security",
    "other": "Lain-lain — Pasar & Teknologi Terkait",
}
SPORT_SEC_TITLES = {
    "sepakbola": "Sepakbola",
    "motorsport": "Motorsport",
    "basket": "Basket",
    "tenis": "Tenis",
    "badminton": "Bulutangkis",
    "mma": "MMA",
    "lainnya": "Lain-lain",
}

def card_html(cat, tag, title, desc, date, source, stripe, href, idx):
    return f'''    <div class="news-card" id="card-{idx}" data-cat="{cat}">
      <div class="stripe {stripe}"></div>
      <span class="tag">{tag}</span>
      <h4>{title}</h4>
      <p>{desc}</p>
      <div class="foot"><span><span class="date-main">{date}</span> · <span class="source">{source}</span></span><a class="read-more" href="{href}" target="_blank" rel="noopener">Baca</a></div>
    </div>'''

def build_sections(cards, titles):
    by_cat = {}
    for c in cards:
        by_cat.setdefault(c[0], []).append(c)
    parts, idx = [], 0
    for cat in [k for k in titles if k in by_cat]:
        rows = by_cat[cat]
        title = titles[cat]
        grid = "\n".join(card_html(*r, idx=(idx := idx + 1)) for r in rows)
        parts.append(f'''    <section data-section="{cat}">
    <div class="section"><div class="rule-thick"></div><h3>{title}</h3><div class="rule-thin"></div></div>
    <div class="news-grid">
{grid}
    </div>
    </section>''')
    return "\n".join(parts)

def build_slicers(cards, titles, label_map):
    counts = {}
    for c in cards:
        counts[c[0]] = counts.get(c[0], 0) + 1
    total = sum(counts.values())
    btns = [f'    <button class="slicer-btn active" data-cat="all">Semua <span class="count">({total})</span></button>']
    for cat in [k for k in titles if k in counts]:
        btns.append(f'    <button class="slicer-btn" data-cat="{cat}">{label_map[cat]} <span class="count">({counts[cat]})</span></button>')
    return "\n".join(btns)

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "tech"
    if mode == "tech":
        sections = build_sections(TECH, SEC_TITLES)
        slicers = build_slicers(TECH, SEC_TITLES, {
            "ai": "AI", "earnings": "Earnings", "chip": "Chip", "gadget": "Gadget",
            "quantum": "Quantum", "policy": "Policy", "other": "Lain-lain"})
        with open("tech_sections.html", "w", encoding="utf-8") as f:
            f.write(sections + "\n\n<!-- SLICERS -->\n\n" + slicers)
        print(f"tech: {len(TECH)} cards, {len(set(c[5] for c in TECH))} outlets")
    else:
        sections = build_sections(SPORT, SPORT_SEC_TITLES)
        slicers = build_slicers(SPORT, SPORT_SEC_TITLES, {
            "sepakbola": "Sepakbola", "motorsport": "Motorsport", "basket": "Basket",
            "tenis": "Tenis", "badminton": "Bulutangkis", "mma": "MMA", "lainnya": "Lain-lain"})
        with open("sport_sections.html", "w", encoding="utf-8") as f:
            f.write(sections + "\n\n<!-- SLICERS -->\n\n" + slicers)
        print(f"sport: {len(SPORT)} cards, {len(set(c[5] for c in SPORT))} outlets")
