Nazev: Email activity state - tydenni pripominka triage a archivace hotova
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Mila chtel, aby Samantha pri startu pripomnela, pokud dele nez 7 dni
  neprobehla e-mailova triage nebo zaloha/archivace dulezitych e-mailu.
- Predtim bylo pravidlo zapsane jen do memory projektu; nyni ma i lokalni
  provozni stav.

Co je hotove:
- Pridan `app/email/activity_state.py`.
- Pridan lokalni stav `data/email/activity_state.json`.
- Vychozi hodnoty jsou:
  - `last_triage_at`: `2026-05-19`
  - `last_archive_at`: `2026-05-19`
- `load_memory()` v `app/samantha_agent.py` pridava startovni sekci
  `EMAIL UDRZBA`.
- Pokud je triage nebo archivace starsi nez 7 dni, Samantha pri startu nabidne
  spusteni triage nebo vyber zprav k zaloze.
- Uspesny `run_email_triage_session` aktualizuje `last_triage_at`.
- Pro budoucí EmailArchiveVault je pripraveno `record_email_archive_completed`.

Co neni hotove:
- `last_archive_at` se zatim neaktualizuje automaticky, protoze kompletni
  `EmailArchiveVault` jeste neni implementovany.
- Zatim neni Samantha tool pro rucni zmenu activity state; stav se meni pres
  service funkce.

Bezpecnost:
- Activity state neobsahuje UID, predmety, tela e-mailu, plne URL, adresy,
  prilohy, tokeny ani hesla.
- Startovni pripominka sama necte e-maily, nestahuje prilohy, neotevira odkazy
  ani nic neuklada.
- `data/email/activity_state.json` je lokalni provozni data soubor, ne memory.

Zmenene nebo relevantni soubory:
- `app/email/activity_state.py`
- `app/email/triage_tools.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `tests/test_email_activity_state.py`
- `tests/test_email_triage_tools.py`
- `data/email/activity_state.json`

Overeni:
- `.venv/bin/python -m compileall app app/samantha_agent.py`
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: 85 testu OK.
