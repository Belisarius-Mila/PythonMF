# Rychlé přidávání knih podle ISBN

Proud `project-knowledge-library`; kanonický handoff
`knowledge_library_article_editing_2026_07_16.md`, existující TVBCP
`knihovna_cockpit.txt`. Návrh a upřesnění Míly13.11.2026.

## Uživatelský průchod

Knihovna → Knihy → Naskenovat / přidat ISBN. Zadní kamera nebo lokální
fotografie čárového kódu, případně ruční ISBN-10/13. Náhled názvu, autora,
roku a obálky; údaje lze opravit. Uložit do knihovny je samostatné potvrzení.
Další kniha začíná nový záměr, dokončené uložení nejde dvojklikem opakovat.

Umístění se při načítání knih na telefonu nezadává. Základní karta může
mít prázdné umístění, autora a anotaci. Nevkládá se fiktivní obsah. Později
Doplnit umístění na Macu → vybrat knihy → přiřadit společné umístění.
Výchozí přehled ukazuje knihy bez umístění; lze zobrazit i ostatní.
Základní kartu lze také upravit stávajícím editorem. Podrobný původní
formulář pro nové knihy si ponechává své validace a stávající funkce.

Stejné ISBN-10/13 znamená stejné vydání. Duplicitní sken nabídne otevření
uložené knihy nebo vědomé přidání dalšího fyzického exempláře.

## Kamera a obálky

Lokálně přibalený zxing-wasm/reader3.1.6, MIT, JS+WASM z jednoho balíčku;
SHA-512 balíčku ověřený proti npm integrity, SHA-256 jednotlivých souborů
v vendor/zxing-3.1.6/provenance.json, licence vedle nich. Pevné verzované
trasy /assets/book-scanner/3.1.6/, žádné stahování runtime z CDN.
Načítání až při použití skeneru, pouze video bez mikrofonu. Jedno platné
knižní ISBN zastaví kameru; zavření, skrytí stránky a pagehide také. Pozdní
povolení kamery po zavření se ihned uvolní. Výsledek dekódování po zavření
nepřepíše nový průchod. Neknižní EAN a neplatné kontrolní číslice se odmítají.

Kamera a fotografie kódu se zpracují v telefonu. Do veřejného katalogu
odchází jen ISBN. Přístup kamery vyžaduje HTTPS/povolení uživatele.
Fyzické ostření/čitelnost na Mílově iPhonu ještě nebyly ověřené.

Miniatura je známá Open Library URL odvozená z ISBN. Při chybě obrázku se
zobrazí Bez obálky a uložení není blokované. Neprovádí se stahování libovolné
URL ani modelové OCR. Vlastní fotografie obálky zůstává podporovaná;
seznam ji upřednostní před katalogovým náhledem. Změna ISBN v editoru
odstraní starý katalogový odkaz, aby neukazoval obálku jiného vydání.
Obálkyknih.cz zatím nejsou integrovány; registrace a vhodnost podmínek pro
soukromý katalog zůstávají otevřené. Pokrytí českých knih ověří skutečný pilot.

## Katalog

Původní lookup_book_by_isbn má nadále výchozí enrich=True. Nová rychlá
cesta enrich=False vrátí první úspěch Knihovny.cz bez čekání na Open Library;
fallback při chybě/nedohledání zůstává. lookup_book_preview normalizuje ISBN
na13 číslic a vytvoří pouze pevný odkaz na obálku. Ostatní staré výsledky
se nemění. Tuto vymezenou část dodala registrovaná Luna, Adam zkontroloval
konkrétní diff, nezávislé větve a převzal přesný candidate_digest.

CatalogPreview má nejvýše200 záznamů v paměti procesu, TTL24h a zámek,
který sdružuje souběžné dotazy stejného ISBN. Open Library opener omezuje
četnost na nejvýše jeden dotaz za sekundu. Cache se neukládá na disk.
Timeout katalogu umožní ručně doplnit název; pozdní výsledek nepřepíše jiný
ISBN ani ruční opravu. Odkaz na obálku není důkaz její skutečné dostupnosti.

