Nazev: Cockpit health stav tlacitek
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-06-04

Co se resilo:
- Po funkcni kontrole Recovery centra Mila chtel pokracovat krokem 2 podle
  ulozeneho planu vyvoje Cockpitu: viditelny health stav tlacitek.
- Cilem bylo, aby Cockpit pri problemu s frontend JS, tlacitky nebo hlavnim API
  nepusobil jako sada mrtvych tlacitek bez vysvetleni.

Co je hotove:
- V Cockpitu je novy viditelny `Health stav Cockpitu` panel pod hlavnim stavem.
- Panel ukazuje:
  - `Frontend` - vychozi text `JS se zatím nespustil`, po nabehu `běží`,
  - `Tlačítka` - kontrolu pritomnosti klicovych tlacitek,
  - `API` - lehky probe `/api/status` a `/api/recovery/status`,
  - `Poslední chyba` - posledni zachycenou frontend/API chybu.
- JS ma globalni `window.addEventListener("error", ...)` a
  `window.addEventListener("unhandledrejection", ...)`.
- Chyby z hlavnich fetch/action cest se propisuji do health panelu pres
  `recordFrontendError`.
- Health check bezi pri startu a potom zhruba kazdych 60 sekund.

Co neni hotove:
- Ceka rucni retest v prohlizeci: overit, ze panel po nabehu ukazuje
  `Frontend běží`, `Tlačítka napojeno`, `API OK` a posledni chyba `žádná`.
- Zatim nejde o plny diagnosticky modal s casy vsech endpointu a logy.

Dalsi krok:
- Rucne otestovat health panel v Cockpitu.
- Potom pokracovat krokem 6 ulozeneho planu: diagnosticky modal s casy endpointu
  a poslednimi chybami.

Navrhovane dalsi kroky:
- Okamzity krok: rucni UI retest health panelu.
- Navazujici krok: implementovat diagnosticky modal.
- Vetsi ergonomicky krok po diagnostice: akcni fronta `Co ted delat`.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/cockpit_development_priorities_2026_06_03.md`

Bezpecnost / neukladat:
- Health panel je read-only.
- Nezobrazuje obsah autosave logu, e-mailu, dokumentu ani soukromych dat.

Dodatecna oprava 2026-06-04:
- Mila nahlasil, ze v Cockpitu zustala posledni chyba
  `API health selhal: /api/status AbortError: Fetch is aborted...`.
- `/api/status` a `/api/recovery/status` byly rucne zmereny a odpovidaly rychle
  kolem 0.3-0.5 s; problem byl tedy pravdepodobne stale zobrazeny abort z
  predchoziho restartu nebo kratkeho timeoutu health probe.
- Frontend health probe ma delsi timeout 6000 ms, `AbortError` se zobrazi jako
  citelny `timeout po 6000 ms` a po uspesne API kontrole se stara API health
  chyba smaze z viditelneho pole `Poslední chyba`.
- Oprava byla overena pres `py_compile`, `tests.test_cockpit`, `node --check`
  vytazeneho cockpit JS a bezpecny restart Cockpitu; novy `/api/status` po
  restartu vratil HTTP 200.
