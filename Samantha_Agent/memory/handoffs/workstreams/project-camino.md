<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

Aktualizováno: 2026-09-16 19:46 CEST

- T016 PASS: přesně 30:24,406, 175 147 072 B, 48 kHz mono, režim Letadlo, převážně pod zámkem a celý poslech OK. T018 PASS podle Míly: AirPods jako skutečný vstup, stání i chůze pod zámkem, bez výpadků; vítr neověřen.
- C01b zahájeno výslovným pokynem Míly; C01a zůstává přijaté. Prototyp 0.2.0 (2) je lokálně připraven pro background audio, přerušení a vědomé pokračování. Verze 0.2.0 je nyní nainstalovaná a spuštěná na iPhonu; inventář 15 původních souborů se před/po shoduje v cestách a velikostech.
- Běžící recorder přežije změnu scenePhase; nový Start/Pokračovat pouze v popředí. Přerušení ihned pozastaví vstup, ověří dostupnou část a nabídne Pokračovat/Ukončit. Pokračování vytváří novou část stejné session s evidovanou pauzou, bez přepisu předchozího média.
- Nové soubory mají completeUntilFirstUserAuthentication; původní C01a soubory se nemigrují ani nemění. Staré JSON podporuje volitelné continuation. Není to C01c segmentový journal ani garance 60s ztráty.
- Ověřeno 47/47 Swift testů, 2/2 UI testy simulátoru včetně snímku obrazovky, finální podepsaný iOS build a strict podpis; UIBackgroundModes=[audio]. Plná projektová brána PASS, 1684/1684 testů.
- Instalace/spuštění 0.2.0 PASS. Krátký test zámku, T016 a T018 PASS podle Míly. Odchozí hovor správně vytvořil přerušenou první část a vědomé pokračování jako druhý samostatný soubor stejné session; úplný T019 a T020–T021/T024/T059 čekají.
- Profil hlavní aplikace do 22. září 18:16 CEST. G0/G1 a terénní připravenost nesplněné; C01c nezahájeno. Původní nahrávky i samostatný Camino Test zůstávají zachované.

### Vzkaz pro pokračování

- Restart a následný schválený úklid dokončeny. Před zahájením instalace bylo na SSD 85,79 GiB volných. Dřívější přesun USA neopakovat.
- Instalace platformy i nepodepsaný build ověřeny. Dokončit T019 příchozím hovorem jednou ignorovaným a jednou přijatým; potom T020–T021/T024/T059. C01c nezahajovat.
- Starší c+p+n d573e90c je historické. Dnešní p+n zahrnuje celý balíček Camina a toto předání; výsledek určuje živý audit a kanonická deployment receipt.

### Rizika

- C01a přijato, ale širší brány G0/G1 a terénní připravenost zůstávají nesplněné.
- T016 a T018 potvrzeny; vítr, úplný T019 a další fyzické scénáře čekají. Segmentace a záchrana po pádu během zápisu patří do C01c.
- Vzorky v telefonu mají jen místní kopii, nejsou určeny pro ostrá média; žádná AI, síť, export nebo automatické mazání.
- Podepsaný build není instalace ani fyzická přejímka; vývojový profil je časově omezený. U01–U11 se neotevírají.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Camino

Nazev: Camino
Pracovni proud: project-camino
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-09-16 19:46 CEST

Co se resilo:
Implementace C01b: audio pod zámkem, přerušení a vědomé pokračování.

Co je hotove:
C01a přijato; implementace a instalace C01b, krátký test zámku, T016 a T018 potvrzeny Mílou; 47 testů jádra, 2 UI testy, podepsaný build a strict podpis. Detaily a hranice důkazů v reportu C01b.

Co neni hotove:
Úplný T019, T020–T021/T024/T059; C01c, G0/G1 a terénní připravenost.

Dalsi krok:
Dokončit T019 příchozím hovorem jednou ignorovaným a jednou přijatým. Potom T020–T021/T024/T059; C01c nezahajovat.

Navrhovane dalsi kroky:
Dokončit T019; potom T020–T021/T024/T059. C01c nezahajovat.

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
