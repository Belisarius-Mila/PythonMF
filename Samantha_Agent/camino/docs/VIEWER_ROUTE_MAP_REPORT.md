# Mapa cesty — místa záznamů (U17)

29. 9. 2026 21:23 CEST. U17 je po schválení „vše p+n“ pushnutá a nasazená
z release `879a2e7199b6`. Každý další povolený GPS bod se spojuje s předchozím,
spojnice jsou čárkované a poslední úsek má malou směrovou šipku. Lokální
projekce **16/16 PASS**, Node frontend **5/5 PASS**, plná brána **1843/1843
PASS**, Cockpit smoke **5/5 PASS**. Řízený stop → upgrade → start Camino služby
zachoval archiv a síť; skutečný privátní HTTPS Viewer audit **13/13 PASS**
(včetně 13 bodů/12 návazných úseků, autentizace, hlaviček a živých assetů).
Safari/OSM dlaždice a vizuální přejímka zůstávají NEOVĚŘENO.

29. 9. 2026. Na požadavek Míly se každý nový GPS bod v chronologii spojuje
s předchozím bodem. Původní blokace podle přesnosti, vzdálenosti, časové mezery,
půlnoci a nejistého času byla odstraněna; označení nepřesnosti a orientační
charakter čáry zůstávají. Změna je lokální a čeká na samostatné nasazení.

28. 9. 2026. Lokální implementace na výslovný pokyn Míly po schválení návrhu.
**Od 23:04 CEST nasazená serverová verze ce903913bb35; bez push, restartu
Cockpitu či změny iPhone buildu 8.** Níže vývojový důkaz a výsledek nasazení.
B04 mazání zůstává pouze buffer. Žádná migrace nebo práce s reálnými GPS.

## Co Jana dostane

Ve Vieweru odkaz Mapa cesty → vysvětlení externího podkladu → Otevřít mapu.
Celá cesta nebo jeden den, orientační spojnice, první/poslední známý bod,
název/čas/přesnost a přímý odkaz do rozbaleného okamžiku v deníku.
Stejné souřadnice mají jeden rozcestník se všemi okamžiky; bod není ztracen.
Textový seznam umožní otevřít okamžik i bez načteného podkladu.
Bez přenosu GPS nejsou body; nejde o živé sledování ani úplný inventář telefonu.
Žádná nová registrace, podpis, instalace na telefonu či placené mapové API.

## Kontrakt a jednoduchá omezení

- Jeden bod na Moment, přílohy sdílejí jeho polohu. Žádná změna zachytávání GPS.
- Chronologie `captured.utc_ms`, při shodě stabilní ID. Dny podle původního
  místního data zachycení, nikoli dne kapitoly. Odkaz vede do současné kapitoly.
- Nejistý čas zůstává označený. Bod bez času lze zobrazit v Neznámý den
  pořízení, nikdy mu nevymýšlet datum nebo pozici.
- Každý další GPS bod se spojí s předchozím bodem v pořadí pořízení, i při
  nepřesnosti nad ±100 m, velké vzdálenosti, časové mezeře, přes půlnoc nebo
  nejistém čase. Jde o orientační vizualizaci zaznamenaných bodů, ne rozpoznání
  chůze/dopravy, měřenou trasu nebo důkaz správnosti GPS. Body se při přerušení
  nezahazují.
- Přerušované spojnice s malou šipkou na konci posledního úseku, žádné
  přichytávání k silnicím, výpočet kilometrů, přehrávací animace, GPX import
  ani pozadí telefonu.
- Obnova po 60 s jen ve viditelné stránce, ručně Obnovit; timeout 15 s,
  žádné souběžné načítání. Nové body automaticky nepřibližují/nehýbou mapou;
  k tomu je Zobrazit všechny body výběru. Změna dne rámuje nový výběr.
- Při chybě načítání/401, skrytí stránky nebo odchodu pryč odstranit vrstvy,
  popupy a seznam. Pozdní odpověď ze zrušeného požadavku je ignorovaná.
