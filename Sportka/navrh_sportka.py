import os
import re
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------
# Nastavení
# ----------------------------
# Cesty k datům na ploše – skript zkusí .xlsx i .csv
DESKTOP = Path.home() / "Desktop"
BASENAME = "vysledky_sportky_50"
POSSIBLE_PATHS = [
DESKTOP / f"{BASENAME}.xlsx",
DESKTOP / f"{BASENAME}.csv",
DESKTOP / BASENAME,  # kdyby byl bez přípony
]

# Počet doporučených sad (ticktů) pro každý tah
NUM_SUGGESTIONS = 5

# Exponenciální útlum pro "čerstvost": 0.97 až 0.995 je rozumné
DECAY = 0.985

# Dirichlet/Laplace vyhlazení (pseudo-počty)
ALPHA = 1.0

# Seed pro reprodukovatelnost
RANDOM_SEED = 20251112
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# ----------------------------
# Pomocné funkce
# ----------------------------
def find_data_path():
    for p in POSSIBLE_PATHS:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"Nenalezen soubor na ploše: {BASENAME} (zkoušeno .xlsx i .csv). "
        f"Zkontroluj prosím název a umístění."
    )

def parse_sestice(text):
    """
    Očekává formát jako: '19, 29, 35, 43, 45, 47 (+26)' nebo bez závorky.
    Vrací list[6] hlavních čísel (1–49). Dodatkové ignorujeme.
    """
    if pd.isna(text):
        return None
    s = str(text)
    # vytáhneme vše před '('
    main_part = s.split('(')[0]
    nums = [int(x) for x in re.findall(r"\d+", main_part)]
    # necháme jen prvních 6
    nums = nums[:6]
    if len(nums) == 6:
        return nums
    return None

def parse_sance(text):
    """
    Očekává 6místné číslo jako string nebo int.
    Vrací list délky 6 s číslicemi 0-9.
    """
    if pd.isna(text):
        return None
    s = re.sub(r"\D", "", str(text))
    if len(s) < 6:
        return None
    s = s[-6:]  # vezmi posledních 6 číslic, kdyby jich bylo víc
    return [int(ch) for ch in s]

def weighted_counts(draws, numbers=49, decay=0.985):
    """
    Exponenciálně vážené počítání výskytů pro čísla 1..numbers.
    Novější záznam má větší váhu. draws je list seznamů po 6 číslech.
    """
    counts = np.zeros(numbers + 1, dtype=float)  # indexujeme 1..49
    n = len(draws)
    for idx, comb in enumerate(draws):
        # recency weight: poslední záznam má nejvyšší váhu
        # idx=0 je nejstarší; dáme mu menší váhu
        age = n - idx  # 1..n
        w = decay ** (age - 1)
        for num in comb:
            if 1 <= num <= numbers:
                counts[num] += w
    return counts

def to_probabilities(counts, alpha=1.0):
    """
    Dirichlet/Laplace vyhlazení: p_i ~ (count_i + alpha) / sum(count + alpha)
    """
    smoothed = counts + alpha
    total = smoothed.sum()
    return smoothed / total

def weighted_sample_without_replacement(population, probs, k):
    """
    Vážený výběr bez opakování z population s pravděpodobnostmi probs.
    Jednoduchý postup: opakovaně losuj 1 prvek, renormalizuj a vyřaď.
    """
    chosen = []
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

def suggest_sets(draws, numbers=49, n_sets=5, decay=DECAY, alpha=ALPHA):
    """
    Vypočítá vážené frekvence, převede na pravděpodobnosti a navrhne n_sets kombinací po 6 číslech.
    Snaží se o rozmanitost návrhů (ne příliš podobné sady).
    """
    counts = weighted_counts(draws, numbers=numbers, decay=decay)
    probs = to_probabilities(counts, alpha=alpha)[1:]  # drop index 0
    population = np.arange(1, numbers + 1)

    suggestions = []
    max_tries = n_sets * 10
    tries = 0
    while len(suggestions) < n_sets and tries < max_tries:
        tries += 1
        cand = weighted_sample_without_replacement(population, probs.copy(), 6)
        # rozmanitost: neklaďme kandidáty s vysokým překryvem s již navrženými
        ok = True
        for prev in suggestions:
            inter = len(set(prev) & set(cand))
            if inter >= 4:  # příliš podobné (4+ stejná čísla)
                ok = False
                break
        if ok:
            suggestions.append(cand)
    return suggestions

