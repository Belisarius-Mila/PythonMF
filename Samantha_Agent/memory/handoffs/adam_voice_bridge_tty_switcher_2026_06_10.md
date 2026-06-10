Nazev: Adam Voice Bridge - automaticky aktivni TTY a Cockpit prepinac
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-06-10

Co se resilo:
- Mila upozornil, ze pri jedine bezici Codex relaci dava smysl, aby se voice bridge automaticky priradil na tuto relaci i kdyz marker ukazuje na stare TTY.
- Cockpit po restartu hlasil, ze marker ukazuje na `ttys001`, ale aktivni Codex relace je `ttys002` a `screen` nebezi.
- Navazujici otazka byla, jak efektivne prepinat voice marker pri vice Codex relacich, napr. kdyz jedna relace bezi dlouhou ulohu a voice bridge ma cilit na jinou volnou relaci.

Co je hotove:
- Commit `88f160f Use active Codex TTY when voice marker is stale`:
  - terminal bridge uz nepouziva stary marker naslepo;
  - pokud marker ukazuje na neaktivni TTY a existuje prave jedna aktivni Codex TTY, pouzije se tato aktivni relace jako `auto_target_tty`;
  - Cockpit status vraci `effective_tty` a srozumitelne hlasi rozdil mezi markerem a skutecnym cilem.
- Commit `db1ceeb Add Cockpit voice bridge TTY switcher`:
  - Cockpit ma v panelu `Hlasovy pokyn` novy blok `Voice bridge cil`;
  - UI zobrazuje aktivni Codex relace a tlacitka pro nastaveni vybrane TTY jako voice bridge marker;
  - backend endpoint `/api/voice-bridge/marker` dovoli nastavit marker jen na TTY, ktera je opravdu mezi aktivnimi Codex relacemi.
- Cockpit byl restartovan a endpoint byl realne overen na aktualnim stavu.
- Marker byl nastaven na `ttys002`; Cockpit hlasi `Bridge cili na ttys002 (marker: ttys002)`.
- Testy prosly: `.venv/bin/python -m unittest tests.test_terminal_bridge tests.test_cockpit` -> `127 tests OK`.
- Python syntax check pro relevantni moduly prosel.

Co neni hotove:
- `screen` stale nebezi, proto Cockpit opravnene drzi varovani `screen nebezi`.
- Neni hotovy plny spravce relaci se stitim, stari relace, vytizenim a dlouhymi ulohami; existuje jen prakticky MVP prepinac cilove TTY.

Dalsi krok:
- Pri dalsim realnem hlasovem testu overit, ze hlasovy pokyn z Cockpitu dojde do relace nastavene pres novy prepinac.

Navrhovane dalsi kroky:
- Okamzite: rucne refreshnout Cockpit a zkontrolovat blok `Voice bridge cil`.
- Pri vice relacich: dlouhou ulohu pustit v jedne relaci a v Cockpitu prepnout marker na volnou relaci.
- Volitelne pozdeji: doplnit k relacim lidske stitky, stari, informaci `screen`/non-screen a varovani pred prepinanim na relaci, ktera vypada vytizene.

Zmenene nebo relevantni soubory:
- `app/speech/terminal_bridge.py`
- `app/cockpit.py`
- `tests/test_terminal_bridge.py`
- `tests/test_cockpit.py`
- `data/private/voice_inbox/current_codex_tty.json` je runtime marker mimo git; aktualne byl nastaven pres Cockpit na `ttys002`.

Bezpecnost / neukladat:
- Neukladat do memory cele hlasove prepisy, soukrome pokyny, tajemstvi, tokeny, API klice ani private runtime obsah.
- Endpoint pro marker smi zapisovat jen runtime marker a jen pro aktivne detekovanou Codex TTY.
