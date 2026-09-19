<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno po fyzickém T050: 2026-09-19 18:06 CEST

### Hotovo
- T043 PASS v rozsahu syntetického C02b: Letový režim přerušil upload při 0/13 serverových částech; po obnově sítě vznikl jediný objekt daného Assetu, 13/13 částí, 100 663 553 B a shodný SHA-256.
- Fyzický průchod odhalil zahozené souběžné impulsy reconciliace a zdánlivě mrtvé tlačítko. Build `Camino Transfer Test` 0.4.0 (2) požadavky koaleskuje; následná 96MiB dávka doběhla automaticky bez dalšího klepnutí.
- Build 2 je strict podepsaný, nainstalovaný a spuštěný na iPhonu 14 Plus / iOS 26.6.1. Camino Audio zůstalo nedotčené; profil harnessu platí do 24. září 2026.
- T043 byl potvrzeně ukončen: vlastněný receiver neběží, `/camino-c02b` je odebraná, původní Serve konfigurace je přesně obnovená a Funnel zůstává vypnutý. Tři ověřené Assety/účtenky, každý 100 663 553 B, jsou zachované.
- Oddělený registrovaný T047 workflow používá vlastní soukromý běh. Jeho read-only audit fail-closed kontroluje relace, stav poslední relace, hash každé přijaté části a finální objekty/účtenky.
- T047 PASS v rozsahu syntetického C02b: první dávka byla zamčená během přenosu a po odemčení se dokončila 13/13; u druhé dávky byl po 1/13 skutečně ukončen proces, serverový stav zůstal 1/13 bez druhého objektu a po ručním relaunchi se doplnily pouze chybějící části do 13/13. Živé potvrzení má 2 relace, 2 ověřené objekty/účtenky, každý 100 663 553 B, celkem 201 327 106 B.
- T049 prošel na iPhonu v syntetickém mobilním rozsahu: bez grantu `Synchronizovat nyní` nechalo novou dávku na 0 %, 0/13 a serveru 0 relací; zrušení potvrzovacího dialogu zachovalo zákaz. Po vědomém povolení této dávky přenos pokračoval a server doložil jedinou ověřenou relaci, 13/13 částí, jeden objekt a účtenku, 100 663 553 B a shodný SHA-256; Míla viděl `Ověřeno na Macu`.
- Další syntetická dávka začala znovu s vypnutým mobilním povolením. Ruční synchronizace zůstala na 0 %, 0/13, 0/2; server nadále viděl jen první relaci a jediný objekt/účtenku. Úplné znění fyzického potvrzovacího dialogu nebylo opsáno.
- T049 bylo registrovaně ukončeno: vlastní receiver neběží, testovací Serve cesta je odebraná, původní konfigurace přesně obnovená, Funnel vypnutý. Jediný ověřený syntetický důkaz zůstává zachovaný. T048 zůstává neaktivní a čeká na cizí Wi-Fi.
- Zdroj `Camino Transfer Test` 0.4.0 (3) vynucuje síťovou politiku dávky u všech HTTPS požadavků. Podepsaný build 3 se na iPhonu fyzicky spustil a prošel uvedeným testem; Camino Audio 0.3.0 (4) zůstává nedotčené.
- T050 PASS v syntetickém fyzickém rozsahu na iPhonu 14 Plus / iOS 26.6.1 s buildem 0.4.0 (3): video ukazuje `Ověřuji`, 100 % a 13/13 během serverového `verifying` bez objektu/účtenky; až potom `Ověřeno na Macu`. Server následně doložil jednu ověřenou relaci, objekt i účtenku o 100 663 553 B se shodným SHA-256. První průchod zachytil jen finále a zůstal neověřený; potvrzovací opakování má vlastní zachovaný soukromý běh.
- Oba běhy T050 jsou potvrzeně ukončené. Poslední audit: `phase=stopped`, receiver/cesta neaktivní, přesná obnova původního Serve, Funnel vypnutý; v druhém běhu zůstává jeden ověřený objekt a účtenka. Soukromé video zůstává mimo Git.

### Otevřeno
- T048 na cizí Wi-Fi je fyzicky NEPROVEDENO. Plné T049 s novým skutečným videem čeká na integrovanou aplikaci; C02b ještě není produkční přenos.

### Rizika
- Receiver je lokální standard-library experiment, ne produkční FastAPI, databáze, trvalá služba ani záloha. T049 nedokládá cizí Wi-Fi ani zadrženou finalizaci.
- T049 v samostatném harnessu nemá kameru a plné kritérium nového skutečného videa se musí ověřit až v integrované aplikaci. Serverových 100 663 553 B není měření spotřeby operátora; retry může přenést více dat.
- Po jednorázovém mobilním grantu může návrat aplikace z Ovládacího centra vyvolat `applicationBecameActive()` → `reconcile()` a rozběhnout čekající dávku bez klepnutí na `Synchronizovat nyní`. Míla to pozoroval; video souhlasí, ale neprokazuje absenci dotyku. Před úpravou UX oddělit čerstvý, ještě nespouštěný přenos od obnovení rozpracovaného přenosu. Video krátce ukazuje `Vyžaduje pozornost` před bezpečným retry; přesná příčina první chyby nebyla zjištěna.

### Další krok
- Až bude dostupná cizí Wi-Fi, provést oddělený T048 podle `C02b_T048_T049_FIELD_PLAN.md`. Před dalším mobilním během rozhodnout a případně opravit neočekávaný automatický start čerstvé dávky; T050 se neopakuje.

### Rozhodnutí
- Serverová pravda a stav `verifying` mají přednost před lokálním byte progress. Dostupná povolená Wi-Fi může spustit automatickou synchronizaci; ruční tlačítko je provozní záloha. Souběžný impuls se koaleskuje, nezahazuje.
- Míla zvolil pořadí T049 před T048 kvůli nedostupné cizí Wi-Fi; nejde o změnu kritérií ani označení T048 za PASS.
- Míla zvolil T050 před dostupností cizí Wi-Fi. Po nezachyceném prvním mezistavu výslovně zvolil opakování se záznamem obrazovky; druhý průchod splnil syntetická kritéria T050. Automatický start není nově schválené UX rozhodnutí.

### Navrhované další kroky
- T047 je fyzicky PASS v syntetickém rozsahu; jeho dva objekty/účtenky a relace zůstávají zachované.
- T049 je v syntetickém mobilním rozsahu hotové a bezpečně ukončené; plné T049 s novým skutečným videem zůstává otevřené.
- T048 provést na cizí Wi-Fi při dostupnosti sítě; plný T049 se skutečným novým videem až v integrované aplikaci. UX automatického startu řešit samostatně před dalším mobilním během.

### Technický stav checkpointu
- Swift transfer core 19/19, T043 ovladač + oba receivery 28/28, T047/T043 workflow modul 11/11 a UI 1/1 PASS; podepsaný build 2, strict kontrola, instalace a launch PASS. Plná projektová brána 1716/1716 PASS.
- Push ani nasazení neproběhly. T043 i T047 cesta/receiver jsou ukončené; původní Serve je přesně obnovený a Funnel vypnutý.
- T049 audit po stopu: `phase=stopped`, `receiver_alive=false`, `private_route_exact=false`, `funnel_enabled=false`, `session_count=1`, `session_verified_count=1`, `latest_session_chunks=13/13`, `object_count=1`, `receipt_count=1`, `verified_match=true`, `verified_byte_count=100663553`. Dřívější Swift core 20/20, iOS UI 1/1, podepsaný build 3 a plná projektová brána 1718/1718 PASS; kód se při fyzickém testu neměnil.
- T050 před fyzickým testem: cílené testy 32/32 a plná projektová brána 1719/1719 PASS; kód se při testu neměnil. Server `verifying` 17:58:22–17:58:36 CEST při 13/13 a 0 objektech/účtenkách; soukromé video ukazuje `Ověřuji` v tomto okně a finální stav až po něm. Poslední T050 status po stopu: `phase=stopped`, `receiver_alive=false`, `private_route_exact=false`, `funnel_enabled=false`, `session_count=1`, `session_verified_count=1`, `object_count=1`, `receipt_count=1`, `verified_match=true`, `verified_byte_count=100663553`. T048 `INACTIVE`, T049 `stopped`; push ani nasazení neproběhly.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Camino

Nazev: Camino
Pracovni proud: project-camino
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-09-19 18:06 CEST

Co se resilo:
Fyzický T050 se zadrženým serverovým ověřením; oddělené potvrzovací opakování a bezpečný stop.

Co je hotove:
V0.5 + U15 platí; C01a/C01b/C01c/C02a jsou přijaty v prototypovém rozsahu. T043 a T047 prošly synteticky, T049 v syntetickém mobilním rozsahu. T050 prošel ve druhém fyzickém syntetickém běhu se souběžným důkazem iPhonu a serveru; oba T050 běhy jsou ukončené, jejich soukromé důkazy zachované. Podrobnosti jsou v aktuálním stavu výše.

Co neni hotove:
C02b není dokončené: T048 je fyzicky neprovedené, plné T049 čeká na nové skutečné video a automatický start po návratu aplikace potřebuje UX rozhodnutí. Produkční FastAPI a trvalá služba také nejsou hotové. Dále plný databázový T061 v C05a, plná integrace T021 v C04, U15 v C03/C04, Viewer C08c–C08f, G0/G1/G8, dlouhodobá spotřeba a terénní připravenost.

Dalsi krok:
Při dostupné cizí Wi-Fi provést T048; před dalším mobilním během vyjasnit neočekávaný automatický start čerstvé dávky.

Navrhovane dalsi kroky:
Plné T049 s novým skutečným videem až v integrované aplikaci; U15 až v C03/C04 a Viewer v C08c–C08f.

Zmenene nebo relevantni soubory:
`camino/`, `memory/projects/camino.md`, katalog, registry a kanonický TVBCP.

