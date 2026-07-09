Nazev: Cockpit Archiv e-mailu nad EmailArchiveVault
Priorita: 1
Stav: hotovo / ceka na rucni UI retest
Pripomenout pri startu: ne
Datum: 2026-07-09

Co se resilo:
- Mila mel potvrzene archivovane iCloud e-maily v EmailArchiveVault, ale v Cockpitu je neumel pohodlne najit ani otevrit.
- Cilem bylo doplnit lokalni read-only prohlizec archivu tak, aby bylo mozne dohledat konkretni archivovany e-mail podle UID, predmetu nebo odesilatele a otevrit ulozene lokalni soubory bez dalsiho sahani na e-mailovy provider.

Co je hotove:
- Do katalogu `Webove aplikace` v Cockpitu pribyla aplikace `Archiv e-mailu` na `/email-archive/`.
- Backend umi read-only vypsat lokalni EmailArchiveVault, nacist detail archivu, nabidnout ulozene `body.html`, `body.txt`, `original.eml`, metadata a metadata priloh.
- Backend umi dohledat a otevrit fyzicky stazene prilohy z document inboxu podle bezpecneho lokalniho nazvu.
- Pridane resolvery odmítaji path traversal a povoluji jen pevne povolene soubory.
- Pridane testy pokryvaji seznam/detail archivu a odmítnuti pokusu o cestu mimo povolene slozky.
- Probehlo HTTP smoke overeni lokalni stranky, API detailu a primych odkazu na ulozene lokalni soubory.

Co neni hotove:
- Nebyl proveden Playwright/browser screenshot test, protoze Playwright neni v aktualnim prostredi dostupny.
- Zbyva rucni klikaci retest primo v Cockpitu.

Dalsi krok:
- V Cockpitu otevrit `Webove aplikace` -> `Archiv e-mailu`, hledat podle UID nebo casti predmetu/odesilatele a overit otevreni HTML/textu/originalniho EML i stazene prilohy.

Navrhovane dalsi kroky:
- Okamzity: rucne otestovat lokalni UI na znamych archivovanych UID z teto prace.
- Volitelne pozdeji: pokud se ukaze potreba, pridat filtr podle data nebo tlacitko `Otevrit slozku v dokumentech`, porad jen read-only a bez mazani/odesilani.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do handoffu ani gitu neukladat cela tela e-mailu, osobni adresy, odkazy z e-mailu, plne private cesty ani obsah priloh.
- `data/email/archive/`, `data/private/documents/` a `data/session_autosave/` zustavaji mimo commit.
- Nova Cockpit stranka je lokalni read-only prohlizec: nevola e-mail provider, nic neposila, nemaze, nepresouva a neotevira externi odkazy.
