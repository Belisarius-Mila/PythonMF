"""
╔══════════════════════════════════════════════════════════════════╗
║         MultiLO — Bulk Image Downloader                         ║
║         Zdroj: Wikipedia REST API + Wikimedia Commons           ║
║         Spuštění: python mlo_image_downloader.py                ║
╚══════════════════════════════════════════════════════════════════╝

Požadavky:
    pip install requests Pillow tqdm

Výstup:
    Složka images/<OKRUH>/<en_nazev>.jpg
    Soubor  images/_report.csv  (přehled co se povedlo / nepovedlo)
"""

import csv
import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

# ── Zkus načíst volitelné závislosti ─────────────────────────────
try:
    import requests
    USE_REQUESTS = True
except ImportError:
    import urllib.request as _urllib_req
    USE_REQUESTS = False
    print("⚠️  'requests' není nainstalován — používám urllib (základní fallback).")

try:
    from tqdm import tqdm
    USE_TQDM = True
except ImportError:
    USE_TQDM = False

# ╔══════════════════════════════════════════════════════════════════╗
# ║  KONFIGURACE — upravte dle potřeby                              ║
# ╚══════════════════════════════════════════════════════════════════╝

CSV_FILE        = "master.csv"          # cesta k vašemu master CSV
OUTPUT_DIR      = "images"             # kam se uloží obrázky
IMG_SIZE        = (400, 400)           # resize na tuto velikost (px), None = bez resize
DELAY_SECONDS   = 0.5                  # pauza mezi requesty (etiketa vůči API)
SKIP_CATEGORIES = {                    # okruhy, které NECHCEME stahovat
    "Dny v týdnu",
    "Měsíce v roce",
    "Číslovky",
}
# Přidejte nebo změňte pokud má slovíčko jiný Wikipedia název:
MANUAL_OVERRIDES = {
    # "EN název v CSV"  : "skutečný Wikipedia název stránky"
    "Bell pepper"       : "Bell_pepper",
    "Blackberry bush"   : "Rubus_fruticosus",
    "Wild rose"         : "Rosa_canina",
    "Horsetail"         : "Equisetum",
    "Blackbird"         : "Common_blackbird",
    "Tit"               : "Tit_(bird)",
    "Finch"             : "Finch",
    "Linden"            : "Tilia",
    "Spruce"            : "Picea",
    "Ash"               : "Fraxinus",
    "Hen"               : "Chicken",
    "Hare"              : "European_hare",
    "Grapes"            : "Grape",
    "Peas"              : "Pea",
    "Beans"             : "Bean",
    "Corn"              : "Maize",
    "Pumpkin"           : "Cucurbita",
    "Rat"               : "Brown_rat",
    "Lawn"              : "Lawn",
}

# ══════════════════════════════════════════════════════════════════


def sanitize_filename(name: str) -> str:
    """Převede EN název na bezpečné jméno souboru."""
    return name.lower().replace(" ", "_").replace("/", "-")


def wikipedia_title(en_word: str) -> str:
    """Vrátí Wikipedia název stránky — buď z override, nebo jako je."""
    return MANUAL_OVERRIDES.get(en_word, en_word.replace(" ", "_"))


def get_wikipedia_image_url(title: str) -> str | None:
    """
    Zavolá Wikipedia REST API a vrátí URL thumbnail obrázku.
    Endpoint: https://en.wikipedia.org/api/rest_v1/page/summary/{title}
    """
    encoded = urllib.parse.quote(title, safe="")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    headers = {
        "User-Agent": "MultiLO-ImageDownloader/1.0 (educational project; contact: your@email.com)"
    }

    try:
        if USE_REQUESTS:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Preferuj 'originalimage', fallback na 'thumbnail'
                img = data.get("originalimage") or data.get("thumbnail")
                if img:
                    return img["source"]
        else:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                img = data.get("originalimage") or data.get("thumbnail")
                if img:
                    return img["source"]
    except Exception as e:
        print(f"    ⚠️  API chyba pro '{title}': {e}")

    return None


def download_image(img_url: str, dest_path: Path) -> bool:
    """Stáhne obrázek z URL a uloží ho. Volitelně resizuje přes Pillow."""
    headers = {
        "User-Agent": "MultiLO-ImageDownloader/1.0 (educational project)"
    }
    try:
        if USE_REQUESTS:
            resp = requests.get(img_url, headers=headers, timeout=15, stream=True)
            resp.raise_for_status()
            raw = resp.content
        else:
            req = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()

        # Pokud je Pillow dostupný a IMG_SIZE nastaveno — resize
        if IMG_SIZE:
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                img.thumbnail(IMG_SIZE, Image.LANCZOS)
                img.save(dest_path, "JPEG", quality=88)
                return True
            except ImportError:
                pass  # Pillow není — uložíme as-is

        # Uložení bez resize
        suffix = dest_path.suffix.lower()
        if suffix not in (".jpg", ".jpeg", ".png", ".webp", ".svg"):
            dest_path = dest_path.with_suffix(".jpg")
        dest_path.write_bytes(raw)
        return True

    except Exception as e:
        print(f"    ❌  Download selhal ({img_url[:60]}…): {e}")
        return False


