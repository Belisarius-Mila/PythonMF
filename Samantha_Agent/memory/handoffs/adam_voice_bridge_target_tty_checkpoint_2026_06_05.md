Nazev: Adam Voice Bridge / cileni na aktualni Codex TTY
Priorita: 1
Stav: ceka na dalsi realny test
Pripomenout pri startu: ne
Datum: 2026-06-05

Co se resilo:
- Hlasovy vstup z Cockpitu se prepisoval a dokazal precist odpoved, ale nedostal se spolehlive do tohoto Codex chatu.
- Prvni chyba byla smerovani na macOS aplikaci Terminal, zatimco aktualni Codex relace bezi ve VS Code integrovanem terminalu.
- Po povoleni ovladani VS Code se pokyn vlozil, ale do jineho integrovaneho terminalu a neodeslal se do aktualniho chatu.

Co je hotove:
- Commit `bf0092d Add VS Code fallback for voice terminal bridge` pridal VS Code fallback pro pripad, ze Terminal tab neexistuje.
- Commit `5a5a544 Route voice status prompts to Codex bridge` opravil smerovani pracovnich hlasovych dotazu typu `napis stav hlasoveho bridge`, aby nekoncily jako lokalni direct response.
- Commit `aea9001 Target voice bridge to current Codex TTY` pridal presne cileni na aktualni Codex TTY:
  - novy git-safe skript `scripts/mark_current_codex_tty.py`,
  - private runtime marker `data/private/voice_inbox/current_codex_tty.json`,
  - bridge nejdriv zkousi doruceni do oznaceneho TTY a teprve potom GUI fallbacky.
- Aktualni private marker ukazuje na `ttys005`, tedy tento Codex chat v teto relaci.
- Adam Voice Mode watcher byl restartovan s terminal bridge zapnutym.
- Stare testovaci pending pokyny byly oznacene jako zpracovane.
- Overeni po posledni uprave: `461 tests OK`.

Co neni hotove:
- Neni jeste potvrzeny dalsi realny hlasovy test po presnem TTY markeru.
- Doruceni pres TTY je citlive na zmenu relace: po restartu Codexu, VS Code nebo otevreni nove relace je potreba znovu spustit `scripts/mark_current_codex_tty.py` v cilovem chatu.
- Pokud macOS nebo sandbox nedovoli TTY injection, bridge ma spadnout zpatky na VS Code GUI fallback nebo pending inbox.

Dalsi krok:
- Nahraj kratky pracovni hlasovy pokyn, napr. `Adame, napis do chatu stav hlasoveho bridge.`
- Pokud se objevi primo v tomto Codex chatu, cileni je funkcni.
- Pokud se objevi v jinem terminalu nebo zustane bez Enteru, zkontrolovat `adam_voice_history.jsonl`, `adam_voice_mode.log` a obsah private markeru.

Navrhovane dalsi kroky:
- Okamzite: realny hlasovy test po markeru `ttys005`.
- Potom: doplnit do Cockpitu diagnosticky radek `Voice bridge target` s TTY markerem, posledni route a posledni chybou.
- Dlouhodobe: udelat z `mark_current_codex_tty.py` maly prikaz v Codex relaci pred zapnutim hlasoveho modu, aby se pri nove relaci nemirilo na stary terminal.

Zmenene nebo relevantni soubory:
- `app/speech/terminal_bridge.py`
- `app/speech/adam_voice_mode.py`
- `scripts/mark_current_codex_tty.py`
- `tests/test_terminal_bridge.py`
- `tests/test_adam_voice_mode.py`
- `data/private/voice_inbox/current_codex_tty.json` je runtime/private marker mimo git.

Bezpecnost / neukladat:
- Do gitu ani memory neukladat plny obsah private hlasoveho inboxu, citlive hlasove pokyny, tokeny, API klice ani private runtime data.
- Automaticke vlozeni do Codex terminalu zustava jen pro pokyny, ktere projdou triage jako bezpecne nebo read-only; zmenove/destruktivni/citlive pokyny maji zustat blokovane nebo vyzadovat rucni potvrzeni.
