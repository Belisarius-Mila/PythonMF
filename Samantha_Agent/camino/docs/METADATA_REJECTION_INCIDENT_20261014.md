# Camino — odmítnutí metadat na Macu 14. 10. 2026

Stav 2026-10-14 20:18 CEST: Míla potvrdil „funguje ok“ po aktualizaci; Mac dokládá pokračující metadata i média. Oprava běží, p+n hotové dávky schválené.

Míla po devíti dnech úspěšných přenosů hlásí, že telefon zůstane u
„Odesílám metadata“ a zobrazí „Domácí Mac změnu odmítl“. Film je odložený.
Odmítnutý název smazané přílohy je zachycený, Mílou potvrzený scénář zopakovaný skutečnými Swift obálkami. Identita konkrétní přílohy se do tohoto Git-safe reportu nezapisuje.

## Původní živý audit před diagnostikou

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

## Nasazená diagnostika před opravou fronty

Pouze zamítnutý POST `/api/v1/operations` zaznamená HTTP status, známý
chybový kód, veřejný důvod ze zdrojového kódu, druh operace a její pořadové
číslo. Neznámé hodnoty jsou redigované. Žádné UUID, tokeny, texty, názvy,
GPS, hlavičky ani média se nezapisují. Ani selhání diagnostiky nemění
odpověď API, transakci či opakování přenosu. Přijaté operace se nelogují.

Produkční změna je jen v `application.py` a novém `metadata_diagnostics.py`.
Bez změny schématu, závislostí, validátorů, journalu, oprávnění nebo telefonu.

## Ověření původní diagnostiky

- Cílené testy diagnostiky a skutečného HTTP endpointu: 17/17 PASS.
- Kontrolují redakci soukromého obsahu, neplatné/velké tělo, pořadová čísla,
  selhání loggeru, shodnou zamítnutou odpověď a stav archivu i přesný retry.
- Izolovaný import kandidátního balíčku v Pythonu běžící služby a katalog
  bezpečných důvodů: PASS; soubory kandidáta odpovídají pracovnímu kódu.
- Plná projektová brána: 1909/1909 PASS (320,413 s); sedm nových
  diagnostických testů samostatně PASS a doplněných do seznamu plné brány.

## Nasazení diagnostiky a zachycení odmítnutí

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


## 2026-10-14 18:41 CEST — oprava po potvrzeném přejmenování/smazání

Míla odpověděl „Ano, několikrát“. Skutečná Swift sekvence dvou názvů následně
smazané přílohy a názvu ponechané přílohy zopakovala HTTP 422. Samotný stávající
server odmítá i prostou metadata změnu na již platnou hodnotu, takže zahození
operace nebo nahodilá náhrada by nezachovala konzistentní revize.

Oprava používá výslovné `cancel_deleted_attachment_title` se vloženou původní
přesnou obálkou. Klient vyžaduje odpovídající místní deletion record, skutečné
422 `invalid_request`, feature `deleted_attachment_title_repair_v1`, stejný
server/epochu, čerstvý kurzor přesně před odmítnutým pořadím a aktuální revizi
Momentu. Před dalším POST atomicky uloží původní obálku i důkaz. Opakování,
restart a ztracená odpověď odesílají shodné uložené bajty.

Server uvnitř téže transakce vyžaduje shodné ID/pořadí/epochu/zařízení/revizi,
stejný Moment a původní platnou změnu názvu Assetu. Cíl nesmí být deklarovaný
nikde v archivu; existence u jiného Momentu nebo jiného druhu také storno
zakazuje. Vložený originál znovu projde původním validátorem a musí stále
selhat výhradně na chybějícím cíli. Storno přijme jeden krok revize bez změny
jakékoli hodnoty Momentu. Přijatá obálka uchová explicitní storno i originál;
historická projekce používá stávající čitelný codec. Schéma zůstává 3,
neprovádí se migrace, přepis původních operací ani obnova chybějících médií.