Bezpecnost / neukladat:
Žádná reálná média, osobní texty, přesná GPS, klíče nebo citlivé síťové údaje v Gitu.

### 2026-09-14 21:22 CEST — Založení Camina před meziúkolem

Hotovo:
- Samostatný katalogový projekt, vlastní paměť, handoff a TVBCP; podklady v0.4 uchované.

Rozhodnutí:
- Míla zadal založení projektu a integraci do Human–Adam, commit, push a nasazení.
- Vývoj se dnes tímto krokem nezahajuje; nejdřív meziúkol, potom C00.
- Potvrzené U01–U11 z podkladů se znovu neotevírají. Návrhy D01–D10 nejsou nová uživatelská rozhodnutí.

Další krok:
- Vyřešit Mílův meziúkol; při návratu ke Caminu začít C00.

Navrhované další kroky:
- Po C00 připravit jen malý audio prototyp C01a podle skutečně ověřeného prostředí.

Technický důkaz:
- Manifest 15/15 shodných SHA-256; ZIP odpovídá všem 16 rozbaleným souborům.
- Testy integrace a stav publikace: viz `memory/reports/camino_registration_2026_09_14.md`.
- Testy aplikace a manuální hardware zkoušky NEPROVEDENO.

Ověření založení: 56/56 testů integrace (54 + 2 profilové testy) a rychlá statická brána OK.
Publikační plná brána a finální nasazení se ověřují registrovaným živým auditem;
tento zápis předchází schválenému push a nasazení.

### 2026-09-14 23:26 CEST — C00, Xcode a checkpoint po recovery záloze

Hotovo:

- C00 a samostatně schválená instalace Xcode dokončeny; projektové předání dorovnáno na skutečný stav.
- Před úklidem vznikla ověřená recovery záloha `20260914_231439`; dokumenty Camina zachované a porovnané pomocí SHA-256.

Rozhodnutí:

- Míla zadal nejdřív ostrou zálohu, potom úklid repozitáře. Úklid tvoří lokální dokumentační checkpoint bez mazání; push ani nasazení nejsou součástí tohoto kroku.
- U01–U11 beze změny. C01a se automaticky nezahajuje.

Další krok:

- Po výslovném zadání C01a připojit odemčený iPhone a ověřit rozpoznání, kompatibilitu a podpis pro malý audio prototyp.

Navrhované další kroky:

- Nahrát, bezpečně dokončit a přehrát krátký neutrální vzorek na skutečném telefonu; server není vstupní podmínka.

Technický důkaz:

- `camino/docs/ENVIRONMENT_AUDIT.md`, `DECISIONS.md`, `XCODE_INSTALLATION.md` a `camino/tasks/C01a_AUDIO_PROTOTYPE.md`.
- Instalační kontroly Xcode/first launch/iPhone SDK prošly; build a fyzické audio testy NEPROVEDENO.
- Recovery: 63 295 souborů, 28 892 kopírováno, 34 360 hardlinků, 43 symlinků, 0 přeskočeno; zkušební obnova AGENTS.md se shodným SHA-256.
- Závěrečná plná kontrolní brána checkpointu: 1684/1684 testů OK; syntaxe a Git safety check OK. Nejde o testy aplikace Camino.

### 2026-09-15 08:19 CEST — C01a: první prototyp, telefon připraven, build blokován

Hotovo:

- Malý prototyp Start/Stop, skutečný vstup, místní evidence a přehrání; 25 testů logiky a syntetického audia prošlo.
- Míla připravil důvěru a Developer Mode; přímý audit potvrdil párování, spojení a vývojové služby telefonu.

Rozhodnutí:

- Na Mílův pokyn pokračovat ve vývoji zahájeno pouze C01a. Žádná placená AI ani další etapa.
- Přímá kompilace není náhrada Xcode buildu, instalace nebo fyzického poslechu. Celý krok zůstává BLOCKED.

Další krok:

- V Xcode → Settings → Components ověřit a zpřístupnit Platform Support iOS 26.2, potom zopakovat build připraveného CaminoAudio projektu.

Navrhované další kroky:

- Po sestavení připravit podpis, nainstalovat prototyp a ručně ověřit neutrální vzorky Komentář/Úvaha. Žádná automatická aktivace mikrofonu.

Technický důkaz:

- `camino/docs/C01a_AUDIO_PROTOTYPE_REPORT.md`, `camino/prototypes/audio/README.md`.
- 25/25 XCTest OK; arm64/iOS kompilace/link exit 0, bez warnings; project.pbxproj lint OK.
- Xcode build exit 70: platform support iOS 26.2 chybí; platné signing identity 0. Fyzické testy NEPROVEDENO.
- Plná společná brána před checkpointem: 1684/1684 testů OK; nové Swift testy jsou samostatných 25/25 výše.

### 2026-09-15 13:34 CEST — Zahájení instalace podpory iOS

- Míla po dokončeném úklidu výslovně zadal spuštění instalace.
- Xcode Components: spuštěn balíček iOS 26.2 + iOS 26.3.1 Simulator; živě potvrzen postup stahování 185 MB z 10,47 GB (2 %). Úvodní odhad před spuštěním byl 8,39 GB.
- Před spuštěním 92 116 107 264 B volných (85,79 GiB). Instalační doklad je soukromý, mimo Git.
- Dokončení instalace, nový Xcode build, signing a fyzická přejímka zatím neověřeny; C01a zůstává BLOCKED.
- Další krok: Po dokončení stahování ověřit instalaci iOS Platform Support v Xcode Components a zopakovat nepodepsaný build C01a. Potom dořešit signing, instalaci na iPhone a fyzickou přejímku T015/T017/T025.

### 2026-09-15 15:01 CEST — Podpora iOS a standardní build ověřeny

- Xcode Components a `simctl list runtimes` potvrdily instalaci; iOS runtime 26.3.1 / 23D8133 dostupný.
- `xcodebuild -project camino/prototypes/audio/CaminoAudio.xcodeproj -scheme CaminoAudio -configuration Debug -destination generic/platform=iOS -derivedDataPath <soukromý-build-adresář> CODE_SIGNING_ALLOWED=NO build`: exit 0, BUILD SUCCEEDED.
- Vznikl skutečný balíček CaminoAudio.app s arm64 executable; `codesign` potvrdil, že není podepsaný. Jediné varování: přeskočená extrakce AppIntents metadat, protože target nemá AppIntents.framework.
- SDK/platforma už build neblokují. Zdroje aplikace beze změny; dřívějších 25 testů logiky se bez nové změny neopakovalo.
- Volné místo po instalaci přibližně 69,3 GiB. Platných podpisových identit aktuálně 0; DEVELOPMENT_TEAM v projektu nenastaven. Přihlášení k Apple Account zatím neověřeno.
- Instalace aplikace na telefon, spuštění a fyzické T015/T017/T025 NEPROVEDENO. C01a zůstává BLOCKED na podpisu a fyzické přejímce; C01b nezahájeno.
- Další krok: Nastavit v Xcode Apple Account a vývojový tým pro podpis, potom podepsat a nainstalovat CaminoAudio na iPhone a provést fyzickou přejímku T015/T017/T025.

### 2026-09-15 18:31 CEST — Podpis ověřen, instalace čeká na telefon

