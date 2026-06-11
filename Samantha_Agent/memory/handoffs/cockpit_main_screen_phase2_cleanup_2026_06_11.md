Nazev: Cockpit hlavni obrazovka faze 2 cleanup
Priorita: 1
Stav: hotovo / rucni retest dobry
Pripomenout pri startu: ne
Datum: 2026-06-11

Co se resilo:
- Po fazi 1 UI cleanupu a fazi 2 read-only auditu Mila schvalil zkusit realizaci navrhu pro hlavni obrazovku Cockpitu.
- Cil byl zmensit ranni hluk: `Co ted delat` ma byt pred hlasem, hlas nema zabirat misto pokud neni aktivni, servis ma mit jedno jasne misto a karta `Stav` ma byt lidstejsi.

Co je hotove:
- V `app/cockpit.py`:
  - horni lista ma nove tlacitko `Servis`, ktere otevira servisni sekci,
  - karta `Akce` je prejmenovana na `Rychle akce`,
  - `Co ted delat` je presunute nad hlasovy panel,
  - `Hlasovy pokyn` je schovany pod rozbalovaci sekci `Hlas`,
  - sekce `Hlas` se automaticky rozbali pri aktivnim hlasovem rezimu, cekajicim pokynu nebo varovani bridge,
  - karta `Stav` ma viditelnejsi lidsky radek `Dokumenty`,
  - servisni detaily `ScanDocu`, `Projekty`, `Kontrola`, `Rychle poznamky` a `Git` jsou pod `Dalsi stav`,
  - servisni akce, technicky stav Cockpitu a servisni prehledy jsou soustredene pod jeden blok `Servis`.
- V `tests/test_cockpit.py` jsou upravena HTML ocekavani pro nove prvky.
- Mila po rucnim retestu napsal, ze Cockpit vypada dobre.

Overeni:
- `.venv/bin/python -m py_compile app/cockpit.py` OK.
- `.venv/bin/python -m unittest tests.test_cockpit` OK, 112 testu.
- Lokalni Cockpit byl restartovan pres `/api/cockpit/restart`.
- Tailscale Cockpit pro iPhone `http://100.89.150.6:8770` byl restartovan pres `/api/cockpit/restart`.
- HTML lokalni i Tailscale instance obsahuje:
  - `Rychle akce`,
  - `serviceBtn`,
  - `servicePanel`,
  - `voiceCommandDetails`,
  - `Co ted delat` pred `Hlasovy pokyn`.
- Smoke check lokalne i pres Tailscale prosel po spusteni mimo sandbox:
  - `/`
  - `/api/status`
  - `/api/recovery/status`

Co neni hotove:
- Zmena zatim ceka na push v ramci navazujiciho checkpointu.
- Nebyla delana screenshot kontrola, jen HTML/API/testy/smoke.
- Pri zpracovani 1 e-mailu Mila narazil na problem; to brat jako samostatne navazani k e-mailovemu workflow, ne jako blokaci UI cleanupu.

Dalsi krok:
- Navazat na konkretni problem po zpracovani 1 e-mailu: nejdriv read-only zjistit, co se stalo v Cockpitu / Email Processing, a teprve potom rozhodnout opravu.

Navrhovane dalsi kroky:
- Ponechat fazi 2 UI cleanupu jako aktualni stav.
- Pushnout lokalni checkpoint commity na GitHub.
- Pri e-mailovem navazani zacit read-only: stav rozhodnuti, work queue, kandidati a cache, bez mazani nebo provider akcí.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/reports/cockpit_main_screen_daily_audit_2026_06_11.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Handoff neobsahuje hesla, tokeny, cele e-maily ani citliva rodinna data.
- Zmena nema menit backendove akce ani potvrzovaci brany.
