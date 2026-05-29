Nazev: Samantha Cockpit - webove aplikace a navazani ze SSH
Priorita: 1
Stav: hotovo lokalne commitnuto
Pripomenout pri startu: ne
Datum: 2026-05-29

Co se resilo:
- Mila chtel v Cockpitu tlacitko `Webove aplikace`, aby nemusel hledat adresy existujicich webovych aplikaci.
- Bylo pridano modalni okno se seznamem aplikaci, kratkym popisem a tlacitkem `Otevrit`.
- Po prvnim testu se ukazalo, ze otevreni aplikace a zavreni jejiho okna zavre i Cockpit.
- Oprava: webove aplikace se uz neoteviraji obycejnym odkazem `target="_blank"`, ale pres rizene samostatne popup okno `SamanthaWebApp_*` pomoci `window.open(..., popup=yes, ...)`.
- Pri navazani z telefonu se znovu objevil problem s diakritikou. Pravdepodobna pricina: startovaci skripty nastavovaly `LANG`/`LC_ALL` jen pokud nebyly nastavene; existujici relace mela `LC_ALL=C.UTF-8`, takze se neprepnula na `cs_CZ.UTF-8`.

Co je hotove:
- `app/cockpit.py` obsahuje katalog webovych aplikaci a endpoint `/api/web-apps`.
- V katalogu jsou:
  - ScanDocu
  - Samantha Cockpit
  - Lekarna
  - Matysek MMTX
  - Colors and Numbers
  - Vocabulary EN
  - Family Video Organizer
- Cockpit umi servirovat lokalni prototyp Family Video Organizer pres `/local-apps/family-video-organizer/`.
- UI ma tlacitko `Webove aplikace`, zaviratelny modal, zavreni pres tlacitko, klik mimo modal a Escape.
- Mila po oprave potvrdil: "OK, ted to funguje dobre".
- Cockpit bezi na `http://127.0.0.1:8770`.
- Posledni overeny proces Cockpitu poslouchal na portu 8770 jako PID `27760`.
- `scripts/samantha_codex.sh` a `scripts/samantha_screen_entry.sh` byly upraveny tak, aby vzdy exportovaly:
  - `LANG=cs_CZ.UTF-8`
  - `LC_ALL=cs_CZ.UTF-8`
  - `LC_CTYPE=cs_CZ.UTF-8`
- Zmeny byly rozdelene do tematickych commitů:
  - `ba8782a Add web apps launcher to Cockpit`
  - `362f742 Force UTF-8 locale for Samantha screen sessions`

Overeni:
- `.venv/bin/python -m py_compile app/cockpit.py tests/test_cockpit.py` proslo.
- `.venv/bin/python -m unittest tests.test_cockpit tests.test_document_vault_tools` proslo: 55 testu OK.
- 2026-05-29 po navazani znovu proslo `.venv/bin/python -m unittest tests.test_cockpit tests.test_document_vault_tools tests.test_tomik_family_video_package`: 57 testu OK.
- `git diff --check` pro commitovane soubory proslo bez vystupu.
- `curl http://127.0.0.1:8770/api/web-apps` vratil katalog.
- `curl http://127.0.0.1:8770/local-apps/family-video-organizer/` vratil HTML FamilyVideoOrganizer.
- HTML Cockpitu obsahuje `openWebApp(app)` a `SamanthaWebApp_`, nikoliv bezne `target="_blank"` pro katalog aplikaci.

Co neni hotove:
- Commity jsou zatim jen lokalne; branch `main` je ahead oproti `origin/main`.
- Push na GitHub zatim nebyl proveden v ramci tohoto checkpointu.
- Zkratka `scripts/start_cockpit.sh` v tomto Codex sandboxu nekdy vypise `spusteno`, ale server hned zmizi; spolehlive fungovalo odpojene spusteni pres `Popen(start_new_session=True)`.

Dalsi krok:
- Pokud Mila chce publikovat posledni lokalni commity, provest push:
  - `git -C /Users/miloslavfalta/Desktop/PythonMF push origin main`
- Pokud Cockpit nebezi, spustit ho odpojene:
  - `.venv/bin/python -c "from pathlib import Path; import subprocess; root=Path('/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent'); log_dir=root/'data/private/cockpit'; log_dir.mkdir(parents=True, exist_ok=True); log=(log_dir/'server.log').open('a', encoding='utf-8'); subprocess.Popen([str(root/'.venv/bin/python'), str(root/'scripts/cockpit_server.py'), '--port', '8770'], cwd=str(root), stdout=log, stderr=subprocess.STDOUT, start_new_session=True); print('started')"`

Navrhovane dalsi kroky:
- Okamzity: podle potreby pushnout lokalni commity na GitHub.
- Rucne jeste jednou zkusit v Cockpitu `Webove aplikace -> Otevrit aplikaci -> zavrit aplikaci`, cockpit musi zustat otevreny.
- Volitelne pozdeji pridat do katalogu dalsi lokalni aplikace nebo zmenit katalog na konfigurovatelny JSON.

Zmenene nebo relevantni soubory:
- `app/cockpit.py` - commitnuto v `ba8782a`.
- `tests/test_cockpit.py` - commitnuto v `ba8782a`.
- `scripts/samantha_codex.sh` - UTF-8 oprava commitnuta v `362f742`.
- `scripts/samantha_screen_entry.sh` - UTF-8 oprava commitnuta v `362f742`.
- `data/private/cockpit/server.log` - lokalni log, necommitovat.
- FamilyVideoOrganizer soubory byly commitnute samostatne jako `d1d7275 Improve Family Video Organizer package`.
- `memory/contacts.md` zustava mimo tento checkpoint a nebyl commitnut.

Bezpecnost / neukladat:
- Necommitovat `data/private/`.
- Necommitovat `data/session_autosave/`.
- Nepouzivat `git add .`.
- Pri commitu pouzit selektivni `git add app/cockpit.py tests/test_cockpit.py`.
- Pred commitem zkontrolovat diff a neprimichat FamilyVideoOrganizer ani soukrome kontakty bez Milova vyslovneho pokynu.

Navazani z telefonu / SSH:
- Pokud SSH pripojeni otevre stejnou `screen` relaci pres prikaz `samantha`, muze se vratit do bezici terminalove relace.
- Pokud uz tato Codex session nebezi nebo se otevre novy Codex, pouzit `codex resume --last` nebo tento handoff.
- Novy Codex ma pri startu precist `AGENTS.md`, `memory/MEMORY_INDEX.md`, tento handoff a pak git status.