def suggest_sance(digit_matrix, n_sets=5):
    """
    digit_matrix: list of digit lists (každá délka 6) – historická Šance.
    Návrh Šance: pro každou pozici vyber digit váženě dle frekvence (s mírným vyhlazením).
    """
    if not digit_matrix:
        return []
    arr = np.array(digit_matrix)  # shape: [N, 6]
    suggestions = []
    for _ in range(n_sets):
        digits = []
        for pos in range(6):
            counts = np.zeros(10, dtype=float)
            # exponenciální vážení podle recency (čerstvé víc váží)
            n = arr.shape[0]
            for i in range(n):
                age = n - i
                w = DECAY ** (age - 1)
                d = int(arr[i, pos])
                counts[d] += w
            counts += 0.5  # jemné vyhlazení
            p = counts / counts.sum()
            d_pick = np.random.choice(np.arange(10), p=p)
            digits.append(int(d_pick))
        suggestions.append("".join(str(d) for d in digits))
    return suggestions

# ----------------------------
# Načtení dat
# ----------------------------
path = find_data_path()
if path.suffix.lower() == ".xlsx":
    df = pd.read_excel(path)
else:
    # pokus o CSV s detekcí oddělovače
    try:
        df = pd.read_csv(path)
    except Exception:
        df = pd.read_csv(path, sep=";")

# Očekávané sloupce: Datum, 1. tah, 2. tah, Šance
# Umožníme tolerantní mapování názvů
colmap = {}
for col in df.columns:
    low = str(col).strip().lower()
    if "datum" in low:
        colmap["Datum"] = col
    elif "1" in low and "tah" in low:
        colmap["1. tah"] = col
    elif "2" in low and "tah" in low:
        colmap["2. tah"] = col
    elif "sance" in low or "šance" in low:
        colmap["Šance"] = col

for needed in ["Datum", "1. tah", "2. tah", "Šance"]:
    if needed not in colmap:
        raise ValueError(f"Chybí očekávaný sloupec: {needed}")

# seřadíme podle data, ať jdeme od nejstaršího k nejnovějšímu
try:
    df["_dt"] = pd.to_datetime(df[colmap["Datum"]], errors="coerce")
    df = df.sort_values("_dt").reset_index(drop=True)
except Exception:
    # když by datumy nešly převést, necháme původní pořadí
    pass

first_draws = []
second_draws = []
sance_digits = []

for _, row in df.iterrows():
    d1 = parse_sestice(row[colmap["1. tah"]])
    d2 = parse_sestice(row[colmap["2. tah"]])
    sc = parse_sance(row[colmap["Šance"]])

    if d1: first_draws.append(d1)
    if d2: second_draws.append(d2)
    if sc: sance_digits.append(sc)

# ----------------------------
# Návrhy
# ----------------------------
first_suggestions = suggest_sets(first_draws, numbers=49, n_sets=NUM_SUGGESTIONS, decay=DECAY, alpha=ALPHA)
second_suggestions = suggest_sets(second_draws, numbers=49, n_sets=NUM_SUGGESTIONS, decay=DECAY, alpha=ALPHA)
sance_suggestions = suggest_sance(sance_digits, n_sets=NUM_SUGGESTIONS)

# ----------------------------
# Výstup
# ----------------------------
print("\n--- Návrhy pro 1. tah ---")
for i, s in enumerate(first_suggestions, 1):
    print(f"{i}. {s}")

print("\n--- Návrhy pro 2. tah ---")
for i, s in enumerate(second_suggestions, 1):
    print(f"{i}. {s}")

print("\n--- Návrhy pro Šanci ---")
for i, s in enumerate(sance_suggestions, 1):
    print(f"{i}. {s}")

# Uložení do CSV na plochu
out_rows = []
for i, s in enumerate(first_suggestions, 1):
    out_rows.append({"Typ": "1. tah", "Návrh #": i, "Čísla": " ".join(map(str, s))})
for i, s in enumerate(second_suggestions, 1):
    out_rows.append({"Typ": "2. tah", "Návrh #": i, "Čísla": " ".join(map(str, s))})
for i, s in enumerate(sance_suggestions, 1):
    out_rows.append({"Typ": "Šance", "Návrh #": i, "Čísla": s})

out_df = pd.DataFrame(out_rows)
out_path = DESKTOP / "navrhy_sportka.csv"
out_df.to_csv(out_path, index=False, encoding="utf-8")
print(f"\nVýsledky uloženy do: {out_path}")
