# Samantha Infrastructure Operating Model

Priorita: 1
Pripomenout pri startu: ne
Datum: 2026-05-23

## Ucel

Kratky provozni rozcestnik pro bezny den, reconnect, git checkpointy, systemove
reporty a sitove incidenty. Detailni pravidla zustavaji v navazujicich
infrastructure/technical souborech.

## Bezny start prace

1. Pokud Mila chce stav, spustit `samantha_health_check(mode="quick")`.
2. Pokud chce vedet, jake reporty existuji, spustit `samantha_system_reports()`.
3. Pokud chce vedet, co Samantha umi a kde jsou rezervy, spustit
   `samantha_capability_audit()`.
4. Pred vetsimi zmenami zkontrolovat `git status --short --branch`.
5. Pri novem opakovatelnem statusu/auditu se zeptat:
   "Udelame z toho novy systemovy report?"

## Pred rizikovou nebo delsi praci

Pouzit `memory/infrastructure/git_checkpoint_protocol.md`.

Prakticky minimalni postup:

1. `git status --short --branch`
2. Rozlisit vlastni zmeny, cizi zmeny, docasne soubory a citliva data.
3. Pridavat jen konkretni cesty, nepouzivat slepe `git add .`.
4. Po hotovem mezikroku udelat maly tematicky commit a push.

## Po reconnectu nebo padu Codexu

Pouzit `memory/infrastructure/codex_reconnect_recovery.md`.

Prakticky minimalni postup:

1. Nejdriv zjistit realny stav gitu a posledni commit.
2. Precist `MEMORY_INDEX.md`, `ACTIVE_PROJECTS.md` a relevantni handoff.
3. Pokud bezi dlouhy proces, nejdriv zkontrolovat jeho vystup/log.
4. Nepokracovat podle stareho handoffu, pokud uz existuje novejsi kanonicky stav.

## Sitovy problem

Pouzit `memory/infrastructure/macos_network_recovery.md`.

Aktualni stav k 2026-05-23:

- domaci Wi-Fi/router/linka zustava pravdepodobnejsi nez Mac stack;
- do instalace nove linky 2026-06-01 resit jen zhorseni;
- po instalaci nove linky udelat 30min watchdog retest:

```bash
cd ~/Desktop/PythonMF/Samantha_Agent
.venv/bin/python scripts/network_watchdog.py --duration 1800 --interval 5
```

## Rust a metriky

Kvantitativni status neni startup povinnost. Je to ad hoc nebo checkpointovy
merak rustu.

Pouzit:

```bash
.venv/bin/python scripts/samantha_quantitative_status.py
```

Ulozit datovou vetu jen kdyz Mila vyslovne chce snapshot:

```bash
.venv/bin/python scripts/samantha_quantitative_status.py --save
```

## Bezpecnost

- Necommitovat `data/session_autosave/`, tokeny, hesla, API klice ani soukroma
  data.
- Systemove reporty maji zustat agregovane a bez soukromeho obsahu.
- Sitove a SSH dokumenty nesmi obsahovat privatni klice, auth keys ani citlivou
  konfiguraci.
