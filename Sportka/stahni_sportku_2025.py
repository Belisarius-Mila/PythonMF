import re
import csv
import datetime as dt
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.sportkasazka.cz"
START_YEAR = 2025
OUT_FILE = "sportka_2025.csv"  # ponechano kvuli kompatibilite se stavajicimi skripty

MONTH_SLUGS = [
    "leden",
    "unor",
    "brezen",
    "duben",
    "kveten",
    "cerven",
    "cervenec",
    "srpen",
    "zari",
    "rijen",
    "listopad",
    "prosinec",
]


def build_urls(start_year: int = START_YEAR, end_date: dt.date | None = None) -> list[str]:
    if end_date is None:
        end_date = dt.date.today()
    urls: list[str] = []
    for year in range(start_year, end_date.year + 1):
        max_month = end_date.month if year == end_date.year else 12
        for month in range(1, max_month + 1):
            slug = MONTH_SLUGS[month - 1]
            urls.append(f"{BASE_URL}/vysledky-{slug}-{year}/")
    return urls

def parse_month(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    txt = soup.get_text("\n").replace("\xa0", " ")
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{2,}", "\n", txt)

    # řádky typu: "14. 12. 2025 - neděle"
    pattern = re.compile(r"(^|\n)(\d{1,2})\.\s*(\d{1,2})\.\s*(20\d{2})\s*-\s*([^\n]+)", re.IGNORECASE)
    matches = list(pattern.finditer(txt))

    def extract_nums(block, label_re, stop_res, maxn, num_re):
        m = re.search(label_re, block, flags=re.IGNORECASE)
        if not m:
            return None
        sub = block[m.end():]
        cut = len(sub)
        for s in stop_res:
            mm = re.search(s, sub, flags=re.IGNORECASE)
            if mm:
                cut = min(cut, mm.start())
        sub = sub[:cut]
        nums = [int(x) for x in re.findall(num_re, sub)]
        return nums[:maxn] if nums else None

    rows = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(txt)
        block = txt[start:end]

        day, month, year = int(m.group(2)), int(m.group(3)), int(m.group(4))
        d = dt.date(year, month, day)

        tah1 = extract_nums(block, r"1\.\s*tah", [r"2\.\s*tah", r"šance", r"SANCE"], 7, r"\b\d{1,2}\b")
        tah2 = extract_nums(block, r"2\.\s*tah", [r"šance", r"SANCE"], 7, r"\b\d{1,2}\b")
        sance = extract_nums(block, r"šance", [r"$"], 6, r"\b\d\b")

        if tah1 and tah2 and sance and len(tah1) >= 7 and len(tah2) >= 7 and len(sance) >= 6:
            rows.append((d, tah1, tah2, sance))

    return rows

def main():
    today = dt.date.today()
    urls = build_urls(end_date=today)
    all_rows = []
    for url in urls:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        all_rows.extend(parse_month(r.text))

    # deduplikace podle data (kdyby se opakovalo)
    seen = set()
    unique = []
    for d, t1, t2, sc in sorted(all_rows, key=lambda x: x[0]):
        if d in seen:
            continue
        seen.add(d)
        unique.append((d, t1, t2, sc))

    # Odfiltruj pripadne budouci datum, kdyby se stranka predem pripravila.
    unique = [row for row in unique if row[0] <= today]

    out = OUT_FILE
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Datum",
            "Tah1_1","Tah1_2","Tah1_3","Tah1_4","Tah1_5","Tah1_6","Tah1_dodatkove",
            "Tah2_1","Tah2_2","Tah2_3","Tah2_4","Tah2_5","Tah2_6","Tah2_dodatkove",
            "Sance_1","Sance_2","Sance_3","Sance_4","Sance_5","Sance_6",
        ])
        for d, t1, t2, sc in unique:
            w.writerow([d.isoformat(), *t1[:7], *t2[:7], *sc[:6]])

    if unique:
        print(f"Hotovo: {out} (záznamů: {len(unique)}), od {unique[0][0]} do {unique[-1][0]}")
    else:
        print(f"Hotovo: {out} (záznamů: 0)")

if __name__ == "__main__":
    main()




