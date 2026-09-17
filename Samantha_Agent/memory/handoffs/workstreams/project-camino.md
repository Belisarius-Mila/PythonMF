<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

Aktualizováno: 2026-09-17 11:32 CEST

- Autoritativní podklady jsou v0.5 + závazný dodatek U15. Původní v0.5 je importovaná beze změny a manifest 6/6 je ověřený. Celé `Do deníku` může po synchronizaci do soukromého Vieweru Jany; samostatná Úvaha vždy začíná `Jen pro mě` a vyžaduje vědomé `Vložit do deníku`.
- Viewer delta audit: Tailscale/Serve/Cockpit tvoří použitelný základ, Funnel je vypnutý, Cockpit smoke 5/5, AC nespí a FileVault je zapnutý. Camino backend/worker/Viewer, samostatná autorizace, záloha, restart a test Janiných zařízení chybějí; G8 NEPROVEDENO.
- Profilový fast-forward má opravený whitespace preflight: používá příchozí `.gitattributes`, bez globálního vypnutí kontroly; regresní test je zelený.
- T016 PASS: přesně 30:24,406, 175 147 072 B, 48 kHz mono, režim Letadlo, převážně pod zámkem a celý poslech OK. T018–T020, T024 a T059 PASS podle Míly. T021 PASS v rozsahu C01b prototypu; plná integrace se zopakuje v C04. T059 po restartu ochránil data a řízené opakování zachytilo všechny značky pod zámkem. Vítr neověřen.
- C01b zahájeno výslovným pokynem Míly; C01a zůstává přijaté. Prototyp 0.2.0 (2) je lokálně připraven pro background audio, přerušení a vědomé pokračování. Verze 0.2.0 je nyní nainstalovaná a spuštěná na iPhonu; inventář 15 původních souborů se před/po shoduje v cestách a velikostech.
- Běžící recorder přežije změnu scenePhase; nový Start/Pokračovat pouze v popředí. Přerušení ihned pozastaví vstup, ověří dostupnou část a nabídne Pokračovat/Ukončit. Pokračování vytváří novou část stejné session s evidovanou pauzou, bez přepisu předchozího média.
- Soubory vytvořené v C01b mají completeUntilFirstUserAuthentication; původní C01a soubory se nemigrují ani nemění. Staré JSON podporuje volitelné continuation. Tyto starší jednotlivé CAF samy nejsou C01c journal ani důkaz 60s cíle.
- Ověřeno 47/47 Swift testů, 2/2 UI testy simulátoru včetně snímku obrazovky, finální podepsaný iOS build a strict podpis; UIBackgroundModes=[audio]. Plná projektová brána PASS, 1684/1684 testů.
- C01b 0.2.0 (2) přijato v prototypovém rozsahu. Krátký test zámku a T016/T018–T021/T024/T059 PASS; T059 prošel po řízeném zopakování jedním nepřerušeným 107,801s souborem. Předchozí nevysvětlený tichý úsek se nezopakoval.
- C01c build 3 při prvním Start padal. Pět shodných crash reportů potvrdilo Swift 6 actor-isolation trap v tap callbacku, nikoli neplatný audioformát nebo první zápis CAF.
- Build 0.3.0 (4) vytváří tap callback v `nonisolated` helperu. 52/52 Swift testů, 2/2 UI testy, nepodepsaný i podepsaný build a strict podpis PASS.
- 0.3.0 (4) je nainstalovaná a spuštěná bez odinstalace. Všech 136 položek se po instalaci a launchi shoduje v cestě, typu i velikosti; pět nedokončených pokusů se nemazalo. Profil do 22. září 18:16 CEST.
- Krátký fyzický Start/Stop buildu 4, T022/T023, fyzická kontinuita segmentů, G0/G1/G8 a terénní připravenost zůstávají NEPROVEDENO.

### Vzkaz pro pokračování

- Restart a následný schválený úklid dokončeny. Před zahájením instalace bylo na SSD 85,79 GiB volných. Dřívější přesun USA neopakovat.
- C01c 0.3.0 (4) je nainstalované. Nejdřív krátký fyzický Start/Stop; T022 spustit až po jeho PASS. Build 3 ani starou 0.2.0 už nepoužívat.
- Viewer nepřeskakovat před C08c–C08f. U15 doménově implementovat v C03/C04; provizorně jej nepřidávat do C01b JSON.
- Po každém Mílou oznámeném výsledku bez další žádosti vyhodnotit stav, říct, zda je potřeba vývoj, a rovnou dát přesný návod i kritéria PASS následujícího neprovedeného testu. Shoda s návrhem nevyžaduje změnu kódu; FAIL nejdřív doložit a potom opravit v aktuální etapě.
- Starší c+p+n d573e90c je historické. Dnešní p+n zahrnuje celý balíček Camina a toto předání; výsledek určuje živý audit a kanonická deployment receipt.

### Rizika

- C01a přijato, ale širší brány G0/G1/G8 a terénní připravenost zůstávají nesplněné.
- C01b přijato v prototypovém rozsahu. Vítr a plná integrace T021 v C04 čekají; jeden nevysvětlený nereprodukovaný tichý úsek z prvního T059 zůstává rizikem.
- C01c build 3 měl potvrzený pád při Start; build 4 jej opravuje, ale fyzický smoke ještě čeká. Kontinuita 55s přechodů, background běh input tapu a rozsah ztráty po pádu zůstávají neověřené do T022/T023.
- Vzorky v telefonu mají jen místní kopii, nejsou určeny pro ostrá média; žádná AI, síť, export nebo automatické mazání.
- Podepsaný build není instalace ani fyzická přejímka; vývojový profil je časově omezený. U01–U15 se bez nového rozhodnutí neotevírají.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Camino

Nazev: Camino
Pracovni proud: project-camino
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-09-17 11:32 CEST

Co se resilo:
Diagnostika a oprava okamžitého pádu C01c při prvním Start.

Co je hotove:
V0.5 + U15 platí; C01a/C01b přijaty. Příčina pádu buildu 3 je potvrzená z pěti shodných crash reportů. Opravený build 0.3.0 (4) prošel 52/52 + 2/2, buildem, strict podpisem, instalací i launchem; všech 136 položek zůstalo beze změny.

Co neni hotove:
Krátký fyzický Start/Stop buildu 4, T022/T023 a plný T061, plná integrace T021 v C04, U15 v C03/C04, Viewer C08c–C08f, G0/G1/G8 a terénní připravenost. První tichý úsek T059 zůstává nereprodukovaným pozorováním.

Dalsi krok:
Provést 10–15s neutrální Start/Stop a poslech na nainstalované 0.3.0 (4); teprve při PASS pokračovat T022.

Navrhovane dalsi kroky:
Po krátkém smoke automaticky předat T022; po T022 vyhodnotit T023 nebo další opravu.

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
