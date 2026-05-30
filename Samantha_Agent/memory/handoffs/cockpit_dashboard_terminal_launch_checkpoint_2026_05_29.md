Nazev: Samantha Cockpit - dashboard a spousteni Samantha/Codex z UI
Priorita: 1
Stav: hotovo, Cockpit commity uz jsou na origin/main
Pripomenout pri startu: ne
Datum: 2026-05-29

Aktualizace 2026-05-29 pozdeji:
- Puvodni stav `branch main ahead 6` je prekryty.
- Podle `git log --oneline --decorate -12` jsou Cockpit commity uz na
  `origin/main`.
- Aktualni `HEAD` i `origin/main` jsou
  `e123d52 Add emotion management tool notes`.
- Dalsi cockpit krok uz neni push sesti commitu; podle potreby rucne retestovat
  tlacitka `Samantha chat` / `Codex CLI`, nebo pokracovat v command inboxu.

Co se resilo:
- Navazalo se na Cockpit po checkpointu `cockpit_web_apps_checkpoint_2026_05_29.md`.
- Míla chtel overit, ze katalog webovych aplikaci uz ma ScanDocu a otevirani aplikaci.
- Potom se pridal horní dashboard `Dnes / Stav / Akce`.
- Nakonec Míla schvalil implementaci tlacitek `Samantha chat` a `Codex CLI`.

Co je hotove:
- Cockpit ma dashboard `Dnes / Stav / Akce`.
- Dashboard ukazuje pocty novych PDF, dokumentu k revizi a problemu.
- Dashboard ukazuje stav ScanDocu, zalohy a gitu.
- `/api/status` vraci read-only `git` souhrn.
- Cockpit ma tlacitka `Samantha chat` a `Codex CLI` v horni liste i v dashboardu.
- Endpoint `/api/samantha/open` otevre macOS Terminal v projektu a spusti `source ~/.zshrc; samantha`.
- Endpoint `/api/codex/open` otevre macOS Terminal v projektu a spusti `source ~/.zshrc; codex resume --last || codex`.
- Implementace je allowlistovana: web neposila libovolny shell prikaz, jen vola pevne backend endpointy.
- Cockpit byl restartovan a bezi na `http://127.0.0.1:8770`.

Commity:
- `d1d7275 Improve Family Video Organizer package`
- `ba8782a Add web apps launcher to Cockpit`
- `362f742 Force UTF-8 locale for Samantha screen sessions`
- `6ca15e7 Record Cockpit web apps checkpoint`
- `e12c4c8 Add Cockpit today dashboard`
- `b9f337c Add Cockpit launch buttons for Samantha and Codex`

Overeni:
- `.venv/bin/python -m unittest tests.test_cockpit tests.test_document_vault_tools` proslo: 55 testu OK.
- `.venv/bin/python -m py_compile app/cockpit.py tests/test_cockpit.py` proslo.
- `git diff --check -- Samantha_Agent/app/cockpit.py Samantha_Agent/tests/test_cockpit.py` proslo bez vystupu.
- Cockpit proces po poslednim restartu poslouchal na portu 8770 jako PID `30834`.

Co neni hotove:
- Puvodni Cockpit push uz neni aktualni problem; Cockpit commity jsou na
  `origin/main`.
- Aktualni `HEAD` i `origin/main` jsou
  `e123d52 Add emotion management tool notes`.
- Externi zaloha Samanthy je stale stara: posledni uspesna zaloha je z 2026-05-19.

Dalsi krok:
- Pri navazani nejdrive spustit:
  - `.venv/bin/python scripts/backup_status.py`
  - `git -C /Users/miloslavfalta/Desktop/PythonMF status --short --branch`
- Podle potreby rucne retestovat `Samantha chat` a `Codex CLI`.
- Pokud se ma navazovat na hlasove/textove ovladani, pokracovat read-only
  command inboxem, ne rizikovymi akcemi bez potvrzeni.

Navrhovane dalsi kroky:
- Okamzity: rucne kliknout v Cockpitu na `Samantha chat` a `Codex CLI`, jestli Terminal otevre spravnou relaci.
- Navazujici: pokud Míla chce ovladani z iPhonu, zacit textovym read-only command inboxem.
- Volitelne pozdeji pridat do dashboardu jasnejsi tlacitko `Pushnout commity` az po navrhu bezpecne potvrzovaci brany.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `scripts/samantha_codex.sh`
- `scripts/samantha_screen_entry.sh`
- `memory/handoffs/cockpit_web_apps_checkpoint_2026_05_29.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Necommitovat `data/private/`.
- Necommitovat `data/session_autosave/`.
- Nepouzivat `git add .`.
- Nepopisovat obsah `memory/contacts.md` bez vyslovneho souhlasu.
- Tlacitka Samantha/Codex jsou urcena jen pro lokalni Cockpit na `127.0.0.1`; neni to obecny web terminal.