Negativní testy odmítají přijaté pořadí, cizí identitu/epochu/revizi, jiný
Moment, živý Asset, audio, neplatný název, duplicitní JSON a nepovolený stav.
68/68 Swift testů a 52 cílených skutečných Swift→API/HTTP/staging/workflow
testů PASS. Závěrečná plná brána 1925/1925 PASS. Izolovaný import v Pythonu služby
PASS. Model místní databáze, vault, kamera a audio zdroje jsou shodné s
přijatým buildem 16; SideStore/iPhone přejímka zatím NEPROVEDENO.

Balíček `Camino-SyncRepair-18-20261014-r2-unsigned.ipa`: 0.1.0 (18), arm64,
`cz.pythonmf.camino.app`, 1247937 B, SHA-256
`42c964f9579fe09663632dbafc7a2dfc85e6e8d6424f2c9a7f04fef07ec64f51`.
CRC, zabalená binárka a skutečný hash pro stahování PASS. IPA je nepodepsaný,
neobsahuje provision/profile, přihlašovací údaje, deník ani média; podepíše
ho SideStore. Přijetí SideStore a zachování telefonních dat není důkaz buildu.
Zdrojový otisk iOS `0a69eb86c479a4f2e9ad55327742ae8498487e198662f426e41096061b65c038`;
původní dřívější balíčky zachované, bez veřejné distribuce.

Pro iPhone vzdálený od Macu je připravené stažení přes existující soukromé
HTTPS `/camino-api/viewer/client-update`, se stávajícím Basic přihlášením
Vieweru. Bez explicitně staged souboru vrací 404; anonymní/odvolaný přístup
401. Ověřuje soukromá práva, pevnou identitu, délku a plný SHA-256, žádná
uživatelská cesta. Soubor ani přístup není nyní aktivovaný. Registrovaný
`camino_service_stage_client_update` zapisuje pouze novou artifact složku,
nikdy ji nepřepisuje a nemění archiv, běžící proces ani síť.

Další krok: po konkrétním aktuálním potvrzení stage/stop/upgrade/start pouze
Camino služby se čtyřmi DB snapshoty a porovnáním celého archivu před/po.
Ověřit chráněné HTTPS a celý hash staženého IPA, potom ruční SideStore import
do stejné aplikace; neodinstalovat. Ověřit původní záznamy, foto/video se
zvukem, Komentář a dokončení metadat i médií. Cockpit/Serve a zálohování
zůstávají mimo rozsah. Přenos není přijatý jako opravený před telefonním testem.
Storno je nová metadata revize, takže běžná kontrola uzavřeného filmu dál
platí; žádný hotový MP4 se nemaže ani automaticky nepřerenderuje.

Doplněný izolovaný důkaz: dosavadní vydání `e815ae75dc38` přečetlo historii
po stornu a přesně zopakovalo všech osm přijatých obálek bez změny stavu.
Kompatibilita ověřená na syntetické DB, bez zápisu do živého archivu.

## 2026-10-14 18:57 CEST — nasazená oprava a iCloud dodání

Míla výslovně požádal o soubor v iCloud Dokumentech a přesnou větou globální
brzdy potvrdil připravené nasazení. Create-only kopie stejného ověřeného IPA
do existujících iCloud Dokumentů nepřepsala žádný soubor. macOS Foundation
pro konkrétní soubor potvrzuje `isUbiquitousItem=true`,
`ubiquitousItemIsUploaded=true`, bez probíhajícího uploadu a bez chyby.
Velikost i plný SHA-256 kopie jsou shodné s balíčkem výše. Viditelnost a
import na iPhonu zatím nejsou fyzicky ověřené.

