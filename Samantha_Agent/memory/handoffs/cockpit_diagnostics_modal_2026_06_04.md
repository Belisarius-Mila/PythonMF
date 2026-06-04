Nazev: Cockpit diagnosticky modal
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-06-04

Co se resilo:
- Po implementaci health panelu Cockpitu se pokracovalo dalsim bodem planu:
  diagnosticky modal s casy endpointu a poslednimi zachycenymi chybami.
- Cilem je mit read-only misto, kde Mila rychle uvidi, jestli Cockpit odpovida,
  ktere endpointy jsou pomale nebo chybove a jestli frontend zachytil chybu.

Co je hotove:
- V sekci `Akce` je nove tlacitko `Diagnostika`.
- Modal `Diagnostika` meri z prohlizece endpointy:
  - `/api/status`
  - `/api/recovery/status`
  - `/api/web-apps`
  - `/api/projects/status`
  - `/api/quick-notes/status`
  - `/api/quantitative-status`
  - `/api/consistency-status`
- Modal ukazuje pro kazdy endpoint stav, HTTP status a cas v ms.
- Modal ukazuje stav frontendu/tlacitek podle health panelu.
- `recordFrontendError` drzi kratkou historii poslednich frontend/API chyb,
  kterou modal zobrazuje.
- Otevirani, zavirani tlacitkem, overlay click a Escape jsou napojene.

Co neni hotove:
- Ceka rucni retest v UI.
- Modal zatim necte serverovy log; ukazuje primarne frontend/API chyby
  zachycene v browseru.
- Bezpecny restart Cockpitu a akcni fronta `Co ted delat` nejsou hotove.

Dalsi krok:
- Rucne otestovat tlacitko `Diagnostika` v Cockpitu.
- Po potvrzeni pokracovat podle ulozeneho planu vetsim ergonomickym krokem:
  akcni fronta `Co ted delat`.

Navrhovane dalsi kroky:
- Okamzity krok: UI retest diagnostickeho modalu.
- Navazujici krok: implementovat jednotnou akcni frontu.
- Volitelne pozdeji: rozsireni diagnostiky o read-only server logy a bezpecny
  restart Cockpitu.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/cockpit_development_priorities_2026_06_03.md`

Bezpecnost / neukladat:
- Diagnostika je read-only.
- Nezobrazuje obsah autosave logu, e-mailu ani dokumentu.
