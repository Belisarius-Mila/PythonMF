Nazev: Cockpit hotkey fallback port po zaseknutem 8770
Priorita: 1
Stav: ceka na retest po restartu Macu
Pripomenout pri startu: ne
Datum: 2026-07-07

Co se resilo:
Mila hlasil, ze globalni zkratka `Ctrl+Option+Command+C` prestala otevirat Cockpit.
Log hotkey agenta ukazal, ze zkratka se ve skutecnosti zachytavala, ale start Cockpitu narazil na mrtve obsazeny port `8770`.

Co je hotove:
- Overeno, ze hotkey agent bezi a loguje stisky zkratky.
- Diagnostikovano, ze `127.0.0.1:8770` a Tailscale `8770` drzely stare Python Cockpit procesy, ale HTTP neodpovidalo.
- `scripts/open_cockpit.py` dostal fallback: pokud je vychozi lokalni `8770` obsazeny a neodpovida, spusti nouzovy Cockpit na dalsim volnem portu, typicky `8771`.
- `scripts/cockpit_launchd_runner.py` ma presnejsi detekci obsazeneho portu pres bind test, aby pri mrtvem portu nevytvarel dalsi neuspesne serverove procesy.
- Pridane testy `tests/test_open_cockpit.py`.
- Commit a push: `afa4f39 Add Cockpit fallback port startup`.
- Pred restartem Macu bezela nouzova instance na `http://127.0.0.1:8771`.

Co neni hotove:
- Definitivne potvrdit po restartu Macu, ze zaseknute procesy zmizely a standardni `http://127.0.0.1:8770` opet odpovida.
- Rucne zkusit `Ctrl+Option+Command+C` po restartu.

Dalsi krok:
Po restartu Macu spustit/zkusit hotkey `Ctrl+Option+Command+C` a overit, zda Cockpit nabehl na standardni `http://127.0.0.1:8770`.

Navrhovane dalsi kroky:
- Pokud `8770` po restartu funguje, neni potreba nic dalsiho; fallback zustava jako pojistka.
- Pokud se znovu otevre `8771`, zkontrolovat `netstat`/procesy a logy `data/private/cockpit/hotkey_agent.log` a `data/private/cockpit/server_8771.log`.

Zmenene nebo relevantni soubory:
- `scripts/open_cockpit.py`
- `scripts/cockpit_launchd_runner.py`
- `tests/test_open_cockpit.py`
- `data/private/cockpit/hotkey_agent.log` jen diagnosticky, necommitovat

Bezpecnost / neukladat:
- Neobsahuje tajemstvi.
- `data/private/` logy a runtime data necommitovat.
