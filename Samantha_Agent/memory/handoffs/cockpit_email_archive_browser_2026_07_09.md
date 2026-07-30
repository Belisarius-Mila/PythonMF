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

Aktualizace 2026-07-30 13:49 CEST - UX0 + UX1:

Co je hotove:
- UX0 potvrdilo, ze stavajici backend je vhodny read-only zaklad, ale puvodni frontend zobrazoval technicke karty, interni identifikatory a tri oddelene seznamy priloh.
- UX1 meni Archiv e-mailu na rozlozeni ve stylu schranky: slozky a pocty, seznam zprav, hledani, filtr zprav s prilohami a citelny detail.
- Detail zobrazuje plain-text telo zpravy primo na strance. Backend ho cte bez vedlejsich ucinku, odmita unik mimo archiv a omezuje velikost na 512 kB.
- Metadata, stazene soubory a dokumenty v trezoru se ve frontendu skladaji do jednoho lidskeho seznamu priloh. Oteviratelna ulozena priloha ma jednu zretelnou akci.
- Mobilni rozlozeni pouziva prechod seznam -> detail a zretelny navrat zpet.
- Puvodni read-only URL a puvodni pole API zustaly zachovane; pribyla jen pole `body_text` a `body_truncated`.
- Cilene testy prosly 233/233. Plna Cockpit quality gate prosla 1243/1243 testy.

Co neni hotove:
- Zmena zatim neni nasazena do beziciho Cockpitu.
- V relaci nebyl dostupny pripojeny prohlizec, proto chybi vizualni desktopovy a mobilni pruchod.

Dalsi krok:
- Po samostatnem potvrzeni nasadit aktualni `main`, spustit smoke test a rucne overit Archiv e-mailu na desktopu i iPhonu vcetne otevreni zname ulozene PDF prilohy.

Bezpecnost:
- UI zustava pouze pro cteni. Nepribylo zadne odesilani, mazani, presouvani ani zapis do schranky nebo dokumentoveho trezoru.
- Do testu ani pameti nebyl vlozen soukromy obsah e-mailu nebo prilohy.
