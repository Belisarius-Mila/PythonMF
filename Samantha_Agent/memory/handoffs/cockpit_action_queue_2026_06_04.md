Nazev: Cockpit akcni fronta Co ted delat
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-06-04

Co se resilo:
- Mila se ptal, co ted v Cockpitu delat po Recovery centru, health panelu
  tlacitek a diagnostickem modalu.
- Navazujici krok z ulozeneho planu byla jednotna akcni fronta `Co ted delat`,
  ktera ma z existujicich stavu vybrat nejblizsi konkretni akce.

Co je hotove:
- `app/cockpit.py` ma novy read-only helper `action_queue_status`.
- Hlavni `/api/status` vraci novy klic `action_queue`.
- Fronta sklada polozky z jiz nactenych dat:
  - konflikty plateb v Reminders,
  - problemove dokumenty ve Downloads,
  - nova PDF,
  - ulozene dokumenty k revizi,
  - prosle/dnesni/brzke pripominky.
- UI Cockpitu ma novy blok `Co ted delat` pod health panelem.
- Polozky maji prioritu, kratky detail a tlacitko na existujici akci:
  `Reminders`, `ScanDocu`, nebo `ScanDocu Review`.
- Testy pokryvaji priorizaci fronty i pritomnost UI markeru.

Co neni hotove:
- Ceka rucni UI retest primo v prohlizeci: vizualni kontrola bloku a klik na
  tlacitko `Otevřít Reminders` / `Zpracovat` / `Revidovat`.
- Bezpecny restart Cockpitu jeste neni implementovany.

Dalsi krok:
- Rucne otevrit `http://127.0.0.1:8770`, zkontrolovat blok `Co ted delat` a
  odkliknout jeho akci.
- Pokud UI retest projde, pokracovat dalsim bodem planu: bezpecny restart
  Cockpitu.

Navrhovane dalsi kroky:
- Okamzite: potvrdit, ze akcni karta v UI vypada dobre a tlacitko otevre
  spravny modal nebo ScanDocu.
- Navazujici: implementovat bezpecny restart Cockpitu jako potvrzovanou akci
  nebo samostatny script, ktery overi PID na portu `8770`, restartuje jen
  Cockpit a znovu overi `/api/status`.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/handoffs/cockpit_action_queue_2026_06_04.md`
- `memory/handoffs/cockpit_development_priorities_2026_06_03.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Overeni:
- `.venv/bin/python -m py_compile app/cockpit.py`
- `.venv/bin/python -m unittest tests.test_cockpit tests.test_quick_notes`
  proslo: 52 testu OK.
- `node --check /private/tmp/cockpit_action_queue_check.js` proslo.
- Live server po restartu bezi na `http://127.0.0.1:8770` jako PID `30855`.
- Live `/api/status` obsahuje `action_queue`; aktualne nasel jednu akutni
  polozku typu `payment_conflict`.

Bezpecnost / neukladat:
- Neukladat cele obsahy e-mailu, dokumentu, autosave logu, tokeny ani klice.
- Akcni fronta ma zustat kratka a read-only; detailni zdroj se ma otevirat az
  pres existujici potvrzovane nebo read-only workflow.
