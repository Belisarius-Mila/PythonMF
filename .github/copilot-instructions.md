# AI Coding Instructions for PythonMF Sportka Project

## Project Overview
Educational Czech lottery number suggestion system with three generation modes exploring probability heuristics. Multiple evolution versions study different algorithmic approaches to avoiding human biases in number selection.

**Key Files:**
- [navrh_sportka_alchymie_v3.py](../navrh_sportka_alchymie_v3.py) – Primary production script with three generation modes
- [navrh_sportka_updated.py](../navrh_sportka_updated.py) – Earlier version with `random` and `weighted` modes
- [stahni_sportku_2025.py](../stahni_sportku_2025.py) – Web scraper for historical draw data

## Architecture Patterns

### Data Input Duality
Scripts support **two CSV schema formats** automatically detected in `load_draws()`:
- **Schema A (Modern)**: Separate numeric columns `Tah1_1…Tah1_6`, `Tah2_1…Tah2_6`, `Datum` (ISO format)
- **Schema B (Legacy)**: Text columns `1. tah`, `2. tah`, `Datum` with fuzzy column name matching using regex

Always preserve backward compatibility when modifying parsers.

### Generation Modes (Environment-Driven)
Set via `SPORTKA_MODE` environment variable:

| Mode | Strategy | Use Case |
|------|----------|----------|
| `random` (v2 default) | Heuristic scoring against human patterns (birthdays 1–31, consecutive runs, bucket concentration) | Reduces ticket splitting |
| `weighted` | Bayesian recency decay (`DECAY=0.985`) + Laplace smoothing (`ALPHA=1.0`) | Experimental frequency analysis |
| `alchemy` (v3 default) | Hard constraint (exactly 3 from 1–31, 3 from 32–49) + exponential recent draw penalties + unique combo preference | Novel aesthetic approach |

**Critical Constraint in Alchemy**: Rejects any combo appearing in historical data (`past_combos` set). This is intentional design, not a bug.

### Scoring Hierarchies
All scoring functions return **lower-is-better** floats:

1. **Hard filters** (return early with penalty > 1e8): Invalid draw structure, mode-specific constraints
2. **Major penalties** (1e5–5e5 range): Decade distribution, consecutive runs, recent draw overlap
3. **Minor penalties** (1–1000 range): Round numbers, frequency tie-breaks

Alchemy mode uses exponential penalties for recent overlap: `1e5 * 10^(overlap_count)` to strongly discourage repetition.

## Critical Developer Workflows

### Run Main Script
```bash
python navrh_sportka_alchymie_v3.py [csv_path]
# Outputs CSV to navrhy_sportka.csv in script directory
```

### Benchmark Performance
```bash
# Synthetic data (1 call = 20 generate operations by default):
python navrh_sportka_alchymie_v3.py --benchmark --benchmark-rows 200 --benchmark-calls 5

# Real data from CSV:
python navrh_sportka_alchymie_v3.py sportka_2025.csv --benchmark-real --benchmark-calls 10
```

### Environment Configuration
```bash
# Mode selection
export SPORTKA_MODE=alchemy  # or: random, weighted

# Algorithm tuning
export SPORTKA_DECAY=0.985           # Recency weight (0.97–0.995)
export SPORTKA_ALPHA=1.0             # Laplace smoothing
export SPORTKA_N=5                   # Number of suggestions
export SPORTKA_SEED=42               # Reproducibility (None = random)
export SPORTKA_REPEAT_PENALTY=4.0    # Alchemy mode: cross-suggestion diversity

# Heuristic thresholds
export SPORTKA_CANDIDATES=50000      # Candidate pool size
export SPORTKA_HEAP_KEEP=1500        # Best candidates retained
export SPORTKA_MAX_LOW31=3           # Max numbers from 1–31
export SPORTKA_MIN_DECADES=3         # Min distinct "decade buckets" (1–9, 10–19, …)
export SPORTKA_OVERLAP_WINDOW=3      # Recent draws to penalize
export SPORTKA_OVERLAP_THRESHOLD=4   # Matches triggering penalty
```

## Project-Specific Patterns

### Path Resolution Strategy
Data files searched in order: script directory → Desktop → legacy filename variants. Supports `.csv` and `.xlsx`. This pattern in `find_data_path()` enables flexibility without external config files.

### Heap-Based Top-K Selection
All modes use max-heap to track `HEAP_KEEP` best candidates incrementally:
```python
item = (-score, cand)  # Negate score for max-heap semantics
if len(heap) < HEAP_KEEP:
    heapq.heappush(heap, item)
else:
    if item[0] > heap[0][0]:  # Better (less negative) score
        heapq.heapreplace(heap, item)
```
This avoids sorting full candidate pool; critical for performance at `NUM_CANDIDATES=50000`.

### Diversity Enforcement
All modes apply `_is_diverse(cand, suggestions)`: reject if overlap ≥ 4 numbers with previous suggestions. This ensures variety in output set.

### Bucket Partitioning
Decade bucketing divides 1–49 into 5 ranges: `(n-1)//10` produces buckets 0–4. Used to enforce distribution heuristic.

## Integration Points

### Data Source
Web scraper [stahni_sportku_2025.py](../stahni_sportku_2025.py) parses Czech Sportka website monthly pages into CSV. Output schema determines which `load_draws()` path is taken.

### Output Format
Results written to `navrhy_sportka.csv` with columns: `Typ` (draw type), `Navrh` (suggestion #), `Cisla` (space-separated numbers).

## Testing & Validation Notes

- No formal test suite; validate via benchmarks (performance regression) and CSV output inspection (heuristic reasonableness)
- Benchmark variance depends on `NUM_CANDIDATES` and data size; control with `--benchmark-calls` to reduce noise
- For new modes: verify `_valid_draw()` and `_passes_rules()` constraints prevent malformed output
- Alchemy mode is memory-heavy at large `NUM_CANDIDATES` (constructs `past_combos` frozenset); monitor with real data

## Language & Conventions

- **Czech naming**: Variable names, comments, docstrings in Czech; keep unchanged to match domain
- **Type hints**: Modern (PEP 604 `|` unions, list generics); use throughout
- **Comments**: Explain "why," not "what"; heuristic rationale already in docstrings
