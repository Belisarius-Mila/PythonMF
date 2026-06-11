Nazev: Cockpit UI cleanup experiment checkpoint
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-06-11

Co se resilo:
- Mila chtel po padu SSH pokracovat na auditu obsahu oken Cockpitu a potom opatrne vyzkouset uklid UI.
- Nejdriv vznikl read-only audit obsahu Cockpitu:
  `memory/reports/cockpit_ui_content_audit_2026_06_11.md`.
- Po Milove otazce, zda "presunout" nebude znamenat, ze veci nebude videt, byl zvolen mirny experiment:
  veci neschovat hluboko, ale dat je za jasne rozbalovaci dvere.

Co je hotove:
- Commit `157425e Add Cockpit UI content audit`:
  - pridal audit obsahu Cockpitu,
  - zaindexoval report v `memory/MEMORY_INDEX.md`.
- Commit `ed2f520 Try Cockpit UI cleanup`:
  - hlavni akce zustaly na ocich,
  - servisni akce jsou pod `Servis`,
  - technicky health panel je pod `Technicky stav Cockpitu`,
  - detaily hlasoveho bridge jsou pod `Pokrocile`,
  - detailni dokumentove karty jsou pod `Dokumenty`,
  - raw prehledy jsou pod `Servisni prehledy`,
  - nazvy jsou lidstejsi: `E-maily`, `Pripomenuti`, `Systemovy souhrn`, `Kontrola nesrovnalosti`, `Souvisejici dokumenty`, `Doplnit udaje`.
- Cockpit byl bezpecne restartovan pres `/api/cockpit/restart`.
- Overeni:
  - `.venv/bin/python -m py_compile app/cockpit.py` OK.
  - `.venv/bin/python -m unittest tests.test_cockpit` OK, 112 testu.
  - `.venv/bin/python scripts/cockpit_smoke_check.py` OK po spusteni mimo sandbox; sandboxova verze hlasila `Operation not permitted`.
  - HTML lokalniho Cockpitu obsahovalo nove sekce `Servis`, `Dokumenty`, `Servisni prehledy`, `E-maily`, `Pripomenuti`, `Kontrola nesrovnalosti`.

Co neni hotove:
- Mila jeste rucne neposoudil, jestli nova podoba Cockpitu opravdu pomaha.
- UI cleanup neni pushnuty na GitHub; vetev `main` je lokalne ahead o 2 commity pred ulozenim tohoto handoffu.
- Nebyla delana vizualni screenshot kontrola v prohlizeci, jen HTML/API/testy/smoke.

Dalsi krok:
- Otevrit Cockpit na `http://127.0.0.1:8770` a rucne projit hlavni obrazovku:
  - je porad jasne, kde jsou dokumenty, e-maily, pripomenuti, knihovna a Janička?
  - neni `Servis` moc schovany?
  - dava smysl, ze `Dokumenty` se rozbali automaticky jen kdyz neco hlasi?
  - najde Mila rychle diagnostiku/restart/terminal, kdyz je potrebuje?

Navrhovane dalsi kroky:
- Okamzite: rucni UI retest Cockpitu.
- Pokud UI sedi: pripadne pushnout commity `157425e` a `ed2f520`.
- Pokud UI skoro sedi: doladit nazvy a rozbaleni sekci, neprekopavat backend.
- Pokud UI nesedi: vratit experiment samostatne revertovanim commitu `ed2f520`; audit `157425e` muze zustat.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/reports/cockpit_ui_content_audit_2026_06_11.md`
- `memory/MEMORY_INDEX.md`
- `memory/ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Handoff neobsahuje hesla, tokeny, API klice, cele e-maily ani citliva rodinna data.
- UI cleanup nemel menit backendove akce ani potvrzovaci brany.
- Pro vraceni UI zmen nepouzivat `git reset --hard`; bezpecnejsi je samostatny revert commitu `ed2f520`.