## Ukládání a obnova

Používá současný soukromý article_archive, sdílený .archive-write zámek,
stejný registr a článkové soubory. Nová karta má book_record_state=basic,
skutečně prázdný article.txt a nepřiřazené umístění. Kompletní anotace/autor/
umístění mohou základní stav při editaci dokončit. Staré karty se nemigrují.

inventory_operations.json je privátní evidence původních požadavků. Před
zápisem souborů se rezervuje konkrétní request_id, otisk a přesná metadata;
ID karty je deterministické z request_id. Stav po pádu se čte přes původní ID.
Status nevytváří knihu ani nepokračuje v zápisu. Explicitní dokončení může
použít jen původní rezervaci. Dvojklik, reload, ztracená odpověď ani restart
nemohou vytvořit další kopii. Starý dokončený požadavek neobnoví vyřazenou
knihu a nepřepíše pozdější editaci. Poškozená evidence/registr zápis blokují.

Přiřazení umístění kontroluje všechny vybrané revize před prvním zápisem,
nejvýše100 knih. Má vlastní stabilní ID a plán změn. Pád uprostřed může
zanechat částečný výsledek; zůstane pending, nikoli falešně hotovo. Dokončení
stejné rezervace přeskočí přesně známé již provedené zápisy a odmítne
cizí změnu. Konflikt lze po přečtení aktuálního stavu vědomě převzít a začít
novým výběrem; původní evidence se nemaže a nová změna nesmí potichu přepsat
mezitím upravené záznamy. Nejde o all-or-nothing transakci více karet.

Browser před jediným POST uloží původní payload/ID do localStorage tohoto
soukromého Cockpitu. Při výpadku nejprve pouze GET stejného ID. Další POST je
jen výslovné Dokončit původní zápis a má totožný původní payload/identitu.
Bez dostupného browserového úložiště se POST nespouští. Neznámý zápis se
nezahazuje ani automaticky neopakuje s novým ID. Potvrzené vyřazení původní
karty lze vzít na vědomí, aniž by se znovu vytvořila.

## Registrované rozhraní

- GET /api/library/book/quick-lookup?isbn=…: pevné veřejné katalogy, RAM cache.
- GET /api/library/books/inventory: aktuální knihy, revize a počet bez umístění.
- GET /api/library/book/quick-status?request_id=…: jen původní identita.
- POST /api/library/book/quick: výslovné uložení základní knihy.
- POST /api/library/books/locations: vybrané ID/revize a konkrétní umístění.
- Statické reader.js, zxing_reader.wasm a LICENSE.txt: pevný allowlist cest.

HTTP zachovává původní Host/Origin ochrany Cockpitu. Pouze hlavní dokument
/ má camera=(self), CSP wasm-unsafe-eval (bez obecného unsafe-eval) a
img-src pro covers.openlibrary.org. Ostatní stránky/API zachovávají původní
zákaz kamery a původní CSP. Žádné mikrofonní oprávnění se nerozšiřuje.
Capability registry
book_inventory_read a book_inventory_save, dvě POST akce v centrálním
registru. Žádná AI, zpráva, mazání, nasazení, služba nebo nová aplikace.

## Přejímka

Cílené Python/Node testy, skutečný pád vlastního procesu, souběh dvou zápisů,
chyba disku po publikaci a uprostřed přiřazení, ochrana pozdější editace,
nejistá odpověď bez replay, checksum, cache, HTTP dotazy a asset allowlist.
Skutečný headless Edge: uložení, duplicita, vědomý další exemplář, přiřazení
umístění dvěma knihám, zahozená serverová odpověď a reload se stejným ID.
Skutečný přibalený WASM dekódoval vykreslený EAN-13 na9780385472579.
Viewport390/1280 ověřený přes CDP bez přetékání, vizuální kontrola390px.
To není fyzická přejímka iPhone kamery nebo nasazeného kompletního Cockpitu.

