# Camino

Aktualizováno: 2026-09-15 21:39 CEST
Pracovní proud: `project-camino` · typ Project · režim active · priorita 1.

## Cíl a hranice

Soukromý offline deník na iPhonu, bezpečné originály a osobní deník na Macu;
volitelný rodinný výběr a film až v dalších etapách. Jeden autor a jeden hlavní
editující iPhone. Web v P0 slouží pro čtení a stav, bez veřejného publikování.

## Aktuální stav

- C01a: oprava přehrávání verze 259b7476 potvrzena Mílou na iPhonu 14 Plus: běží čas i modrý průběh a nové přehrání po Stop začíná od začátku. Instalace/spuštění ověřeny; 32 testů jádra a 2 UI testy simulátoru prošly. Metadata 5 vzorků ověřena; první odmítnutí bez zahájení záznamu potvrzeno Mílou, zbývá návrat po povolení mikrofonu.
- Camino Test je samostatně nainstalovaný a spuštěný; oba bundle ověřeny v telefonu. Po restartu Xcode znovu fungují vývojové služby. Načtena metadata 5 vzorků a ověřena shoda velikostí CAF; audio se nekopírovalo. První odmítnutí mikrofonu s vysvětlením a bez nahrávání Míla potvrdil.
- Míla potvrdil funkční Komentář (čas, signál, uložení a celý poslech), Úvahu bez internetu, zachování a přehrání obou vzorků po úplném ukončení aplikace bez samovolného záznamu a správné hlášení zakázaného mikrofonu s funkčním záznamem po jeho povolení.
- Xcode 26.3 / iOS SDK 26.2: podepsaný Debug build CaminoAudio pro iPhone prošel (exit 0), `codesign --verify --deep --strict` exit 0. Jedna platná vývojová identita; profil platí do 2026-09-22 18:16 CEST. Výběr týmu je pouze v ignorovaném LocalSigning.xcconfig.
- Úplná přejímka C01a otevřená: oprava zobrazení je potvrzena na telefonu; metadata vzorků jsou ověřena, první odmítnutí systémového dialogu potvrzeno, zbývá následné povolení a vědomý Start. Mikrofon iPhonu doložen snímkem, doplňující Komentář uživatel přehrál. C01b nezahájeno.
- Restart a následný schválený úklid dokončeny. Před zahájením instalace bylo na SSD 85,79 GiB volných. Dřívější přesun USA neopakovat.
- Poslední doložené c+p+n: d573e90c, 1684 testů, smoke 5/5. Nový zápis ručních zkoušek vzniká po tomto nasazení.


## Zdroje a návaznost

- Kořen projektu: `camino/`, instrukce `camino/AGENTS.md`.
- Autoritativní podklady: `camino/CAMINO_podklady_v0.4/README_v0.4.md`,
  `CAMINO_funkcni_specifikace_v0.4.md`, `CAMINO_Codex_v0.4.md` a akceptační scénáře.
- Kanonický handoff: `memory/handoffs/workstreams/project-camino.md`.
- Kanonický TVBCP: `memory/tvbcp/workstreams/project-camino.md`.
- Původní balíček se nemění; nové auditní a vývojové výsledky patří mimo něj.
- Katalogové přidání samo neotevírá soukromé vlákno. To vznikne až při otevření projektu.

## Pevná pravidla

Originály jsou neměnné, bez automatického mazání. Offline záznam nečeká na síť,
GPS ani AI. „Do deníku“ je stále soukromé; „Jen pro mě“ vylučuje všechny filmy
a rodinné výstupy. Externí přepis není důkaz zálohy. Lidskou revizi AI nepřepíše.

## Rizika a otevřeno

- Bez funkčního Xcode buildu, podpisu a fyzické přejímky nelze prototyp označit za přijatý; G0/G1 nesplněné.
- Pouze krátké foreground audio; žádná segmentace, záchrana po pádu během zápisu ani pokračování pod zámkem.
- Vzorky v telefonu mají jen místní kopii, nejsou určeny pro ostrá média; žádná AI, síť, export nebo automatické mazání.
- Podepsaný build není instalace ani fyzická přejímka; vývojový profil je časově omezený. U01–U11 se neotevírají.

## Další krok

V Camino Test povolit mikrofon přes Nastavení, vrátit se a ověřit, že nahrávání nezačne samo. Potom vědomým Start pořídit krátký neutrální vzorek, Stop a přehrát. T025 a přejímka C01a zůstávají otevřené; C01b nezahajovat.

Historický doklad založení:
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
