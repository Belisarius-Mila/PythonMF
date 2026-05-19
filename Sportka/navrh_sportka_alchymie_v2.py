import os
import re
import random
import heapq
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------
# Sportka – návrh čísel (edukativní / pro zábavu)
# Poznámka: u férové loterie minulá losování nezvyšují šanci na výhru.
# Tento skript řeší hlavně (a) pohodlné načtení dat, (b) opakovatelnost,
# (c) volby generování: "random" (méně-populární), "alchemy" (alchymie), "weighted" (experiment).
# ------------------------------------------------------------

# ----------------------------
# Nastavení
# ----------------------------
# Kde hledat data
DESKTOP = Path.home() / "Desktop"
SCRIPT_DIR = Path(__file__).resolve().parent

# Preferovaný soubor, který teď používáš
DEFAULT_BASENAME = "sportka_2025"
POSSIBLE_PATHS = [
    # 1) složka skriptu
    SCRIPT_DIR / f"{DEFAULT_BASENAME}.csv",
    SCRIPT_DIR / f"{DEFAULT_BASENAME}.xlsx",
    # 2) plocha
    DESKTOP / f"{DEFAULT_BASENAME}.csv",
    DESKTOP / f"{DEFAULT_BASENAME}.xlsx",
    # 3) starší název (kompatibilita)
    SCRIPT_DIR / "vysledky_sportky_50.xlsx",
    SCRIPT_DIR / "vysledky_sportky_50.csv",
    DESKTOP / "vysledky_sportky_50.xlsx",
    DESKTOP / "vysledky_sportky_50.csv",
]

# Kolik sad navrhnout
NUM_SUGGESTIONS = int(os.getenv("SPORTKA_N", "5"))

# Režim generování čísel:
#   - "random"   = náhodně, ale vybíráme „méně populární“ kombinace (doporučený default)
#   - "weighted" = vážení podle historie (spíš experiment / hraní si s daty)
#   - "alchemy"  = alchymie: 3 čísla 1–31 + 3 čísla 32–49, silně se vyhýbá posledním tahům a opakování celé kombinace
MODE = os.getenv("SPORTKA_MODE", "alchemy").strip().lower()
print(f"[sportka] MODE={MODE} (nastav SPORTKA_MODE pro změnu)")

# Pro „weighted“ režim: exponenciální útlum pro čerstvost (0.97–0.995 rozumné)
DECAY = float(os.getenv("SPORTKA_DECAY", "0.985"))

# Pro „weighted“ režim: Dirichlet/Laplace vyhlazení (pseudo-počty)
ALPHA = float(os.getenv("SPORTKA_ALPHA", "1.0"))

# Seed pro reprodukovatelnost (nastav jen když chceš stejné výsledky pokaždé).
# Pokud zůstane None, bude to pokaždé jiné (standardní chování).
_seed_env = os.getenv("SPORTKA_SEED", "").strip()
RANDOM_SEED = int(_seed_env) if _seed_env else None
if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
# ----------------------------
# Heuristiky pro „méně populární“ kombinace (MODE=random)
# Pozn.: Nezvyšují šanci trefit výherní čísla. Snaží se snížit riziko
# dělení výhry s dalšími hráči (lidé často sázejí narozeniny, vzory atd.).
# ----------------------------
NUM_CANDIDATES = int(os.getenv("SPORTKA_CANDIDATES", "50000"))
HEAP_KEEP = int(os.getenv("SPORTKA_HEAP_KEEP", "1500"))  # kolik nejlepších kandidátů si držet
MAX_LOW31 = int(os.getenv("SPORTKA_MAX_LOW31", "3"))     # max počet čísel 1–31
MIN_DECADES = int(os.getenv("SPORTKA_MIN_DECADES", "3")) # min počet „desítek“ (1–9, 10–19, ... 40–49)
OVERLAP_WINDOW = int(os.getenv("SPORTKA_OVERLAP_WINDOW", "3"))  # kolik posledních tahů penalizovat
OVERLAP_THRESHOLD = int(os.getenv("SPORTKA_OVERLAP_THRESHOLD", "4"))  # od kolika shod penalizovat

