# C01a — audio prototyp: průběžné předání

Aktualizováno: 2026-09-15 19:25 CEST. Specifikace v0.4; U01–U11 beze změny.

**C01a: lokální oprava indikace přehrávání, ruční retest čeká.** Dosavadní nahrávání a poslech uživatelsky prošly; nehybný ukazatel odhalen snímkem a opraven. Nová verze prošla 28 testy, podepsaným buildem a strict podpisem; na telefonu dosud není. Úplná přejímka C01a a G0/G1 zůstávají otevřené.

## Aktuální oprava přehrávání

### 2026-09-15 19:25 CEST — Oprava zobrazení průběhu přehrávání

- Míla po doplňujícím testu potvrdil přehrání Komentáře a nahlásil chybějící průběh. Snímek IMG_0503.PNG ukazuje režim Letadlo, Přehrávám, čas 00:30, název Mikrofon iPhonu a uložený Komentář 00:30. Obrázek nebyl kopírován do Gitu. Sám nedokládá pohyb času ani vypnutí Wi-Fi; přehrání potvrzuje uživatel.
- Příčina ověřena v kódu: společná obrazovka při poslechu dál zobrazovala elapsed posledního záznamu, vstup a mikrofonní meter. Playback tick pouze hlídal konec, nečetl pozici přehrávače.
- Oprava: AVAudioPlayer.currentTime a duration přes AudioDriver; samostatný stav přehrávání v controlleru a oznámení změny při každém odečtu. SwiftUI při poslechu zobrazuje uplynulý/celkový čas a modrý průběh místo údajů mikrofonu. Žádné dopočítávání času podle timeru. [Apple currentTime](https://developer.apple.com/documentation/avfaudio/avaudioplayer/currenttime).
- Ověření: 28/28 Swift XCTest, podepsaný Debug xcodebuild generic/platform=iOS exit 0 a codesign --verify --deep --strict exit 0. Tři nové testy pokrývají skutečnou pozici vs. čas záznamu/nástěnné hodiny, chybné hodnoty a Stop/opakování/odchod do pozadí; rozšířen test přirozeného konce.
- Zápis a formát médií se nemění. Nová verze zatím NENÍ nainstalovaná na iPhonu; ruční UI/poslech opravy NEOVĚŘENO. Před aktualizací čeká potvrzení, že nahrávání i přehrávání stojí. Existující vzorky zachovat, aplikaci neodinstalovávat.
- T015: doplňující Komentář přehrán podle uživatele, screenshot v režimu Letadlo; offline test proběhl podle zadaného postupu, samostatný technický důkaz vypnuté Wi-Fi chybí. T017: název vstupu Mikrofon iPhonu nyní doložen snímkem (při poslechu šlo o zachovaný údaj záznamu). Přesná metadata vzorků a první odmítnutí systémového dialogu T025 zůstávají otevřené.
- Další krok: Při zastaveném záznamu i přehrávání aktualizovat aplikaci v připojeném iPhonu a ručně ověřit běžící čas/průběh, Stop a opakované přehrání existujícího vzorku. Potom doplnit zbývající doklady C01a a první odmítnutí oprávnění; C01b nezahajovat.

## Předchozí ruční zkoušky

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

## Historické potvrzení otevření

### 2026-09-15 18:39 CEST — Míla potvrdil otevření aplikace; zadal c+p+n

- Míla výslovně potvrdil, že se Camino Audio na iPhonu otevřelo. Otevření je potvrzení uživatele; nejde o automaticky ověřený průchod UI, mikrofon ani poslech. Předchozí blokace spuštění již podle tohoto potvrzení nebrání otevření.
- Podepsaný build, strict podpis a instalace mají strojové doklady; profil platí do 2026-09-22 18:16 CEST. Ruční T015/T017/T025, oba audio vzorky a poslech zůstávají NEPROVEDENO, C01a není přijaté.
- Míla zadal nejprve commit + push + nasazení aktuálního balíčku do Cockpitu. Autorizace zahrnuje čekající lokální commity a tento redigovaný stav; po c+p+n se zatím další vývoj ani nahrávání nespouští.
- Doklad výsledku c+p+n: aktuální GitHub batch audit, plná brána a kanonická simple-main deployment receipt s novým PID, shodou otisku a smoke 5/5; historické nasazení není důkaz tohoto kroku.
- Další krok: Po uzavření schváleného c+p+n pokračovat ruční přejímkou C01a na iPhonu: T015/T017/T025, neutrální krátký Komentář a Úvaha, Stop a poslech; nahrávání zahajuje Míla. C01b nezahajovat.

## Historická instalace na iPhone

### 2026-09-15 18:36 CEST — Aplikace nainstalována, spuštění odmítnuto

- iPhone 14 Plus živě ověřen: wired, tunnel connected, Developer Mode enabled. Zařízení odpovídá vývojovému profilu; podpis znovu ověřen strict kontrolou.
- `devicectl device install app`: exit 0, success, přesný bundle cz.pythonmf.camino.audio.prototype v installedApplications. Instalace na telefon PASS.
- `devicectl device process launch`: exit 1, FBSOpenApplicationErrorDomain / Security. Hlášení uvádí podpis, oprávnění nebo nepotvrzenou důvěru profilu; vzhledem k platnému podpisu a úspěšné instalaci je dalším krokem ruční kontrola důvěry. Příčina zatím není definitivně potvrzena.
- Spuštění, UI, mikrofon a fyzický poslech NEOVĚŘENO; C01a stále BLOCKED, C01b nezahájeno. Žádné nahrávání nebylo spuštěno.
- Další krok: Na iPhonu potvrdit důvěru vlastnímu vývojářskému účtu v Nastavení → Obecné → VPN a správa zařízení. Potom ověřit spuštění Camino Audio a provést fyzickou přejímku T015/T017/T025.

## Historické ověření podpisu

### 2026-09-15 18:31 CEST — Podpis ověřen, instalace čeká na telefon

- Míla nastavil tým v Xcode. Aktuálně jedna platná podpisová identita; automatický vývojový podpis a profil ověřeny. Účty, certifikáty a identifikátory týmu nejsou v Gitu.
- Podepsaný `xcodebuild` Debug / generic/platform=iOS: exit 0. `codesign --verify --deep --strict` nad CaminoAudio.app: exit 0. Vývojový profil platí do 2026-09-22 18:16 CEST, obsahuje jedno zařízení.
- První build v projektovém data/private skončil na FinderInfo u .app. Nový DerivedData adresář v /private/tmp problém odstranil bez změny zdrojů či odstraňování atributů originálů. [Apple QA1940](https://developer.apple.com/library/archive/qa/qa1940/_index.html).
- Volba týmu z Xcode přesunuta do existujícího mechanismu LocalSigning.xcconfig; význam verzovaných nastavení projektu je shodný s původním HEAD, zachováno jen formátování Xcode.
- Poslední devicectl inventura: iPhone 14 Plus odpojený; Developer Mode enabled je evidovaný stav, nikoli důkaz aktuálního spojení. Instalace, spuštění a fyzický poslech NEPROVEDENO; C01a zůstává BLOCKED.
- Další krok: Připojit a odemknout iPhone, ověřit dostupnost zařízení a nainstalovat podepsaný CaminoAudio.app. Potom provést fyzickou přejímku T015/T017/T025; nahrávání zahajuje uživatel vědomým Start.

## Historické ověření platformy a buildu

### 2026-09-15 15:01 CEST — Podpora iOS a standardní build ověřeny

- Xcode Components a `simctl list runtimes` potvrdily instalaci; iOS runtime 26.3.1 / 23D8133 dostupný.
- `xcodebuild -project camino/prototypes/audio/CaminoAudio.xcodeproj -scheme CaminoAudio -configuration Debug -destination generic/platform=iOS -derivedDataPath <soukromý-build-adresář> CODE_SIGNING_ALLOWED=NO build`: exit 0, BUILD SUCCEEDED.
- Vznikl skutečný balíček CaminoAudio.app s arm64 executable; `codesign` potvrdil, že není podepsaný. Jediné varování: přeskočená extrakce AppIntents metadat, protože target nemá AppIntents.framework.
- SDK/platforma už build neblokují. Zdroje aplikace beze změny; dřívějších 25 testů logiky se bez nové změny neopakovalo.
- Volné místo po instalaci přibližně 69,3 GiB. Platných podpisových identit aktuálně 0; DEVELOPMENT_TEAM v projektu nenastaven. Přihlášení k Apple Account zatím neověřeno.
- Instalace aplikace na telefon, spuštění a fyzické T015/T017/T025 NEPROVEDENO. C01a zůstává BLOCKED na podpisu a fyzické přejímce; C01b nezahájeno.
- Další krok: Nastavit v Xcode Apple Account a vývojový tým pro podpis, potom podepsat a nainstalovat CaminoAudio na iPhone a provést fyzickou přejímku T015/T017/T025.

## Historický audit zařízení a překážek — 08:19 CEST

- Připojený iPhone 14 Plus: iOS 26.6.1 / build 23G83; ověřeno přes devicectl.
- `pairingState=paired`, `transportType=wired`, `tunnelState=connected`.
- Po Mílově zapnutí a restartu: `developerModeStatus=enabled`,
  `ddiServicesAvailable=true`. Identifikátory zařízení, osobní jméno a účty
  se do tohoto reportu nekopírují.
- Xcode 26.3 / build 17C529, iPhone SDK 26.2. Existující SDK ani úspěšný
  `checkFirstLaunchStatus` nejsou důkaz funkčního Xcode buildu.
- Skutečný `xcodebuild` se schématem CaminoAudio a cílem generic/platform=iOS
  selhal exit 70: iOS 26.2 není nainstalované, požadována platforma přes
  Xcode → Settings → Components. Alternativa `-sdk iphoneos` bez destination
  také neměla dostupný cíl. Žádné přepínání interních příznaků Xcode.
- Apple rozlišuje Platform Support a simulator runtimes; bez podpory platformy
  Xcode odmítá build i pro fyzické zařízení. Je třeba v Components ověřit,
  zda je položka ke stažení, nebo k zapnutí; skutečný stav jejího UI NEOVĚŘENO.
  [Apple: spuštění na zařízení](https://developer.apple.com/documentation/xcode/running-your-app-on-simulated-or-physical-devices),
  [Apple: součásti Xcode](https://developer.apple.com/documentation/xcode/downloading-and-installing-additional-xcode-components).
- Před prototypem bylo na Macu 18,8 GiB volných. Zde nebyla spuštěna další
  instalace platformy ani simulátoru. Kapacitní rozpočet konkrétního balíčku
  je nutný před velkým stažením; automatické mazání nepovoleno.
- Bezpečný výpis počtu platných codesigning identit: **0**. Stav přihlášení
  Apple Account v Xcode NEOVĚŘENO. Klíče, přihlašovací údaje ani celé profily
  nebyly čteny. Placené členství se nekupovalo.

## Implementovaný rozsah

`prototypes/audio/` obsahuje Xcode projekt, samostatně testovatelný Swift balíček,
SwiftUI obrazovku a adaptér AVAudioRecorder/AVAudioPlayer. Jeden aktivní recorder
nebo player. První povolení mikrofonu nikdy samo nezačne záznam; následuje nový
Start. UI stav Nahrávám vyžaduje postup mediálního času a dostupnou skutečnou
route, úroveň signálu se aktualizuje z recorderu. Ticho není samo o sobě chyba.

Každý pokus má atomicky výhradně vytvořený adresář (mkdir/EEXIST), neměnný
started.json, nový audio.caf a create-only completed.json až po potvrzení
ukončení a dekódování celého krátkého souboru. Opakovaný Stop nesmí přepsat
hotový záznam. Načtení kontroluje identitu draftu a skutečné parametry média.
Neúplné či poškozené položky se zachovají a viditelně započítají. Jde o jednoduchou
prototypovou evidenci; segmentový journal, transakční obnova a pád během zápisu
z F18/F42 nejsou tímto splněny.

Vzorky zůstávají v Application Support aplikace, mimo cache a repozitář.
Složka je vyloučena ze systémové zálohy; v této etapě existuje jen místní kopie.
Žádné síťové API, iCloud kontejnery, File Sharing, AI, GPS, galerie ani export.
Žádná aplikace zatím na telefonu neběžela, mikrofon nebyl agentem zapnut.

## Ověření

| Kontrola | Skutečný výsledek |
|---|---|
| `swift test --package-path camino/prototypes/audio --scratch-path /private/tmp/camino_audio_swift_build_20260915` | **25/25 XCTest OK**. Závěrečný automatický výpis Swift Testing 0 testů je jiný runner, nenahrazuje počet XCTest. |
| Logika a chyby | První/odmítnuté oprávnění, dvojitý Start, opožděné spuštění a Stop, přerušení během přípravy, výpadek vstupu/času, souběh playeru, selhání startu/Stop/evidence/přehrávání, návrat po restartu. |
| Soubory | Kolize UUID bez přepisu, druhé dokončení bez přepisu, poškozený/nesprávný draft, neúplné a chybějící médium, neplatná délka. |
| Skutečné syntetické audio na Macu | 0,5 s PCM/CAF, 48 kHz, mono, 16 bitů: celý soubor dekódovaný, délka/parametry ověřeny, uložený a znovu načtený. Samostatně platné ticho a odmítnuté poškozené CAF. Není to zkouška mikrofonu ani poslech. |
| Přímý `swiftc -typecheck` pro arm64-apple-ios17.0 s SDK 26.2 | Exit 0. |
| Přímá kompilace a linkování všech Core/AudioIO/App zdrojů (`swiftc -emit-executable -parse-as-library -swift-version 6`) | Exit 0 bez warnings; procesové SDKROOT a `xcrun --sdk iphoneos`, bez systémové změny. |
| `vtool -show-build` nad výsledkem | Mach-O arm64, platform IOS, minos 17.0, sdk 26.2. Samostatný executable není podepsaný instalační balíček ani náhrada Xcode buildu. |
| `plutil -lint` nad project.pbxproj | OK. |
| Společná plná brána `scripts/cockpit_quality_gate.py` | **1684/1684 testů OK**, oddělené od 25 Swift testů. |
| Standardní Xcode build | **PASS**, 15:01 CEST exit 0, nepodepsaný arm64 .app. Původní blokace platformy odstraněna. |
| Signing / instalace / spuštění | **Signing PASS**, 1 platná identita, strict podpis OK. Instalace PASS; otevření potvrzeno Mílou, audio přejímka čeká. |
| T015/T017/T025, ruční poslech, UI na telefonu | **ČÁSTEČNĚ OVĚŘENO** uživatelem; podrobný rozsah a mezery v aktuální sekci. |
| G0/G1, T079 upgrade a migrace, terén | **NEPROVEDENO / nesplněno**. |

Build logy a syntetické fixture jsou lokálně mimo Git. Soukromé inventury
zařízení nejsou součástí commitu. Původní podklady v0.4 zůstaly neměnné.

## Návrhové parametry a omezení

- iOS minimum 17 odpovídá AVAudioApplication a použitému SwiftUI; není změnou
  cílového telefonu ani minimální verze budoucího P0.
- PCM/CAF mono 48 kHz / 16 bitů odpovídá návrhu C00; fyzická route může mít
  jiné parametry, dokončený soubor se ověřuje podle skutečného obsahu.
- Watchdog postupu mediálního času 2 s; timeout callbacku Stop 3 s. Konzervativní
  prototypové hodnoty k fyzickému ověření, nikoli provozní garance za zámku.
- C01a je výhradně foreground. Odchod do neaktivního stavu ukončuje záznam;
  soubor má ochranu Complete. Pokračování pod zámkem je samostatné C01b.
- Chybějící callback, chybný zápis nebo neúplné dekódování nikdy neznamenají
  Uloženo; soubor zůstává zachovaný. C01c teprve doplní záchranu při pádu.
- Dílčí fyzické zkoušky uživatelsky prošly; úplná přejímka a doklady ještě nejsou uzavřené. Není určeno pro ostrá média.

## Jediný následující krok

Při zastaveném záznamu i přehrávání aktualizovat aplikaci v připojeném iPhonu a ručně ověřit běžící čas/průběh, Stop a opakované přehrání existujícího vzorku. Potom doplnit zbývající doklady C01a a první odmítnutí oprávnění; C01b nezahajovat.
