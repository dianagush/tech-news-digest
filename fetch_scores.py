"""Ambil skor & jadwal multi-cabang dari ESPN (via Firecrawl) + timnas Indonesia
(TheSportsDB), lalu embed sebagai konstanta JS `SCORES` di sport.html.

Kenapa Firecrawl: site.api.espn.com balik 403 kalau di-request langsung dari
jaringan ini. POST api.firecrawl.dev/v1/scrape dengan formats=["rawHtml"]
mengembalikan body JSON API apa adanya. 1 credit per call.

JENDELA WAKTU
    Hasil pertandingan disaring ke jendela yang SAMA dengan digest berita
    (default: kemarin 11:00 WIB -> hari ini 11:00 WIB). Query ESPN memakai
    `?dates=YYYYMMDD-YYYYMMDD`; penyaringan presisi tetap dilakukan di sini
    memakai timestamp tiap laga, karena `dates` hanya presisi per hari UTC.
    Laga di LUAR jendela dan belum dimainkan masuk grup "Jadwal".

Pemakaian:
    python fetch_scores.py                                   # jendela default 24 jam
    python fetch_scores.py --since "2026-08-10 11:00"        # jendela custom
    python fetch_scores.py --since "2026-08-10 11:00" --until "2026-08-11 11:00"
    python fetch_scores.py --dump                            # fetch, jangan embed
    python fetch_scores.py --offline                         # pakai cache, 0 call

Idempoten: dua run dengan data sama menghasilkan file byte-identical.
"""
import json
import os
import pathlib
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

REPO = pathlib.Path(__file__).resolve().parent
PAGE = REPO / "sport.html"
CACHE = REPO / "scores-cache.json"
BADGES = REPO / "badges-cache.json"

WIB = timezone(timedelta(hours=7))
UTC = timezone.utc
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
         "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

# ---------------------------------------------------------------- konfigurasi
# (slug ESPN, label tampil, cabang, jenis render)
FEEDS = [
    ("soccer/eng.1",           "Liga Inggris",          "sepakbola",  "match"),
    ("soccer/esp.1",           "Liga Spanyol",          "sepakbola",  "match"),
    ("soccer/ita.1",           "Liga Italia",           "sepakbola",  "match"),
    ("soccer/ger.1",           "Liga Jerman",           "sepakbola",  "match"),
    ("soccer/fra.1",           "Liga Prancis",          "sepakbola",  "match"),
    ("soccer/idn.1",           "Liga 1 Indonesia",      "sepakbola",  "match"),
    ("soccer/uefa.champions",  "Liga Champions",        "sepakbola",  "match"),
    ("soccer/club.friendly",   "Persahabatan Klub",     "sepakbola",  "match"),
    ("soccer/fifa.friendly",   "Persahabatan Timnas",   "sepakbola",  "match"),
    ("basketball/nba",         "NBA",                   "basket",     "match"),
    ("mma/ufc",                "UFC / MMA",             "mma",        "bout"),
    ("racing/f1",              "Formula 1",             "motorsport", "event"),
    ("racing/motogp",          "MotoGP",                "motorsport", "event"),
    ("tennis/atp",             "Tenis ATP",             "tenis",      "event"),
]

# Timnas Indonesia: feed kualifikasi AFC di ESPN kosong (fifa.world.q / .afc /
# afc.world.cup.q semua 0 event) — pakai TheSportsDB.
TSDB_KEY = "3"
TIMNAS_ID = "140164"

MAX_RESULTS = 10    # maksimal hasil per grup
MAX_FIXTURES = 3    # maksimal jadwal per grup
THROTTLE = 6        # detik jeda antar call Firecrawl (hindari 429)
BACKOFF_429 = 30    # detik tunggu setelah kena 429, dikali nomor percobaan

