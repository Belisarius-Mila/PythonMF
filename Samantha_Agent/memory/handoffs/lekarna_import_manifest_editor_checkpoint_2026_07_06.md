Nazev: Lekarna import - editor manifestu a Peroxid checkpoint
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-07-06

Co se resilo:
- Rucni integracni test Spravy Lekarny nad fotkou `IMG_9560.JPG` z Downloads.
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
- Peroxid byl rucne prijat do lokalni evidence: CSV ma 73 radku, foto zdroj existuje a `scripts/lekarna_photo_import.py validate` vratil `missing_sources=0`.
- Lokalni export a sifrovany webovy bundle byly pregenerovane.

Co neni hotove:
- Prijaty radek Peroxidu zustal obsahove slabsi:
  - `mnozstvi` prazdne,
  - `PIL_Short` fallback,
  - `PIL_Source` fallback,
  - `PIL_Match_Status=ceka_na_pil_overeni`,
  - `Search_Tags` prazdne.
- Sifrovany bundle neni pushnuty na GitHub Pages.
- Kod Cockpitu a testy nejsou commitnute.

Dalsi krok:
- Po navratu opravit radek Peroxidu v lokalnim CSV, znovu pregenerovat sifrovany bundle, commitnout/pushnout jen verejne bezpecne soubory.

Navrhovane dalsi kroky:
- Okamzite: dokoncit urgentni MMTX narozeninovou scenu.
- Potom: opravit Peroxid, zkontrolovat Spravu Lekarny na dalsi fotce a publikovat az cisty sifrovany bundle.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `data/lekarna/domaci_leky.csv` lokalni soukrome, necommitovat
- `data/lekarna/Leky_v_Krabickach/peroxid_vodiku_100_ml.jpg` lokalni soukrome, necommitovat
- `docs/lekarna/encrypted-data/lekarna.enc.json`

Bezpecnost / neukladat:
- Necommitovat `Samantha_Agent/data/lekarna/`.
- Necommitovat `docs/lekarna/private-data/`.
- Neopisovat heslo pro sifrovany balicek; je v macOS Keychain.
