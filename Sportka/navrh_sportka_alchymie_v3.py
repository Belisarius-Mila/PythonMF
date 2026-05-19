import os
import re
import random
import heapq
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

# Sportka – návrh čísel (edukativní). Minulá losování nezvyšují šanci na výhru.
# MODE: random (méně-populární), alchemy (3x low/high, vyhýbá se posledním),
#       weighted (experiment), balanced (mix + lepší pokrytí napříč návrhy),
#       cover (agresivní pokrytí čísel napříč více tikety).

# Nastavení
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
#   - "balanced" = mix kandidátů + výběr sad s lepším pokrytím čísel napříč návrhy
#   - "cover"    = ještě silnější preference pokrytí (pro více tiketů)
MODE = os.getenv("SPORTKA_MODE", "alchemy").strip().lower()

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
# Heuristiky pro „méně populární“ kombinace (MODE=random).
NUM_CANDIDATES = int(os.getenv("SPORTKA_CANDIDATES", "50000"))
HEAP_KEEP = int(os.getenv("SPORTKA_HEAP_KEEP", "1500"))  # kolik nejlepších kandidátů si držet
MAX_LOW31 = int(os.getenv("SPORTKA_MAX_LOW31", "3"))     # max počet čísel 1–31
MIN_DECADES = int(os.getenv("SPORTKA_MIN_DECADES", "3")) # min počet „desítek“ (1–9, 10–19, ... 40–49)
OVERLAP_WINDOW = int(os.getenv("SPORTKA_OVERLAP_WINDOW", "3"))  # kolik posledních tahů penalizovat
OVERLAP_THRESHOLD = int(os.getenv("SPORTKA_OVERLAP_THRESHOLD", "4"))  # od kolika shod penalizovat
REPEAT_PENALTY = float(os.getenv("SPORTKA_REPEAT_PENALTY", "4.0"))  # měkká penalizace opakování čísel napříč návrhy (alchemy)
PACK_REPEAT_PENALTY = float(os.getenv("SPORTKA_PACK_REPEAT_PENALTY", "7.0"))  # balanced: penalizace opakování napříč celou sadou
MAX_MATCH_LAST = int(os.getenv("SPORTKA_MAX_MATCH_LAST", "6"))  # 6 = vypnuto; např. 2 => max 2 shody s poslednim tahem
PACK_MODE_WEIGHTS = {
    "random": float(os.getenv("SPORTKA_BAL_W_RANDOM", "1.0")),
    "alchemy": float(os.getenv("SPORTKA_BAL_W_ALCHEMY", "1.0")),
    "weighted": float(os.getenv("SPORTKA_BAL_W_WEIGHTED", "0.7")),
}
INJECT_HOT_NUMBER = os.getenv("SPORTKA_INJECT_HOT", "1").strip().lower() not in {"0", "false", "no", "off"}
HOT_TOP_N = int(os.getenv("SPORTKA_HOT_TOP_N", "6"))

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

def _valid_draw(draw: list[int], numbers: int = 49) -> bool:
    return len(draw) == 6 and len(set(draw)) == 6 and all(1 <= n <= numbers for n in draw)

def _passes_rules(cand: list[int], *, low31_eq: int | None = None, low31_max: int | None = None) -> bool:
    low31 = sum(1 for x in cand if x <= 31)
    if low31_eq is not None and low31 != low31_eq:
        return False
    if low31_max is not None and low31 > low31_max:
        return False
    if _max_consecutive_run(cand) >= 3:
        return False
    if len({_decade_bucket(x) for x in cand}) < MIN_DECADES:
        return False
    return True

def _is_diverse(cand: list[int], chosen: list[list[int]]) -> bool:
    return all(len(set(prev) & set(cand)) < 4 for prev in chosen)


def _passes_last_draw_filter(cand: list[int], draws: list[list[int]]) -> bool:
    if MAX_MATCH_LAST >= 6 or not draws:
        return True
    last = set(draws[-1])
    return len(last & set(cand)) <= MAX_MATCH_LAST


def _pairwise_overlap(a: list[int], b: list[int]) -> int:
    return len(set(a) & set(b))