def load_csv(csv_path: str) -> list[dict]:
    """Načte CSV a vrátí seznam slovníků."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        # Detekce oddělovače
        sample = f.read(2048)
        f.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # Normalizace názvů sloupců (trim whitespace)
            rows.append({k.strip(): v.strip() for k, v in row.items()})
    return rows


def main():
    print("╔══════════════════════════════════════════╗")
    print("║   MultiLO — Image Bulk Downloader        ║")
    print("╚══════════════════════════════════════════╝\n")

    # ── Načtení CSV ──────────────────────────────────────────────
    if not os.path.exists(CSV_FILE):
        print(f"❌  Soubor '{CSV_FILE}' nenalezen.")
        print(f"   Ujistěte se, že skript je ve stejné složce jako CSV,")
        print(f"   nebo upravte proměnnou CSV_FILE na správnou cestu.")
        return

    rows = load_csv(CSV_FILE)
    print(f"✅  Načteno {len(rows)} řádků z '{CSV_FILE}'")

    # ── Filtrování — jen relevantní okruhy ───────────────────────
    to_process = [
        r for r in rows
        if r.get("OKRUH", "") not in SKIP_CATEGORIES
        and r.get("EN", "").strip()
    ]
    # Deduplikace podle EN názvu (stejné zvíře v různých okruzích)
    seen = set()
    unique = []
    for r in to_process:
        key = r["EN"].strip()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    print(f"📋  Ke zpracování: {len(unique)} unikátních slovíček")
    print(f"⏭️   Přeskočeny okruhy: {', '.join(SKIP_CATEGORIES)}\n")

    # ── Vytvoření výstupních složek ───────────────────────────────
    base = Path(OUTPUT_DIR)
    base.mkdir(exist_ok=True)

    categories = set(r["OKRUH"] for r in unique)
    for cat in categories:
        (base / cat).mkdir(exist_ok=True)

    # ── Hlavní smyčka ─────────────────────────────────────────────
    report = []
    iterator = tqdm(unique, desc="Stahuji") if USE_TQDM else unique

    ok_count = 0
    fail_count = 0
    skip_count = 0

    for row in iterator:
        en_word  = row["EN"].strip()
        okruh    = row["OKRUH"].strip()
        cz_word  = row.get("CZ", "").strip()
        filename = sanitize_filename(en_word) + ".jpg"
        dest     = base / okruh / filename

        status = ""
        img_url = ""

        # Přeskočit pokud soubor již existuje
        if dest.exists():
            if not USE_TQDM:
                print(f"  ⏭️  [{okruh}] {en_word} — již existuje, přeskakuji")
            status = "SKIP_EXISTS"
            skip_count += 1
        else:
            if not USE_TQDM:
                print(f"  🔍  [{okruh}] {en_word} ({cz_word})")

            wiki_title = wikipedia_title(en_word)
            img_url    = get_wikipedia_image_url(wiki_title)

            if img_url:
                success = download_image(img_url, dest)
                if success:
                    status = "OK"
                    ok_count += 1
                    if not USE_TQDM:
                        print(f"       ✅  Uloženo → {dest}")
                else:
                    status = "FAIL_DOWNLOAD"
                    fail_count += 1
            else:
                status = "FAIL_NO_IMAGE"
                fail_count += 1
                if not USE_TQDM:
                    print(f"       ❌  Obrázek nenalezen na Wikipedii")

            time.sleep(DELAY_SECONDS)

        report.append({
            "OKRUH"   : okruh,
            "CZ"      : cz_word,
            "EN"      : en_word,
            "STATUS"  : status,
            "IMG_URL" : img_url,
            "FILE"    : str(dest) if status == "OK" else "",
        })

    # ── Report ────────────────────────────────────────────────────
    report_path = base / "_report.csv"
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["OKRUH","CZ","EN","STATUS","IMG_URL","FILE"])
        writer.writeheader()
        writer.writerows(report)

    print("\n╔══════════════════════════════════════════╗")
    print("║   Hotovo!                                ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  ✅  Staženo:       {ok_count:>4}                   ║")
    print(f"║  ⏭️   Přeskočeno:    {skip_count:>4} (již existovaly) ║")
    print(f"║  ❌  Selhalo:       {fail_count:>4}                   ║")
    print(f"║  📄  Report:  {str(report_path):<26} ║")
    print("╚══════════════════════════════════════════╝\n")

    if fail_count > 0:
        print("💡  Tip: Otevřete _report.csv a filtrujte STATUS=FAIL_*")
        print("   Pro nenalezené přidejte záznam do MANUAL_OVERRIDES v tomto skriptu.")


if __name__ == "__main__":
    main()

