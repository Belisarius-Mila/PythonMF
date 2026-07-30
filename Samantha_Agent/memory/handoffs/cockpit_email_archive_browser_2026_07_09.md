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

Aktualizace 2026-07-30 13:54 CEST - nasazeni UX0 + UX1:

Co je hotove:
- Commit `d051791` byl rizene nasazen do Cockpitu jako novy proces s odpovidajicim kodovym otiskem.
- Povinny post-restart smoke test prosel 5/5.
- Zivy strukturální test potvrdil HTTP 200 pro `/email-archive/`, pritomnost noveho schrankoveho frontendu a funkcni read-only seznam i detail vcetne poli pro telo zpravy.

Dalsi krok:
- Rucne projit vzhled a ovladani na desktopu a iPhonu a otevrit jednu znamou ulozenou PDF prilohu.

Technicky dukaz:
- Nasazeny commit: `d051791da4a158159d40f07a566b2bcca78f2a39`.
- Cockpit PID po restartu: `17232`.
- Kodovy otisk: `28abaf2394075c6a`.

Aktualizace 2026-07-30 14:18 CEST - prvni UX ladeni:

Hotovo:
- Seznam se radi podle data prijeti z hlavicky e-mailu; cas archivace a lokalni mtime jsou jen bezpecne nahradni hodnoty.
- Detail muze z immutable `original.eml` read-only odvodit uplnejsi textovou alternativu. HTML se nikdy nerenderuje primo; prevadi se na text, ignoruje aktivni obsah a zustava velikostne omezeny.
- Ulozene PDF se z Archivu otevre primym odkazem na originalni soubor. Mobilni iframe uz neni primarni cestou k priloze.
- Strukturalni kontrola skutecneho archivu potvrdila, ze testovany PDF soubor je shodny s prilozenym originalem a problem byl ve zpusobu mobilniho zobrazeni, ne v datech.
- Cilene testy prosly 235/235 a plna Cockpit quality gate 1245/1245.

Rozhodnuti:
- Soukromy archiv ani dokumentovy trezor se kvuli oprave neprepisuji. Ladeni zustava read-only.

Dalsi krok:
- Po samostatnem potvrzeni nasadit aktualni `main`, spustit smoke 5/5 a na iPhonu overit poradi zprav a otevreni celeho vicestrankoveho PDF.

Technicky dukaz:
- Produkcni a testovaci zmeny jsou v `app/email/archive_browser.py`, `app/frontend/email_archive/app.js`, `tests/test_email_archive_browser.py` a `tests/test_cockpit_frontend.py`.

Aktualizace 2026-07-30 14:37 CEST - nasazeni prvniho UX ladeni:

Hotovo:
- Commit `94c6eff` byl rizene nasazen do Cockpitu.
- Novy proces a kodovy otisk odpovidaji auditovanemu commitu; povinny smoke prosel 5/5.
- Zivy read-only test potvrdil sestupne razeni podle data prijeti nad 117 archivnimi zaznamy.
- Zivy test detailu potvrdil primy odkaz na originalni PDF a platnou PDF signaturu.

Dalsi krok:
- Na iPhonu rucne potvrdit poradi zprav a otevreni vsech stran vicestrankoveho PDF.

Technicky dukaz:
- Nasazeny commit: `94c6eff75ec6c0bd25d79a557d2c4072ebdb9986`.
- Cockpit PID po restartu: `27805`.
- Kodovy otisk: `b59ab10222e987b9`.

Aktualizace 2026-07-30 15:03 CEST - UX2 pravdiva navigace:

Hotovo:
- Horni tlacitko `E-maily` otevre maly rozcestnik se samostatnou volbou pro zpracovani novych zprav a pro Archiv e-mailu.
- Horni technicka tlacitka ScanDocu nahradilo tlacitko `Dokumenty`; ScanDocu a jeho revizni rezim jsou uvnitr dokumentove sekce.
- Katalog Webovych aplikaci uz neobsahuje ScanDocu, E-maily ani Archiv e-mailu. Skutecne samostatne aplikace v katalogu zustaly.
- Prime odkazy z konkretni akcni fronty zustaly zachovane, stejne jako vsechny puvodni URL a backendove operace.
- Cilene testy prosly 226/226 a plna Cockpit quality gate 1246/1246.

Rozhodnuti:
- Informacni architektura se ridi lidskou oblasti pouziti, ne tim, zda ma schopnost vlastni webovou stranku.

Dalsi krok:
- Po samostatnem potvrzeni nasadit aktualni `main`, spustit smoke 5/5 a rucne overit `E-maily -> Zpracovani`, `E-maily -> Archiv` a `Dokumenty -> ScanDocu`.

Technicky dukaz:
- Zmeny jsou v `app/cockpit.py`, `app/frontend/cockpit/page.html`, `app/frontend/cockpit/app.js`, `tests/test_cockpit.py` a `tests/test_cockpit_frontend.py`.