Po samostatně schváleném p+n ověřit Mílův iPhone, oprávnění/ostření/rotaci,
Safari i ikonu Cockpitu, skutečná ISBN přibližně20 knih a doplnění na Macu.
Měřit první start zvlášť od opakovaného skenu, katalog, obálky a zápis.

Zdroje: https://github.com/Sec-ant/zxing-wasm ;
https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia ;
https://openlibrary.org/dev/docs/api/covers ; https://openlibrary.org/developers/api .

Dodatečná integrační kontrola našla původní camera=() a CSP zákaz WASM/
externích obálek; bez změny by izolovaná komponentová QA neprokázala funkci
v produkčních hlavičkách. Úprava omezená na hlavní dokument,327 bezpečnostních/
integračních testů PASS. Headless celé COCKPIT_HTML se skutečnými hlavičkami
prošel stejný tok. Chromium mock kamera: povolené pouze video, stop ukončil
oběhové stopy; fyzický objektiv iPhone tím není ověřený.

Finální místní stav13.11.: dokončeno, plná brána3783 OK/31 skip,646,686s
samotné testy. Všech21 zdrojů shodných s tested_sources_final.json.
Bez p+n nebo fyzické iPhone kamery. Kompletní Downloads testovací scénář
Samantha_Knihovna_ISBN_testovaci_scenar_2026-11-13.txt navazuje až po vydání.


## 2026-11-13 15:59 CET — Lokální oprava nereagujícího startu kamery

Hotovo: Připravené okamžité vyžádání kamery po klepnutí, bez předchozího
čekání na JS/WASM čtečku. Stav je u tlačítka před náhledem, opakované klepnutí
při startu blokované; chyba povolení či čtečky je viditelná. Načítání JS/WASM
má15s mez a při chybě ukončí stream. Pozdní starý start nezastaví novou kameru.

Rozhodnutí: Míla nahlásil první fyzický iPhone problém „Skenovat kamerou“
bez viditelné reakce. Konkrétní příčina na jeho zařízení ještě není potvrzená;
čeká informace Safari versus ikona a znění původního stavu. Oprava odstraňuje
prokázané čekání před žádostí a chybějící ohraničení chyb. Zápisy knih,
umístění, katalogy, oprávnění HTTP a modely se nemění.

Další krok: Samostatné p+n opraveného commitu a znovu fyzický iPhone sken.
Navrhované další kroky: Po úspěšném startu pilot přibližně20 knih, včetně
duplicity a chybějící obálky. E-mailový A+C zůstává odložený.

Technický důkaz: První verze je již vydaná v0ec447e7, runtime účtenka
1267634111aad32de7f188312d900770 confirmed; dnešní následný audit HTTP/HTTPS
potvrdil přesně shodné HTML, camera=(self) a obě čtecí asset URL HTTP200.
Regrese okamžité žádosti FAIL před opravou → PASS po ní; šest nových
Node průchodů (odmítnutí, timeout, chybějící API, chyba WASM, zavření, restart)
a původní životní cyklus/ukládání PASS.60 cílených Python testů PASS/13,294s,
rychlá statická brána PASS. Celé COCKPIT_HTML se skutečnými hlavičkami,
viewport390, falešná video-only kamera před uvolněním pozdrženého reader.js,
viditelný stav a následné načtení skutečného WASM PASS. Zablokovaný WASM
zobrazí chybu, ukončí stopy a znovu zpřístupní tlačítko.0 zápisů archivu.
Nová oprava je pouze lokální, bez p+n a bez potvrzené fyzické iPhone přejímky.
Logy library_camera_start_browser_20261113.log a library_camera_start_static_20261113.log;
privátní doklad camera_start_fix_browser_qa/result.json.