# Feed persahabatan memuat ratusan laga divisi bawah / tim cadangan yang tidak
# menarik. Grup ber-flag `big_only` disaring: minimal satu tim harus ada di
# daftar klub besar Eropa di bawah. Feed liga (eng.1, esp.1, dst) TIDAK disaring
# — pesertanya memang sudah kasta teratas. Liga 1 Indonesia & timnas juga tidak
# disaring karena relevan bagi pembaca Indonesia.
BIG_ONLY = {"soccer/club.friendly"}

BIG_CLUBS = {
    # Inggris
    "arsenal", "aston villa", "chelsea", "everton", "liverpool",
    "manchester city", "manchester united", "newcastle united",
    "tottenham hotspur", "west ham united",
    # Spanyol
    "athletic club", "atletico madrid", "atlético madrid", "barcelona",
    "real betis", "real madrid", "real sociedad", "sevilla", "valencia",
    "villarreal",
    # Italia
    "ac milan", "atalanta", "fiorentina", "internazionale", "inter milan",
    "juventus", "lazio", "napoli", "roma",
    # Jerman
    "bayer leverkusen", "bayern munich", "borussia dortmund",
    "borussia monchengladbach", "borussia mönchengladbach",
    "eintracht frankfurt", "rb leipzig", "vfb stuttgart", "werder bremen",
    # Prancis
    "lille", "lyon", "marseille", "monaco", "olympique lyonnais",
    "paris saint-germain", "paris saint germain",
    # Belanda / Portugal / Skotlandia / Turki
    "ajax", "psv eindhoven", "feyenoord", "benfica", "fc porto", "porto",
    "sporting cp", "celtic", "rangers", "besiktas", "beşiktaş",
    "fenerbahce", "fenerbahçe", "galatasaray",
}

# Tim cadangan / kelompok umur — jangan lolos hanya karena nama induknya cocok.
RESERVE_MARKERS = (" ii", " iii", " b", " u16", " u17", " u18", " u19", " u20",
                   " u21", " u23", " reserves", " youth", " academy", " women",
                   " wanita", " putri")


def is_big_club(nama):
    """True kalau `nama` adalah klub besar Eropa (bukan tim cadangan/junior)."""
    n = " ".join((nama or "").lower().split())
    if n.endswith(RESERVE_MARKERS):
        return False
    return any(club in n for club in BIG_CLUBS)


def has_big_club(game):
    return is_big_club(game.get("h")) or is_big_club(game.get("a"))


def _fc_key():
    for p in (pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "hermes" / ".env",
              pathlib.Path.home() / "AppData" / "Local" / "hermes" / ".env"):
        if p.exists():
            m = re.search(r"FIRECRAWL[A-Z_]*=(\S+)",
                          p.read_text(encoding="utf-8", errors="ignore"))
            if m:
                return m.group(1).strip().strip('"').strip("'")
    key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if key:
        return key
    sys.exit("FATAL: FIRECRAWL_API_KEY tidak ditemukan di .env maupun environment")


