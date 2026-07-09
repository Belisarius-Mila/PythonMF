Nazev: Cockpit startup health a VoiceBridge retest
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-07-09

Co se resilo:
- Stabilita spousteni Samantha Cockpitu pres globalni hotkey a servisni restart.
- Predchozi problem: prohlizecova diagnostika umela hlasit `Load failed` a startovaci cesta byla zavisla na tezsim `/api/status`.
- Cilem bylo oddelit rychly server health od tezkych dashboard dat a overit, ze tim neni rozbity VoiceBridge.

Co je hotove:
- Commit `ec0faab Stabilize Cockpit startup checks`:
  - `open_cockpit.py` ceka dele a opakovane cte otisk kodu pred rozhodnutim o restartu.
  - `restart_cockpit.py` ma delsi cekani na ukonceni a launchd restart.
  - `cockpit_smoke_check.py` uz pri `RemoteDisconnected` vraci citelny FAIL misto tracebacku.
- Commit `49bc4e4 Add lightweight Cockpit health endpoint`:
  - Novy endpoint `/api/server/health` vraci jen rychly server stav, PID, host, port a `code_stamp`.
  - `open_cockpit.py`, `restart_cockpit.py`, `cockpit_launchd_runner.py`, frontend health a restart cekani pouzivaji lehky health endpoint.
  - Smoke check kontroluje i `/api/server/health`.
- Commit `e510994 Add Cockpit status timing`:
  - `/api/status` vraci `status_timing` s celkovym casem, casy sekci a tremi nejpomalejsimi sekcemi.
  - Mereni ukazalo, ze startup uz nema stat na tezkych dashboard vypoctech.
- Lokalni i Tailscale Cockpit byly restartovane a smoke check prosel.
- Mila udelal rucni hotkey test:
  - `Ctrl+Option+Command+C` otevrel `http://127.0.0.1:8770/?cockpit_launch=...`.
  - Diagnostika nehlasila `Load failed`.
  - Frontend JS bezel, tlacitka byla napojena, posledni chyba zadna.
  - Vsechny diagnosticke endpointy vratily OK.
- Rychlost z rucni diagnostiky:
  - `/api/server/health` cca 22 ms.
  - `/api/status` cca 2655 ms, ale OK.
  - Tezsi servisni endpointy jako kvantitativni stav a systemovy audit byly pomalejsi, ale OK.
- VoiceBridge regresni test z Cockpitu prosel:
  - hlasovy pokyn dosel do Codexu,
  - `processing_by_codex` mezistav se zapsal do Cockpitu,
  - `voice_bridge` hlasil `ok`,
  - `voice_mode` bezel a poslouchal,
  - bridge cilil na aktualni Codex relaci,
  - finalni odpoved byla zapsana zpet pres `scripts/adam_voice_reply.py --latest-command`,
  - Mac TTS se nespoustel.

Co neni hotove:
- Neni potreba dal optimalizovat `voice_bridge`; Mila spravne upozornil, ze je citlivy a dlouho ladeny.
- Neni nutne hned ladit `document_due_candidates`; kolem stovek ms nejde o stabilitni problem.
- Tezky `/api/status` zustava pomalejsi, ale po oddeleni `/api/server/health` uz neblokuje startup/hotkey.
- Recovery zaloha zatim neprobehla, protoze externi cil nebyl pri posledni kontrole pripojeny.

Dalsi krok:
- Pokud je pripojeny `/Volumes/SamanthaSecureBackup/SamanthaBackups`, spustit standardni recovery zalohu:
  `.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups --progress-every 5000`

Navrhovane dalsi kroky:
- Okamzite: zkontrolovat repo a stav backup cile, potom provest zalohu.
- Volitelne pozdeji: nechat `/api/status` timing v klidu sbirat signal a zasahovat jen pokud dashboard zacne realne vadit nebo endpointy timeoutuji.
- Do VoiceBridge nesahat bez noveho konkretniho duvodu; pred zasahem cist `handoffs/voicebridge_operational_contract_2026_06_30.md`.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `scripts/open_cockpit.py`
- `scripts/restart_cockpit.py`
- `scripts/cockpit_launchd_runner.py`
- `scripts/cockpit_smoke_check.py`
- `tests/test_cockpit.py`
- `tests/test_open_cockpit.py`
- `tests/test_restart_cockpit.py`
- `memory/handoffs/voicebridge_operational_contract_2026_06_30.md`

Overeni:
- `.venv/bin/python -m unittest tests.test_open_cockpit tests.test_restart_cockpit`
- `.venv/bin/python -m unittest tests.test_cockpit`
- `.venv/bin/python scripts/cockpit_smoke_check.py --base-url http://127.0.0.1:8770 --timeout 8`
- `.venv/bin/python scripts/cockpit_smoke_check.py --base-url http://100.89.150.6:8770 --timeout 8`
- Rucni hotkey test Mily pres `Ctrl+Option+Command+C`.
- VoiceBridge zakaznicky test pres Cockpit.

Bezpecnost / neukladat:
- Neopisovat plne soukrome hlasove historie, e-maily, dokumenty ani tajemstvi.
- Nesahat do VoiceBridge internich cest bez samostatneho duvodu a minimalniho regresniho testu.
- Nepoustet Mac TTS, pokud Cockpit audio kanal odpoved prehraje v prohlizeci nebo pokud o to Mila vyslovne nepozada.