- Samostatná revokovatelná Basic reader autentizace na HTML, JSON i assetech.
  Mapový JSON používá stejnou transakční viewer_snapshot projekci jako deník.
  Žádný owner endpoint, nezávislá databáze trasy ani uložený veřejný GeoJSON.
  `no-store, private`, tokeny nejsou v URL; proxy prefix `/camino-api` zachovaný.

## Externí podklad

Leaflet 1.9.4 JS/CSS lokálně s licencí a ověřenými upstream SHA-256;
provenience a normalizované lokální hashe v `server/map_assets/README.md`.
OpenStreetMap až po kliknutí, pouze pro aktuální viewport, HTTPS, viditelná
atribuce, standardní browser HTTP cache, anonymní CORS bez credentials.
Jen stránka mapy má `Referrer-Policy: origin` (žádné ID/cesty v Referer), CSP
`img-src` explicitně povoluje tile.openstreetmap.org; script/connect zůstává self.
Žádný CDN skript, geokódování, tiles proxy, prefetch/offline stahování.
Podklad je best-effort: výpadek poskytovatele neblokuje deník a seznam bodů.
Podmínky ověřené podle [OSM Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/)
a verze podle [Leaflet Download](https://leafletjs.com/download.html).

## Ověření

- Projekce + runtime/audio regrese: **30/30 PASS**.
- HTTP Viewer včetně mapy, autentizace, revokace, hlaviček, proxy a anchor:
  **17/17 PASS**, izolovaná syntetická data; použit stávající serverový Python
  environment, bez změny jeho balíčků, služby nebo archivu.
- Node frontend **5/5 PASS**: consent/no-network-before-click, empty/stale data,
  seskupení, text-safe popup, filtr, stabilní viewport, zrušený request,
  návrat z pozadí/bfcache, výpadek podkladu, deníkový hash bez přehrání.
  Test je součástí běžné brány přes ViewerRuntimeTests.
- Leaflet upstream SRI JS/CSS ověřené, JS syntax PASS.
- Plná brána **1843/1843 PASS** (256 s unit suite), log mimo Git:
  `/private/tmp/camino-route-map-full-gate.log`.
- Skutečný prohlížeč/Safari, externí dlaždice a fyzická UX: **NEOVĚŘENO**.
  CUA neposkytuje browser; offline fake-DOM/Leaflet test není vizuální důkaz.
  Během vývoje nebyly stahované mapové dlaždice ani odeslané osobní souřadnice.

Míla 28. 9. potvrdil, že Jana používala dosavadní Viewer na vlastním Macu přes
Cockpit. To je základní uživatelský důkaz Vieweru, nikoli PASS nové mapy,
celého G8, jiných sítí nebo iPhonu.

## Další krok — samostatné nasazení a krátká přejímka

Po souhlasu nasadit server ze zkontrolovaného commitu existujícím řízeným
postupem, zachovat archiv, reader/owner přístup a Serve/Funnel. Cockpit ani
telefon kvůli mapě nepotřebují novou verzi. Podklady jsou součástí standardního
release archivu celé složky server; žádný ruční kopírovací krok do produkce.

1. Z Janina Vieweru otevřít mapu, potvrdit podklad; zoom/posun/atribuce na Macu
   a podle dostupnosti Safari iPhone, popup a odkaz rozbalí správný okamžik.
2. Celá cesta/jeden den: přibližné body označené, dny oddělené, deník nadále
   chronologicky. Přílohy nepřidávají falešné nové body.
3. Jeden nový povolený GPS okamžik synchronizovat; bod do minuty nebo po
   Obnovit, bez skoku zoomu. Pozdní záznam patří podle pořízení.
4. Na syntetickém/uživatelem vybraném testovacím okamžiku přijmout skrytí či
   zámek: při nové odpovědi bod, popup i link pryč. Výpadek spojení → poctivá
   hláška a skryté staré body; po návratu aktuální stav.

Fyzické výsledky zapsat jednotlivě, ne opakovat celou historickou sadu.

## Nasazení 2026-09-28 23:04 CEST

Míla samostatně schválil nasazení a krátkou zkoušku; následně přesnou globální
brzdu. Registrované stop → potvrzeno loaded=false → upgrade → start.
Neměnný release **ce903913bb35**, kód shodný s právě ověřenou plnou bránou
1843/1843. Před upgradem konzistentní snapshoty metadat, media DB a obou auth
DB, původní konfigurace i LaunchAgent zachované v soukromé upgrade účtence.

Živý důkaz po startu:

- Služba configured/owned/loaded/running=true; privátní HTTPS a Cockpit zdravé,
  Funnel off; síťové cesty nebyly změněné.
- Archiv shodný s dokončenou přednasazovací účtenkou: 53 Momentů, 177 operací,
  62 médií / 271 510 864 B, všechna média hashově ověřená. Identita, epocha,
  kurzor a oba recovery flagy zachované (flagy=false).
- Obsah obou tabulek oprávnění shodný s předchozími snapshoty, existující
  owner i reader credential fungují. Žádná rotace ani zveřejnění tajemství.
- Mapa HTML a JSON přes skutečné HTTPS 200; čtyři JS/CSS soubory 200 a přesná
  byte shoda s release. Správný `/camino-api` prefix, consent a CSP/referrer
  hlavičky; běžný Viewer zůstává no-referrer.
- 9 bodů v jednom dni přesně odpovídá aktuálním povoleným neskrytým `diary`
  Momentům s GPS. Souřadnice i názvy porovnané jen v paměti, nevypisované.
  Chronologie podle pořízení a všechny deníkové anchor cíle ověřené.
- Všech 6 mapových endpointů odmítá anonymní i owner Bearer přístup 401;
  reader nesmí do owner API, owner API 200. Žádný test neměnil osobní obsah.

Browser automation neposkytuje žádný prohlížeč. Dlaždice OSM, vizuální mapa,
zoom/klik/Safari a nový bod po fyzické synchronizaci jsou **NEOVĚŘENO**;
HTTP/JSON kontrola není jejich náhradou. Mílovi předaný krátký průchod
Viewer → Mapa cesty → Otevřít mapu → bod → okamžik v deníku.
Žádný push, instalace telefonu, restart Cockpitu ani test smazání/skrytí
reálných záznamů nebyl proveden.

## Uživatelská přejímka 2026-09-28 23:09 CEST

Míla výslovně chválí mapu a její fungování; základní fyzická přejímka U17
**PASS podle uživatele**. Předchozí NEOVĚŘENO samotného zobrazení/fungování
tím nahrazené v rozsahu jeho praktické zkoušky. Neuvedl zařízení/prohlížeč
ani výsledky jednotlivých scénářů, proto nejde o plošný Safari/iPhone/G8 PASS,
nový bod po přenosu nebo odvolání/výpadek. Pro dnešek práci ukončuje;
nic dalšího nenasazovat, běžně používat stejnou verzi. Bez dalšího runtime zásahu.

## Nasazení 2026-09-29 21:23 CEST

Míla výslovně schválil kompletní „vše p+n“. Po předchozím ověření plné brány
proběhl GitHub batch push čtyř čekajících commitů na `main`, fast-forward
zarovnání obou čistých profilových workspace a řízené nasazení Cockpitu.
Aktuální `main` i `origin/main` jsou `879a2e7199b6`; Cockpit byl restartován
a novém procesu a smoke je **5/5 PASS**.

Camino managed service prošla registrovaným stop → upgrade → start. Upgradeytvořil neměnný release z tohoto commitu, zachoval předchozí soukromý archiv,\konfiguraci a data; Serve cesta zůstala stejná a Funnel je vypnutý.

Redigovaný živý HTTPS audit je **13/13 PASS**: Viewer mapa a map-data 200,nonymní i owner přístup k Vieweru 401, správný `/camino-api` prefix, CSP aeferrer hlavičky, mapové assety 200 s `no-store`, živý JavaScript obsahuje\čárkované úseky i koncovou šipku a 13 bodů má 12 návazných úseků. Kontrola
evypsala žádné souřadnice, názvy ani tokeny a neměnila osobní data.

Safari/OSM dlaždice, zoom/popup, skutečná vizuální šipka a nový bod po fyzické\synchronizaci zůstávají **NEOVĚŘENO**. Telefon kvůli serverové mapě nepotřebuje
ový build; fyzická přejímka se provede při běžném používání Vieweru.
