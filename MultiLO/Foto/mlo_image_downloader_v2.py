"""
╔══════════════════════════════════════════════════════════════════╗
║         MultiLO — Bulk Image Downloader v2                      ║
║         Opraveno: Wikimedia hlavičky + Manual overrides         ║
║         Spuštění: python mlo_image_downloader_v2.py             ║
╚══════════════════════════════════════════════════════════════════╝

Co je nového oproti v1:
  - Opravené HTTP hlavičky pro Wikimedia (řeší 90 FAIL_DOWNLOAD)
  - Retry logika (3 pokusy s exponenciálním backoff)
  - MANUAL_OVERRIDES pro 13 FAIL_NO_IMAGE položek
  - Režim --retry: přeskočí OK, zpracuje jen FAILy z _report.csv
  - Lepší detekce formátu souboru (jpg/png/webp)

Požadavky:
    pip install requests Pillow tqdm

Spuštění (poprvé nebo znovu od začátku):
    python mlo_image_downloader_v2.py

Spuštění (pouze retry selhání z minulého běhu):
    python mlo_image_downloader_v2.py --retry
"""

import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import requests
    USE_REQUESTS = True
except ImportError:
    USE_REQUESTS = False
    print("⚠️  'requests' není nainstalován — pip install requests")
    sys.exit(1)

try:
    from tqdm import tqdm
    USE_TQDM = True
except ImportError:
    USE_TQDM = False

try:
    from PIL import Image
    USE_PILLOW = True
except ImportError:
    USE_PILLOW = False
    print("⚠️  'Pillow' není nainstalován — obrázky se neuloží v resize")

# ╔══════════════════════════════════════════════════════════════════╗
# ║  KONFIGURACE                                                    ║
# ╚══════════════════════════════════════════════════════════════════╝

CSV_FILE        = "master.csv"
REPORT_FILE     = "images/_report.csv"
OUTPUT_DIR      = "images"
IMG_SIZE        = (400, 400)      # None = bez resize
DELAY_SECONDS   = 0.8             # zvýšeno kvůli Wikimedia rate limit
MAX_RETRIES     = 3               # počet pokusů při selhání

SKIP_CATEGORIES = {
    "Dny v týdnu",
    "Měsíce v roce",
    "Číslovky",
}

# ── Opravené hlavičky pro Wikimedia ──────────────────────────────
# Wikimedia blokuje generické User-Agenty — vyžaduje identifikaci
WIKIMEDIA_HEADERS = {
    "User-Agent": "MultiLO-ImageDownloader/2.0 (educational non-commercial project; https://github.com/yourname/multiLO; contact: your@email.com)",
    "Accept": "image/webp,image/jpeg,image/png,*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "cs,en;q=0.9",
    "Referer": "https://en.wikipedia.org/",
}

WIKIPEDIA_API_HEADERS = {
    "User-Agent": "MultiLO-ImageDownloader/2.0 (educational; contact: your@email.com)",
    "Accept": "application/json",
}

# ── Manuální override pro FAIL_NO_IMAGE položky ──────────────────
# Formát: "EN název" : "Wikipedia název stránky"
MANUAL_OVERRIDES = {
    # ── Původní overrides ──
    "Bell pepper"       : "Bell_pepper",
    "Blackberry bush"   : "Rubus_fruticosus",
    "Wild rose"         : "Rosa_canina",
    "Horsetail"         : "Equisetum",
    "Blackbird"         : "Common_blackbird",
    "Tit"               : "Paridae",
    "Finch"             : "Fringillidae",
    "Linden"            : "Tilia",
    "Spruce"            : "Picea_abies",
    "Ash"               : "Fraxinus_excelsior",
    "Hen"               : "Chicken",
    "Hare"              : "European_hare",
    "Grapes"            : "Grape",
    "Peas"              : "Pea",
    "Beans"             : "Common_bean",
    "Corn"              : "Maize",
    "Pumpkin"           : "Cucurbita_maxima",
    "Rat"               : "Brown_rat",
    "Lawn"              : "Lawn",

    # ── Nové: oprava FAIL_NO_IMAGE ──────────────────────────────
    # Ptáci
    "Goldfinch"         : "European_goldfinch",      # Čížek
    "Thrush"            : "Song_thrush",             # Drozd
    "Buzzard"           : "Common_buzzard",          # Káně
    "Sparrow"           : "House_sparrow",           # Vrabec

    # Rostliny
    "Elder"             : "Sambucus_nigra",          # Bez černý
    "Violet"            : "Viola_(plant)",           # Fialka
    "Nettle"            : "Urtica_dioica",           # Kopřiva
    "Mint"              : "Mentha",                  # Máta
    "Reed"              : "Phragmites",              # Rákos
    "Daisy"             : "Bellis_perennis",         # Sedmikráska

    # Zelenina a ovoce
    "Kiwi"              : "Actinidia_deliciosa",     # Kiwi
    "Mandarin"          : "Mandarin_orange",         # Mandarinka
    "Pepper"            : "Capsicum_annuum",         # Paprika

    # Základní barvy — Wikipedia hledá podle pojmu barvy
    "Orange"            : "Orange_(colour)",         # Oranžová
    "Red"               : "Red",
    "Blue"              : "Blue",
    "Green"             : "Green",
    "Yellow"            : "Yellow",
    "Black"             : "Black",
    "White"             : "White",
    "Brown"             : "Brown",
    "Pink"              : "Pink",
    "Purple"            : "Purple",
}

