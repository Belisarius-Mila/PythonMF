# Název stávající cesty a záhlaví

2026-10-04 — server nasazen, build 16 připraven; fyzická přejímka čeká.

## Ovládání

Hlavní obrazovka má malé jednořádkové záhlaví **Caminos de descubrimiento**,
pod ním **Camino**, název aktivní cesty a datum. Text záhlaví se podle
dostupné šířky zmenšuje. Označení zkušební cesty se zobrazuje jen při `isTest`.

**Nabídka → Cesty → Upravit název cesty** upraví stávající cestu. U výchozí
Zkoušky je ve formuláři předvyplněno **Camino de Santiago** a vypnutá
zkušební volba. Teprve **Uložit** změnu provede; **Zrušit** nic neukládá.
Ostatní cesty mají ve formuláři své dosavadní hodnoty.

Nová cesta ani přesun Momentů nevznikají. Název musí být neprázdný, na
jednom řádku, nejvýše 160 Unicode skalárů. Soukromí a obsah Momentů,
kapitoly, soubory, mapa, přihlašovací údaje i identita cesty zůstávají.

## Trvalost a přenos

Původní `TripRecord.name` a obálka `create_trip` se nemění. Historie nových
názvů je v existujícím `SettingRecord`; zápis historie a zkušební volby je
atomický. Core Data schéma se nemigruje. Opakované uložení stejného názvu
nepřidává další operaci.

Každý nový název má trvalé UUID a samostatnou operaci `set_trip_title`
s očekávanou revizí názvu, počínaje 1. Fronta zachovává již připravené
přesné obálky i stavy verified médií. Telefon před odesíláním vyžaduje
serverovou schopnost `trip_title_v1`. Explicitní přejmenování se zařadí
i bez živých Momentů; prázdná historická kostra bez změn se dál neposílá.

Server používá dosavadní transakční `accepted_operations` jako historii
názvů, bez nového schématu a bez přepsání původního Tripu. Kontroluje
existenci cesty, formát a pořadí revizí. Retry stejné obálky vrací původní
účtenku. Konflikt využívá dosavadní fail-closed mechanismus.

Viewer čte poslední přijatý název pouze po ověření oprávnění cesty.
Používá dál stejné ID, URL, povolené Momenty, mapové body i mediální
odvozeniny. HTML název escapuje. Zamčený Viewer neprozradí ani nový název.

## Pořadí nasazení

Nejdřív nasadit server se schopností `trip_title_v1`, potom nový build
iOS do stejné aplikace přes SideStore. Teprve pak uložit nový název.
Při opačném pořadí starý server změnu nepřijme a telefon pravdivě požádá
o aktualizaci serveru; čekající metadata mohou pozastavit i ostatní přenosy.
Při návratu ke staré verzi aplikace/serveru by se mohl zobrazit původní
název. Není to postup pro obnovení staré verze po přejmenování.

Fyzicky ověřit po jednom: zachované Momenty po aktualizaci, uložený název
po restartu iPhonu a stejný Viewer s novým názvem po přenosu. Testy na
syntetických datech nenahrazují tuto přejímku.

## Výsledek lokálního ověření

- SwiftPM 64/64 PASS: rename + reopen + opakované uložení, zachování ID,
  Momentu, kapitoly, Assetu, původního create payloadu, přesných starých
  obálek a verified médií; capability gate a druhé přejmenování.
- Server/Viewer 34/34 PASS: pořadí revizí, formát a chybějící parent,
  konflikt bez přepsání původních dat, zachovaný fail-closed export,
  restart, retry create_trip, escaped HTML, stejné mapové body a auth.
- 6 obálek vytvořených Swift testem → izolovaný Python API: všechny přijaty,
  exact retry vrací stejné účtenky, reopen zachoval Trip/Moment/Asset a
  nejnovější název. Žádná skutečná uživatelská média se pro test nečetla.
- Finální generic iOS build PASS; plná projektová brána 1849/1849 PASS.
- Simulátorová aplikace a nový UI test sestaveny. Dva pokusy včetně restartu
  simulátoru nedospěly ke spuštění testovacího případu; běhy zastaveny.
  Screenshot záhlaví ani UI PASS tím nejsou doloženy. Fyzická přejímka
  vyžaduje nový build a skutečné použití na iPhonu.

Soukromé dočasné logy mají prefix `/private/tmp/camino-trip-`; nepatří do
Gitu. Tyto testy předcházely následujícímu nasazení; GitHub push neproběhl.

## Nasazení a instalační balíček

Registrované stop/upgrade/start nasadilo release `16de4d0b7973`; archiv
zůstal zachovaný včetně dalších prázdných cest. Plná brána 1850/1850 PASS.
Živě ověřena schopnost `trip_title_v1`, HTTPS owner 200, Viewer Jana 200,
anonym 401 a oba příznaky blokace false. Původní přístupy a URL zachovány.

**Camino-16-20261004.ipa**, verze 0.1.0 (16), je v Downloads. Má 1 258 019 B,
SHA-256 `b41390c6eabc88671cc285fd27646a52ab31617bf7aeb063e9ee4e0998929f3e`.
Stejné iOS zdroje jako `4ecd21f9`; stejná identita aplikace jako build 15.
Podpis a ZIP ověřeny i po rozbalení. Profil platí do 2026-10-11 22:09 UTC;
SideStore při instalaci použije svůj podpis.

Aktualizovat existující aplikaci přes SideStore. Potom v původní cestě
otevřít **Nabídka → Cesty → Upravit název cesty → Uložit**. Ověřit zachované
Momenty, záhlaví a přenos nového názvu do Vieweru. Instalace na telefon,
fyzická a vizuální přejímka zatím neproběhly. Novou cestu nezakládat.
