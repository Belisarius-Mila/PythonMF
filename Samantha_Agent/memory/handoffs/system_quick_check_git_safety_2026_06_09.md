Nazev: System quick check a git safety preflight
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-09

Co se resilo:
- Navazujici mala robustnostni davka po Cockpit smoke/backup/bridge checkpointu.
- Cilem bylo pridat rychlou predcommitovou pojistku a jeden read-only ranni/reconnect health souhrn.

Co je hotove:
- Pridan `scripts/git_safety_check.py`: kontroluje staged soubory pred commitem, blokuje `.env`, `data/private/` a `data/session_autosave/`, varuje pred velkymi a mediálními/binarnimi soubory.
- Pridan `scripts/system_quick_check.py`: read-only souhrn pro git, backup, Cockpit smoke, Adam bridge readiness a autosave health.
- Pridany testy `tests/test_safety_quick_checks.py`.

Co neni hotove:
- Skripty nejsou zatim napojene do Cockpit UI ani git hooku.
- `system_quick_check.py` pri realnem spusteni 2026-06-09 hlasil provozni varovani: `screen` nebezel a `data/session_autosave/latest_info.txt` byl stary asi 2880 minut.

Dalsi krok:
- Pred dalsim commitem lze spoustet `.venv/bin/python scripts/git_safety_check.py`.
- Pri startu/reconnectu lze spustit `.venv/bin/python scripts/system_quick_check.py`.
- Resit autosave/screen jen pokud Mila chce obnovit `samantha`/`screen` startovni vrstvu nebo pokud bude potreba hlasovy bridge stabilizovat.

Navrhovane dalsi kroky:
- Okamzite: commitnout a pushnout jako maly infrastrukturalni checkpoint.
- Volitelne: pozdeji napojit `git_safety_check.py` jako rucni krok do git checkpoint protokolu nebo do Cockpit diagnostiky; git hook zatim nezavadet automaticky.

Zmenene nebo relevantni soubory:
- `scripts/git_safety_check.py`
- `scripts/system_quick_check.py`
- `tests/test_safety_quick_checks.py`

Bezpecnost / neukladat:
- Skripty jsou read-only v beznem rezimu.
- `git_safety_check.py` jen cte staged git obsah a vraci varovani/blok.
- Handoff neobsahuje tajemstvi, cele e-maily ani soukroma data.
