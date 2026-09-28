# Mapa cesty — místa záznamů (U17)

28. 9. 2026. Lokální implementace na výslovný pokyn Míly po schválení návrhu.
**Zatím bez push, nasazení, restartu služby/Cockpitu či změny iPhone buildu 8.**
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
- Nejistý čas zůstává označený, bez spojnice. Bod bez času lze zobrazit
  v Neznámý den pořízení, nikdy mu nevymýšlet datum nebo pozici.
- Spojovat jen sousední body téhož dne, s kladným časovým rozdílem nejvýše
  6 hodin, vzdáleností do 20 km a oběma přesnostmi nejvýše ±100 m.
  Nepřekračovat datovou hranici. Jde o ochranné heuristiky, ne rozpoznání
  chůze/dopravy nebo důkaz správnosti GPS. Body se při přerušení nezahazují.
- Přerušované spojnice, žádné přichytávání k silnicím, výpočet kilometrů,
  přehrávací animace, GPX import ani pozadí telefonu.
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
- Node frontend **4/4 PASS**: consent/no-network-before-click, empty/stale data,
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