def _max_consecutive_run(nums_sorted: list[int]) -> int:
    """Maximální délka souvislé posloupnosti (např. 5-6-7 má délku 3)."""
    if not nums_sorted:
        return 0
    best = 1
    cur = 1
    for a, b in zip(nums_sorted, nums_sorted[1:]):
        if b == a + 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best

def _decade_bucket(n: int) -> int:
    # 1–9 => 0, 10–19 => 1, 20–29 => 2, 30–39 => 3, 40–49 => 4
    return (n - 1) // 10

def popularity_score(cand: list[int], recent_draws: list[list[int]]) -> float:
    """Nižší je lepší. Přidává penalizace za „populární“ lidské vzorce."""
    s = 0.0
    nums = sorted(cand)

    # (1) Narozeniny: čísla 1–31 jsou u lidí typicky nadhodnocená.
    low31 = sum(1 for x in nums if x <= 31)
    s += low31 * 1.0
    if low31 > MAX_LOW31:
        s += 1000.0 * (low31 - MAX_LOW31)  # tvrdý trest

    # (2) Dlouhé souvislé řady (např. 11-12-13) – lidé je volí častěji.
    if _max_consecutive_run(nums) >= 3:
        s += 250.0

    # (3) Rozprostření napříč „desítkami“
    decades = {_decade_bucket(x) for x in nums}
    if len(decades) < MIN_DECADES:
        s += 200.0 * (MIN_DECADES - len(decades))

    # (4) Přílišná koncentrace v jedné „desítce“ (např. 4 čísla z 20–29)
    bucket_counts = {}
    for x in nums:
        b = _decade_bucket(x)
        bucket_counts[b] = bucket_counts.get(b, 0) + 1
    max_in_bucket = max(bucket_counts.values())
    if max_in_bucket >= 4:
        s += 50.0 * (max_in_bucket - 3)

    # (5) Penalizace vysokého překryvu s posledními tahy (behaviorální – někteří „honí“ poslední čísla)
    for j, d in enumerate(recent_draws[::-1]):  # j=0 nejnovější
        inter = len(set(nums) & set(d))
        if inter >= OVERLAP_THRESHOLD:
            # nejnovější tah penalizuj víc
            weight = 1.0 + 0.5 * j
            s += weight * (300.0 * (inter - (OVERLAP_THRESHOLD - 1)))

    # (6) Jemné penalizace „kulatých“ a „oblíbených“ čísel (malý efekt)
    roundish = {5, 7, 10, 14, 20, 21, 28, 30, 35, 40, 42, 45, 49}
    s += 0.2 * sum(1 for x in nums if x in roundish)

    return s

