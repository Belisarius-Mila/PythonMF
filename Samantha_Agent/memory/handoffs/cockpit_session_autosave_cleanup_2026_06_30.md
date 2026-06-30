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