def _pack_stats(suggestions: list[list[int]]) -> dict[str, float]:
    if not suggestions:
        return {"unique_numbers": 0, "avg_overlap": 0.0, "max_overlap": 0.0}
    overlaps = []
    for i in range(len(suggestions)):
        for j in range(i + 1, len(suggestions)):
            overlaps.append(_pairwise_overlap(suggestions[i], suggestions[j]))
    unique_numbers = len(set().union(*[set(s) for s in suggestions]))
    return {
        "unique_numbers": float(unique_numbers),
        "avg_overlap": float(np.mean(overlaps)) if overlaps else 0.0,
        "max_overlap": float(max(overlaps)) if overlaps else 0.0,
    }


def _proposal_score_for_export(cand: list[int], draws: list[list[int]], mode: str) -> float:
    """Hrubé skóre pro export/porovnání (nižší je lepší)."""
    recent = draws[-OVERLAP_WINDOW:] if draws else []
    if mode in {"alchemy", "balanced", "cover"} and cand:
        freq: dict[int, int] = {i: 0 for i in range(1, 50)}
        for d in draws:
            for x in d:
                if 1 <= x <= 49:
                    freq[x] += 1
        past_combos: set[frozenset[int]] = {frozenset(d) for d in draws if len(d) == 6}
        if all(1 <= x <= 49 for x in cand):
            sc = alchemy_score(cand, recent, freq, past_combos)
            if sc < 1e9:
                return float(sc)
    return float(popularity_score(cand, recent))

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


def most_frequent_numbers(draws: list[list[int]], top_n: int = 6) -> list[tuple[int, int]]:
    """Vrátí nejčastější čísla ve formátu [(cislo, pocet), ...]."""
    counts: Counter[int] = Counter()
    for draw in draws:
        counts.update(draw)
    return counts.most_common(top_n)


def _inject_hot_number_into_candidate(
    cand: list[int],
    hot_numbers: list[int],
    draws: list[list[int]],
    numbers: int,
) -> list[int]:
    """
    Z kandidáta vytvoří variantu "5 původních + 1 hot číslo".
    Pokud nejde najít validní variantu, vrací původní kandidát.
    """
    if len(cand) != 6 or not hot_numbers:
        return cand

    idxs = list(range(6))
    random.shuffle(idxs)
    hot = hot_numbers[:]
    random.shuffle(hot)

    for drop_idx in idxs:
        base5 = [x for i, x in enumerate(cand) if i != drop_idx]
        for h in hot:
            if h in base5:
                continue
            merged = sorted(base5 + [h])
            if _valid_draw(merged, numbers) and _passes_last_draw_filter(merged, draws):
                return merged
    return cand


def _apply_hot_number_mix(
    suggestions: list[list[int]],
    draws: list[list[int]],
    numbers: int,
) -> list[list[int]]:
    if not INJECT_HOT_NUMBER or not suggestions:
        return suggestions

    hot_numbers = [n for n, _ in most_frequent_numbers(draws, top_n=max(1, HOT_TOP_N))]
    if not hot_numbers:
        return suggestions

    mixed: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for cand in suggestions:
        updated = _inject_hot_number_into_candidate(cand, hot_numbers, draws, numbers)
        t_updated = tuple(updated)
        if t_updated not in seen:
            mixed.append(updated)
            seen.add(t_updated)
            continue
        t_orig = tuple(sorted(cand))
        if t_orig not in seen:
            mixed.append(sorted(cand))
            seen.add(t_orig)
    return mixed

# Pomocné funkce (parsování)
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
    nums = [int(x) for x in re.findall(r"\d+", main_part)][:6]
    return nums if _valid_draw(nums, numbers) else None


