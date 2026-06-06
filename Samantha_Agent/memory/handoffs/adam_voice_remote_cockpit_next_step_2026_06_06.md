Nazev: Adam Voice Remote Cockpit - dalsi velky krok
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-06

Co se resilo:
- Ladeni Adam Voice Mode a terminal bridge z Cockpitu/iPhonu/SSH.
- Cockpit uz ukazuje, ktere Codex relace bezi a ktera je cil voice bridge markeru.
- Pri startu nove `screen` relace se Codex zepta, jestli ma nastavit voice marker na tuto relaci; vychozi odpoved je ano.
- Bylo pridano pravidlo pro rucni pokyn `Prosím převezmi voice marker`: Codex se nejdrive zepta `Mám převzít voice marker? y/n` a az po `y/ano` spusti marker skript.
- Opravena ergonomie iPhone text fallbacku: po uspesnem `Odeslat přepis Adamovi` se textarea `Přepis` vymaze, pri chybe text zustava.
- Opravena dorucovaci logika terminal bridge: pokud existuje oznaceny TTY marker a doruceni do nej je neoverene, bridge uz nepada na VS Code GUI fallback, aby netvrdil falesny uspech v jine relaci.

Co je hotove:
- `scripts/codex_session_report.py` vypisuje read-only prehled bezicich Codex relaci, bridge marker a kandidaty na rucni ukonceni.
- `scripts/samantha_codex.sh` pred startem/napojenim vypisuje report Codex relaci.
- `scripts/samantha_screen_entry.sh` se pri nove relaci pta na nastaveni voice markeru.
- Cockpit panel `Hlasový pokyn` ma radek `Codex relace`, napriklad `ttys002 -> Codex | ttys005 -> voice bridge`.
- Adam Voice Mode watcher byl restartovan a bezi na novejsim kodu.
- Testy prosly: cela sada `478 tests OK`; cilene hlasove/cockpit testy `131 tests OK`; Cockpit testy po posledni UI uprave `90 tests OK`.

Co neni hotove:
- Vzdalena prace stale neni plne prakticka, pokud Mila neni u Macu.
- Hlasova odpoved se ted prehrava na Macu, ne na telefonu. To je pri SSH/iPhone praci limitujici.
- Pokud Codex potrebuje potvrzeni rizikoveho kroku, zadost se objevi hlavne v terminalu/chat kontextu; pri vzdalenem provozu musi byt viditelna v Cockpitu.
- Chybi potvrzena smycka `pokyn -> zpracovani -> odpoved -> prehrani na telefonu -> stav v Cockpitu`.

Dalsi krok:
- Implementovat `Remote Voice Cockpit` jako dalsi velky krok:
  1. Adamova posledni odpoved se ulozi do private runtime souboru, napr. `data/private/voice_inbox/last_adam_response.json`.
  2. Cockpit ji bude pollingem nacitat a zobrazovat v panelu `Hlasový pokyn`.
  3. iPhone Cockpit bude mit tlacitko `Přehrát Adamovu odpověď`; pokud to iOS dovoli, pozdeji zkusit automaticke prehrani po uzivatelske aktivaci hlasoveho modu.
  4. Potvrzovaci zadosti pro rizikove kroky budou chodit do Cockpitu jako approval karta: co chce Adam udelat, proc je to rizikove, presna potvrzovaci veta a volby `Schválit` / `Zamítnout`.

Navrhovane dalsi kroky:
- Okamzite: navrhnout datovy format pro `last_adam_response.json` a `approval_requests.jsonl`.
- Potom: pridat read-only Cockpit endpointy a UI pro posledni odpoved + prehrani na iPhonu.
- Navazne: pridat approval centrum, ale s potvrzovacimi branami podle typu rizika; jedno kliknuti nesmi schvalovat mazani, platby, odesilani, commit/push ani tajemstvi bez presne formulace.
- Dlouhodobe: Cockpit ma byt remote-first ovladaci panel, zvukovy vystup a approval centrum pro praci z iPhonu/SSH.

Zmenene nebo relevantni soubory:
- `AGENTS.md`
- `app/cockpit.py`
- `app/speech/adam_voice_mode.py`
- `app/speech/terminal_bridge.py`
- `scripts/codex_session_report.py`
- `scripts/samantha_codex.sh`
- `scripts/samantha_screen_entry.sh`
- `tests/test_adam_voice_mode.py`
- `tests/test_cockpit.py`
- `tests/test_terminal_bridge.py`
- `tests/test_codex_session_report.py`
- `memory/technical/session_recovery_rules.md`
- `memory/projects/tts_edge_audio_tools.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do gitu ani memory neukladat obsah soukromych hlasovych pokynu, cele prepisy s citlivymi detaily, API klice, tokeny, hesla, osobni identifikatory ani private runtime markery mimo obecny popis.
- `data/private/voice_inbox/` zustava private runtime oblast mimo git.
