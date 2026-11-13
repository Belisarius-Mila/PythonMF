# Rychlé ISBN přidávání knih — místní vývoj13.11.2026

Míla schválil plán Knihobot-like rozšíření současné Knihovny. Výslovné
upřesnění: umístění se doplní až na Macu. Stávající podrobný formulář,
archiv a vlastní fotografie se zachovávají. E-mailová přejímka A+C odložená.

## Místní výsledek

Sken zadní kamerou, lokální fotografie kódu nebo ruční ISBN, rychlý katalogový
náhled a miniatura, potvrzené základní uložení do stejného Mac archivu,
duplicita/otevření původní karty/vědomý další exemplář. Karta bez umístění,
autora nebo anotace zůstává čitelná a editovatelná. Na Macu přehled bez
umístění a potvrzené přiřazení vybraným knihám s ochranou jejich revizí.

Trvalé identity a rezervace před zápisem, čtení výsledku původního požadavku
po ztrátě HTTP odpovědi, žádný druhý záznam po restartu/reloadu/dvojkliku.
Nejasná/částečná změna umístění zůstává viditelná; cizí editace se nepřepisuje.
Detailní kontrakt a hranice: technical/book_quick_inventory.md.

## Luna

Jediné registrované app.luna_development.preview/run/accept. Žádný nativní
pomocník, jiný model, změna rolí nebo opakování. Job
2eb5904075b9cd83e1c376cf01360bdf, gpt-6-luna/high podle schváleného JSON;
source c3e26c82876ccff9fcf27f1c57aa7a465abfd131. Katalogové enrich=False
zachovává starou výchozí cestu.12 původních testů před/po PASS, Adam navíc
nezávisle ověřil rychlý úspěch bez druhého katalogu, výchozí enrichment,
fallback, ISBN-10 převod a neplatný vstup bez sítě. Přesný digest
198e901969385f484debbeef705868cd3f000d782d8179a4e97c10d4ebdac0c4 accepted.
15870 tokenů, odhad0,049555 Standard kreditu za tuto modelovou část;
není to faktura ani celková cena vývoje. Private luna_result/acceptance.json.

## Ověření

368 cílených integračních testů PASS před závěrečnými čistě prezentačními
úpravami; finální plná brána pokryje aktuální zdroj. Původní tři neúspěchy
integračního běhu byly detekce nového delegovaného GET registru, společný
POST if místo explicitních větví a statické počítání labelu checkboxu.
Opraveno v odpovídajících zdrojích/kontraktech, následně368 PASS.

Headless Edge na samostatném loopback test serveru a syntetickém archivu:
390/1280px a shodná scrollWidth, skutečné uložení3 knih, dvě přiřazení
umístění, vědomý další exemplář, ztracená odpověď po serverovém zápisu,
reload a GET původního ID bez druhého POST. Reálný vendored WASM přečetl
vykreslený EAN-13. Obálky v browser QA záměrně nedostupné, uložení fungovalo.
Vizuálně zkontrolovaný390px screenshot. První testovací navigace chybně
vybrala CDP extension background místo page; opravený runner vybírá page.
Nešlo o produktovou chybu; finální browser výsledek je samostatný PASS.

Důkazy: logs/library_isbn_browser_qa_final_20261113.log,
private library_isbn_development_20261113/browser_qa_final/result.json
+ quick_book_390/1280.png. Screenshot je komponentová QA, nikoli fyzický iPhone.
Jednorázový veřejný český katalogový dotaz na9788025229033:0,583s a druhý
z RAM cache0,000s. Jedno měření není záruka rychlosti/pokrytí jiných knih.
Odkaz cover_url není důkaz skutečně dostupné obálky.

## Otevřené a hranice

Finální plná kontrolní brána prošla; místní checkpoint po přezkoumání diffu.
Zatím žádný push/p+n/deployment, fyzická kamera na iPhonu nebo20 skutečných
soukromých knih. Soukromý živý archiv nebyl testy změněný. Vendoring≈0,94MiB
JS+WASM, pevná3.1.6 licence a provenance. Registrace Obálkyknih.cz neproběhla.
Data worktree, ScienceNews, role, pošta a dohlížitel nebyly přepínané.

## Kontrola plné stránky a bezpečnostních hlaviček

Dodatečný audit odhalil, že původní hlavní stránka zakazuje kameru a WASM
a CSP blokuje externí miniatury. Opravená pouze root stránka: camera=(self),
wasm-unsafe-eval a img-src covers.openlibrary.org; ostatní dokumenty/API
zachovávají původní hlavičky. Obecný unsafe-eval se nepovoluje. Nový skutečný
HTTP test ověřuje root i zachování staré politiky jiných tras.327 cílených
bezpečnostních/integračních PASS; sady se překrývají s předchozími368.

Původní plná brána záměrně ukončena SIGTERM143 jako překonaná; nebyla
dokladem PASS. Ověřená vlastní process group43663, žádná sledovaná služba.
Finální brána běží nad nově zmrazenými21 zdroji v tested_sources_final.json.

Headless plné COCKPIT_HTML, skutečné aplikační hlavičky a izolovaný backend
prošly uložení/duplicitu/další exemplář/umístění/disconnect/reload/WASM
v šířkách390/1280. Následná Chromium fake-camera zkouška ověřila povolení
video-only a skutečné ukončení tracků po Stop. Fyzický iPhone objektiv
nebyl otevřený. Logy library_isbn_full_cockpit_qa_final_20261113.log a
library_isbn_camera_policy_qa_20261113.log. Syntetický archiv měl3 knihy,
žádná změna živé soukromé knihovny. Chyba prvního full-page runneru byla
falsy serializace DOM elementu při čekání, opravená na explicitní boolean.

## Finální výsledek

Plná brána PASS:3783 testů,31 skip,646,686s samotné testy a654,3s fáze.
Log library_isbn_full_gate_final_20261113.log. Finální21 zdrojových otisků
v tested_sources_final.json potvrzených po bráně. Překonaná brána exit143
není důkaz úspěchu. Současná nová úplná brána zahrnuje i HTTP security test.

Samostatný p+n/deploy nebyl schválený ani provedený. Fyzická iPhone kamera,
Safari/PWA oprávnění/ostření a pokrytí20 skutečných knih zůstávají otevřené.
Downloads Samantha_Knihovna_ISBN_testovaci_scenar_2026-11-13.txt je celý
vykonatelný přejímací postup, ověřený zpětným načtením. Žádný test nesahal
do skutečného soukromého archivu. Kamerový prototyp je lokální software,
ne důkaz skutečného zařízení. Další krok: vydání a fyzická přejímka.


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
