Nazev: Cockpit priority vyvoje a stabilizace
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-03

Co se resilo:
- Mila chtel ulozit navrh priorit vyvoje Cockpitu tak, aby sel znovu vyvolat
  i po padu systemu nebo nove Codex relaci.
- Seznam vznikl po ladeni hotkey, pomaleho `/api/status`, mrtvych tlacitek
  kvuli JavaScript chybe a naslednem oddeleni tezkych reportu do lazy-load
  endpointu.

Co je hotove:
- Priorita 2 z navrhu je implementovana: hlavni `/api/status` je lehci a uz
  netaha `quantitative`, `projects` ani `consistency`.
- Priorita 1 z navrhu je implementovana jako MVP Recovery centrum a ceka na
  rucni retest v UI.
- Priorita 3 z navrhu je implementovana jako viditelny health panel Cockpitu
  a ceka na rucni retest v UI.
- Diagnosticky modal z priority 6 je implementovany jako read-only modal
  `Diagnostika` a ceka na rucni retest v UI.
- Priorita 4 z navrhu je implementovana jako blok `Co ted delat`:
  `/api/status` vraci `action_queue`, UI ukazuje prioritizovane karty a
  tlacitka vedou na existujici akce Reminders/ScanDocu.
- Priorita 5 z navrhu je implementovana jako bezpecny restart Cockpitu:
  tlacitko `Restart Cockpitu`, endpoint `/api/cockpit/restart` a worker
  `scripts/restart_cockpit.py` overuji, ze cilovy PID je `cockpit_server.py`.
- Tezsi bloky se nacitaji samostatne pres:
  - `/api/quantitative-status`
  - `/api/projects/status`
  - `/api/consistency-status`
- Hotkey start Cockpitu byl opraven tak, aby neoveroval beh pres pomaly
  `/api/status`, ale pres hlavni stranku.
- JavaScript chyba v kvantitativnim modalu byla opravena.

Co neni hotove:
- Vsech sest puvodnich priorit je implementovanych jako MVP.
- Zbyva rozhodnout dalsi smer mimo tento seznam.

Dalsi krok:
- Rozhodnout, jestli dalsi prace bude UI uklid Cockpitu nebo navrat k
  obecnemu zpracovani dokumentu / document vaultu.

Navrhovane dalsi kroky:
1. Recovery centrum
   - Karta pro situaci "neco spadlo / nevim, kde navazat".
   - Ukazat: Cockpit/ScanDocu/autosave stav, posledni autosave cas, git stav,
     posledni dulezite handoffy a jasny postup `samantha` /
     `codex resume --last`.

2. Lehci `/api/status`
   - Hotovo v teto relaci.
   - Hlavni refresh Cockpitu ma byt rychly a vzdy odpovedet.
   - Tezke veci jako kvantitativni status, consistency audit a projekty
     nacitat az samostatne.

3. Viditelny health stav tlacitek
   - Hotovo jako MVP 2026-06-04.
   - Panel ukazuje `Frontend`, `Tlačítka`, `API` a `Poslední chyba`.
   - Ceka rucni retest v UI.
   - Kdyz JS spadne nebo endpoint neodpovi, Cockpit ma ukazat jednoduchy
     cerveny panel typu:
     "Frontend skript nebezi / API status timeout / otevri recovery."
   - Nemaji vznikat jen "mrtva tlacitka" bez vysvetleni.

4. Akcni fronta misto mnoha panelu
   - Hotovo jako MVP 2026-06-04.
   - `/api/status` vraci `action_queue`; UI ma blok `Co ted delat` pod health
     panelem.
   - Ceka rucni UI retest.
   - Jeden blok "Co ted delat":
     - dokument ceka na revizi,
     - konflikt plateb,
     - nova PDF,
     - pripomenuti k rozhodnuti.
   - Vedle kazde polozky ma byt presna dalsi akce.

5. Bezpecny restart Cockpitu
   - Hotovo jako MVP 2026-06-04.
   - Live API retest prosel: PID `31544` byl overen jako `cockpit_server.py`,
     ukoncen a Cockpit byl znovu spusten jako PID `31583`.
   - Mila potvrdil rucni UI retest: restart Cockpitu probehl.
   - Tlacitko nebo script "Restartovat Cockpit", ktery:
     - zjisti PID na `8770`,
     - overi, ze jde opravdu o Cockpit,
     - ukonci ho,
     - spusti novy,
     - otevre stranku.
   - Restart ma mit potvrzeni nebo jasnou bezpecnostni branu.

6. Diagnosticky modal
   - Hotovo jako MVP 2026-06-04.
   - Modal meri endpointy z prohlizece a ukazuje posledni frontend/API chyby.
   - Ceka rucni retest v UI.
   - Modal "Diagnostika":
     - frontend JS OK,
     - `/api/status` cas odpovedi,
     - `/api/web-apps` OK,
     - `/api/quantitative-status` OK,
     - `/api/projects/status` OK,
     - `/api/consistency-status` OK,
     - posledni chyby z logu.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `scripts/open_cockpit.py`
- `tests/test_cockpit.py`
- `tests/test_quantitative_status.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/cockpit_recovery_center_priority_2026_06_03.md`
- `memory/handoffs/cockpit_action_queue_2026_06_04.md`
- `memory/handoffs/cockpit_safe_restart_2026_06_04.md`

Bezpecnost / neukladat:
- Neukladat obsah autosave logu, e-mailu, dokumentu, tokenu ani citlivych dat.
- Recovery a diagnostika maji byt read-only, dokud Mila nepotvrdi akci, ktera
  meni soubory, restartuje proces nebo spousti obnovu.