# ----------------------------
# Pomocné funkce (parsování)
# ----------------------------
def find_data_path(cli_path: str | None = None) -> Path:
    if cli_path:
        p = Path(cli_path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Soubor nenalezen: {p}")
        return p

    for p in POSSIBLE_PATHS:
        if p.exists():
            return p

    tried = "\n".join(str(p) for p in POSSIBLE_PATHS)
    raise FileNotFoundError(
        "Nenalezen datový soubor. Hledal jsem:\n"
        f"{tried}\n\n"
        "Tip: dej sportka_2025.csv do stejné složky jako navrh_sportka.py, "
        "nebo nastav cestu jako argument: python navrh_sportka.py /cesta/k/souboru.csv"
    )


def parse_sestice(text, numbers: int = 49) -> list[int] | None:
    """Parsu 6 hlavních čísel z textu typu '19, 29, 35, 43, 45, 47 (+26)'."""
    if pd.isna(text):
        return None
    s = str(text)
    main_part = s.split("(")[0]
    nums = [int(x) for x in re.findall(r"\d+", main_part)]
    nums = nums[:6]
    if len(nums) != 6:
        return None
    if any(n < 1 or n > numbers for n in nums):
        return None
    # unikátnost
    if len(set(nums)) != 6:
        return None
    return nums


def parse_sance(text) -> list[int] | None:
    """Parsu Šanci jako 6 číslic (0–9)."""
    if pd.isna(text):
        return None
    s = re.sub(r"\D", "", str(text))
    if len(s) < 6:
        return None
    s = s[-6:]
    return [int(ch) for ch in s]


# ----------------------------
# Modelování frekvencí a návrhy
# ----------------------------
def weighted_counts(draws: list[list[int]], numbers: int = 49, decay: float = 0.985) -> np.ndarray:
    """Vážené počty výskytů čísel 1..numbers (index 0 nepoužit)."""
    counts = np.zeros(numbers + 1, dtype=float)
    n = len(draws)
    for i, draw in enumerate(draws):
        # i=0 nejstarší, i=n-1 nejnovější
        age = n - i
        w = decay ** (age - 1)
        for num in draw:
            if 1 <= num <= numbers:
                counts[num] += w
    return counts


def to_probabilities(counts: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    smoothed = counts + alpha
    total = smoothed.sum()
    return smoothed / total


def weighted_sample_without_replacement(population: np.ndarray, probs: np.ndarray, k: int) -> list[int]:
    """Vážený výběr bez opakování."""
    chosen: list[int] = []
    pop = population.copy()
    p = probs.copy()

    for _ in range(k):
        p = p / p.sum()
        pick = np.random.choice(pop, p=p)
        chosen.append(int(pick))
        mask = pop != pick
        pop = pop[mask]
        p = p[mask]

    return sorted(chosen)



def alchemy_score(
    cand: list[int],
    recent_draws: list[list[int]],
    freq: dict[int, int],
    past_combos: set[frozenset[int]],
) -> float:
    """
    „Alchymistické“ skóre: nižší je lepší.

    Nezvyšuje šanci trefit tažená čísla; jen tvoří kombinace s příběhem:
      - přesně 3 čísla 1–31 a 3 čísla 32–49
      - silně se vyhýbá překryvu s posledním slosováním
      - preferuje celé kombinace, které se v datech nikdy nevyskytly
      - jako tie-break preferuje „chladnější“ čísla (nižší roční frekvence)
    """
    nums = sorted(cand)

    # (A) tvrdě preferujeme kombinace, které se v datech nevyskytly jako celek
    fs = frozenset(nums)
    if fs in past_combos:
        return 1e9

    # (B) přesně 3 čísla <=31 a 3 čísla >=32
    low31 = sum(1 for x in nums if x <= 31)
    if low31 != 3:
        return 1e8 + abs(low31 - 3) * 1e6

    s = 0.0

    # (C) rozprostření napříč „desítkami“
    decades = {_decade_bucket(x) for x in nums}
    if len(decades) < MIN_DECADES:
        s += 5000.0 * (MIN_DECADES - len(decades))

    # (D) souvislé řady délky >=3
    if _max_consecutive_run(nums) >= 3:
        s += 2000.0

    # (E) „extrémně nepravděpodobné“ vůči poslednímu slosování: silná penalizace překryvu
    if recent_draws:
        last = set(recent_draws[-1])
        inter_last = len(last & set(nums))
        if inter_last > 0:
            # exponenciální trest: 1 shoda je už hodně „podezřelá“, 2+ téměř vyloučí
            s += 1e5 * (10 ** inter_last)

    # (F) penalizuj vysoký překryv (>= OVERLAP_THRESHOLD) s posledními OVERLAP_WINDOW tahy
    for r in recent_draws:
        inter = len(set(r) & set(nums))
        if inter >= OVERLAP_THRESHOLD:
            s += 5e5 * (inter - OVERLAP_THRESHOLD + 1) ** 3

    # (G) tie-break: preferuj „chladnější“ čísla
    s += float(sum(freq.get(x, 0) for x in nums))

    # (H) jemná penalizace „kulatých“ čísel
    s += 5.0 * sum(1 for x in nums if x % 10 == 0)

    return s


def suggest_sets_alchemy(
    draws: list[list[int]],
    numbers: int = 49,
    n_sets: int = 5,
) -> list[list[int]]:
    """Generátor pro MODE=alchemy."""
    if numbers != 49:
        raise ValueError("Alchemy režim je navržený pro Sportku 1–49.")

    # frekvence čísel v rámci zadaných tahů
    freq: dict[int, int] = {i: 0 for i in range(1, numbers + 1)}
    for d in draws:
        for x in d:
            if 1 <= x <= numbers:
                freq[x] += 1

    past_combos: set[frozenset[int]] = {frozenset(d) for d in draws}
    recent = draws[-OVERLAP_WINDOW:] if draws else []

    low_pool = list(range(1, 32))
    high_pool = list(range(32, numbers + 1))

    # Max-heap držící HEAP_KEEP nejlepších kandidátů: ukládáme (-score, cand)
    heap: list[tuple[float, list[int]]] = []

    for _ in range(NUM_CANDIDATES):
        cand = sorted(random.sample(low_pool, 3) + random.sample(high_pool, 3))
        score = alchemy_score(cand, recent, freq, past_combos)

        item = (-score, cand)
        if len(heap) < HEAP_KEEP:
            heapq.heappush(heap, item)
        else:
            if item[0] > heap[0][0]:
                heapq.heapreplace(heap, item)

    best = sorted([(-neg, cand) for neg, cand in heap], key=lambda x: x[0])

    suggestions: list[list[int]] = []
    for score, cand in best:
        if len(suggestions) >= n_sets:
            break

        # tvrdá pravidla dle zadání
        low31 = sum(1 for x in cand if x <= 31)
        if low31 != 3:
            continue
        if _max_consecutive_run(cand) >= 3:
            continue
        if len({_decade_bucket(x) for x in cand}) < MIN_DECADES:
            continue

        # rozmanitost vůči už vybraným: nepovolíme 4+ shod
        if all(len(set(prev) & set(cand)) < 4 for prev in suggestions):
            suggestions.append(cand)

    return suggestions


def suggest_sets(
    draws: list[list[int]],
    numbers: int = 49,
    n_sets: int = 5,
    mode: str = "random",
    decay: float = DECAY,
    alpha: float = ALPHA,
) -> list[list[int]]:
    """
    Navrhne n_sets kombinací po 6 číslech.

    - mode='random'   : „méně populární“ kombinace – generujeme mnoho kandidátů náhodně,
                       každému spočítáme popularity_score (heuristiky proti lidským vzorcům),
                       a vybereme nejlépe skórující sady s kontrolou rozmanitosti.
    - mode='weighted' : vážené podle historie (recency + vyhlazení) – spíš experiment.
    """
    population = np.arange(1, numbers + 1)

    if mode == "weighted":
        counts = weighted_counts(draws, numbers=numbers, decay=decay)
        probs = to_probabilities(counts, alpha=alpha)[1:]  # drop index 0

        suggestions: list[list[int]] = []
        max_tries = n_sets * 30

        for _ in range(max_tries):
            if len(suggestions) >= n_sets:
                break

            cand = weighted_sample_without_replacement(population, probs.copy(), 6)

            # rozmanitost: nepovolíme 4+ shod v sadě
            if all(len(set(prev) & set(cand)) < 4 for prev in suggestions):
                suggestions.append(cand)

        return suggestions

    if mode == "alchemy":
        return suggest_sets_alchemy(draws, numbers=numbers, n_sets=n_sets)

    # MODE=random (default): hledání „méně populárních“ kombinací
    recent = draws[-OVERLAP_WINDOW:] if draws else []

    # Max-heap držící HEAP_KEEP nejlepších kandidátů: ukládáme (-score, cand)
    heap: list[tuple[float, list[int]]] = []

    for _ in range(NUM_CANDIDATES):
        cand = sorted(random.sample(range(1, numbers + 1), 6))
        score = popularity_score(cand, recent)

        item = (-score, cand)
        if len(heap) < HEAP_KEEP:
            heapq.heappush(heap, item)
        else:
            # pokud je nový kandidát lepší (nižší score) než nejhorší v heapu
            if item[0] > heap[0][0]:
                heapq.heapreplace(heap, item)

    # Seřadíme nejlepší kandidáty podle skóre vzestupně
    best = sorted([(-s, c) for s, c in heap], key=lambda x: x[0])

    # Vybereme n_sets sad s dodatečnou rozmanitostí (ať nejsou skoro stejné)
    suggestions: list[list[int]] = []
    for score, cand in best:
        if len(suggestions) >= n_sets:
            break

        # tvrdá pravidla (podle tvých preferencí) – když poruší, přeskoč
        low31 = sum(1 for x in cand if x <= 31)
        if low31 > MAX_LOW31:
            continue
        if _max_consecutive_run(cand) >= 3:
            continue
        if len({_decade_bucket(x) for x in cand}) < MIN_DECADES:
            continue

        # rozmanitost vůči už vybraným
        if all(len(set(prev) & set(cand)) < 4 for prev in suggestions):
            suggestions.append(cand)

    # Fallback: když by byla pravidla příliš přísná, doplň uniformní náhodou
    while len(suggestions) < n_sets:
        cand = sorted(random.sample(range(1, numbers + 1), 6))
        if all(len(set(prev) & set(cand)) < 4 for prev in suggestions):
            suggestions.append(cand)

    return suggestions


def suggest_sance(
    digit_matrix: list[list[int]],
    n_sets: int = 5,
    mode: str = "random",
    decay: float = DECAY,
) -> list[str]:
    """
    Návrh Šance (6 číslic).
    - mode='random'   : 6 náhodných číslic 0–9
    - mode='weighted' : váženě podle historie po pozicích (recency)
    """
    suggestions: list[str] = []
    if mode != "weighted" or not digit_matrix:
        for _ in range(n_sets):
            suggestions.append("".join(str(int(x)) for x in np.random.randint(0, 10, size=6)))
        return suggestions

    arr = np.array(digit_matrix, dtype=int)
    for _ in range(n_sets):
        digits: list[int] = []
        for pos in range(6):
            counts = np.zeros(10, dtype=float)
            n = arr.shape[0]
            for i in range(n):
                age = n - i
                w = decay ** (age - 1)
                d = int(arr[i, pos])
                counts[d] += w
            counts += 0.5
            p = counts / counts.sum()
            d_pick = np.random.choice(np.arange(10), p=p)
            digits.append(int(d_pick))
        suggestions.append("".join(str(d) for d in digits))
    return suggestions


# ----------------------------
# Načtení dat (podpora dvou schémat)
# ----------------------------
def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)

    # CSV: zkus odhad separátoru + fallback na české varianty
    try:
        return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
    except Exception:
        try:
            return pd.read_csv(path, sep=";", encoding="utf-8-sig")
        except Exception:
            return pd.read_csv(path, sep=";", encoding="cp1250")


def load_draws(df: pd.DataFrame) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
    """
    Vrátí (first_draws, second_draws, sance_digits).
    Podporuje:
      A) sportka_2025.csv: sloupce Tah1_1..Tah1_6, Tah2_1..Tah2_6, Sance_1..Sance_6, Datum (ISO)
      B) starší export: Datum, 1. tah, 2. tah, Šance (textové sloupce)
    """
    cols = set(df.columns.astype(str))

    # Schéma A
    schema_a = all(c in cols for c in [
        "Datum",
        "Tah1_1","Tah1_2","Tah1_3","Tah1_4","Tah1_5","Tah1_6",
        "Tah2_1","Tah2_2","Tah2_3","Tah2_4","Tah2_5","Tah2_6",
        "Sance_1","Sance_2","Sance_3","Sance_4","Sance_5","Sance_6",
    ])

    if schema_a:
        # seřadit podle data (dayfirst není třeba, máme ISO)
        dt_ser = pd.to_datetime(df["Datum"], errors="coerce")
        df2 = df.assign(_dt=dt_ser).sort_values("_dt").reset_index(drop=True)

        first_draws: list[list[int]] = []
        second_draws: list[list[int]] = []
        sance_digits: list[list[int]] = []

        bad = 0
        for _, row in df2.iterrows():
            d1 = [int(row[f"Tah1_{i}"]) for i in range(1, 7)]
            d2 = [int(row[f"Tah2_{i}"]) for i in range(1, 7)]
            sc = [int(row[f"Sance_{i}"]) for i in range(1, 7)]

            # validace
            if len(set(d1)) != 6 or any(n < 1 or n > 49 for n in d1):
                bad += 1
                continue
            if len(set(d2)) != 6 or any(n < 1 or n > 49 for n in d2):
                bad += 1
                continue
            if any(d < 0 or d > 9 for d in sc):
                bad += 1
                continue

            first_draws.append(d1)
            second_draws.append(d2)
            sance_digits.append(sc)

        return first_draws, second_draws, sance_digits

    # Schéma B (tolerantní mapování názvů sloupců)
    colmap: dict[str, str] = {}
    for col in df.columns:
        low = str(col).strip().lower()
        if re.search(r"\bdatum\b", low):
            colmap["Datum"] = col
        elif re.search(r"\b1\.\s*tah\b|\btah\s*1\b", low):
            colmap["1. tah"] = col
        elif re.search(r"\b2\.\s*tah\b|\btah\s*2\b", low):
            colmap["2. tah"] = col
        elif re.search(r"\bšance\b|\bsance\b", low):
            colmap["Šance"] = col

    for needed in ["Datum", "1. tah", "2. tah", "Šance"]:
        if needed not in colmap:
            raise ValueError(f"Chybí očekávaný sloupec: {needed}")

    # seřadíme podle data – u českých exportů bývá den první
    try:
        df2 = df.copy()
        df2["_dt"] = pd.to_datetime(df2[colmap["Datum"]], errors="coerce", dayfirst=True)
        df2 = df2.sort_values("_dt").reset_index(drop=True)
    except Exception:
        df2 = df

    first_draws = []
    second_draws = []
    sance_digits = []
    bad = 0

    # DŮLEŽITÉ: ukládej jen řádky, kde se podařilo naparsovat všechno, aby se seznamy nerozjely.
    for _, row in df2.iterrows():
        d1 = parse_sestice(row[colmap["1. tah"]])
        d2 = parse_sestice(row[colmap["2. tah"]])
        sc = parse_sance(row[colmap["Šance"]])

        if d1 and d2 and sc:
            first_draws.append(d1)
            second_draws.append(d2)
            sance_digits.append(sc)
        else:
            bad += 1

    if bad:
        print(f"Pozor: vyřazeno {bad} řádků kvůli parsování (nevadí, jen informace).")

    return first_draws, second_draws, sance_digits


# ----------------------------
# Spuštění
# ----------------------------
if __name__ == "__main__":
    import sys

    cli_path = sys.argv[1] if len(sys.argv) >= 2 else None
    path = find_data_path(cli_path)
    df = read_table(path)

    first_draws, second_draws, sance_digits = load_draws(df)

    print(f"Načteno losování: {len(first_draws)} (zdroj: {path.name})")
    print(f"Režim: MODE={MODE!r}, SEED={RANDOM_SEED}")

    # Návrhy
    first_suggestions = suggest_sets(first_draws, numbers=49, n_sets=NUM_SUGGESTIONS, mode=MODE, decay=DECAY, alpha=ALPHA)
    second_suggestions = suggest_sets(second_draws, numbers=49, n_sets=NUM_SUGGESTIONS, mode=MODE, decay=DECAY, alpha=ALPHA)

    # Šance – default držíme random (prakticky dává větší smysl), ale dá se přepnout env: SPORTKA_SANCE_MODE=weighted
    sance_mode = os.getenv("SPORTKA_SANCE_MODE", "random").strip().lower()
    sance_suggestions = suggest_sance(sance_digits, n_sets=NUM_SUGGESTIONS, mode=sance_mode, decay=DECAY)

    # Výstup
    print("\n--- Návrhy pro 1. tah ---")
    for i, s in enumerate(first_suggestions, 1):
        print(f"{i}. {s}")

    print("\n--- Návrhy pro 2. tah ---")
    for i, s in enumerate(second_suggestions, 1):
        print(f"{i}. {s}")

    print("\n--- Návrhy pro Šanci ---")
    for i, s in enumerate(sance_suggestions, 1):
        print(f"{i}. {s}")

    # Uložení do CSV – default do složky skriptu (ať se to neztratí).
    out_rows = []
    for i, s in enumerate(first_suggestions, 1):
        out_rows.append({"Typ": "1. tah", "Navrh": i, "Cisla": " ".join(map(str, s))})
    for i, s in enumerate(second_suggestions, 1):
        out_rows.append({"Typ": "2. tah", "Navrh": i, "Cisla": " ".join(map(str, s))})
    for i, s in enumerate(sance_suggestions, 1):
        out_rows.append({"Typ": "Šance", "Navrh": i, "Cisla": s})

    out_df = pd.DataFrame(out_rows)
    out_path = SCRIPT_DIR / "navrhy_sportka.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\nVýsledky uloženy do: {out_path}")
