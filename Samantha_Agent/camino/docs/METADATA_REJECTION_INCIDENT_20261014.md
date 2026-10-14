# Camino — odmítnutí metadat na Macu 14. 10. 2026

Stav 2026-10-14 18:01 CEST: diagnostika nasazená, zachycené odmítnutí změny názvu přílohy; přenos není opravený.

Míla po devíti dnech úspěšných přenosů hlásí, že telefon zůstane u
„Odesílám metadata“ a zobrazí „Domácí Mac změnu odmítl“. Film je odložený.
Technický důvod je nyní zachycený; konkrétní cíl ani spouštěč chybějící vazby nejsou zatím prokázané.

## Živě ověřeno

- Vlastněná Camino služba běží z dosavadního vydání `e95568b7999e`.
- Owner health/state přes loopback i soukromé HTTPS vrací 200. Přihlašování
  funguje; archiv nehlásí blokaci výstupů ani povinnou reconciliaci.
- Read-only kontrola SQLite prošla. Archiv má 740 přijatých operací, kurzor
  740, 103 Momentů a žádný uložený konfliktní kandidát.
- Všech 234 ověřených originálů, celkem 1 870 503 746 B, prošlo úplnou
  kontrolou velikosti a SHA-256. Deklarováno je 268 Assetů; rozdíl 34 sám
  nedokazuje ztrátu dat, mohou čekat na navazující přenos médií.
- Otisk identity archivu: `b04d0c118ef8d5f1e257f9366f0e38a1040057d15f3a5dae5c3ee83cb36311f5`.
  Tři tripy, otisk `96ac10597472a769971bc3f4ff3117e5752e623888bd950414a9592ca8d23c08`.
- Tailscale Serve otisk zůstal `1568d3d56928ccfc88baea55fdead012ba433f119c935f3cd256bc121c1c5be5`;
  Funnel je vypnutý. Síť ani její chybějící starší vlastnická účtenka se neopravovaly.

## Proč chybí konkrétní důvod

Telefon převádí obecné odmítnutí API na společnou červenou hlášku. Server
vrací kód a vysvětlení, ale běžící vydání nemá záznam odmítnutých metadat
a HTTP access log je vypnutý. Zdravé spojení a prázdná tabulka konfliktů
nevylučují například neplatnou deklaraci nebo chybějící závislost operace.
Žádná z těchto hypotéz zatím není potvrzená.

## Připravená změna

Pouze zamítnutý POST `/api/v1/operations` zaznamená HTTP status, známý
chybový kód, veřejný důvod ze zdrojového kódu, druh operace a její pořadové
číslo. Neznámé hodnoty jsou redigované. Žádné UUID, tokeny, texty, názvy,
GPS, hlavičky ani média se nezapisují. Ani selhání diagnostiky nemění
odpověď API, transakci či opakování přenosu. Přijaté operace se nelogují.

Produkční změna je jen v `application.py` a novém `metadata_diagnostics.py`.
Bez změny schématu, závislostí, validátorů, journalu, oprávnění nebo telefonu.

## Ověření přípravy

- Cílené testy diagnostiky a skutečného HTTP endpointu: 17/17 PASS.
- Kontrolují redakci soukromého obsahu, neplatné/velké tělo, pořadová čísla,
  selhání loggeru, shodnou zamítnutou odpověď a stav archivu i přesný retry.
- Izolovaný import kandidátního balíčku v Pythonu běžící služby a katalog
  bezpečných důvodů: PASS; soubory kandidáta odpovídají pracovnímu kódu.
- Plná projektová brána: 1909/1909 PASS (320,413 s); sedm nových
  diagnostických testů samostatně PASS a doplněných do seznamu plné brány.

## Další krok a bezpečnostní hranice

Míla přesnou větou globální brzdy potvrdil nasazení této diagnostiky.
Registrované stop/upgrade/start přepnuly pouze vlastní Camino službu na
`e815ae75dc38`, PID 75891. Všechny identity, tripy, 740 operací, kurzor 740,
103 Momentů a 234 ověřených originálů se všemi SHA-256 jsou před/po přesně
shodné. Čtyři DB snapshoty mají ověřené účtenky/hash a původní konfigurace
je zachovaná. Owner HTTP/HTTPS i Viewer/mapa 200, foto/audio/video Range 206,
anonymní Viewer 401. Cockpit zůstal PID 35526 / `4f1f0c17ac72659f`, smoke
5/5; Serve má shodný otisk a Funnel je vypnutý. Telefon se neměnil.
Karta schvalování je vyčištěná. Mílův následný pokus zachytil odmítnutí operace 741.

Nový bezpečný log dvakrát zaznamenal stejnou operaci 741, HTTP 422,
`invalid_request`, `kind=update_metadata`, důvod
`title target must be a photo or video of this Moment`. Jde o změnu názvu
přílohy, jejíž cílové médium není platnou fotografií/videem daného Momentu.
Samotný log nerozlišuje nedeklarovaný, smazaný či jinam patřící cíl.

Čtení klienta prokazuje riziko názvů smazaných příloh: `allMediaAssets`
vyřadí smazané Assety, snapshot zachová operace názvu a
`suppressDeletedContent` vyřadí deklaraci, ale ne název přílohy u ponechaného
Momentu. Mílovo přejmenování/smazání dosud není potvrzené; tuto možnost
nevydávat za prokázaný spouštěč. Další krok je toto upřesnění a cílená oprava.
Další telefonní retry nyní není potřeba. Neuvolňovat validaci, neměnit
identity/epochu/kurzor a nemaž ani frontu či originály.
Telefon se neodinstaluje ani znovu nepáruje. Hotový film se nepřerenderuje.

Recovery kontrola znovu hlásí zálohu z 27. 9. a zastavený autosave; Míla
byl upozorněn. Tento incident je nezměnil. Integritní audit není další záloha.
