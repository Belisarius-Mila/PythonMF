Nazev: Lekarna import - editor manifestu a cleanup testovaciho prijmu
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-07-06

Co se resilo:
- Rucni integracni test Spravy Lekarny nad novou fotkou z Downloads.
- OpenAI Vision draft vyzadoval potvrzeni a pri behu selhal na `Resource deadlock avoided`, proto se pouzil macOS Vision fallback.
- Ukazalo se, ze workflow umelo vytvorit manifest a hned ho prijmout, ale nemelo lidsky editovatelny mezikrok.

Co je hotove:
- Do `app/cockpit.py` byl doplnen editor automatickeho import manifestu:
  - nacteni manifestu `/api/lekarna/import/manifest/load`,
  - ulozeni oprav `/api/lekarna/import/manifest/save`,
  - UI tlacitka `Nacist kontrolu navrhu` a `Ulozit opravy navrhu`,
  - apply pred prijmem automaticky ulozi aktualni editovany manifest.
- Do apply kroku byla doplnena validacni brzda kvality: slaby OCR fallback se uz nema prijmout na sklad.
- Testy `tests.test_cockpit` prosly.
- Cockpit byl restartovan lokalne i pres Tailscale.
- Testovaci prijem byl pozdeji podle Milova potvrzeni odstranen z lokalni evidence i z weboveho exportu.
- Lokalni export a sifrovany webovy bundle byly po cleanupu pregenerovane.

Co neni hotove:
- Pro dalsi realny test je potreba vzit jiny lek z ciste nove fotky a projit tok od zacatku.
- Overit, ze povinna cervena pole a napovedy v editoru manifestu vedou k lepsimu rucnimu doplneni pred prijmem.

Dalsi krok:
- Otestovat Spravu Lekarny na jinem leku: pripravit navrh, zkontrolovat cervena pole, ulozit opravy, prijmout na sklad a overit web export + sifrovany bundle.

Navrhovane dalsi kroky:
- Okamzite: vybrat novou fotku jineho leku a spustit cisty end-to-end test.
- Potom: podle vysledku upravit automatiku tak, aby bez rucne doplnenych povinnych poli neslo prijmout slaby navrh.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `data/lekarna/domaci_leky.csv` lokalni soukrome, necommitovat
- `docs/lekarna/encrypted-data/lekarna.enc.json`

Bezpecnost / neukladat:
- Necommitovat `Samantha_Agent/data/lekarna/`.
- Necommitovat `docs/lekarna/private-data/`.
- Neopisovat heslo pro sifrovany balicek; je v macOS Keychain.
