Nazev: Full-access destruktivni prikazovy guard
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-29

Co se resilo:
- Po vypnuti Codex sandboxu bylo potreba pridat technickou brzdu proti omylem spustenemu mazani a destruktivnim git prikazum.
- Textove pravidlo `global_safety_brake.md` zustava hlavni procesni brzda, ale ve full-access rezimu je doplneno o shell wrappery.

Co je hotove:
- Pridan `scripts/destructive_command_guard.py`, ktery klasifikuje rizikove prikazy a vyzaduje presnou globalni potvrzovaci vetu.
- Pridany wrappery v `scripts/safe_bin/` pro `rm`, `git`, `find` a `mv`.
- `scripts/samantha_screen_entry.sh` pridava `scripts/safe_bin/` na zacatek `PATH`, takze nove relace spustene pres `samantha` pouziji guard automaticky.
- Guard blokuje zejmena:
  - mazani v `PythonMF`,
  - `rm -rf` a hromadne mazani,
  - `find ... -delete` a `find ... -exec rm`,
  - `git reset --hard`, `git clean`, force push a mazani git vetvi/tagu,
  - hromadne presuny a presuny private/memory/autosave dat.
- `git -C ... reset --hard` je pokryty specialne, aby globalni git volby neobesly parser.

Co neni hotove:
- Guard neumi zachytit vedome obejiti absolutni cestou typu `/bin/rm` nebo `/usr/bin/git`; to zustava pod pravidlem globalni brzdy a lidskym posouzenim.
- Aktualne bezici Codex relace nemusi mit novy `PATH`; plne automaticke zapojeni plati po novem startu pres `samantha`.
- Guard neresi destruktivni akce v libovolnem Python/shell skriptu, pokud skript primo vola absolutni binarky nebo maze pres Python API.

Dalsi krok:
- Commit + push hotove ochrany.
- Po novem startu pres `samantha` overit, ze `which rm`, `which git`, `which find`, `which mv` ukazuji do `scripts/safe_bin/`.

Navrhovane dalsi kroky:
- Okamzite: po pushi spustit `scripts/work_context_guard.py`.
- Volitelne pozdeji: doplnit safe wrappers i pro dalsi rizikove prikazy, pokud se objevi v realnem provozu.

Zmenene nebo relevantni soubory:
- `scripts/destructive_command_guard.py`
- `scripts/safe_bin/rm`
- `scripts/safe_bin/git`
- `scripts/safe_bin/find`
- `scripts/safe_bin/mv`
- `scripts/samantha_screen_entry.sh`
- `memory/technical/global_safety_brake.md`
- `tests/test_safety_quick_checks.py`

Overeni:
- `.venv/bin/python -m unittest tests.test_safety_quick_checks`
- `.venv/bin/python -m unittest tests.test_safety_quick_checks tests.test_capability_registry`
- `.venv/bin/python -m py_compile scripts/destructive_command_guard.py`
- Smoke test: wrapper blokuje `rm` v `PythonMF`, `find ... -delete`, `git reset --hard` i `git -C ... reset --hard`; `git status` prochazi.

Bezpecnost / neukladat:
- Potvrzovaci veta neni tajemstvi, ale zamerna pauza pred rizikovym krokem.
- Handoff neobsahuje soukroma data ani tajemstvi.