Registrované staging/stop/upgrade/start nasadily pouze Camino server
`d5d19b4b9ddd`, PID 7951. Owner loopback i soukromé HTTPS health/state 200;
obě cesty hlásí `deleted_attachment_title_repair_v1`, kurzor 740 a flags false.
Viewer, den 6. 10. a mapa 200, skutečné foto/audio/video Range 206,
anonymní přístup 401. Chráněný náhradní download IPA vrací celý soubor 200
se shodným SHA-256; HEAD 200, Range 206, anonymní i owner Bearer 401.
Soubor je dostupný pouze se stávajícím Basic přihlášením Vieweru.

Úplný audit před/po zachoval identitu, epochu, tripy, 740 operací, kurzor 740,
103 Momentů a všech 234 ověřených originálů / 1 870 503 746 B se shodnými
SHA-256. Čtyři DB snapshoty mají ověřené účtenky/hash/quick_check; všechny
řádky všech tabulek metadata/auth/media/readers jsou shodné se živými DB.
Původní konfigurace a LaunchAgent jsou zachované. Cockpit zůstal PID 35526
/ `4f1f0c17ac72659f`, smoke 5/5. Serve má shodný otisk, Funnel je vypnutý.
Karta schvalování je vyčištěná. GitHub push nebyl součástí tohoto kroku.

Důkazy: `logs/camino_repair_upgrade_baseline_20261014.log`,
`logs/camino_repair_upgrade_verified_20261014.log`,
`logs/camino_repair_icloud_delivery_20261014.log` (ignorované místní účtenky).
Povinná předchozí plná brána 1925/1925 a Swift 68/68 PASS; zdrojový kód se
po ní neměnil. Telefonní instalace a přenos nejsou těmito audity nahrazené.

Další krok: Soubory → iCloud Drive → Dokumenty →
`Camino-SyncRepair-18-20261014-r2-unsigned.ipa`; SideStore My Apps → +,
aktualizovat původní Camino bez odinstalování, zachovat stejný Apple účet
a dříve ověřené Customize AppID ON / Append Team ID OFF. Tyto volby jsou
z předchozího postupu; dnešní podpis/import na zařízení se teprve ověří.
Otevřít původní ikonu, ověřit staré záznamy a zkusit jeden sync. Úspěšné
dokončení metadat i médií, foto/video se zvukem a Komentář čekají na Mílu.


## 2026-10-14 20:18 CEST — telefonní přijetí a schválená publikace

Míla po instrukci aktualizace IPA18 odpověděl „funguje ok“ a zadal p+n.
Tím je funkční aktualizace a odblokování přenosu uživatelsky přijaté.
Samostatný nový retest foto/video se zvukem, Komentáře, přesná verze z UI
a číselné telefonní fronty nejsou touto obecnou odpovědí doložené.

Čerstvý read-only Mac audit potvrzuje kurzor/operace 740 → 767, jedno
`cancel_deleted_attachment_title` a 30 nově ověřených médií. Všech
264 originálů / 2 068 743 342 B prošlo úplnou kontrolou SHA-256.
Všech 740 původně přijatých paketů je přesně zachovaných v aktuálním ledgeru;
účtenky původních 234 médií také. Server/epocha/zařízení i tripy zůstaly shodné,
flags false. Souhrnný identity hash nyní obsahuje nový kurzor, jeho změna
proto není důkazem rotace identity. Archiv zůstává u 103 Momentů.

Camino stále `d5d19b4b9ddd`, PID 7951, owner HTTP/HTTPS a repair feature PASS.
Cockpit nyní PID 9218 / `118d4c6208030edb`, smoke 5/5 a shodný otisk
se současným zdrojovým main; tento krok žádnou službu nerestartoval.
Serve shodný, Funnel off. Vlastní vývojový kód se od brány 1925/1925
nezměnil; aktualizují se pouze projektové zápisy a LL-065.
Míla autorizoval fast-forward push celé hotové dávky. Nové nasazení téhož
kódu není potřebné; IPA a všechna soukromá data zůstávají mimo veřejný Git.
Důkaz `logs/camino_repair_phone_acceptance_20261014.log`.
