# Samantha Agent

Project workspace for Samantha Agent.

## Lokalni agent

Zakladni CLI vstup bezi nad OpenAI Agents SDK:

```bash
.venv/bin/python -m app.samantha_agent "Na cem mame pokracovat?"
```

Agent pri startu nacita jen kompakni kontext z `memory/samantha_core.md`,
`memory/ACTIVE_PROJECTS.md`, `memory/MEMORY_INDEX.md`, aktivnich pripominek a
e-mailove udrzby. Konkretni kontext dohledava pres tool `search_memory`, ktery
prohledava markdown soubory v `memory/`. Je to prvni lokalni RAG-like vrstva bez
vektorove databaze.

Diagnostiku pameti umi agent pres tool `memory_status`: pocet markdown souboru,
velikost startup/plneho kontextu, priority 1 a `[PRIPOMENOUT]` polozky.
Vyhledavani pouziva jednoduchy in-memory index markdown snippetů. Index se v
behu procesu znovu pouzije, dokud se nezmeni seznam, velikost nebo `mtime` `.md`
souboru; potom se automaticky sestavi znovu.

Testy:

```bash
.venv/bin/python -m unittest discover -s tests
```

## Denni rutina ve 3:00

Bezpecny vstupni bod pro denni udrzbu je:

```bash
.venv/bin/python scripts/daily_3am.py
```

Rutina loguje do `logs/daily_3am.log`, pouziva lock proti soubehu a denni stav
v `data/daily_3am/`, aby bylo opakovane spusteni idempotentni. Návod pro macOS
`launchd`, `pmset wakeorpoweron` a GitHub Actions je v
[`docs/daily_3am.md`](docs/daily_3am.md).
