Nazev: Cockpit autosave cleanup
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-30

Co se resilo:
- `data/session_autosave/` narostlo na cca 16 GB kvuli opakovanym timestampovanym kopiam dlouhych Codex session.
- Cil byl zavest bezpecnou retenční proceduru a tlacitko do servisni casti Cockpitu.

Co je hotove:
- Pridan skript `scripts/cleanup_session_autosave.py`.
- Vychozi dry-run nic nemaze a jen pocita nazvy/velikosti souboru.
- Ostre mazani vyzaduje `--apply --confirm 'SMAZAT STARE AUTOSAVE'`.
- Retence ponechava vsechny timestampovane snapshoty za posledni 3 dny a jako pojistku nejnovejsich 12 casovych snapshotu.
- Skript nikdy nemaze `latest_session.jsonl`, `latest_session.txt`, `latest_info.txt` ani netypicke soubory.
- Cockpit ma novy endpoint `POST /api/session-autosave/cleanup`.
- Cockpit `Servis` ma tlacitko `Autosave uklid`, panel `Autosave uklid`, dry-run tlacitko a potvrzene tlacitko `Vycistit stare autosave`.
- Backend i pri UI potvrzeni vyzaduje presnou potvrzovaci frazi `SMAZAT STARE AUTOSAVE`.
- Dokumentace je doplnena v `memory/technical/session_recovery_rules.md`.

Co neni hotove:
- Ostry cleanup realneho `data/session_autosave/` zatim nebyl spusten.
- Realny adresar stale zabira cca 16 GB.

Dalsi krok:
- V Cockpitu otevrit `Servis -> Autosave uklid`, zkontrolovat dry-run a po Milove potvrzeni kliknout `Vycistit stare autosave`.

Navrhovane dalsi kroky:
- Okamzity: uvolnit cca 14 GB pres potvrzene tlacitko nebo CLI.
- Volitelne: pozdeji zvazit automaticky nenasilny reminder, kdyz `data/session_autosave/` prekroci napr. 5 GB.

Zmenene nebo relevantni soubory:
- `scripts/cleanup_session_autosave.py`
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `tests/test_safety_quick_checks.py`
- `memory/technical/session_recovery_rules.md`

Overeni:
- `.venv/bin/python -m unittest tests.test_cockpit`
- `.venv/bin/python -m unittest tests.test_cockpit.CockpitTests.test_cockpit_post_action_registry_matches_do_post_routes tests.test_cockpit.CockpitTests.test_cockpit_post_action_registry_has_required_metadata tests.test_cockpit.CockpitTests.test_frontend_literal_routes_exist_in_backend tests.test_cockpit.CockpitTests.test_cockpit_html_contains_document_work_controls tests.test_cockpit.CockpitTests.test_session_autosave_cleanup_action_requires_confirmation_to_delete tests.test_cockpit.CockpitTests.test_session_autosave_cleanup_action_deletes_old_snapshots_after_confirmation tests.test_safety_quick_checks`
- `.venv/bin/python -m py_compile app/cockpit.py scripts/cleanup_session_autosave.py`
- HTTP dry-run po restartu Cockpitu: `POST /api/session-autosave/cleanup` vratil `delete_count` 2082 a odhad uvolneni 14.23 GiB.

Bezpecnost / neukladat:
- Autosave logy mohou obsahovat citliva data; skript ani Cockpit endpoint necistou jejich obsah.
- Necommitovat `data/session_autosave/`.
- Nespoustet ostry cleanup bez potvrzeni, protoze jde o mazani lokalnich nouzovych snapshotu.

## Provozni oprava 2026-07-10

- Puvodnich cca 16 GiB uz v adresari neni; read-only kontrola namerila cca
  1,29 GiB. Dry-run spravne vratil nula kandidatu, protoze vsechny zbyvajici
  snapshoty byly mladsi nez tri dny.
- Nalezena skutecna pricina noveho rychleho rustu: hlavni `samantha_codex` a
  spravovana `samantha_janicka` spoustely kazda vlastni globalni watcher a oba
  kopirovaly posledni Codex session.
- Managed Adam/Janička relace nyni dostavaji `SAMANTHA_AUTOSAVE_WATCH=0`.
  `autosave_codex_session.sh --watch` navic pouziva singleton lock, takze druhy
  watcher se sam odmitne spustit.
- Ukonceni watcheru prerusi i jeho cekajici `sleep`, uklidi lock a skutecne
  skonci. Tim je opravena pricina osireleho watcheru po ukonceni Janičky.
- `autosave_status.py`, Recovery centrum i Autosave uklid ukazuji watcher count
  a vice nez jeden watcher je varovani.
- Zivy nadbytecny watcher patrici Janičce byl setrne ukoncen; Janička light
  zustala bez preruseni bezet. Zivy stav je jeden watcher a dry-run nula souboru
  ke smazani. Zadny autosave snapshot se pri oprave nemazal.
- Backend autosave logika je vyjmuta z monolitu do `app/autosave_service.py`.

Dalsi krok: pouze sledovat rust. Cleanup znovu nabidne kandidaty az po prekroceni
tridenni retence; ostry cleanup zustava potvrzovana mazaci akce.

Implementace je v commitu `67ba77e`; GitHub Actions Cockpit Quality Gate beh
cislo 11 skoncil uspesne:
`https://github.com/Belisarius-Mila/PythonMF/actions/runs/29119991977`.