- Míla nastavil tým v Xcode. Aktuálně jedna platná podpisová identita; automatický vývojový podpis a profil ověřeny. Účty, certifikáty a identifikátory týmu nejsou v Gitu.
- Podepsaný `xcodebuild` Debug / generic/platform=iOS: exit 0. `codesign --verify --deep --strict` nad CaminoAudio.app: exit 0. Vývojový profil platí do 2026-09-22 18:16 CEST, obsahuje jedno zařízení.
- První build v projektovém data/private skončil na FinderInfo u .app. Nový DerivedData adresář v /private/tmp problém odstranil bez změny zdrojů či odstraňování atributů originálů. [Apple QA1940](https://developer.apple.com/library/archive/qa/qa1940/_index.html).
- Volba týmu z Xcode přesunuta do existujícího mechanismu LocalSigning.xcconfig; význam verzovaných nastavení projektu je shodný s původním HEAD, zachováno jen formátování Xcode.
- Poslední devicectl inventura: iPhone 14 Plus odpojený; Developer Mode enabled je evidovaný stav, nikoli důkaz aktuálního spojení. Instalace, spuštění a fyzický poslech NEPROVEDENO; C01a zůstává BLOCKED.
- Další krok: Připojit a odemknout iPhone, ověřit dostupnost zařízení a nainstalovat podepsaný CaminoAudio.app. Potom provést fyzickou přejímku T015/T017/T025; nahrávání zahajuje uživatel vědomým Start.

### 2026-09-15 18:36 CEST — Aplikace nainstalována, spuštění odmítnuto

- iPhone 14 Plus živě ověřen: wired, tunnel connected, Developer Mode enabled. Zařízení odpovídá vývojovému profilu; podpis znovu ověřen strict kontrolou.
- `devicectl device install app`: exit 0, success, přesný bundle cz.pythonmf.camino.audio.prototype v installedApplications. Instalace na telefon PASS.
- `devicectl device process launch`: exit 1, FBSOpenApplicationErrorDomain / Security. Hlášení uvádí podpis, oprávnění nebo nepotvrzenou důvěru profilu; vzhledem k platnému podpisu a úspěšné instalaci je dalším krokem ruční kontrola důvěry. Příčina zatím není definitivně potvrzena.
- Spuštění, UI, mikrofon a fyzický poslech NEOVĚŘENO; C01a stále BLOCKED, C01b nezahájeno. Žádné nahrávání nebylo spuštěno.
- Další krok: Na iPhonu potvrdit důvěru vlastnímu vývojářskému účtu v Nastavení → Obecné → VPN a správa zařízení. Potom ověřit spuštění Camino Audio a provést fyzickou přejímku T015/T017/T025.

### 2026-09-15 18:39 CEST — Míla potvrdil otevření aplikace; zadal c+p+n

- Míla výslovně potvrdil, že se Camino Audio na iPhonu otevřelo. Otevření je potvrzení uživatele; nejde o automaticky ověřený průchod UI, mikrofon ani poslech. Předchozí blokace spuštění již podle tohoto potvrzení nebrání otevření.
- Podepsaný build, strict podpis a instalace mají strojové doklady; profil platí do 2026-09-22 18:16 CEST. Ruční T015/T017/T025, oba audio vzorky a poslech zůstávají NEPROVEDENO, C01a není přijaté.
- Míla zadal nejprve commit + push + nasazení aktuálního balíčku do Cockpitu. Autorizace zahrnuje čekající lokální commity a tento redigovaný stav; po c+p+n se zatím další vývoj ani nahrávání nespouští.
- Doklad výsledku c+p+n: aktuální GitHub batch audit, plná brána a kanonická simple-main deployment receipt s novým PID, shodou otisku a smoke 5/5; historické nasazení není důkaz tohoto kroku.
- Další krok: Po uzavření schváleného c+p+n pokračovat ruční přejímkou C01a na iPhonu: T015/T017/T025, neutrální krátký Komentář a Úvaha, Stop a poslech; nahrávání zahajuje Míla. C01b nezahajovat.

### 2026-09-15 19:15 CEST — Uživatelské zkoušky krátkého audia

- Zařízení: iPhone 14 Plus / iOS 26.6.1; Camino Audio 0.1.0 (1), instalovaný podepsaný Debug build z 15. září. Níže je svědectví Míly z řízených kroků v konverzaci, nikoli měření na dálku.
- Komentář: podle potvrzení běžel čas, reagoval ukazatel signálu, Stop dokončil uložení a celý záznam byl slyšet včetně začátku a konce. Zadáno asi 30 s; skutečná délka a stav sítě nebyly změřeny.
- Úvaha: Míla potvrdil všechny kroky zkoušky v režimu Letadlo s vypnutou Wi-Fi, včetně uložení a poslechu. Zadáno asi 30 s; skutečná délka nebyla změřena.
- Opětovné otevření po ukončení přes přepínač aplikací: oba dokončené vzorky zachovány a přehratelné, mikrofon se sám nespustil — uživatelský PASS. Není to zkouška pádu během zápisu.
- Odebrání oprávnění v Nastavení: aplikace oznámila zakázaný mikrofon; po povolení vše fungovalo — uživatelský PASS tohoto scénáře. První odmítnutí systémového dialogu tím není ověřeno; samovolný Start po změně oprávnění nebyl v poslední odpovědi zvlášť popsán.
- T015 částečně ověřeno (oba typy a poslech, offline výslovně jen Úvaha), T017 částečně (signál a hlas, bez potvrzení názvu vstupu), T025 částečně (odebrání/povolení v Nastavení). Neoznačovat celé scénáře za PASS.
- Přesné délky, velikosti a SHA-256 telefonních vzorků dosud nezjištěny; obsah ani soubory nahrávek se nepřenášely. Žádný hlášený funkční FAIL, ale C01a zatím formálně nepřijato; G0/G1 neuzavřeny.
- Dřívější c+p+n d573e90c dokončeno: 1684 testů, šest commitů pushnuto, canonical deployment receipt deployed a smoke 5/5. Tento nový zápis výsledků vzniká až po tomto nasazení a je určen k místnímu commitu.
- Další krok: Doplnit krátký Komentář bez internetu a potvrdit název zobrazeného vstupu. Potom doplnit doklady vzorků a přesný scénář prvního odmítnutí oprávnění T025; dosavadní výsledky neopakovat bez důvodu. C01b nezahajovat.

### 2026-09-15 19:25 CEST — Oprava zobrazení průběhu přehrávání

- Míla po doplňujícím testu potvrdil přehrání Komentáře a nahlásil chybějící průběh. Snímek IMG_0503.PNG ukazuje režim Letadlo, Přehrávám, čas 00:30, název Mikrofon iPhonu a uložený Komentář 00:30. Obrázek nebyl kopírován do Gitu. Sám nedokládá pohyb času ani vypnutí Wi-Fi; přehrání potvrzuje uživatel.
- Příčina ověřena v kódu: společná obrazovka při poslechu dál zobrazovala elapsed posledního záznamu, vstup a mikrofonní meter. Playback tick pouze hlídal konec, nečetl pozici přehrávače.
- Oprava: AVAudioPlayer.currentTime a duration přes AudioDriver; samostatný stav přehrávání v controlleru a oznámení změny při každém odečtu. SwiftUI při poslechu zobrazuje uplynulý/celkový čas a modrý průběh místo údajů mikrofonu. Žádné dopočítávání času podle timeru. [Apple currentTime](https://developer.apple.com/documentation/avfaudio/avaudioplayer/currenttime).
- Ověření: 28/28 Swift XCTest, podepsaný Debug xcodebuild generic/platform=iOS exit 0 a codesign --verify --deep --strict exit 0. Tři nové testy pokrývají skutečnou pozici vs. čas záznamu/nástěnné hodiny, chybné hodnoty a Stop/opakování/odchod do pozadí; rozšířen test přirozeného konce.
- Zápis a formát médií se nemění. Nová verze zatím NENÍ nainstalovaná na iPhonu; ruční UI/poslech opravy NEOVĚŘENO. Před aktualizací čeká potvrzení, že nahrávání i přehrávání stojí. Existující vzorky zachovat, aplikaci neodinstalovávat.
- T015: doplňující Komentář přehrán podle uživatele, screenshot v režimu Letadlo; offline test proběhl podle zadaného postupu, samostatný technický důkaz vypnuté Wi-Fi chybí. T017: název vstupu Mikrofon iPhonu nyní doložen snímkem (při poslechu šlo o zachovaný údaj záznamu). Přesná metadata vzorků a první odmítnutí systémového dialogu T025 zůstávají otevřené.
- Další krok: Při zastaveném záznamu i přehrávání aktualizovat aplikaci v připojeném iPhonu a ručně ověřit běžící čas/průběh, Stop a opakované přehrání existujícího vzorku. Potom doplnit zbývající doklady C01a a první odmítnutí oprávnění; C01b nezahajovat.

### 2026-09-15 20:15 CEST — Přerušení poslechu, práce bez telefonu

Hotovo:

- Poslech po události přerušení ihned skončí a obrazovka přizná přerušení; další poslech vyžaduje Přehrát. Čas i průběh se vynulují.

Rozhodnutí:

- Na Mílův pokyn pokračováno bez připojeného telefonu v opravách C01a. C01b nezahájeno; bez změny formátu a zápisu médií.

Další krok:

- Po připojení telefonu a zastavení záznamu/poslechu aktualizovat aplikaci a ověřit průběh, Stop, opakované přehrání a přerušení poslechu.

Navrhované další kroky:

- Doplnit metadata neutrálních vzorků a první odmítnutí systémového oprávnění. Fyzická přejímka C01a zůstává otevřená.

Technický důkaz:

- Regresní test před opravou selhal: přerušení nechalo stav playing. Po opravě 30/30 Swift XCTest; podepsaný Debug xcodebuild a strict codesign exit 0. Dva nové testy ověřují okamžitou reakci bez timeru a opakované události bez automatického spuštění či změny nahrávek.
- Instalace této verze, simulátor a fyzické zkoušky NEPROVEDENO. Starší verze zůstává v iPhonu.

### 2026-09-15 20:20 CEST — Srozumitelné chyby při zahájení poslechu

Hotovo:

- Nedostupný soubor má vlastní hlášení, odlišné od chyby načtení/přehrání. Nastavení mikrofonu se nabízí jen při zakázaném oprávnění. Po chybě lze vybrat jinou nahrávku.

Rozhodnutí:

- Pokračování bez telefonu v C01a; žádné nové projektové rozhodnutí ani zahájení C01b.

Další krok:

- Po připojení telefonu a zastavení záznamu/poslechu aktualizovat aplikaci a ověřit opravený průběh, Stop a opakované přehrání.

Navrhované další kroky:

- Dokončit ruční přejímku včetně oprávnění a metadat neutrálních vzorků.

Technický důkaz:

- 32/32 Swift XCTest, podepsaný Debug xcodebuild a strict codesign exit 0. Dva nové testy: nedostupný soubor bez změny evidence a následný poslech jiného vzorku; nabídka nastavení podle oprávnění i při nesouvisející chybě uložení.
- Pět zdrojových/testovacích souborů; formát ani zápis médií beze změny. Instalace a fyzický retest NEPROVEDENO, C01a stále nepřijato.

### 2026-09-15 20:42 CEST — Ověření rozhraní v iOS simulátoru

Hotovo:

- Dva opakovatelné UI testy ovládají SwiftUI a skutečný AVAudioPlayer: čas i průběh postupují, Stop a opakování fungují; vzorek přežije ukončení aplikace a návrat sám nic nepřehraje. Prohlédnutý snímek ukazuje 00:03 / 00:30, modrý průběh a dostupný Stop bez překryvů.

Rozhodnutí:

- Další práce bez telefonu zůstává v C01a. Samostatné schéma CaminoAudioUITests, pouze tiché syntetické audio a oddělené UUID úložiště. Pomocný kód se překládá jen pro Debug simulátor; návrat aplikace nesmí vytvořit náhradní vzorek.

Další krok:

- Po připojení telefonu a zastavení záznamu/poslechu aktualizovat aplikaci a ověřit opravený průběh, Stop a opakované přehrání.

Navrhované další kroky:

- Dokončit fyzickou přejímku oprávnění a metadat neutrálních vzorků. C01b nezahájeno.

Technický důkaz:

- CaminoAudioUITests: 2/2 PASS, 0 skipped, xcodebuild test exit 0; iPhone 14 Plus simulátor, iOS 26.3.1 / 23D8133, x86_64. Snímek exportován z xcresult a vizuálně zkontrolován. Logy, výsledek a snímek zůstávají mimo Git.
- Dřívějších 32 testů jádra se beze změny jádra neopakovalo. Standardní podepsaný iPhone build a strict podpis OK; testovací vstupní značky nejsou v jeho programu.
- Mikrofon, fyzický poslech, iOS 26.6.1 a instalace aktualizace na telefon NEOVĚŘENO tímto krokem. C01a/G0/G1 stále nepřijato.

### 2026-09-15 21:09 CEST — Aktualizace opravené aplikace na iPhone

Hotovo:

- Po Mílově potvrzení připravenosti aktualizována aplikace na připojeném iPhonu 14 Plus a úspěšně spuštěna. Instalovaná verze zahrnuje opravy průběhu, přerušení a hlášení chyb poslechu.

Rozhodnutí:

- Aktualizace stejného bundle bez odinstalace; před zahájením potvrzen zastavený záznam i poslech. Nahrávání nebylo spuštěno.

Další krok:

- V otevřeném Caminu přehrát existující vzorek a ověřit běžící čas, modrý průběh, Stop a opakované přehrání. Potom doplnit metadata neutrálních vzorků a první odmítnutí oprávnění; C01b nezahajovat.

Navrhované další kroky:

- Po dílčím retestu dokončit fyzickou přejímku C01a; nová etapa není tímto krokem zahájena.

Technický důkaz:

- Zdroj aplikace 259b7476, Camino Audio 0.1.0 (1). Znovu ověřen strict podpis, platný profil a shoda zařízení. Devicectl install i launch: exit 0 / success; inventář potvrzuje přesný bundle aplikace.
- Soukromé identifikátory, instalační doklady a runtime média zůstávají mimo Git. Zachování a poslech konkrétních vzorků po této aktualizaci čekají na potvrzení uživatele; C01a/G0/G1 stále otevřené.

### 2026-09-15 21:18 CEST — Míla potvrdil opravu přehrávání na iPhonu

Hotovo:

- Míla potvrdil, že nové přehrání podle zadaného postupu po Stop začíná od začátku, a následně potvrdil běžící čas i modrý průběh. Regrese z původního snímku je uživatelsky ověřena jako opravená na telefonu.

Rozhodnutí:

- Zkoušku opraveného průběhu neopakovat bez nového důvodu. Celé C01a zatím neuzavírat kvůli zbývajícím dokladům a prvnímu odmítnutí oprávnění.

Další krok:

- Při dostupném odemčeném telefonu doplnit délku a velikost neutrálních vzorků; potom provést první odmítnutí systémové žádosti o mikrofon na samostatné testovací instalaci podle T025. C01b nezahajovat.

Navrhované další kroky:

- Po dokončení těchto dokladů vyhodnotit přijetí C01a.

Technický důkaz:

- Uživatelské potvrzení v této konverzaci, iPhone 14 Plus / iOS 26.6.1, instalovaný zdroj 259b7476. Není to nové automatické měření ani přejímka systémových přerušení.
- Pokus o read-only inventář souborových metadat v kontejneru Camino přes devicectl skončil outcome timeout / exit 2. Délky a velikosti nebyly získány; žádný zvukový soubor se nekopíroval. Kód se neměnil, testy se neopakovaly.

### 2026-09-15 21:25 CEST — Připraven oddělený test mikrofonu, čeká obnovení spojení

Hotovo:

- Sestaven a podepsán Camino Test se samostatným bundle cz.pythonmf.camino.audio.permissioncheck; původní Camino ani jeho úložiště se neměnily. Testovací instalace zatím nezačala.

Rozhodnutí:

- Míla zadal pokračování přejímky a potvrdil připravený telefon. T025 používá novou samostatnou instalaci, aby nebylo nutné odinstalovat původní aplikaci s nahrávkami.

Další krok:

- Po odpojení a opětovném připojení kabelu ověřit živé vývojové spojení s odemčeným iPhonem. Potom dokončit čtení metadat a instalaci připraveného Camino Test pro první odmítnutí mikrofonu; C01b nezahajovat.

Navrhované další kroky:

- V Camino Test ručně odmítnout první systémovou žádost, později povolit mikrofon a ověřit nový vědomý Start. Do té doby T025 neoznačovat za PASS.

Technický důkaz:

- Samostatný Debug build ze zdroje 0fbfd0b3: xcodebuild exit 0, strict codesign exit 0; bundle a jméno ověřeny z Info.plist. Profil do 2026-09-22 21:20 CEST; účty, podpisové identity a balíček zůstávají mimo Git.
- Telefon v inventáři connected, ale živé details/apps skončily timeoutem. Opakovaný nerekurzivní inventář metadat: com.apple.mobiledevice / -402653181, Failed to allocate RSD device. Bez výpisu médií, bez kopírování audia, bez instalace či spuštění nové aplikace.
- Míla dostal požadavek na odpojení/připojení kabelu a ponechání telefonu odemčeného. Odpověď dosud čeká. Kód se neměnil, testy jádra/UI se neopakovaly; oprava přehrávání zůstává uživatelsky potvrzená.

### 2026-09-15 21:37 CEST — Obnovené spojení, Camino Test nainstalován a metadata ověřena

Hotovo:
- Přepojení kabelu nepomohlo. Po Mílou provedeném restartu Xcode živý seznam aplikací uspěl; VPN ani síťová konfigurace se neměnily. Příčina původní chyby RSD není definitivně určena.
- Strict podpis, oddělený bundle a profil pro cílový telefon ověřeny. Instalace a spuštění Camino Test: exit 0 / success; původní Camino i Camino Test přítomné. Profil testovací aplikace platí do 22. září 21:20 CEST.
- Přečteno pouze 5 completed.json a inventář souborů původního Camina. Všech 5 byteCount odpovídá skutečné velikosti příslušného CAF; 48 kHz, mono, interrupted=false. Obsah audia se nepřenášel ani neposlouchal nástrojem.

Rozhodnutí:
- První odmítnutí oprávnění se zkouší v oddělené aplikaci. Instalace sama není fyzický PASS T025. Původní nahrávky zachovány; C01b nezahájeno.

Další krok:
- V nainstalovaném Camino Test dokončit ruční první odmítnutí mikrofonu, následné povolení v Nastavení a nový vědomý Start. T025 a přejímka C01a zůstávají otevřené; C01b nezahajovat.

Navrhované další kroky:
- Po uživatelském výsledku doplnit T025 a vyhodnotit rozsah přejímky C01a; dosavadní úspěšné testy neopakovat bez důvodu.

Technický důkaz:
- Soukromá instalační účtenka latest_permission_check.txt odkazuje na poslední xcode_restart pokus: apps/install/launch/apps_after, 5 metadata copy receipts a file_sizes; git-safe tabulka délek/velikostí je v C01a_AUDIO_PROTOTYPE_REPORT.md.
- Kód aplikace se neměnil; dřívějších 32 testů jádra a 2 UI testy nebyly opakovány. T025 první odmítnutí/povolení zatím uživatelsky NEOVĚŘENO; G0/G1 neuzavřeny.

### 2026-09-15 21:39 CEST — První odmítnutí mikrofonu uživatelsky potvrzeno

- Hotovo / důkaz: Míla po zadání Start → Nepovolovat v samostatném Camino Test potvrdil hlášení zakázaného mikrofonu a že nahrávání nezačalo. Tato část T025 je uživatelský PASS.
- Rizika: následné povolení, návrat bez automatického záznamu a nový vědomý Start v této instalaci dosud NEOVĚŘENO; celý T025 ani C01a nejsou uzavřeny.
- Další krok: V Camino Test povolit mikrofon přes Nastavení, vrátit se a ověřit, že nahrávání nezačne samo. Potom vědomým Start pořídit krátký neutrální vzorek, Stop a přehrát. T025 a přejímka C01a zůstávají otevřené; C01b nezahajovat.
- Kód se neměnil; dřívější testy jádra/UI se neopakovaly.

### 2026-09-15 21:43 CEST — T025 dokončeno, C01a přijato v prototypovém rozsahu

Hotovo:
- Míla potvrdil všechny tři zadané kroky v Camino Test: povolení mikrofonu, návrat bez automatického záznamu a vědomý Start krátkého vzorku, Stop a poslech. Spolu s předchozím odmítnutím jde o uživatelský PASS T025 v C01a.
- Vyhodnocena podmínka přijetí z C01a_AUDIO_PROTOTYPE.md: automatizovaná část A i fyzická část B doloženy, žádný známý otevřený FAIL vedoucí ke ztrátě/přepsání souboru či nevyžádanému mikrofonu. C01a přijato.

Rozhodnutí a rizika:
- Přijetí platí pro krátký foreground prototyp. T015 je splněno jen bez integrace Momentu; zámek, hovory, dlouhý běh a obnova při pádu během zápisu nejsou otestované funkce této etapy. G0/G1 zůstávají nesplněné.
- Nahrávky mají jen místní kopii a prototyp není pro ostrá média. Profil původní aplikace vyprší 22. září 18:16 CEST.

Další krok:
- C01a uzavřeno; vyčkat na zadání C01b pro audio pod zámkem, přerušení a vědomé pokračování. C01b automaticky nezahajovat.

Technický důkaz:
- Fyzické zkoušky: řízené uživatelské potvrzení z dnešní konverzace; výsledky a hranice důkazů v C01a_AUDIO_PROTOTYPE_REPORT.md.
- Dosavadních 32 Swift testů a 2 UI testy simulátoru PASS; podepsaný build, strict podpis, instalace/spuštění a metadata mají místní účtenky. Kód se nyní neměnil a testy nebyly bez nového důvodu opakovány.

### 2026-09-15 21:57 CEST — C01b zahájeno, připraven background audio prototyp

Hotovo:
- Výslovný pokyn Míly zahájit C01b; nové zadání a report. Verze 0.2.0 (2), background audio, explicitní navazující části a pauza, bezpečné omezení nového Start na popředí, lokální oznámení jen při již uděleném oprávnění.
- 47 Swift testů PASS, 2 UI testy PASS; snímek vizuálně zkontrolován. Finální podepsaný build a strict podpis PASS, správné UIBackgroundModes. Plná projektová brána PASS, 1684/1684 testů.

Rozhodnutí:
- Změna ochrany platí jen pro nově vytvořené soubory; legacy data bez migrace. Žádný push/deploy, nákup ani C01c. Fyzická přejímka se nenahrazuje simulátorem.

Rizika:
- C01b dosud nepřijato, skutečný zámek/hovor/30 minut/Bluetooth a T059 NEPROVEDENO. Jediný soubor na nepřerušený úsek může být při pádu neúplný; žádná garance záchrany nebo kontinuity segmentů.

Další krok:
- Po potvrzení připraveného telefonu nainstalovat 0.2.0 (2) bez odinstalace a provést nejdřív krátkou zkoušku zámku. Potom T016/T018–T021/T024/T059 podle zadání C01b; C01c nezahajovat.

Technický důkaz:
- C01b_BACKGROUND_AUDIO_REPORT.md, C01b_BACKGROUND_AUDIO.md a soukromá účtenka latest_c01b.txt. 15 nových testů C01b + 32 dosavadních; hlasy ani soukromé identifikátory nejsou v Gitu.

### 2026-09-15 22:03 CEST — C01b 0.2.0 nainstalováno a spuštěno na iPhonu

Hotovo / důkaz:
- Míla potvrdil připojený odemčený telefon a zastavené audio. Aktuální zdroje se shodují s buildovou účtenkou 0d2ae8e0; strict podpis a platný profil pro připojený telefon ověřeny.
- devicectl install a launch: exit 0 / success. Následný živý seznam aplikací potvrzuje hlavní bundle s verzí 0.2.0. Bez odinstalace.
- Inventář před/po: stejné relativní cesty a velikosti všech 15 souborů původních pěti pokusů. Jde o metadata, nikoli porovnání obsahu či hashů; audio se nekopírovalo.

Otevřeno / rizika:
- Míla dostal postup krátkého offline testu zámku; výsledek dosud čeká. Instalace není PASS fyzického zámku, hovoru, Bluetooth ani 30minutového záznamu. C01b/G0/G1 nepřijato; C01c nezahájeno.

Další krok:
- Dokončit krátkou offline zkoušku zámku v nainstalované verzi 0.2.0 (2): asi 30 s pod zámkem se slyšitelným počítáním, Stop a celý poslech. Potom T016/T018–T021/T024/T059; C01c nezahajovat.

Ověření:
- Kód se neměnil; dřívějších 47 Swift testů, 2 UI testy a plná brána 1684 testů nebyly opakovány. Soukromé instalační účtenky jsou pod latest_c01b.txt / latest_install.txt.

### 2026-09-15 22:15 CEST — Krátký funkční test zámku potvrzen

Hotovo:
- Míla potvrdil nahrávání během zámku, pokračování po odemčení a přehrání záznamu v hlavním Camino Audio 0.2.0 (2). Krátké funkční ověření zámku: PASS podle uživatele.

Rozhodnutí:
- Žádné nové rozhodnutí. C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.

Další krok:
- Provést T016: 30 minut záznamu převážně pod zámkem, průběžné neosobní zvukové značky, Stop a celý poslech; doplnit délku/velikost z metadat. Potom T018–T021/T024/T059; C01c nezahajovat.

Navrhované další kroky:
- Po T016 ověřit dostupná sluchátka a přerušení hovorem/změnou vstupu; poté zbývající scénáře C01b.

Technický důkaz:
- Uživatelské potvrzení z fyzického telefonu po instalaci 0.2.0. Přesná délka, velikost, úplnost poslechu a offline režim nejsou touto odpovědí samostatně doloženy; metadata nového vzorku ani aktuální verze iOS nebyly v tomto kroku čteny. Audio zůstalo na telefonu.
- Kód beze změn; automatické testy se neopakovaly. Krátká zkouška neuzavírá 30minutový T016, hovor, sluchátka ani ochranu po restartu.

### 2026-09-15 22:17 CEST — Konec dne, předání a schválené p+n

Hotovo:
- C01a přijato; C01b 0.2.0 (2) nainstalováno. Míla potvrdil krátký test zámku, pokračování po odemčení a přehrání. Dnešní práce je přerušená, 30minutový T016 nebyl proveden.

Rozhodnutí:
- Míla výslovně zadal ukončení dne a p+n celého čekajícího balíčku. Oprávnění zahrnuje tento závěrečný zápis, push na main a řízené nasazení do Cockpitu.
- C01b/G0/G1 zůstávají otevřené, C01c nezahájeno. Testy na telefonu pokračují až při příštím návratu.

Další krok:
- Příště navázat 30minutovým T016 v Camino Audio: režim Letadlo a vypnutá Wi-Fi, převážně zamčený telefon, průběžné hlasové značky, Stop, celý poslech a délka/velikost.

Navrhované další kroky:
- Potom dostupná sluchátka, přerušení hovorem/změnou vstupu a zbývající scénáře C01b.

Technický důkaz:
- 47 Swift testů a 2 UI testy PASS; krátký fyzický test potvrzen uživatelem. Přesná délka/velikost krátkého vzorku a jeho offline režim samostatně nedoloženy.
- Doklad p+n určuje aktuální GitHub batch audit a kanonická simple-main deployment receipt: cílový commit, brána, nový proces, otisk a smoke. Při zápisu tohoto předání p+n ještě probíhá; starší nasazení není důkaz výsledku.
- Profil hlavní aplikace do 2026-09-22 18:16 CEST; audio pouze na telefonu, bez ověřené další kopie. Žádná soukromá média v balíčku.

### 2026-09-16 13:43 CEST — T016 PASS podle Míly

Hotovo:
- Přibližně 30:16 nahrávání v režimu Letadlo, převážně pod zámkem, proběhlo bez problému a celý záznam se přehrál. T016 je podle uživatelského fyzického testu PASS.
- Přehrávání při zamčené obrazovce neběželo; background přehrávání není kritériem T016.

Rizika:
- Velikost souboru nebyla sdělena. Dnešní zpráva znovu neověřila verzi aplikace, model telefonu ani iOS; navazuje na evidovaný kontext 0.2.0 (2), iPhone 14 Plus / iOS 26.6.1.
- C01b/G0/G1 zůstávají otevřené, C01c nezahájeno. Audio je pouze na telefonu.

Další krok:
- T018 s dostupnými sluchátky, potom T019–T021/T024/T059.

Technický důkaz:
- Uživatelské potvrzení z fyzického telefonu; žádná média ani soukromý obsah nebyly přeneseny. Kód beze změn, automatické testy se neopakovaly.

### 2026-09-16 19:46 CEST — T018 PASS, T019 dílčí důkaz

Hotovo:
- T018 PASS podle Míly: AirPods jako aktivní mikrofon, stání i chůze pod zámkem, bez výpadků a celý poslech OK. Vítr nebyl přítomen.
- T016 opraven živými technickými metadaty na 30:24,406 a 175 147 072 B.
- Telefonát ukončil první část jako přerušenou; vědomé Pokračovat vytvořilo samostatný soubor stejné session s evidovanou pauzou. Grafické seskupení je správné, nejde o fyzické slepení médií.
- Pozdější záznam mikrofonem iPhonu byl samostatná nová session; v kapse byl podle Míly tišší a méně kvalitní.

Rizika:
- Úplný T019 a T020 čekají. T019 vyžaduje příchozí hovor ignorovaný i přijatý; T020 změnu skutečně aktivního vstupu během běžícího záznamu. Vítr neověřen, C01b/G0/G1 otevřené, C01c nezahájeno.

Další krok:
- Dokončit T019, potom T020–T021/T024/T059.

Technický důkaz:
- Připojený iPhone 14 Plus, Camino Audio 0.2.0 (2); CoreDevice inventář a pouze technické JSON účtenky. Žádný CAF ani jeho obsah se nekopíroval či poslouchal. Kód beze změn.

### 2026-09-16 20:02 CEST — Automatický návod k dalšímu testu

Rozhodnutí:
- Po každém Mílou oznámeném výsledku fyzického testu Adam bez další žádosti vyhodnotí stav, řekne, zda je potřeba vývoj, a rovnou poskytne podmínky, přesný postup a kritéria PASS následujícího neprovedeného testu.
- Při shodě s návrhem se kód nemění jen proto, že test skončil. Při FAIL se nejdřív zaznamená přesný projev, potom se opraví C01b a zopakuje dotčený scénář. C01c se nezahajuje.

Další krok:
- Dokončit T019 příchozím běžným telefonním hovorem jednou ignorovaným a jednou přijatým; potom automaticky předat T020.

Technický důkaz:
- Pouze projektový zápis pravidla; kód aplikace ani soukromá data se neměnily.

### 2026-09-16 20:25 CEST — T019 PASS

Hotovo / důkaz:
- Míla potvrdil PASS ignorovaného i přijatého příchozího hovoru: obě části přehratelné, nic z hovoru v audu a žádné samovolné pokračování.
- Technická metadata potvrzují dvě přerušené první části a jejich samostatná vědomá pokračování stejné session, s pauzami 43,153 s a 112,272 s; všechny čtyři části jsou 48 kHz mono. Žádný CAF se nekopíroval ani neposlouchal.

Rozhodnutí a rizika:
- Chování odpovídá návrhu C01b; oprava ani nový build nejsou potřeba. T020–T021/T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.

Další krok:
- Provést T020 změnou skutečně aktivního vstupu během běžícího záznamu; potom automaticky předat T021.

### 2026-09-16 20:39 CEST — T020 PASS

Hotovo / důkaz:
- Odpojení aktivních AirPods přerušilo záznam; všechny části jsou podle Míly přehratelné, vědomé pokračování použilo mikrofon iPhonu a nic se samo neobnovilo. AirPods se znovu staly skutečným vstupem až při dalším vědomém spuštění.
- Metadata potvrzují tři samostatné části jedné session, dvě systémová přerušení a dvě explicitní continuation s pauzami 28,002 s a 90,312 s. Žádný CAF se nekopíroval ani neposlouchal.

Rozhodnutí a rizika:
- T020 PASS; oprava ani nový build nejsou potřeba. Pouhé Bluetooth připojení není důkaz aktivní route. T021/T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.

Další krok:
- Provést T021 v prototypovém rozsahu; video/Moment patří až do C04. Potom automaticky předat T024.

### 2026-09-16 21:27 CEST — T021 PASS v rozsahu C01b prototypu

Hotovo / důkaz:
- Míla potvrdil blokaci přehrávače a druhého recorderu, pokračování stejné Úvahy po návratu z jiné aplikace, růst času a celý poslech jedné nepřerušené části.
- Metadata potvrzují poslední Úvahu 56,350 s, 48 kHz mono, `interrupted=false`, bez continuation. Dřívější samostatný přípravný pokus byl oddělen. Žádný CAF se nekopíroval ani neposlouchal.

Rozhodnutí a rizika:
- T021 PASS v rozsahu C01b prototypu; úplný test videa/Momentu se zopakuje v C04. Oprava ani nový build nejsou potřeba. T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.

Další krok:
- Provést T024, potom automaticky předat T059.

### 2026-09-16 21:43 CEST — v0.5, U15 a Viewer readiness

Hotovo / důkaz:
- Ověřený původní balíček v0.5 je v `camino`; 6/6 manifestovaných souborů a lokální ZIP odpovídají Downloads. Novější U15 dodatek odstraňuje významový rozpor bez změny původního balíčku.
- Read-only audit potvrdil Tailscale online, Serve HTTPS na živý Cockpit bez Funnel, smoke 5/5, AC `sleep=0` a FileVault zapnutý.

Rozhodnutí a rizika:
- Celé `Do deníku` je po synchronizaci Viewer-eligible pro Janu. Samostatná Úvaha je výchozím stavem `Jen pro mě`; `Vložit do deníku` je vědomá revizní akce.
- Viewer a U15 nejsou implementované v runtime. U15 patří do C03/C04, Viewer do C08c–C08f. C01b prototyp a jeho data zůstaly beze změny; G8 NEPROVEDENO.

Další krok:
- Provést T024, potom T059; C01c nezahajovat před uzavřením C01b.

### 2026-09-16 21:48 CEST — Oprava bezpečného profilového syncu

Hotovo / důkaz:
- Preflight workspace používá atributy přijímaného `FETCH_HEAD`; test reprodukuje nový `.gitattributes` a Markdown hard break v jednom commitu. Prošlo 192 souvisejících testů a rychlá kontrolní brána.

Rozhodnutí a rizika:
- Nejde o vypnutí kontroly whitespace. Zůstávají kontroly čistoty, povolených cest, mazání, divergence a fast-forward-only.

Další krok:
- Po commitu zopakovat dorovnání čistých profilů; v Caminu pokračovat T024.

### 2026-09-16 22:41 CEST — T024 PASS

Hotovo / důkaz:
- Míla potvrdil očekávaný relaunch po nuceném ukončení aplikace za rozpracované Úvahy. Snímek ukazuje `Připraveno` 00:00, vědomý `Start`, jednu neověřenou položku a dostupné přehrání zachovaných částí.
- CoreDevice inventář a malé JSON účtenky potvrzují dokončenou session 25,093 s + continuation 2,254 s a nový samostatný pokus s `started.json`, ale bez `completed.json`. Žádný CAF se nekopíroval ani neposlouchal.

Rozhodnutí a rizika:
- T024 PASS; oprava ani nový build nejsou potřeba. Nuceně ukončený pokus byl samostatná nová Úvaha, ne continuation, ale splňuje kanonická kritéria T024.
- Důkaz nezahrnuje záchranu otevřeného CAF, segmentový journal ani 60s limit ztráty C01c. T059 a širší G0/G1 zůstávají otevřené.

Další krok:
- Provést T059; C01c nezahajovat před uzavřením C01b.

### 2026-09-16 23:09 CEST — první T059: ochrana PASS, audio FAIL

Hotovo / důkaz:
- Před prvním odemknutím po restartu byl telefon pro vývojové služby `unavailable`; obsah aplikace se nečetl. Po odemknutí Camino ukázalo `Připraveno 00:00`, nic se samo nespustilo, počet neúplných zůstal 1 a testovací soubor byl přehratelný.
- Míla během zámku mluvil, ale tato část nebyla v poslechu slyšet. Metadata potvrzují jeden souvislý dokončený Komentář 53,567 s, 5 146 528 B, 48 kHz mono, `interrupted=false`. Žádný CAF se nekopíroval ani neposlouchal nástrojem.

Rozhodnutí a rizika:
- T059 ochrana/restart PASS, audio část FAIL. Souvislý mediální čas neprokazuje slyšitelný signál a příčina zatím není známá.
- Protože T016 pod zámkem dříve prošel, kód ani build se před řízenou reprodukcí nemění. Při opakovaném FAIL následuje diagnostika a oprava C01b; C01c zůstává nezahájeno.

Další krok:
- Zopakovat pouze audio část T059 s potvrzeným Mikrofonem iPhonu, telefonem na stole a přesnými hlasovými značkami před zámkem, pod zámkem a po odemčení.

### 2026-09-16 23:21 CEST — T059 PASS po opakování; C01b přijato

Hotovo / důkaz:
- Všechny značky před zámkem, tři pod zámkem a po odemčení byly podle Míly slyšitelné; jedna nepřerušená část, nic nečekaného.
- Metadata potvrzují dokončený Komentář 107,801 s, 10 352 992 B, 48 kHz mono, `interrupted=false`, bez continuation. Žádný CAF se nekopíroval ani neposlouchal nástrojem; název vstupu nebyl ve výsledné odpovědi zopakován.

Rozhodnutí a rizika:
- T059 PASS po řízeném zopakování; C01b přijato v prototypovém rozsahu. Oprava ani nový build nejsou potřeba.
- První 53,567s pokus s neslyšitelným vysloveným úsekem pod zámkem se nezopakoval a zůstává evidovaný jako nevysvětlené pozorování. C01c a G0/G1 nejsou uzavřené ani automaticky zahájené.

Další krok:
- Vyčkat na výslovný pokyn k C01c. T022 spustit až na jeho novém buildu, nikoli na 0.2.0.

### 2026-09-17 07:59 CEST — C01c 0.3.0 nainstalováno

Hotovo / důkaz:
- Segmentový journal, 55s checkpoint, obnova platných částí a sekvenční přehrání jsou implementované. Legacy C01a/C01b se nemigruje ani nepřepisuje.
- 52/52 Swift testů, 2/2 UI testy, podepsaný build a strict podpis PASS. První UI runner skončil před bootstrapem; čisté opakování prošlo a snímek byl vizuálně v pořádku.
- Instalace/spuštění na iPhone PASS. Před/po přesně 111 položek a shodný hash relativních cest/velikostí; žádný CAF kopírován ani poslouchán.
- Plná projektová brána PASS, 1685/1685 testů. První průchod zasáhlo jediné nesouvisející časovací selhání; cílené opakování 1/1 a následující celý průchod prošly.

Rozhodnutí a rizika:
- C01c je zahájené, ne přijaté. Fyzické T022/T023 musí ověřit skutečný input, zámek, pád a slyšitelnou kontinuitu přechodů.
- Otevřený konec se nikdy nevydává za úplný; plný databázový T061 zůstává C05a.

Další krok:
- T022 na 0.3.0: souvislý neutrální záznam nejméně 2:15, značky kolem checkpointů, nucené ukončení, relaunch bez mikrofonu a poslech zachovaného rozsahu.

### 2026-09-17 11:32 CEST — Oprava pádu C01c při Start

Hotovo / důkaz:
- Pět shodných crash reportů ukazuje `SIGTRAP` v `_swift_task_checkIsolatedSwift` uvnitř tap callbacku. Build 3 zdědil `MainActor` do callbacku spouštěného na real-time audio frontě.
- Build 0.3.0 (4) vytváří callback mimo actor izolaci. 52/52 Swift testů, 2/2 UI testy, oba arm64 buildy, strict podpis, rychlá statická brána, instalace a launch PASS.
- Všech 136 položek před instalací zůstalo po instalaci i launchi shodných v cestě, typu a velikosti. Pět nedokončených pokusů se nemazalo; žádný CAF se nekopíroval ani neposlouchal.

Rozhodnutí a rizika:
- Swift 6 strict concurrency zůstává zapnuté. Automatické ověření není fyzický důkaz skutečného tap callbacku; C01c zůstává rozpracované.

Další krok:
- Na buildu 4 provést krátký neutrální Start/Stop a celý poslech. Při PASS pokračovat T022; při FAIL znovu nemačkat Start a získat nový crash report.

### 2026-09-17 11:46 CEST — Krátký fyzický smoke buildu 4 PASS

Hotovo / důkaz:
- Míla potvrdil Start bez pádu, růst času i ukazatele a přehrání nového záznamu po Stop.
- Dokončený Komentář má 10,7 s, 2 058 496 B, 48 kHz mono, jeden segment, bez přerušení, recovery a mezery. Všech 136 předchozích položek zůstalo shodných; přibylo sedm očekávaných položek. Žádný CAF se nekopíroval ani neposlouchal nástrojem.

Rozhodnutí a rizika:
- Oprava pádu je fyzicky potvrzená; před T022 není potřeba další vývoj. C01c zůstává rozpracované do T022/T023.

Další krok:
- Provést první průchod T022 na 0.3.0 (4), potom vyhodnotit opakování v jiné fázi otevřeného segmentu.

### 2026-09-17 13:12 CEST — T022/T023 PASS; C01c přijato

Hotovo / důkaz:
- T022 prošlo ve dvou odlišných fázích otevřené části. Po obou pádech se mikrofon sám nespustil, obnovené částečné nahrávky byly pravdivě označené a zachovaný rozsah přehratelný. První průchod ukázal tři části a 02:18 zachovaného rozsahu.
- T023 prošlo souvislým nejméně čtyřminutovým poslechem. Značky před a po čtyřech 55s hranicích byly podle Míly slyšet jednou, ve správném pořadí a bez mezery, opakování či useknutí.

Rozhodnutí a rizika:
- C01c 0.3.0 (4) je přijato v prototypovém rozsahu; další oprava ani nový build nejsou potřeba.
- G0/G1/G8, dlouhodobá terénní spotřeba a plný databázový T061 zůstávají otevřené. Telefon nebyl při závěrečném zápisu připojený; poslech T023 je doložen Mílou, ne technickým čtením audia.

Další krok:
- Vyčkat na výslovný pokyn k C02a; C01c dále nerozšiřovat.

### Automatický checkpoint 2026-09-17 14:19 CEST

- Pracovní proud: `project-camino`
- Hotovo: Lokální C02a přijímač bezpečně ověřuje syntetický soubor serverovým hashem bez přepisu či duplicit; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (9): `Samantha_Agent/camino/README.md`, `Samantha_Agent/camino/docs/DECISIONS.md`, `Samantha_Agent/memory/projects/camino.md`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/camino_receiver.py`, `Samantha_Agent/camino/docs/C02a_SYNTHETIC_RECEIVER_REPORT.md`, `Samantha_Agent/camino/tasks/C02a_SYNTHETIC_RECEIVER.md`, `Samantha_Agent/tests/test_camino_receiver.py`
- Commit: `Implement Camino C02a synthetic receiver`
- Další krok: Po checkpointu autorizovat privátní HTTPS smoke přes Tailscale Serve se syntetickým souborem

### 2026-09-17 15:19 CEST — C02a privátní HTTPS smoke PASS

Hotovo:
- Dočasná privátní HTTPS cesta Tailscale Serve předala syntetický soubor loopback přijímači; server ověřil délku a SHA-256 a bezpečně zachoval právě jeden výsledek.
- Chybný hash i konflikt byly odmítnuty, identický retry nevytvořil duplicitu. Cockpit zůstal dostupný, Funnel vypnutý a původní Serve konfigurace byla přesně obnovena.

Rozhodnutí:
- C02a je přijato v prototypovém rozsahu. Produkční cíl zůstává FastAPI v samostatném prostředí; dočasný standard-library receiver se nepovyšuje na trvalou službu.

Další krok:
- Vyčkat na výslovný pokyn k C02b.

Navrhované další kroky:
- V C02b ověřit velký soubor, části, přerušení a skutečný iOS klient na cizí síti; T043/T048/T051 zatím ponechat otevřené.

Technický důkaz:
- Tailnet HTTPS health 200; upload 201; retry 200 s `created=false`; chybný hash 422; konflikt 409; úložiště 1 objekt + 1 účtenka. Kořen Cockpitu 200, Funnel pouze tailnet, Serve stav po testu shodný s výchozím.

### 2026-09-17 16:13 CEST — C02b zahájeno; části a pravdivá fronta lokálně ověřené

Hotovo:
- Receiver bezpečně eviduje 8MiB části, po přerušení vrací chybějící indexy a finalizuje jediný objekt až po serverové kontrole celkové délky a SHA-256.
- Swift model po relaunchi používá serverovou pravdu, bez sítě čeká, 100 % bytů drží jako `verifying` a mobilní povolení nepřenáší na novou dávku.

Rozhodnutí:
- První checkpoint C02b zafixoval serverový kontrakt a čistou reconciliaci. Skutečný `URLSession` klient a fyzické scénáře navážou; žádný veřejný fallback nevzniká.

Další krok:
- Vytvořit nativní iOS harness se souborovými úlohami `URLSession`, trvalou frontou a nejvýše dvěma připravenými částmi.

Navrhované další kroky:
- Po buildu a instalaci provést T043 a odděleně T047–T050 přes privátní HTTPS na fyzickém telefonu a cizí síti.

Technický důkaz:
- Python C02b 9/9, Swift 9/9, C02a regrese 10/10 a plná projektová brána 1704/1704 PASS. Fyzický iPhone test NEPROVEDENO; push ani nasazení neproběhly.

### 2026-09-17 16:53 CEST — C02b druhý checkpoint; iOS harness připraven k instalaci

Hotovo:
- Samostatná aplikace `Camino Transfer Test` vytváří pouze syntetickou dávku 96 MiB + 257 B. Má trvalý journal, Keychain token, jednu background `URLSession`, souborové uploady a nejvýše dvě připravené 8MiB části.
- Po relaunchi znovu porovnává server, 100 % bytů nevydává za ověření a mobilní povolení váže jen na aktuální dávku. Serverový snapshot s cizími či chybějícími indexy odmítá.

Rozhodnutí:
- Harness má vlastní bundle ID a nepřistupuje k Fotkám, mikrofonu ani kontejneru Camino Audio. Force quit neslibuje background pokračování; po ručním návratu proběhne reconciliace.

Další krok:
- Připojit a odemknout iPhone, lokálně podepsat a nainstalovat harness bez odinstalace Camino Audio; potom provést první řízený T043 přes privátní HTTPS.

Navrhované další kroky:
- Po T043 samostatně provést T047–T050 včetně zámku, force quit, cizí sítě, jednorázových mobilních dat a zadrženého serverového ověření.

Technický důkaz:
- Python C02b 10/10, Swift core 18/18, C02a regrese 10/10, UI simulátoru 1/1, nepodepsaný arm64 iOS build a plná projektová brána 1705/1705 PASS.
- Instalace, privátní HTTPS běh i fyzické T043/T047–T050 jsou NEPROVEDENO. Push, nasazení ani Tailscale/Funnel změna neproběhly.

### 2026-09-17 19:58 CEST — C02b nainstalováno; T043 čeká na potvrzení trasy

Hotovo:
- `Camino Transfer Test` 0.4.0 (1) byl automaticky podepsán místním vývojovým týmem, strict ověřen, nainstalován a po odemčení spuštěn na iPhonu 14 Plus / iOS 26.6.1. Samostatný bundle neodinstaloval ani neměnil Camino Audio.
- Přidán registrovaný vratný workflow pro jedinou privátní Serve cestu `/camino-c02b`, loopback receiver, bezpečné předání URL/token přes schránku, read-only důkaz a přesné ukončení se srovnáním původní konfigurace.

Rozhodnutí:
- Síťový zápis se nespustí ad hoc. Přesný `camino_c02b_t043_start` čeká na samostatné potvrzení po zobrazeném náhledu. Funnel se nezapíná a kořen Cockpitu se nesmí změnit.

Další krok:
- Po potvrzení spustit workflow, vložit URL a token do otevřeného harnessu, vytvořit syntetickou dávku a řízeně přerušit a obnovit síť u T043.

Navrhované další kroky:
- Po serverovém `verified` ověřit jediný objekt/účtenku, shodnou délku/hash a obnovu chybějících částí; potom dočasnou trasu registrovaně ukončit.

Technický důkaz:
- Podepsaný generic iOS build a `codesign --verify --deep --strict` PASS; instalace i launch PASS. Vývojový profil harnessu platí do 24. září 2026.
- Cílené workflow testy 4/4; související sada 30/30; plná projektová brána 1709/1709 PASS. Serve/Funnel zůstaly po read-only auditu beze změny; fyzické T043/T047–T050 jsou NEPROVEDENO.

### 2026-09-17 20:08 CEST — První T043 start bezpečně vrácen; entrypoint opraven

Hotovo:
- Potvrzený `camino_c02b_t043_start` skončil před otevřením receiver portu. Přímé spuštění souboru z `app/` vložilo tento adresář na začátek importní cesty a místní `app/email` zastínilo standardní Python balíček `email`.
- Fail-closed rollback odebral `/camino-c02b`, ukončil receiver a nevytvořil aktivní běh. Živý audit potom potvrdil jediný původní Serve handler, žádný listener na portu 8765 a žádnou aktivní Camino cestu.
- Receiver se nyní spouští modulově přes `python -m app.camino_chunk_receiver`; vlastnictví procesu kontroluje stejný modulový podpis a nový regresní test ověřuje, že entrypoint načte standardní `email` správně.

Rozhodnutí:
- Původní potvrzení se po opravě nepoužije automaticky. Opakování stejného síťového workflow vyžaduje nový náhled a nové samostatné potvrzení.

Další krok:
- Znovu zobrazit přesný `camino_c02b_t043_start`; po potvrzení připravit URL/token a pokračovat fyzickým T043.

Technický důkaz:
- Regresní test modulu PASS; cílená sada 31/31 a plná projektová brána 1710/1710 PASS. T043 zůstává NEPROVEDENO, Funnel ani kořen Cockpitu se nezměnily.

### 2026-09-17 20:15 CEST — Druhý start bezpečně vrácen; systémový CA trust doplněn

Hotovo:
- Druhý start potvrdil opravený receiver, ale privátní HTTPS smoke skončil na `CERTIFICATE_VERIFY_FAILED` v Python.org instalaci. Workflow znovu odebralo `/camino-c02b`, ukončilo receiver a nezanechalo aktivní běh.
- Podle LL-025 a existující macOS zkušenosti používá kontrolní `urllib` explicitní `/etc/ssl/cert.pem`; ověřování certifikátu zůstává zapnuté. Přímý tailnet Cockpit health s tímto kontextem vrátil HTTP 200.

Rozhodnutí:
- Přesný příkaz a jeho zápisový rozsah zůstaly stejné; Mílovo potvrzení se použije k dokončení opraveného startu bez třetí žádosti.

Další krok:
- Po checkpointu znovu spustit registrovaný start, vložit zkopírovanou URL a následně token do harnessu a pokračovat T043.

Technický důkaz:
- TLS regresní test zachovává `ssl.create_default_context` a načítá systémový CA bundle. Cílená sada 32/32 a plná projektová brána 1711/1711 PASS; Serve má opět jen původní handler a port 8765 neposlouchá.

### 2026-09-17 21:01 CEST — T043 PASS; fyzický zádrhel fronty opraven

Hotovo:
- T043 fyzicky přerušil upload Letovým režimem při klientských 5 %, 0/13 potvrzených částech a 2/2 připravených. Mac doložil relaci `uploading` s 0/13 přijatými částmi a bez nového finálního objektu.
- Po návratu sítě bylo přijato 13/13 částí; pro testovaný Asset vznikl jediný objekt a účtenka, oba 100 663 553 B, se shodným SHA-256. T043 je PASS v rozsahu syntetického C02b experimentu.
- Opakované ruční klepnutí odhalilo, že callback během běžící reconciliace mohl být zahozen. Build 0.4.0 (2) používá koaleskující bránu; je strict podepsaný, nainstalovaný a spuštěný. Následná celá dávka doběhla po automatickém síťovém impulsu bez dalšího klepnutí.

Rozhodnutí:
- Dostupná povolená Wi-Fi může spustit přenos automaticky; `Synchronizovat nyní` je ruční provozní záloha. Souběžné impulsy se koaleskují místo tichého zahození.

Další krok:
- Po samostatném potvrzení registrovaně ukončit T043 receiver a Serve cestu; poté odděleně provést T047 se zámkem a force quit.

Technický důkaz:
- Živý receiver eviduje tři rozdílné ověřené syntetické Assety/účtenky, každý 13/13 a 100 663 553 B; celkem 301 990 659 B. Funnel je vypnutý.
- Swift 19/19, T043 ovladač + oba receivery 28/28 a UI 1/1 PASS; podepsaný build 2, strict podpis, instalace a launch PASS. Plná projektová brána 1713/1713 PASS.


### 2026-09-17 21:23 CEST — T043 ukončeno; oddělené T047 připraveno

Hotovo:
- Potvrzený stop odebral jen `/camino-c02b`, zastavil pouze vlastněný T043 receiver a doložil přesnou obnovu původního Serve. Funnel zůstal vypnutý; tři relace jsou `verified` 13/13 a jejich tři objekty/účtenky zůstaly hashově shodné, celkem 301 990 659 B.
- Připravený T047 workflow používá vlastní soukromý stav a nový prázdný receiver. Read-only audit fail-closed ověřuje relace, stav poslední relace, každý přijatý chunk a finální objekty/účtenky. iOS build 0.4.0 (2) se neměnil.

Rozhodnutí:
- Zámek a force quit se provedou jako dvě různé dávky. Po force quit se nejprve zaznamená serverový mezistav a teprve potom proběhne ruční relaunch a klientská reconciliace.

Další krok:
- Po samostatném potvrzení spustit `camino_c02b_t047_start`, vložit novou URL/token a provést nejprve dávku se zámkem.

Technický důkaz:
- Živý T043 audit: `stopped`, receiver i cesta neaktivní, Funnel vypnutý, 3/3 relace ověřené a 39/39 částí. T047 audit: `INACTIVE`, žádný běh zatím nevznikl.
- T047/T043 workflow modul 11/11, související sada 37/37 a plná projektová brána 1716/1716 PASS.

### 2026-09-18 08:23 CEST — T047 PASS; relaunch obnovil chybějící části

Hotovo:
- První T047 dávka byla testována pod zámkem telefonu. Po odemčení UI pravdivě
  ukázalo mezistav a server dokončil všech 13 částí.
- U druhé dávky byl po přijetí 1/13 částí skutečně ukončen proces. Audit po
  20 s zůstal na 1/13 bez druhého objektu; po ručním relaunchi UI ukázalo
  15 %, 1/13, 1/2 a server doplnil jen chybějící části do 13/13.
- Živé potvrzení má 2 relace, 2 ověřené objekty/účtenky, každý 100 663 553 B,
  celkem 201 327 106 B. T047 je PASS v rozsahu syntetického C02b experimentu.

Rozhodnutí:
- T047 se uzavírá až registrovaným stopem po samostatném potvrzení; T048–T050
  zůstávají oddělené.

Další krok:
- Po potvrzení spustit `camino_c02b_t047_stop`, ověřit přesnou obnovu Serve a
  potom pokračovat T048–T050.

Technický důkaz:
- `receiver_alive=true`, `private_route_exact=true`, `funnel_enabled=false`,
  `object_count=2`, `receipt_count=2`, `verified_match=true`,
  `session_count=2`, `session_verified_count=2`, `latest_session_chunks=13/13`.
- Swift 19/19, T047/T043 workflow 11/11, související sada 37/37 a plná
  projektová brána 1716/1716 PASS. Push ani nasazení neproběhly.

### 2026-09-18 08:29 CEST — T047 ukončeno a Serve obnoveno

Hotovo:
- Registrovaný stop odebral pouze `/camino-c02b`, zastavil pouze vlastněný T047
  receiver a porovnal Serve s přesným stavem před testem.
- Funnel zůstal vypnutý. Dva ověřené objekty/účtenky, dvě relace a celkem
  201 327 106 B zůstaly zachované; syntetický důkaz se nemaže.

Další krok:
- T048–T050 zůstávají samostatné a fyzicky NEPROVEDENO.

Technický důkaz:
- Živý audit po stopu: `phase=stopped`, `receiver_alive=false`,
  `funnel_enabled=false`, `object_count=2`, `receipt_count=2`,
  `verified_match=true`, `session_count=2`, `session_verified_count=2`,
  `latest_session_chunks=13/13`.

### 2026-09-19 11:12 CEST — T048 připraveno; nejprve syntetické T049

Hotovo:
- Oddělené potvrzované workflow T048 a T049 mají vlastní soukromý stav a
  bezpečný start, kontrolu, token i stop. Žádný nový receiver ani Serve cesta
  nebyly spuštěny; T047 důkazy zůstávají zachované.
- `Camino Transfer Test` 0.4.0 (3) před mobilním grantem ukazuje jednu dávku
  o 100 663 553 B a upozornění na další bajty při retry. Všechny požadavky
  mají per-request síťovou politiku. Build 3 je podepsaný a nainstalovaný,
  Camino Audio zůstává nainstalované. Pokus o launch blokoval zámek iPhonu.

Rozhodnutí:
- Na Mílův pokyn půjde nejprve T049 bez cizí Wi-Fi, potom T048 při dostupné
  jiné Wi-Fi. Jde jen o změnu pořadí, nikoli o snížení akceptačních kritérií.

Další krok:
- Odemknout iPhone, ověřit launch buildu 3 a po samostatném potvrzení spustit
  registrované T049 workflow pro fyzickou syntetickou mobilní zkoušku.

Navrhované další kroky:
- Po T049 receiver/cestu registrovaně ukončit; T048 provést odděleně při jiné
  Wi-Fi včetně portálu, bude-li dostupný. T050 zůstává samostatné.

Technický důkaz:
- Swift 20/20, Python workflow 13/13, iOS UI 1/1, podepsaný iOS build a
  strict podpis PASS; plná projektová brána 1718/1718 PASS.
- Read-only T048/T049 `INACTIVE`; T047 `stopped`, receiver/cesta neaktivní,
  Funnel vypnutý, dva objekty/účtenky hashově shodné. Fyzické T048–T050
  NEPROVEDENO. Harness nepokrývá skutečné nové video pro plný T049.

### 2026-09-19 18:06 CEST — T050 fyzicky ověřeno a oba běhy ukončené

Hotovo:
- První syntetický průchod T050 doložil pouze konečné ověření; chybějící
  souběžný mezistav nebyl vydán za PASS. Po samostatném potvrzení byl běh
  zastaven bez smazání důkazu a vznikl nový oddělený běh.
- Ve druhém průchodu záznam iPhonu ukázal `Ověřuji` při 100 % a 13/13 v době,
  kdy server hlásil `verifying` bez objektu a účtenky. Poté iPhone přešel na
  `Ověřeno na Macu` a server vytvořil právě jeden hashově ověřený objekt a
  účtenku. T050 je PASS pouze v syntetickém C02b rozsahu.
- Potvrzený stop odebral jen vlastní T050 trasu a přijímač, přesně obnovil
  původní Serve a ponechal Funnel vypnutý. Dva soukromé běhy zůstaly zachované;
  video je mimo Git.

Rozhodnutí:
- Míla zvolil opakování kvůli chybějícímu důkazu přechodného stavu. Samovolný
  start po návratu z Ovládacího centra není odsouhlasené chování produktu;
  před další mobilní zkouškou se vyjasní, zda čerstvá dávka vyžaduje výslovný
  start, aniž by se oslabila obnova již rozpracovaného přenosu.

Další krok:
- T048 na cizí Wi-Fi podle připraveného postupu, až bude síť dostupná.

Navrhované další kroky:
- Samostatně vyřešit UX automatického startu a krátkého `Vyžaduje pozornost`
  před bezpečným retry; plné T049 se skutečně novým videem až v integrované
  aplikaci.

Technický důkaz:
- Server 17:58:22–17:58:36 CEST: `verifying`, 13/13, 0 objektů a účtenek;
  snímky soukromého videa v tomto okně: `Ověřuji`, 100 %, 13/13. Následně
  `verified`, jeden objekt/účtenka, 100 663 553 B, shodný SHA-256.
- Audit po stopu druhého běhu: `phase=stopped`, `receiver_alive=false`,
  `private_route_exact=false`, `funnel_enabled=false`, `session_count=1`,
  `session_verified_count=1`, `object_count=1`, `receipt_count=1`,
  `verified_match=true`. iPhone build 0.4.0 (3) se neměnil; předchozí
  automatická brána 1719/1719 PASS, v tomto kroku neopakovaná.