def espn(slug, key, dates=None):
    """Ambil scoreboard ESPN lewat Firecrawl. Balik dict, atau None kalau gagal.

    Firecrawl free tier membatasi request per menit — belasan call beruntun kena
    HTTP 429. Jeda tetap antar call + backoff panjang khusus 429.
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/{slug}/scoreboard"
    if dates:
        url += f"?dates={dates}"
    body = json.dumps({"url": url, "formats": ["rawHtml"]}).encode()
    for attempt in (1, 2, 3):
        req = urllib.request.Request(
            "https://api.firecrawl.dev/v1/scrape", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=120))
            time.sleep(THROTTLE)
            return json.loads(r.get("data", {}).get("rawHtml", "") or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(BACKOFF_429 * attempt)
                continue
            print(f"WARN {slug}: HTTP {e.code}", file=sys.stderr)
            return None
        except Exception as e:                                  # noqa: BLE001
            if attempt < 3:
                time.sleep(THROTTLE)
                continue
            print(f"WARN {slug}: {type(e).__name__} {e}", file=sys.stderr)
            return None
    return None


def tsdb(path):
    url = f"https://www.thesportsdb.com/api/v1/json/{TSDB_KEY}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=45))
    except Exception as e:                                      # noqa: BLE001
        print(f"WARN tsdb {path}: {type(e).__name__} {e}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------- util waktu
def parse_iso(iso):
    """ISO ESPN ('2026-08-21T10:30Z') -> datetime aware UTC, atau None."""
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, TypeError):
        return None


def wib(iso):
    """ISO ESPN -> ('2026-08-21', '21 Agu 17:30') dalam WIB."""
    dt = parse_iso(iso)
    if not dt:
        return "", ""
    d = dt.astimezone(WIB)
    return d.strftime("%Y-%m-%d"), f"{d.day} {BULAN[d.month - 1]} {d:%H:%M}"


def default_window():
    """Jendela default: kemarin 11:00 WIB -> hari ini 11:00 WIB."""
    now = datetime.now(WIB)
    until = now.replace(hour=11, minute=0, second=0, microsecond=0)
    if now < until:
        until -= timedelta(days=1)
    return until - timedelta(days=1), until


def parse_arg_dt(s):
    """'2026-08-10 11:00' / '2026-08-10T11:00' -> datetime aware WIB."""
    s = s.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=WIB)
        except ValueError:
            continue
    sys.exit(f"FATAL: format tanggal tidak dikenal: {s!r} (pakai 'YYYY-MM-DD HH:MM')")


def fmt_window(since, until):
    a, b = since.astimezone(WIB), until.astimezone(WIB)
    return (f"{a.day} {BULAN[a.month - 1]} {a:%H:%M} → "
            f"{b.day} {BULAN[b.month - 1]} {b.year} {b:%H:%M} WIB")


def dates_param(since, until):
    """Rentang tanggal UTC untuk `?dates=` — dilebarkan 1 hari tiap sisi agar
    laga di tepi jendela tidak terpotong oleh pembulatan hari UTC."""
    a = (since.astimezone(UTC) - timedelta(days=1)).strftime("%Y%m%d")
    b = (until.astimezone(UTC) + timedelta(days=1)).strftime("%Y%m%d")
    return f"{a}-{b}"


def status_of(comp, iso):
    """-> (teks status, 'post'|'in'|'pre')."""
    t = (comp.get("status") or {}).get("type") or {}
    state = t.get("state") or "pre"
    if state == "post":
        return "Selesai", "post"
    if state == "in":
        return (t.get("shortDetail") or t.get("detail") or "Berlangsung").strip(), "in"
    _, jam = wib(iso)
    return (jam + " WIB") if jam else (t.get("shortDetail") or "Dijadwalkan"), "pre"


def logo_of(c):
    team = c.get("team") or {}
    logos = team.get("logos") or []
    if logos:
        return logos[0].get("href", "")
    return team.get("logo", "") or ""


# ---------------------------------------------------------------- parsing
def parse_match(data):
    """Sepakbola / NBA: dua tim + skor."""
    out = []
    for ev in data.get("events") or []:
        comp = (ev.get("competitions") or [{}])[0]
        cs = comp.get("competitors") or []
        if len(cs) != 2:
            continue
        home = next((c for c in cs if c.get("homeAway") == "home"), cs[0])
        away = next((c for c in cs if c.get("homeAway") == "away"), cs[1])
        st, state = status_of(comp, ev.get("date"))
        out.append({
            "h": (home.get("team") or {}).get("displayName", "?"),
            "a": (away.get("team") or {}).get("displayName", "?"),
            "hs": home.get("score") if state != "pre" else None,
            "as": away.get("score") if state != "pre" else None,
            "hl": logo_of(home), "al": logo_of(away),
            "st": st, "state": state,
            "d": wib(ev.get("date"))[0], "ts": ev.get("date"),
        })
    return out


def parse_bout(data):
    """UFC: kartu tanding — nama vs nama, tanpa skor."""
    out = []
    for ev in data.get("events") or []:
        comp = (ev.get("competitions") or [{}])[0]
        cs = comp.get("competitors") or []
        st, state = status_of(comp, ev.get("date"))
        base = {"st": st, "state": state, "d": wib(ev.get("date"))[0],
                "ts": ev.get("date"), "note": ev.get("name", "")}
        if len(cs) == 2:
            def nm(c):
                a = c.get("athlete") or {}
                return a.get("displayName") or a.get("fullName") or "?"
            out.append({**base, "h": nm(cs[0]), "a": nm(cs[1]),
                        "hs": None, "as": None, "hl": "", "al": ""})
        else:
            out.append({**base, "n": ev.get("name", "?")})
    return out


def parse_event(data):
    """F1 / MotoGP / Tenis: satu event (balapan / turnamen), tanpa dua sisi."""
    out = []
    for ev in data.get("events") or []:
        comps = ev.get("competitions") or []
        comp = comps[0] if comps else {}
        st, state = status_of(comp, ev.get("date"))
        venue = ((comp.get("venue") or {}).get("fullName")
                 or (ev.get("venue") or {}).get("fullName") or "")
        out.append({"n": ev.get("name") or ev.get("shortName") or "?",
                    "st": st, "state": state, "venue": venue,
                    "d": wib(ev.get("date"))[0], "ts": ev.get("date")})
    return out


def parse_timnas():
    """Timnas Indonesia via TheSportsDB (hasil terakhir + jadwal berikutnya)."""
    games = []
    badges = json.loads(BADGES.read_text(encoding="utf-8")) if BADGES.exists() else {}

    def push(ev, done):
        tanggal = ev.get("dateEvent", "")
        jam = (ev.get("strTime") or "")[:5]
        ts = f"{tanggal}T{jam or '00:00'}:00Z" if tanggal else ""
        h, a = ev.get("strHomeTeam", "?"), ev.get("strAwayTeam", "?")
        games.append({
            "h": h, "a": a,
            "hs": ev.get("intHomeScore") if done else None,
            "as": ev.get("intAwayScore") if done else None,
            "hl": badges.get(h, ""), "al": badges.get(a, ""),
            "st": "Selesai" if done else (wib(ts)[1] + " WIB" if ts else "Dijadwalkan"),
            "state": "post" if done else "pre",
            "d": tanggal, "ts": ts, "note": ev.get("strLeague", ""),
        })

    for ev in (tsdb(f"eventslast.php?id={TIMNAS_ID}").get("results") or [])[:5]:
        push(ev, True)
    for ev in (tsdb(f"eventsnext.php?id={TIMNAS_ID}").get("events") or [])[:5]:
        push(ev, False)
    return games


# ---------------------------------------------------------------- penyaringan
def split_window(games, since, until):
    """-> (hasil dalam jendela, jadwal setelah jendela).

    Hasil  = laga yang SUDAH/SEDANG dimainkan dengan kickoff >= since.
             (Tanpa batas atas: refresh sore 18:00/22:00 harus menangkap laga
             malam yang selesai SETELAH `until`, supaya papan skor tidak basi.
             Pada run pagi 11:00 hasilnya identik dengan batas ketat, karena
             belum ada laga yang selesai setelah 11:00 hari itu.)
    Jadwal = laga belum dimainkan dengan kickoff >= until.
    Laga di luar jendela yang sudah selesai SEBELUM since sengaja DIBUANG —
    jendela skor harus konsisten dengan jendela berita.
    """
    hasil, jadwal = [], []
    for g in games:
        dt = parse_iso(g.get("ts"))
        if dt is None:
            continue
        played = g["state"] in ("post", "in")
        if dt >= since and played:
            hasil.append(g)
        elif dt >= until and not played:
            jadwal.append(g)
    hasil.sort(key=lambda g: g["ts"], reverse=True)
    jadwal.sort(key=lambda g: g["ts"])
    return hasil[:MAX_RESULTS], jadwal[:MAX_FIXTURES]


# ---------------------------------------------------------------- rakit
def build(since, until, offline=False):
    if offline:
        if not CACHE.exists():
            sys.exit("FATAL: --offline tapi scores-cache.json tidak ada")
        return json.loads(CACHE.read_text(encoding="utf-8"))

    key = _fc_key()
    dates = dates_param(since, until)
    parsers = {"match": parse_match, "bout": parse_bout, "event": parse_event}
    results, fixtures, calls = [], [], 0

    def add(sport, label, kind, games):
        hasil, jadwal = split_window(games, since, until)
        if hasil:
            results.append({"sport": sport, "label": label, "kind": kind, "games": hasil})
        if jadwal:
            fixtures.append({"sport": sport, "label": label, "kind": kind, "games": jadwal})

    for slug, label, sport, kind in FEEDS:
        data = espn(slug, key, dates)
        calls += 1
        if data:
            games = parsers[kind](data)
            if slug in BIG_ONLY:
                games = [g for g in games if has_big_club(g)]
            add(sport, label, kind, games)

    add("sepakbola", "Timnas Indonesia", "match", parse_timnas())

    now = datetime.now(WIB)
    payload = {
        "window": fmt_window(since, until),
        "since": since.astimezone(WIB).isoformat(),
        "until": until.astimezone(WIB).isoformat(),
        "updated": f"{now.day} {BULAN[now.month - 1]} {now.year} {now:%H:%M} WIB",
        "results": results,
        "fixtures": fixtures,
        "calls": calls,
    }
    CACHE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


def embed(payload):
    """Ganti konstanta SCORES di sport.html. Idempoten."""
    if not PAGE.exists():
        print(f"SKIP embed: {PAGE.name} belum ada")
        return False
    html = PAGE.read_text(encoding="utf-8")
    js = "const SCORES = " + json.dumps(payload, ensure_ascii=False) + ";"
    new, n = re.subn(r"const SCORES = \{.*?\};", lambda _m: js, html, count=1, flags=re.S)
    if not n:
        print("FAIL: penanda `const SCORES = {...};` tidak ditemukan di sport.html",
              file=sys.stderr)
        return False
    if new != html:
        PAGE.write_text(new, encoding="utf-8")
    return True


def main():
    args = sys.argv[1:]

    def opt(name):
        return args[args.index(name) + 1] if name in args and len(args) > args.index(name) + 1 else None

    since_s, until_s = opt("--since"), opt("--until")
    if since_s or until_s:
        d_since, d_until = default_window()
        since = parse_arg_dt(since_s) if since_s else d_since
        until = parse_arg_dt(until_s) if until_s else d_until
    else:
        since, until = default_window()
    if since >= until:
        sys.exit(f"FATAL: --since ({since}) harus lebih awal dari --until ({until})")

    data = build(since, until, offline="--offline" in args)
    nr = sum(len(g["games"]) for g in data["results"])
    nf = sum(len(g["games"]) for g in data["fixtures"])
    print(f"jendela: {data['window']}")
    print(f"call   : {data.get('calls', 0)} (Firecrawl credit)")
    print(f"hasil  : {nr} laga / {len(data['results'])} grup")
    for g in data["results"]:
        print(f"  - {g['label']:<22} {len(g['games'])}")
    print(f"jadwal : {nf} laga / {len(data['fixtures'])} grup")
    for g in data["fixtures"]:
        print(f"  - {g['label']:<22} {len(g['games'])}")
    if "--dump" not in args:
        ok = embed(data)
        print(f"embed  : {'OK ' + PAGE.name if ok else 'TIDAK'}")
    if nr == 0 and nf == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