# ══════════════════════════════════════════════════════════════════


def sanitize_filename(name: str) -> str:
    return name.lower().replace(" ", "_").replace("/", "-")


def wikipedia_title(en_word: str) -> str:
    return MANUAL_OVERRIDES.get(en_word, en_word.replace(" ", "_"))


def get_wikipedia_image_url(title: str) -> str | None:
    """Wikipedia REST API → vrátí URL nejlepšího dostupného obrázku."""
    encoded = urllib.parse.quote(title, safe="")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=WIKIPEDIA_API_HEADERS, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                img = data.get("originalimage") or data.get("thumbnail")
                if img:
                    return img["source"]
                return None
            elif resp.status_code == 404:
                return None  # stránka neexistuje — nemá cenu opakovat
        except requests.RequestException as e:
            wait = 2 ** attempt
            print(f"    ⚠️  API pokus {attempt+1}/{MAX_RETRIES} selhal: {e} — čekám {wait}s")
            time.sleep(wait)

    return None


def download_image(img_url: str, dest_path: Path) -> bool:
    """
    Stáhne obrázek s Wikimedia-kompatibilními hlavičkami.
    Klíčová oprava oproti v1: správný User-Agent + Referer.
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                img_url,
                headers=WIKIMEDIA_HEADERS,
                timeout=20,
                stream=True,
                allow_redirects=True,
            )
            resp.raise_for_status()
            raw = resp.content

            # Detekce skutečného formátu podle Content-Type
            ct = resp.headers.get("Content-Type", "")
            if "png" in ct:
                ext = ".png"
            elif "svg" in ct:
                ext = ".svg"
                dest_path = dest_path.with_suffix(".svg")
                dest_path.write_bytes(raw)
                return True
            else:
                ext = ".jpg"

            dest_path = dest_path.with_suffix(ext)

            if USE_PILLOW and IMG_SIZE:
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                img.thumbnail(IMG_SIZE, Image.LANCZOS)
                img.save(dest_path.with_suffix(".jpg"), "JPEG", quality=88)
            else:
                dest_path.write_bytes(raw)

            return True

        except requests.HTTPError as e:
            if e.response.status_code in (403, 429):
                wait = 3 ** attempt
                print(f"    🚫  HTTP {e.response.status_code} — čekám {wait}s (pokus {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                print(f"    ❌  HTTP chyba {e.response.status_code}: {img_url[:70]}")
                return False
        except Exception as e:
            wait = 2 ** attempt
            print(f"    ⚠️  Pokus {attempt+1}/{MAX_RETRIES}: {e} — čekám {wait}s")
            time.sleep(wait)

    return False


def load_csv(csv_path: str) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(2048); f.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        return [{k.strip(): v.strip() for k, v in row.items()} for row in reader]


def load_report_fails(report_path: str) -> list[dict]:
    """Načte z _report.csv pouze řádky se statusem FAIL_*."""
    fails = []
    with open(report_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["STATUS"].startswith("FAIL"):
                fails.append(row)
    return fails


def process_items(items: list[dict], base: Path, retry_mode: bool = False):
    ok_count = fail_count = skip_count = 0
    report = []

    iterator = tqdm(items, desc="Stahuji") if USE_TQDM else items

    for row in iterator:
        en_word = row["EN"].strip()
        okruh   = row["OKRUH"].strip()
        cz_word = row.get("CZ", "").strip()

        # V retry módu může být URL již v reportu — použijeme ji přímo
        known_url = row.get("IMG_URL", "").strip() if retry_mode else ""

        filename = sanitize_filename(en_word) + ".jpg"
        dest     = base / okruh / filename

        # Zajisti složku
        (base / okruh).mkdir(parents=True, exist_ok=True)

        status  = ""
        img_url = known_url

        if dest.exists() and not retry_mode:
            status = "SKIP_EXISTS"
            skip_count += 1
            if not USE_TQDM:
                print(f"  ⏭️  [{okruh}] {en_word} — přeskakuji")
        else:
            if not USE_TQDM:
                print(f"  🔍  [{okruh}] {en_word} ({cz_word})")

            # Pokud nemáme URL (FAIL_NO_IMAGE nebo první běh), zavoláme API
            if not img_url:
                wiki_title = wikipedia_title(en_word)
                img_url    = get_wikipedia_image_url(wiki_title)
                if not img_url:
                    # Zkusíme ještě alternativní název pokud override existuje
                    alt_title = MANUAL_OVERRIDES.get(en_word)
                    if alt_title and alt_title != wiki_title:
                        img_url = get_wikipedia_image_url(alt_title)

            if img_url:
                success = download_image(img_url, dest)
                if success:
                    status = "OK"
                    ok_count += 1
                    if not USE_TQDM:
                        print(f"       ✅  → {dest.name}")
                else:
                    status = "FAIL_DOWNLOAD"
                    fail_count += 1
                    if not USE_TQDM:
                        print(f"       ❌  Download selhal")
            else:
                status = "FAIL_NO_IMAGE"
                fail_count += 1
                if not USE_TQDM:
                    print(f"       ❌  Obrázek nenalezen")

            time.sleep(DELAY_SECONDS)

        report.append({
            "OKRUH"   : okruh,
            "CZ"      : cz_word,
            "EN"      : en_word,
            "STATUS"  : status,
            "IMG_URL" : img_url,
            "FILE"    : str(dest) if status == "OK" else "",
        })

    return report, ok_count, fail_count, skip_count


def save_report(report: list[dict], path: Path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["OKRUH","CZ","EN","STATUS","IMG_URL","FILE"])
        writer.writeheader()
        writer.writerows(report)


def print_summary(ok, skip, fail, report_path):
    print("\n╔══════════════════════════════════════════╗")
    print("║   Hotovo!                                ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  ✅  Staženo:       {ok:>4}                   ║")
    print(f"║  ⏭️   Přeskočeno:    {skip:>4}                   ║")
    print(f"║  ❌  Selhalo:       {fail:>4}                   ║")
    print(f"║  📄  Report: {str(report_path):<29}║")
    print("╚══════════════════════════════════════════╝")
    if fail > 0:
        print(f"\n💡  Tip: Filtrujte STATUS=FAIL_* v {report_path}")
        print("   Přidejte problematické názvy do MANUAL_OVERRIDES a spusťte --retry")


def main():
    retry_mode = "--retry" in sys.argv

    print("╔══════════════════════════════════════════╗")
    print("║   MultiLO — Image Downloader v2          ║")
    if retry_mode:
        print("║   Režim: RETRY (pouze selhání)           ║")
    else:
        print("║   Režim: FULL (celý CSV)                 ║")
    print("╚══════════════════════════════════════════╝\n")

    base        = Path(OUTPUT_DIR)
    report_path = base / "_report.csv"
    base.mkdir(exist_ok=True)

    # ── Výběr vstupních dat ───────────────────────────────────────
    if retry_mode:
        if not report_path.exists():
            print(f"❌  Report '{report_path}' nenalezen. Spusťte nejprve bez --retry.")
            return
        items = load_report_fails(str(report_path))
        print(f"📋  Retry: {len(items)} selhání z předchozího běhu\n")
    else:
        if not os.path.exists(CSV_FILE):
            print(f"❌  CSV soubor '{CSV_FILE}' nenalezen.")
            return
        rows = load_csv(CSV_FILE)
        print(f"✅  Načteno {len(rows)} řádků z '{CSV_FILE}'")

        to_process = [r for r in rows
                      if r.get("OKRUH","") not in SKIP_CATEGORIES
                      and r.get("EN","").strip()]

        seen, items = set(), []
        for r in to_process:
            k = r["EN"].strip()
            if k not in seen:
                seen.add(k); items.append(r)

        print(f"📋  Ke zpracování: {len(items)} unikátních slovíček")
        print(f"⏭️   Přeskočené okruhy: {', '.join(SKIP_CATEGORIES)}\n")

    # ── Zpracování ────────────────────────────────────────────────
    report, ok, fail, skip = process_items(items, base, retry_mode)

    # ── Uložení reportu ───────────────────────────────────────────
    if retry_mode and report_path.exists():
        # Merge: původní OK záznamy + nové výsledky retry
        existing = []
        with open(report_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing = [r for r in reader if not r["STATUS"].startswith("FAIL")]
        merged = existing + report
        save_report(merged, report_path)
    else:
        save_report(report, report_path)

    print_summary(ok, skip, fail, report_path)


if __name__ == "__main__":
    main()