# Modelování frekvencí a návrhy
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
    used_counts: dict[int, int] = {}
    remaining = best.copy()

    # Greedy výběr s měkkou penalizací opakování čísel napříč návrhy.
    # Cíl: aby se v jedné sadě návrhů příliš nelepila „magnetická“ čísla (např. 22, 45),
    # ale zároveň zůstal zachovaný „alchymistický“ charakter skóre.
    while len(suggestions) < n_sets and remaining:
        pick_idx: int | None = None
        pick_cand: list[int] | None = None
        pick_score = float("inf")

        for idx, (score, cand) in enumerate(remaining):
            if not _passes_rules(cand, low31_eq=3):
                continue

            # rozmanitost vůči už vybraným: nepovolíme 4+ shod
            if not _is_diverse(cand, suggestions):
                continue

            # měkká penalizace opakování čísel napříč návrhy (kvadratická – druhé použití je mírně penalizované,
            # třetí výrazněji, atd.)
            rep_pen = REPEAT_PENALTY * sum((used_counts.get(x, 0) ** 2) for x in cand)
            adj = score + rep_pen

            if adj < pick_score:
                pick_score = adj
                pick_idx = idx
                pick_cand = cand

        if pick_idx is None or pick_cand is None:
            break

        suggestions.append(pick_cand)
        for x in pick_cand:
            used_counts[x] = used_counts.get(x, 0) + 1
        remaining.pop(pick_idx)

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

            if _is_diverse(cand, suggestions) and _passes_last_draw_filter(cand, draws):
                suggestions.append(cand)

        while len(suggestions) < n_sets:
            cand = sorted(random.sample(range(1, numbers + 1), 6))
            if _is_diverse(cand, suggestions) and _passes_last_draw_filter(cand, draws):
                suggestions.append(cand)

        return _apply_hot_number_mix(suggestions, draws, numbers)

    if mode == "alchemy":
        res = suggest_sets_alchemy(draws, numbers=numbers, n_sets=n_sets)
        res = [c for c in res if _passes_last_draw_filter(c, draws)]
        while len(res) < n_sets:
            c = sorted(random.sample(range(1, numbers + 1), 6))
            if _is_diverse(c, res) and _passes_last_draw_filter(c, draws):
                res.append(c)
        return _apply_hot_number_mix(res, draws, numbers)

    if mode == "balanced":
        return _apply_hot_number_mix(
            suggest_sets_balanced(draws, numbers=numbers, n_sets=n_sets, decay=decay, alpha=alpha),
            draws,
            numbers,
        )
    if mode == "cover":
        return _apply_hot_number_mix(
            suggest_sets_cover(draws, numbers=numbers, n_sets=n_sets, decay=decay, alpha=alpha),
            draws,
            numbers,
        )

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

        if not _passes_rules(cand, low31_max=MAX_LOW31):
            continue

        if _is_diverse(cand, suggestions) and _passes_last_draw_filter(cand, draws):
            suggestions.append(cand)

    while len(suggestions) < n_sets:
        cand = sorted(random.sample(range(1, numbers + 1), 6))
        if _is_diverse(cand, suggestions) and _passes_last_draw_filter(cand, draws):
            suggestions.append(cand)

    return _apply_hot_number_mix(suggestions, draws, numbers)


