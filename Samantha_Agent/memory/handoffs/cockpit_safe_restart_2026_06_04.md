Nazev: Cockpit bezpecny restart
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-06-04

Co se resilo:
- Mila po potvrzeni bloku `Co ted delat` chtel pokracovat poslednim bodem
  ulozeneho planu: bezpecny restart Cockpitu.
- Cilem bylo pridat potvrzovanou akci, ktera neukonci libovolny proces, ale jen
  overeny lokalni `cockpit_server.py` na portu `8770`.

Co je hotove:
- Pridan script `scripts/restart_cockpit.py`.
- Pridan backend helper `start_cockpit_restart_action`.
- Pridan endpoint `POST /api/cockpit/restart`.
- V UI v kartě `Akce` je nove tlacitko `Restart Cockpitu`.
- Frontend pred restartem ukaze potvrzeni pres `window.confirm`.
- Backend restart spusti samostatny worker, ktery:
  - znovu overi cilovy PID pres `ps`,
  - povoli jen proces obsahujici `scripts/cockpit_server.py`,
  - posle mu `SIGTERM`,
  - pocka na uvolneni portu,
  - znovu spusti Cockpit pres `scripts/open_cockpit.py --no-open`.
- Restart loguje do `data/private/cockpit/restart.log`.

Co neni hotove:
- Automaticke otevreni prohlizece pres macOS `open` v teto relaci selhalo kvuli
  LaunchServices, proto byl live retest proveden pres API.
- Nic zasadniho k bezpecnemu restartu Cockpitu.

Dalsi krok:
- Bezpecny restart je potvrzeny i rucnim UI retestem.
- Dalsi rozhodnuti: pokracovat drobnym UI uklidem Cockpitu, nebo se vratit k
  obecnemu zpracovani dokumentu / document vaultu.

Navrhovane dalsi kroky:
- Okamzite: zadny dalsi restart krok neni nutny.
- Navazujici: rozhodnout, zda dalsi cockpit prace bude drobne UI cisteni, nebo
  presun na obecne zpracovani dokumentu / dokumentovy vault.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `scripts/restart_cockpit.py`
- `tests/test_cockpit.py`
- `memory/handoffs/cockpit_safe_restart_2026_06_04.md`
- `memory/handoffs/cockpit_development_priorities_2026_06_03.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Overeni:
- `.venv/bin/python -m py_compile app/cockpit.py scripts/restart_cockpit.py`
- `.venv/bin/python -m unittest tests.test_cockpit tests.test_quick_notes`
  proslo: 54 testu OK.
- `node --check /private/tmp/cockpit_restart_check.js` proslo.
- Live endpoint `POST /api/cockpit/restart` vratil `restart_started` pro PID
  `31544`.
- Worker ukoncil overeny Cockpit PID `31544` a spustil novy proces PID `31583`.
- Live `/api/status` po restartu odpovida.
- Mila potvrdil rucni UI retest: restart Cockpitu probehl.

Bezpecnost / neukladat:
- Neukladat obsah dokumentu, e-mailu, autosave logu, tokeny ani klice.
- Restart ma zustat potvrzovany a smi ukoncovat jen overeny `cockpit_server.py`;
  pokud PID neodpovida, musi akce skončit jako `unsafe_target`.
