Nazev: Cockpit Recovery centrum po padu Samanthy
Priorita: 1
Stav: ceka na implementaci
Pripomenout pri startu: ano
Datum: 2026-06-03

Co se resilo:
- Mila se ptal na recovery postup, kdyz Samantha nebo Codex spadne uprostred
  prace.
- Existujici technicka pravidla uz pokryvaji `samantha`, `screen`,
  `codex resume --last`, autosave session logu a dlouhe ukoly se stavovym
  vystupem.
- Navrzeny dalsi prakticky krok je udelat v Cockpitu male Recovery centrum,
  aby navazani po padu nebylo jen terminalovy postup.

Co je hotove:
- Pravidla navazani jsou popsana v `memory/technical/session_recovery_rules.md`
  a `memory/infrastructure/codex_reconnect_recovery.md`.
- Pri startu pres `samantha` ma bezet autosave do `data/session_autosave/`.
- Zapisuje se priorita 1 pripominka, aby se pri dalsi praci na Cockpitu
  nezapomnelo na recovery centrum.

Co neni hotove:
- Cockpit zatim nema samostatny panel / kartu pro obnovu kontextu po padu.
- Neni hotovy endpoint/report, ktery by lidsky shrnul posledni autosave,
  posledni git stav, posledni handoff a doporuceny navazovaci krok.

Dalsi krok:
- Pri dalsi praci na Cockpitu navrhnout a implementovat maly panel
  `Recovery centrum` nebo `Obnova po padu`.

Navrhovane dalsi kroky:
- Okamzity krok: pridat v Cockpitu viditelnou priorita 1 kartu, ktera ukaze
  stav recovery navazani.
- Minimalni obsah karty: posledni autosave timestamp, posledni git status
  summary, odkaz na `codex_reconnect_recovery.md`, posledni relevantni handoff
  a kratky textovy postup `samantha` / `codex resume --last`.
- Volitelne pozdeji: tlacitko pro read-only recovery report, ktery nic nemaze
  a nic neprepisuje.

Zmenene nebo relevantni soubory:
- `memory/technical/session_recovery_rules.md`
- `memory/infrastructure/codex_reconnect_recovery.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- budoucne pravdepodobne `app/cockpit.py` a `tests/test_cockpit.py`

Bezpecnost / neukladat:
- Do memory ani gitu neukladat obsah citlivych autosave logu.
- `data/session_autosave/` zustava jen nouzova lokalni obnova a nikdy se
  necommituje.
- Recovery centrum ma byt read-only, dokud Mila sam nepotvrdi jakoukoli akci,
  ktera meni soubory nebo spousti obnovu.
