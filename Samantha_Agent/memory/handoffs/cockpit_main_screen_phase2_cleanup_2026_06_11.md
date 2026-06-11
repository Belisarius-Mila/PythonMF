Nazev: Cockpit hlavni obrazovka faze 2 cleanup
Priorita: 1
Stav: ceka na rucni retest
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
- Mila jeste neretestoval novou podobu na iPhonu a Macu rucne.
- Zmena neni pushnuta na GitHub.
- Nebyla delana screenshot kontrola, jen HTML/API/testy/smoke.

Dalsi krok:
- Rucne otevrit Cockpit na iPhonu pres `http://100.89.150.6:8770/?v=20260611-phase2` a zkontrolovat:
  - jestli je `Co ted delat` opravdu hned po rannim stavu,
  - jestli sbaleny `Hlas` nechybi pri bezne praci,
  - jestli je `Servis` snadno najitelny,
  - jestli karta `Stav` neni moc osekana.

Navrhovane dalsi kroky:
- Pokud UI sedi: ponechat fazi 2 a pripadne pozdeji pushnout checkpoint commity.
- Pokud UI skoro sedi: doladit nazvy nebo rozbaleni bez backend zmen.
- Pokud UI nesedi: vratit samostatne tento faze 2 commit; faze 1 muze zustat.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/reports/cockpit_main_screen_daily_audit_2026_06_11.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Handoff neobsahuje hesla, tokeny, cele e-maily ani citliva rodinna data.
- Zmena nema menit backendove akce ani potvrzovaci brany.