def _generate_candidate_pool(
    draws: list[list[int]],
    numbers: int,
    *,
    target_pool_size: int = 200,
    decay: float = DECAY,
    alpha: float = ALPHA,
) -> list[list[int]]:
    """
    Kandidátní pool pro balanced režim.
    Míchá výstupy z random/alchemy/weighted, pak deduplikuje.
    """
    candidates: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()

    def _add_many(mode_name: str, count: int) -> None:
        if count <= 0:
            return
        # Pro balanced režim nechceme znovu spouštět extrémně drahé vyhledávání
        # ve velkých dávkách. "random" generujeme přímo a "alchemy" držíme malé.
        if mode_name == "random":
            recent = draws[-OVERLAP_WINDOW:] if draws else []
            tries = 0
            max_tries = count * 80
            while tries < max_tries and count > 0:
                tries += 1
                c = sorted(random.sample(range(1, numbers + 1), 6))
                if not _passes_rules(c, low31_max=MAX_LOW31):
                    continue
                if not _passes_last_draw_filter(c, draws):
                    continue
                # lehká kvalita přes popularity score
                if popularity_score(c, recent) > 25:
                    continue
                t = tuple(c)
                if t in seen:
                    continue
                seen.add(t)
                candidates.append(c)
                count -= 1
            return

        if mode_name == "alchemy":
            count = min(count, max(10, n_sets_hint * 2))

        try:
            res = suggest_sets(draws, numbers=numbers, n_sets=count, mode=mode_name, decay=decay, alpha=alpha)
        except Exception:
            return
        for c in res:
            t = tuple(sorted(c))
            if t not in seen and _valid_draw(list(t), numbers):
                seen.add(t)
                candidates.append(list(t))

    # Hrubé rozdělení poolu mezi režimy
    total_w = sum(max(0.0, w) for w in PACK_MODE_WEIGHTS.values()) or 1.0
    alloc = {
        k: max(0, int(target_pool_size * max(0.0, PACK_MODE_WEIGHTS[k]) / total_w))
        for k in PACK_MODE_WEIGHTS
    }
    # dorovnat na přesný target (přebytky doplníme randomem)
    short = max(0, target_pool_size - sum(alloc.values()))
    alloc["random"] += short

    n_sets_hint = max(1, target_pool_size // 40)

    _add_many("random", alloc["random"])
    if numbers == 49:
        _add_many("alchemy", alloc["alchemy"])
    _add_many("weighted", alloc["weighted"])

    # Fallback: doplň čistě náhodné kandidáty
    tries = 0
    while len(candidates) < target_pool_size and tries < target_pool_size * 20:
        tries += 1
        c = sorted(random.sample(range(1, numbers + 1), 6))
        t = tuple(c)
        if t in seen:
            continue
        if _max_consecutive_run(c) >= 4:
            continue
        if not _passes_last_draw_filter(c, draws):
            continue
        seen.add(t)
        candidates.append(c)

    return candidates


def suggest_sets_balanced(
    draws: list[list[int]],
    numbers: int = 49,
    n_sets: int = 5,
    decay: float = DECAY,
    alpha: float = ALPHA,
) -> list[list[int]]:
    """
    Balanced režim:
      1) vytvoří pool kandidátů z více režimů
      2) greedy vybere sady s penalizací opakování čísel napříč balíčkem
    Cíl: lepší pokrytí (coverage) při zachování rozumných heuristik.
    """
    recent = draws[-OVERLAP_WINDOW:] if draws else []
    pool = _generate_candidate_pool(draws, numbers, target_pool_size=max(120, n_sets * 40), decay=decay, alpha=alpha)
    if not pool:
        return []

    # Předskóruj kandidáty společným stylem (pro 49 upřednostníme alchemy/logiku, jinak popularity)
    freq: dict[int, int] = {i: 0 for i in range(1, numbers + 1)}
    for d in draws:
        for x in d:
            if 1 <= x <= numbers:
                freq[x] += 1
    past_combos: set[frozenset[int]] = {frozenset(d) for d in draws}

    base_scores: dict[tuple[int, ...], float] = {}
    for c in pool:
        t = tuple(c)
        if numbers == 49:
            sc = alchemy_score(c, recent, freq, past_combos)
            if sc >= 1e9:
                sc = popularity_score(c, recent) + 500.0
        else:
            sc = popularity_score(c, recent)
        base_scores[t] = float(sc)

    chosen: list[list[int]] = []
    used_counts: dict[int, int] = {}
    remaining = pool[:]

    while len(chosen) < n_sets and remaining:
        best_idx = None
        best_adj = float("inf")

        for idx, cand in enumerate(remaining):
            if not _is_diverse(cand, chosen):
                continue
            if not _passes_last_draw_filter(cand, draws):
                continue
            # měkké pokrytí: penalizuj opakování čísel napříč balíčkem
            rep = PACK_REPEAT_PENALTY * sum((used_counts.get(x, 0) ** 2) for x in cand)
            # drobný bonus za nová čísla v balíčku (lepší coverage)
            new_bonus = -1.5 * sum(1 for x in cand if used_counts.get(x, 0) == 0)
            adj = base_scores[tuple(cand)] + rep + new_bonus
            if adj < best_adj:
                best_adj = adj
                best_idx = idx

        if best_idx is None:
            break

        pick = remaining.pop(best_idx)
        chosen.append(pick)
        for x in pick:
            used_counts[x] = used_counts.get(x, 0) + 1

    # Fallback doplnění
    while len(chosen) < n_sets:
        c = sorted(random.sample(range(1, numbers + 1), 6))
        if _is_diverse(c, chosen) and _passes_last_draw_filter(c, draws):
            chosen.append(c)

    return chosen


def suggest_sets_cover(
    draws: list[list[int]],
    numbers: int = 49,
    n_sets: int = 5,
    decay: float = DECAY,
    alpha: float = ALPHA,
) -> list[list[int]]:
    """
    Cover režim: maximalizuje pokrytí čísel napříč balíčkem tiketů.
    Je to vědomě "portfolio" režim, ne pokus o predikci.
    """
    pool = _generate_candidate_pool(draws, numbers, target_pool_size=max(220, n_sets * 70), decay=decay, alpha=alpha)
    if not pool:
        return []

    recent = draws[-OVERLAP_WINDOW:] if draws else []
    scored = []
    for c in pool:
        base = popularity_score(c, recent)
        if numbers == 49:
            low31 = sum(1 for x in c if x <= 31)
            base += abs(low31 - 3) * 2.5
        scored.append((base, c))
    scored.sort(key=lambda x: x[0])

    chosen: list[list[int]] = []
    used_counts: dict[int, int] = {}

    while len(chosen) < n_sets and scored:
        best_idx = None
        best_score = float("inf")
        for idx, (base, c) in enumerate(scored[: min(len(scored), 120)]):
            if not _is_diverse(c, chosen):
                continue
            if not _passes_last_draw_filter(c, draws):
                continue
            overlap_pen = 14.0 * sum((used_counts.get(x, 0) ** 2) for x in c)
            novelty_bonus = -4.0 * sum(1 for x in c if used_counts.get(x, 0) == 0)
            # lehký bonus za zastoupení "slabě pokrytých" dekád
            decade_counts: dict[int, int] = {}
            for prev in chosen:
                for x in prev:
                    b = _decade_bucket(x)
                    decade_counts[b] = decade_counts.get(b, 0) + 1
            decade_bonus = 0.0
            for x in c:
                decade_bonus += 0.3 * decade_counts.get(_decade_bucket(x), 0)
            adj = base + overlap_pen + novelty_bonus + decade_bonus
            if adj < best_score:
                best_score = adj
                best_idx = idx
        if best_idx is None:
            break
        _, pick = scored.pop(best_idx)
        chosen.append(pick)
        for x in pick:
            used_counts[x] = used_counts.get(x, 0) + 1

    while len(chosen) < n_sets:
        c = sorted(random.sample(range(1, numbers + 1), 6))
        if _is_diverse(c, chosen) and _passes_last_draw_filter(c, draws):
            chosen.append(c)
    return chosen


# Načtení dat (podpora dvou schémat)
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


def load_draws(df: pd.DataFrame) -> tuple[list[list[int]], list[list[int]]]:
    """
    Vrátí (first_draws, second_draws).
    Podporuje:
      A) sportka_2025.csv: sloupce Tah1_1..Tah1_6, Tah2_1..Tah2_6, Datum (ISO)
      B) starší export: Datum, 1. tah, 2. tah (textové sloupce)
    """
    cols = set(df.columns.astype(str))

    # Schéma A
    schema_a = all(c in cols for c in [
        "Datum",
        "Tah1_1","Tah1_2","Tah1_3","Tah1_4","Tah1_5","Tah1_6",
        "Tah2_1","Tah2_2","Tah2_3","Tah2_4","Tah2_5","Tah2_6",
    ])

    if schema_a:
        # seřadit podle data (dayfirst není třeba, máme ISO)
        dt_ser = pd.to_datetime(df["Datum"], errors="coerce")
        df2 = df.assign(_dt=dt_ser).sort_values("_dt").reset_index(drop=True)

        first_draws: list[list[int]] = []
        second_draws: list[list[int]] = []
        bad = 0
        for _, row in df2.iterrows():
            d1 = [int(row[f"Tah1_{i}"]) for i in range(1, 7)]
            d2 = [int(row[f"Tah2_{i}"]) for i in range(1, 7)]

            if not _valid_draw(d1) or not _valid_draw(d2):
                bad += 1
                continue

            first_draws.append(d1)
            second_draws.append(d2)

        return first_draws, second_draws

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
    for needed in ["Datum", "1. tah", "2. tah"]:
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
    bad = 0

    for _, row in df2.iterrows():
        d1 = parse_sestice(row[colmap["1. tah"]])
        d2 = parse_sestice(row[colmap["2. tah"]])
        if d1 and d2:
            first_draws.append(d1)
            second_draws.append(d2)
        else:
            bad += 1

    if bad:
        print(f"Pozor: vyřazeno {bad} řádků kvůli parsování (nevadí, jen informace).")

    return first_draws, second_draws


# Spuštění
if __name__ == "__main__":
    import argparse
    import sys
    import time

    def run_benchmark_synthetic(calls: int = 20, rows: int = 200) -> None:
        np.random.seed(0)
        draws = [
            sorted(np.random.choice(np.arange(1, 50), size=6, replace=False).tolist())
            for _ in range(rows)
        ]
        _run_benchmark_core(draws, calls=calls, label=f"synthetic rows={rows}")

    def run_benchmark_real(draws: list[list[int]], calls: int = 20) -> None:
        if not draws:
            print("Benchmark: zadne realne tahy.")
            return
        _run_benchmark_core(draws, calls=calls, label=f"real rows={len(draws)}")

    def _run_benchmark_core(draws: list[list[int]], calls: int, label: str) -> None:
        start = time.perf_counter()
        for _ in range(calls):
            suggest_sets(draws, numbers=49, n_sets=NUM_SUGGESTIONS, mode=MODE, decay=DECAY, alpha=ALPHA)
        total = time.perf_counter() - start
        avg = total / calls if calls else 0.0
        print(f"Benchmark ({label}, calls={calls})")
        print(f"total: {total:.4f}s")
        print(f"avg: {avg:.4f}s per call")

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("path", nargs="?", help="Cesta k souboru (csv/xlsx).")
    parser.add_argument("--mode", choices=["random", "weighted", "alchemy", "balanced", "cover"], help="Rezim generovani.")
    parser.add_argument("--n", type=int, help="Pocet navrhu pro kazdy tah.")
    parser.add_argument("--max-match-last", type=int, dest="max_match_last", help="Max shod s poslednim tahem (0-6, 6=vypnuto).")
    parser.add_argument("--benchmark", action="store_true", help="Benchmark na syntetickych datech.")
    parser.add_argument("--benchmark-real", action="store_true", help="Benchmark na realnych datech ze souboru.")
    parser.add_argument("--benchmark-calls", type=int, default=20, help="Kolik volani benchmarku.")
    parser.add_argument("--benchmark-rows", type=int, default=200, help="Pocet radku pro synteticky benchmark.")
    args = parser.parse_args()

    # CLI override (silnejsi nez env/default)
    if args.mode:
        MODE = args.mode
    if args.n is not None:
        if args.n <= 0:
            print("--n musi byt kladne cislo.")
            sys.exit(1)
        NUM_SUGGESTIONS = args.n
    if args.max_match_last is not None:
        if not (0 <= args.max_match_last <= 6):
            print("--max-match-last musi byt v intervalu 0..6.")
            sys.exit(1)
        MAX_MATCH_LAST = args.max_match_last

    print(f"[sportka] MODE={MODE} (nastav SPORTKA_MODE pro změnu)")

    if args.benchmark:
        run_benchmark_synthetic(calls=args.benchmark_calls, rows=args.benchmark_rows)
        sys.exit(0)

    if args.benchmark_real:
        if not args.path:
            print("Benchmark-real vyzaduje cestu k souboru.")
            sys.exit(1)
        path = find_data_path(args.path)
        t0 = time.perf_counter()
        df = read_table(path)
        first_draws, second_draws = load_draws(df)
        t_load = time.perf_counter() - t0
        all_draws = first_draws + second_draws
        print(f"Benchmark-real: soubor={path.name}, rows={len(all_draws)}, load_time={t_load:.3f}s")
        run_benchmark_real(all_draws, calls=args.benchmark_calls)
        sys.exit(0)

    cli_path = args.path
    path = find_data_path(cli_path)
    df = read_table(path)

    first_draws, second_draws = load_draws(df)

    print(f"Načteno losování: {len(first_draws)} (zdroj: {path.name})")
    print(f"Režim: MODE={MODE!r}, SEED={RANDOM_SEED}")
    if MAX_MATCH_LAST < 6:
        print(f"Filtr: max shod s poslednim tahem = {MAX_MATCH_LAST}")
    if MODE == "alchemy":
        print(f"Alchemy: repeat_penalty={REPEAT_PENALTY}")
    if MODE == "balanced":
        print(
            f"Balanced: pack_repeat_penalty={PACK_REPEAT_PENALTY}, "
            f"weights={PACK_MODE_WEIGHTS}"
        )
    if MODE == "cover":
        print("Cover: agresivni pokryti napric tikety (portfolio rezim)")

    all_draws = first_draws + second_draws
    top1 = most_frequent_numbers(first_draws, top_n=6)
    top2 = most_frequent_numbers(second_draws, top_n=6)
    top_all = most_frequent_numbers(all_draws, top_n=6)
    print(f"Top 6 nejcastejsich (1. tah): {top1}")
    print(f"Top 6 nejcastejsich (2. tah): {top2}")
    print(f"Top 6 nejcastejsich (souhrn): {top_all}")

    def print_suggestions(title: str, suggestions: list[list[int]]) -> None:
        print(f"\n--- {title} ---")
        for i, s in enumerate(suggestions, 1):
            print(f"{i}. {s}")
        stats = _pack_stats(suggestions)
        print(
            f"Pokrytí: unique={int(stats['unique_numbers'])}, "
            f"avg_overlap={stats['avg_overlap']:.2f}, "
            f"max_overlap={int(stats['max_overlap'])}"
        )

    # Návrhy
    first_suggestions = suggest_sets(first_draws, numbers=49, n_sets=NUM_SUGGESTIONS, mode=MODE, decay=DECAY, alpha=ALPHA)
    second_suggestions = suggest_sets(second_draws, numbers=49, n_sets=NUM_SUGGESTIONS, mode=MODE, decay=DECAY, alpha=ALPHA)

    # Výstup
    print_suggestions("Návrhy pro 1. tah", first_suggestions)
    print_suggestions("Návrhy pro 2. tah", second_suggestions)

    def _rows_with_metrics(label: str, suggestions: list[list[int]], draws: list[list[int]]) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        last = set(draws[-1]) if draws else set()
        for i, s in enumerate(suggestions, 1):
            score_val = _proposal_score_for_export(s, draws, MODE)
            rows.append(
                {
                    "Typ": label,
                    "Navrh": i,
                    "Cisla": " ".join(map(str, s)),
                    "Score": round(float(score_val), 2),
                    "Suma": int(sum(s)),
                    "Low31": int(sum(1 for x in s if x <= 31)),
                    "ShodyPosledniTah": int(len(last & set(s))) if last else 0,
                }
            )
        st = _pack_stats(suggestions)
        rows.append(
            {
                "Typ": label,
                "Navrh": "METRIKY",
                "Cisla": "",
                "Score": "",
                "Suma": "",
                "Low31": f"unique={int(st['unique_numbers'])}",
                "ShodyPosledniTah": f"avg_ov={st['avg_overlap']:.2f};max_ov={int(st['max_overlap'])}",
            }
        )
        return rows

    out_rows = _rows_with_metrics("1. tah", first_suggestions, first_draws) + _rows_with_metrics("2. tah", second_suggestions, second_draws)

    out_df = pd.DataFrame(out_rows)
    out_path = SCRIPT_DIR / "navrhy_sportka.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\nVýsledky uloženy do: {out_path}")
