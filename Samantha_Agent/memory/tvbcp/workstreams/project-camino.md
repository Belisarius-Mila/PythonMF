<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno po fyzickém T049: 2026-09-19 11:45 CEST

### Hotovo
- T043 PASS v rozsahu syntetického C02b: Letový režim přerušil upload při 0/13 serverových částech; po obnově sítě vznikl jediný objekt daného Assetu, 13/13 částí, 100 663 553 B a shodný SHA-256.
- Fyzický průchod odhalil zahozené souběžné impulsy reconciliace a zdánlivě mrtvé tlačítko. Build `Camino Transfer Test` 0.4.0 (2) požadavky koaleskuje; následná 96MiB dávka doběhla automaticky bez dalšího klepnutí.
- Build 2 je strict podepsaný, nainstalovaný a spuštěný na iPhonu 14 Plus / iOS 26.6.1. Camino Audio zůstalo nedotčené; profil harnessu platí do 24. září 2026.
- T043 byl potvrzeně ukončen: vlastněný receiver neběží, `/camino-c02b` je odebraná, původní Serve konfigurace je přesně obnovená a Funnel zůstává vypnutý. Tři ověřené Assety/účtenky, každý 100 663 553 B, jsou zachované.
- Oddělený registrovaný T047 workflow používá vlastní soukromý běh. Jeho read-only audit fail-closed kontroluje relace, stav poslední relace, hash každé přijaté části a finální objekty/účtenky.
- T047 PASS v rozsahu syntetického C02b: první dávka byla zamčená během přenosu a po odemčení se dokončila 13/13; u druhé dávky byl po 1/13 skutečně ukončen proces, serverový stav zůstal 1/13 bez druhého objektu a po ručním relaunchi se doplnily pouze chybějící části do 13/13. Živé potvrzení má 2 relace, 2 ověřené objekty/účtenky, každý 100 663 553 B, celkem 201 327 106 B.
- T049 prošel na iPhonu v syntetickém mobilním rozsahu: bez grantu zůstala dávka na 0 %, 0/13 a serveru 0 relací; zrušení dialogu zákaz zachovalo. Po grantu server doložil jedinou ověřenou relaci, 13/13 částí, jeden objekt a účtenku, 100 663 553 B a shodný SHA-256. Míla viděl `Ověřeno na Macu`.
- Nová syntetická dávka mobilní povolení nezdědila: po `Synchronizovat nyní` zůstala na 0 %, 0/13, 0/2 a server stále evidoval jen první relaci. T049 bylo registrovaně ukončeno; receiver/cesta vypnuté, původní Serve přesně obnovený, Funnel vypnutý a důkaz zachovaný. T048 je neaktivní.
- `Camino Transfer Test` 0.4.0 (3) se na iPhonu fyzicky spustil; Camino Audio 0.3.0 (4) zůstává nedotčené. Kód při testu nebyl měněn.

### Otevřeno
- T048 a T050 jsou fyzicky NEPROVEDENO. Plné T049 s novým skutečným videem čeká na integrovanou aplikaci.

### Rizika
- Receiver je lokální standard-library experiment, ne produkční FastAPI, databáze, trvalá služba ani záloha. T049 neprokazuje cizí Wi-Fi ani zadrženou finalizaci.
- Harness nemá kameru; plné kritérium nového skutečného videa se musí ověřit až v integrované aplikaci. Úplné znění fyzického potvrzovacího dialogu nebylo opsáno a serverový počet bajtů není měření spotřeby operátora.

### Další krok
- Při dostupné cizí Wi-Fi provést oddělený T048; bez ní lze po samostatném zadání připravit T050 se zadrženým serverovým ověřením.

### Rozhodnutí
- Serverová pravda a stav `verifying` mají přednost před lokálním byte progress. Dostupná povolená Wi-Fi může spustit automatickou synchronizaci; ruční tlačítko je provozní záloha. Souběžný impuls se koaleskuje, nezahazuje.
- Míla zvolil pořadí T049 před T048 kvůli nedostupné cizí Wi-Fi; nejde o změnu kritérií ani označení T048 za PASS.

### Navrhované další kroky
- T047 je fyzicky PASS v syntetickém rozsahu; jeho dva objekty/účtenky a relace zůstávají zachované.
- Plné T049 s novým skutečným videem ověřit až v integrované aplikaci.
- T050 zůstává samostatný fyzický test; zatím se nespouští.

### Technický stav checkpointu
- Swift transfer core 19/19, T043 ovladač + oba receivery 28/28, T047/T043 workflow modul 11/11 a UI 1/1 PASS; podepsaný build 2, strict kontrola, instalace a launch PASS. Plná projektová brána 1716/1716 PASS.
- Push ani nasazení neproběhly. T043 i T047 cesta/receiver jsou ukončené; původní Serve je přesně obnovený a Funnel vypnutý.
- T049 audit po stopu: `phase=stopped`, receiver/cesta vypnuté, Funnel vypnutý, 1/1 relace ověřená, 13/13 částí, jeden objekt/účtenka a 100 663 553 B se shodným hashem. Dřívější Swift core 20/20, iOS UI 1/1, podepsaný build 3 a plná projektová brána 1718/1718 PASS.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: Camino

Pracovni proud: `project-camino`
Typ: `Project`
Rezim: `active`
Priorita: 1

## Cíl a hranice

Soukromý cestovní deník podle v0.5 + U15: jeden autor na iPhonu, soukromý
owner archiv a read-only Camino Viewer pro Janu bez veřejného webu. `Jen pro mě`
je vyloučeno; celé `Do deníku` je po synchronizaci Viewer-eligible.

## Aktuální stav a další krok

- V0.5 importovaná beze změny, 6/6 manifestovaných souborů ověřeno; U15 je závazný novější dodatek. Samostatná Úvaha začíná `Jen pro mě` a do deníku se převádí vědomě.
- Viewer delta audit potvrdil Tailscale/Serve/Cockpit základ, smoke 5/5, Funnel vypnutý, AC bez spánku a FileVault zapnutý. Viewer služby, autorizace, záloha/restart a Janina vzdálená zkouška chybějí; G8 NEPROVEDENO.
- Profilový fast-forward nyní kontroluje whitespace s příchozími `.gitattributes`; ostatní fail-closed brány zůstávají zachované.
- T016 PASS: přesně 30:24,406, 175 147 072 B, 48 kHz mono, režim Letadlo, převážně pod zámkem a celý poslech OK. T018–T020, T024 a T059 PASS podle Míly. T021 PASS v rozsahu C01b prototypu; plná integrace se zopakuje v C04. T059 po restartu ochránil data a řízené opakování zachytilo všechny značky pod zámkem. Vítr neověřen.
- C01b 0.2.0 (2) je historicky přijaté pro background audio, přerušení a vědomé pokračování; před přechodem na C01c prošla instalace i zachování tehdejších 15 položek. Aktuálně je na iPhonu C01c 0.3.0 (4).
- Běžící recorder přežije změnu scenePhase; nový Start/Pokračovat pouze v popředí. Přerušení ihned pozastaví vstup, ověří dostupnou část a nabídne Pokračovat/Ukončit. Pokračování vytváří novou část stejné session s evidovanou pauzou, bez přepisu předchozího média.
- Soubory vytvořené v C01b mají completeUntilFirstUserAuthentication; původní C01a soubory se nemigrují ani nemění. Staré JSON podporuje volitelné continuation. Tyto starší jednotlivé CAF samy nejsou C01c journal ani důkaz 60s cíle.
- Ověřeno 47/47 Swift testů, 2/2 UI testy simulátoru včetně snímku obrazovky, finální podepsaný iOS build a strict podpis; UIBackgroundModes=[audio]. Plná projektová brána PASS, 1684/1684 testů.
- C01b 0.2.0 (2) přijato v prototypovém rozsahu. Krátký test zámku a T016/T018–T021/T024/T059 PASS; T059 prošel po řízeném zopakování jedním nepřerušeným 107,801s souborem. Předchozí nevysvětlený tichý úsek se nezopakoval.
- Po každém Mílou oznámeném výsledku fyzického testu Adam bez další žádosti vyhodnotí stav, řekne, zda je potřeba vývoj, a rovnou předá podmínky, přesný postup a kritéria PASS následujícího neprovedeného testu. Shoda s návrhem sama změnu kódu nevyvolává.
- C01c build 3 při prvním Start padal. Pět shodných crash reportů potvrdilo Swift 6 actor-isolation trap: inline tap callback zdědil `MainActor`, ale běžel na real-time audio frontě.
- Opravený build 0.3.0 (4) vytváří callback v `nonisolated` helperu. 52/52 Swift + 2/2 UI PASS, oba arm64 buildy, strict podpis, instalace i launch PASS; všech 136 položek se po instalaci shoduje v cestě, typu a velikosti.
- Pět nedokončených pokusů z pádů zůstalo zachováno. Profil hlavní aplikace do 22. září 18:16 CEST. Krátký fyzický smoke buildu 4 PASS podle Míly: bez pádu, rostoucí čas i ukazatel a přehratelný nový záznam.
- T022 PASS ve dvou odlišných fázích otevřené části: klidový relaunch, pravdivé označení obnoveného rozsahu a přehratelné uzavřené části. T023 PASS přes čtyři poslechnuté 55s hranice bez opakování či nevysvětlené díry. C01c je přijato v prototypovém rozsahu; G0/G1/G8 a terénní připravenost zůstávají nesplněné.
- C02a minimální receiver prošel 10/10 automatickými testy i privátním HTTPS smoke přes dočasnou Tailscale Serve cestu. Správný upload vytvořil právě jeden objekt a účtenku, retry neduplikoval, chybný hash a konflikt byly odmítnuty. Funnel zůstal vypnutý, Cockpit dostupný a původní Serve stav byl obnoven.
- C02b má fyzický PASS T043 v syntetickém rozsahu. Letový režim zachytil relaci s 0/13 přijatými částmi; po návratu sítě vznikl jediný objekt daného Assetu, 13/13, 100 663 553 B a shodný SHA-256.
- `Camino Transfer Test` 0.4.0 (2) koaleskuje souběžné impulsy reconciliace; následná celá dávka doběhla automaticky. Build 0.4.0 (3) přidal per-request síťovou politiku a prošel syntetickou mobilní částí T049. Swift 20/20, Python workflow 13/13, UI 1/1 a plná brána 1718/1718 PASS při jeho přípravě. T043/T047/T049 receiver i testovací cesta jsou po jejich bězích ukončené, Serve obnovený, Funnel vypnutý.


T048 provést odděleně při dostupné cizí Wi-Fi; bez ní lze po samostatném zadání připravit T050. C01c ani C02a dále nerozšiřovat bez nového důvodu.

## Rizika

- C01a přijato, ale širší brány G0/G1/G8 a terénní připravenost zůstávají nesplněné.
- C01b přijato v prototypovém rozsahu. Vítr a plná integrace T021 v C04 čekají; jeden nevysvětlený nereprodukovaný tichý úsek z prvního T059 zůstává rizikem.
- C01c je přijato v prototypovém rozsahu po T022/T023. Výsledek nepokrývá dlouhodobou terénní spotřebu ani plný databázový a serverový T061, který zůstává C05a.
- C02a je přijato jen v omezeném serverovém prototypu. Smoke z téhož Macu přes tailnet DNS není důkaz iPhone klienta, cizí sítě, přerušení velkého souboru, trvalé služby ani úplných T043/T048/T051.
- C02b má T043 a T047 PASS v syntetickém rozsahu a T049 úspěšnou syntetickou mobilní část. Přesný výpadek nebyl po opravě zopakován na buildu 2. T048, T050 a plné T049 se skutečným videem zůstávají NEPROVEDENO; receiver není produkční služba ani záloha.
- Vzorky v telefonu mají jen místní kopii, nejsou určeny pro ostrá média; žádná AI, síť, export nebo automatické mazání.
- Instalace a launch nejsou fyzická přejímka přenosu; vývojový profil je časově omezený do 24. září 2026. U01–U15 se bez nového rozhodnutí neotevírají.

## Chronologické záznamy

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

- Stav: T016 dokončen fyzickým uživatelským testem v Camino Audio. Přibližná délka 30:16, režim Letadlo, převážně zamčený telefon, nahrávání bez hlášeného výpadku a celý záznam přehratelný.
- Důkaz: svědectví Míly. Velikost souboru nebyla sdělena; verze aplikace, telefon a iOS nebyly v dnešní zprávě znovu čteny a navazují na evidovaný kontext 0.2.0 (2), iPhone 14 Plus / iOS 26.6.1.
- Pozorování: přehrávání při zamčené obrazovce neběželo. Není to akceptační kritérium T016 a nevzniklo rozhodnutí rozšířit rozsah.
- Rizika: T018–T021/T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno. Jediný soubor úseku není segmentový journal ani garance 60s obnovy. Audio zůstává pouze na telefonu.
- Další krok: T018 s dostupnými sluchátky, potom T019–T021/T024/T059.
- Ověření: kód beze změn, automatické testy se neopakovaly; změněn pouze projektový zápis.

### 2026-09-16 19:46 CEST — T018 PASS a dílčí T019

- Stav: T018 PASS podle Míly s AirPods jako zobrazeným aktivním vstupem; stání i chůze pod zámkem, několikaminutové úseky, bez výpadků, celý poslech OK. Vítr nebyl přítomen.
- Důkaz: CoreDevice potvrdil Camino Audio 0.2.0 (2) a opravil T016 na 30:24,406 / 175 147 072 B / 48 kHz mono. Žádný CAF se nekopíroval ani neposlouchal.
- Telefonát: první samostatná část 3:08,56 byla označena `interrupted=true`; Pokračovat vytvořilo druhý samostatný soubor 4:53,57 ve stejné session s pauzou 2:25,13. Grafické seskupení není fyzické slepení médií.
- Mikrofon iPhonu: pozdější záznam byl nová session bez continuation. Podle Míly byl v kapse tišší a méně kvalitní; nejde o automatické pokračování.
- Rizika: úplný T019 a T020 čekají; T019 vyžaduje příchozí hovor ignorovaný i přijatý, T020 změnu aktivního vstupu během záznamu. C01b/G0/G1 otevřené, C01c nezahájeno.
- Další krok: dokončit T019, potom T020–T021/T024/T059.

### 2026-09-16 20:02 CEST — Automatický návod k dalšímu testu

- Rozhodnutí: po každém Mílou oznámeném výsledku fyzického testu Adam bez další žádosti vyhodnotí PASS/FAIL/BLOCKED či dílčí stav, řekne, zda je potřeba vývoj, a rovnou poskytne podmínky, přesný postup a kritéria PASS následujícího neprovedeného testu.
- Hranice: shoda s návrhem nevyžaduje změnu kódu. Při FAIL se nejdřív doloží přesný projev, potom se opraví C01b a zopakuje dotčený scénář. C01c zůstává mimo rozsah.
- Další krok: dokončit T019 příchozím běžným telefonním hovorem jednou ignorovaným a jednou přijatým; potom automaticky předat T020.
- Ověření: pouze projektový zápis pravidla; kód aplikace ani soukromá data se neměnily.

### 2026-09-16 20:25 CEST — T019 PASS

- Stav: ignorovaný i přijatý příchozí hovor PASS podle Míly; obě části přehratelné, nic z hovoru v audu a žádné samovolné pokračování.
- Důkaz: technická metadata potvrzují dvě přerušené první části 44,410 s a 26,798 s a jejich samostatná vědomá pokračování stejné session 21,551 s a 20,999 s, s pauzami 43,153 s a 112,272 s. Všechny části jsou 48 kHz mono; žádný CAF se nekopíroval ani neposlouchal.
- Rozhodnutí: chování odpovídá návrhu C01b, oprava ani nový build nejsou potřeba.
- Rizika: T020–T021/T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.
- Další krok: provést T020 změnou skutečně aktivního vstupu během běžícího záznamu; potom automaticky předat T021.

### 2026-09-16 20:39 CEST — T020 PASS

- Stav: odpojení aktivních AirPods přerušilo záznam, části zůstaly přehratelné, nic se samo neobnovilo a AirPods se znovu staly aktivním vstupem až při dalším vědomém spuštění. T020 PASS podle Míly.
- Důkaz: metadata potvrzují tři části jedné session — 34,776 s přerušená, 25,944 s navazující a přerušená, 18,215 s navazující a dokončená — s pauzami 28,002 s a 90,312 s; 48 kHz mono. Žádný CAF se nekopíroval ani neposlouchal.
- Rozhodnutí: pouhé Bluetooth připojení není aktivní route; vstup AirPods se potvrdil až při vědomé reaktivaci audio session. Oprava ani nový build nejsou potřeba.
- Rizika: T021/T024/T059, C01b/G0/G1 otevřené; C01c nezahájeno.
- Další krok: provést T021 v prototypovém rozsahu; potom automaticky předat T024.

### 2026-09-16 21:27 CEST — T021 PASS v rozsahu C01b prototypu

- Stav: volba typu a Přehrát byly za běžící Úvahy neaktivní, druhý recorder nešel spustit, po návratu z jiné aplikace pokračovala stejná session a čas narostl; jedna část bez přerušení a celý poslech OK podle Míly.
- Důkaz: poslední Úvaha 56,350 s, 5 413 696 B, 48 kHz mono, `interrupted=false`, bez continuation. Dřívější samostatný přípravný pokus byl oddělen; žádný CAF se nekopíroval ani neposlouchal.
- Rozhodnutí: T021 PASS v rozsahu C01b prototypu; plný scénář videa/Momentu se zopakuje v C04. Oprava ani nový build nejsou potřeba.
- Rizika: T024/T059, C01b/G0/G1 otevřené; C01c nezahájeno.
- Další krok: provést T024, potom automaticky předat T059.

### 2026-09-16 21:43 CEST — Přijetí v0.5, rozhodnutí U15 a delta C00

Hotovo:
- Původní v0.5 je importovaná a ověřená; vznikl závazný U15 dodatek a Viewer readiness audit bez změny systému.

Rozhodnutí:
- Celé `Do deníku` může být po synchronizaci dostupné Janě v soukromém Vieweru. Samostatná Úvaha vždy vzniká `Jen pro mě` a vyžaduje vědomé `Vložit do deníku`.
- Původní balíček se kvůli manifestu nepřepisuje. U15 se implementuje v C03/C04, Viewer v C08c–C08f; C01b zůstává izolovaný audio prototyp.

Další krok:
- Provést T024, potom T059; C01c nezahajovat před uzavřením C01b.

Navrhované další kroky:
- Po C01b pokračovat C01c; následně zachovat pořadí malých etap v0.5 a před C08 dokončit potřebný datový, přenosový a serverový základ.

Technický důkaz:
- Manifest v0.5 6/6, přesná kopie ZIP; Tailscale 1.102.4 online, Serve bez Funnel, Cockpit smoke 5/5, AC `sleep=0`, FileVault zapnutý. Viewer/G8 NEPROVEDENO.

### 2026-09-16 21:48 CEST — Oprava profilového whitespace preflightu

Hotovo:
- Human–Adam workspace umí bezpečně převzít commit, který současně přidává importovaný Markdown i jeho `.gitattributes`.

Rozhodnutí:
- Preflight používá atributy z `FETCH_HEAD`; globální ignorování whitespace ani oslabení ostatních sync bran nebylo přijato.

Další krok:
- Po commitu zopakovat dorovnání čistých profilů; Camino pokračuje T024.

Navrhované další kroky:
- Žádný nový produktový krok; oprava pouze odstraňuje falešný blokátor převzetí již schváleného balíčku.

Technický důkaz:
- Regresní test + 192 souvisejících testů PASS; rychlá kontrolní brána PASS.

### 2026-09-16 22:41 CEST — T024 PASS

Hotovo:
- Po nuceném ukončení aplikace za rozpracované Úvahy zůstal relaunch v klidu, dříve dokončené části byly přehratelné a nový neověřený pokus byl viditelně započítán.

Rozhodnutí:
- T024 PASS; oprava ani nový build nejsou potřeba. Samostatný rozpracovaný pokus splňuje kanonický scénář i bez vazby continuation.

Další krok:
- Provést T059; C01c nezahajovat před uzavřením C01b.

Navrhované další kroky:
- Po T059 vyhodnotit C01b a teprve potom případně zahájit C01c.

Technický důkaz:
- Snímek ukazuje `Připraveno` 00:00, vědomý `Start`, jednu neověřenou položku a přehratelné části. CoreDevice metadata: zachovaná dokončená session 25,093 s + 2,254 s, nový pokus jen `started.json` bez `completed.json`; žádný CAF se nekopíroval ani neposlouchal.

### 2026-09-16 23:09 CEST — první T059: ochrana PASS, audio FAIL

Hotovo:
- Ochrana před prvním odemknutím, klidový relaunch, zachovaný počet neúplných položek a přehratelnost souboru prošly. Vyslovený hlas během zamčené části však v poslechu chyběl.

Rozhodnutí:
- T059 zůstává otevřený jako FAIL audio části. Před změnou kódu proběhne řízená reprodukce, protože T016 pod zámkem dříve prošel.

Další krok:
- Zopakovat audio část T059 s Mikrofonem iPhonu a přesnými hlasovými značkami; při opakovaném FAIL diagnostikovat C01b.

Navrhované další kroky:
- C01c nezahajovat, dokud není T059 vysvětlený a C01b uzavřené.

Technický důkaz:
- Před prvním odemknutím `unavailable` bez čtení kontejneru; po odemknutí `Připraveno 00:00`, žádné samovolné nahrávání a count 1. Dokončený Komentář 53,567 s, 5 146 528 B, 48 kHz mono, bez přerušení; audio neposloucháno nástrojem.

### 2026-09-16 23:21 CEST — T059 PASS po opakování; C01b přijato

Hotovo:
- Řízené zopakování zachytilo všechny hlasové značky před zámkem, pod zámkem i po odemčení a zůstalo jednou nepřerušenou částí.

Rozhodnutí:
- T059 PASS po opakování; C01b přijato v prototypovém rozsahu. Bez opravy a nového buildu.

Další krok:
- Vyčkat na výslovný pokyn k C01c; T022 netestovat na 0.2.0.

Navrhované další kroky:
- Po schválení vyvinout C01c a potom předat T022, následně T023/T061.

Technický důkaz:
- Komentář 107,801 s, 10 352 992 B, 48 kHz mono, bez přerušení/continuation; poslech potvrzuje Míla, CAF nebyl kopírován ani poslouchán nástrojem. První tichý úsek zůstává nevysvětleným nereprodukovaným pozorováním.

### 2026-09-17 07:59 CEST — C01c 0.3.0: implementace a instalace

Hotovo:
- Segmentový zápis s 55s checkpointem, create-only journalem, obnovou po pádu a sekvenčním přehráním. Staré C01a/C01b zůstává bez migrace.
- 52/52 Swift testů, 2/2 UI testy, signed build, strict podpis, instalace a launch PASS.
- Plná projektová brána PASS, 1685/1685 testů; po jednom nesouvisejícím časovacím selhání prošel cílený test 1/1 a celý opakovaný průchod čistě.

Rozhodnutí:
- C01c zůstává rozpracované do fyzických T022/T023. Platná otevřená část je po pádu vždy označena jako částečná s možným chybějícím koncem.

Další krok:
- T022 na fyzickém telefonu; potom automaticky T023 nebo oprava C01c.

Navrhované další kroky:
- Po přijetí T022/T023 uzavřít prototypový rozsah C01c; plný T061 zopakovat v C05a.

Technický důkaz:
- Build 0.3.0 (3), profil do 22. 9. 18:16 CEST. Dvoučástový UI fixture 15 + 15 s. Inventář před/po instalaci 111 položek se shodným SHA-256 cest/velikostí; audio se nečetlo.

### 2026-09-17 11:32 CEST — Oprava pádu C01c při Start

Hotovo:
- Crash reporty určily chybnou actor izolaci tap callbacku. Build 4 vytváří callback v `nonisolated` kontextu a zachovává Swift 6 strict concurrency.
- 52/52 Swift testů, 2/2 UI testy, nepodepsaný i podepsaný arm64 build, strict podpis, rychlá statická brána, instalace a launch PASS.

Rozhodnutí:
- C01c se nepřijímá bez fyzického mikrofonu. Pět nedokončených pokusů se nemaže; nejsou vydávány za dokončené nahrávky.

Další krok:
- Krátký neutrální Start/Stop a celý poslech na 0.3.0 (4); při PASS pokračovat T022.

Navrhované další kroky:
- Po T022 vyhodnotit T023 nebo další opravu; plný T061 zůstává C05a.

Technický důkaz:
- Pět shodných `SIGTRAP` v `_swift_task_checkIsolatedSwift`. Všech 136 položek před instalací zůstalo po instalaci a launchi shodných v cestě, typu a velikosti; audio se nekopírovalo ani neposlouchalo.

### 2026-09-17 11:46 CEST — Krátký fyzický smoke buildu 4 PASS

Hotovo:
- Míla potvrdil, že Start nepadá, čas i ukazatel rostou a nový záznam lze po Stop přehrát.

Rozhodnutí:
- Oprava pádu je fyzicky potvrzená; před T022 není potřeba další vývoj. Krátký smoke nenahrazuje T022 ani přijetí C01c.

Další krok:
- Provést první průchod T022 na 0.3.0 (4), potom test zopakovat s pádem v jiné fázi otevřeného segmentu.

Technický důkaz:
- Účtenka: Komentář 10,7 s, 2 058 496 B, 48 kHz mono, jeden segment, `interrupted=false`, `recovered=false`, bez mezery. Všech 136 předchozích položek zůstalo shodných; přibylo sedm očekávaných položek. Žádný CAF se nekopíroval ani neposlouchal nástrojem.

### 2026-09-17 13:12 CEST — T022/T023 PASS; C01c přijato

Hotovo:
- T022 prošlo dvěma nucenými ukončeními v odlišných fázích otevřené části. Relaunch zůstal bez mikrofonu, obnovený rozsah byl pravdivě označený a přehratelný.
- T023 prošlo souvislým testem přes čtyři 55s hranice bez slyšitelného opakování, nevysvětlené mezery nebo useknutí.

Rozhodnutí:
- C01c 0.3.0 (4) je přijato v prototypovém rozsahu. C01c se dál nerozšiřuje; plný databázový a serverový T061 patří do C05a.

Další krok:
- Vyčkat na výslovný pokyn k C02a.

Navrhované další kroky:
- V C02a připravit pouze minimální přijímač syntetického souboru a porovnání hashe přes soukromé HTTPS. U15 zůstává C03/C04 a Viewer C08c–C08f.

Technický důkaz:
- První T022 ukázalo tři obnovitelné části a 02:18 zachovaného přehratelného rozsahu; druhé splnilo stejná kritéria při pozdějším pádu. Osm značek T023 kolem čtyř hranic bylo podle Míly slyšet jednou a ve správném pořadí. Audio nebylo čteno nástrojem; telefon byl při závěrečném zápisu nedostupný.

### 2026-09-17 14:19 CEST – Lokální C02a přijímač bezpečně ověřuje syntetický soubor serverovým hashem bez přepisu či duplicit

Hotovo:
- Lokální C02a přijímač bezpečně ověřuje syntetický soubor serverovým hashem bez přepisu či duplicit
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- C02a zůstává izolovaný standard-library prototyp; produkční serverový cíl zůstává FastAPI v samostatném prostředí Camina

Další krok:
- Po checkpointu autorizovat privátní HTTPS smoke přes Tailscale Serve se syntetickým souborem

Navrhované další kroky:
- Ověřit správný upload a shodu velikosti/SHA-256
- Ověřit chybný hash a identický retry
- Potvrdit, že Funnel ani veřejná cesta nejsou aktivní

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-camino`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-09-17 15:19 CEST — C02a privátní HTTPS smoke PASS

Hotovo:
- Dočasná privátní HTTPS cesta Tailscale Serve předala syntetický soubor loopback přijímači. Server potvrdil vlastní délku a SHA-256 a vytvořil právě jeden objekt a jednu účtenku.
- Chybný hash i konflikt byly odmítnuty, identický retry neduplikoval. Kořen Cockpitu zůstal dostupný, Funnel vypnutý a původní Serve konfigurace byla přesně obnovena.

Rozhodnutí:
- C02a je přijato v prototypovém rozsahu. Produkční cíl zůstává FastAPI v samostatném prostředí; dočasný standard-library receiver se nepovyšuje na trvalou službu.

Další krok:
- Vyčkat na výslovný pokyn k C02b.

Navrhované další kroky:
- V C02b ověřit velký soubor, souborové části, přerušení a skutečný iOS klient na cizí síti bez veřejného alternativního endpointu.

Technický důkaz:
- Tailnet HTTPS health 200; upload 201; retry 200 s `created=false`; chybný hash 422; konflikt 409; úložiště 1 objekt + 1 účtenka se shodným serverovým hashem. Cockpit health 200, pouze tailnet, Serve stav po testu shodný s výchozím.

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
- Build 0.4.0 (2) opravuje zahozené souběžné impulsy reconciliace. Je strict podepsaný, nainstalovaný a spuštěný; následná celá dávka doběhla automaticky bez dalšího klepnutí.

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

### 2026-09-19 11:45 CEST — T049 syntetická mobilní část ověřena a ukončena

Hotovo:
- Při zkoušce na iPhonu bez mobilního grantu nová dávka zůstala na 0 %, 0/13;
  ruční synchronizace neodeslala serveru relaci. Zrušení potvrzovacího dialogu
  zachovalo zákaz. Po vědomém povolení této jediné dávky Mac ověřil 13/13 částí,
  jeden objekt a účtenku, 100 663 553 B a shodný SHA-256; Míla viděl
  `Ověřeno na Macu`.
- Další syntetická dávka povolení nezdědila: po ruční synchronizaci zůstala na
  0 %, 0/13, 0/2. Server nadále evidoval pouze první ověřenou relaci. T049
  bylo potvrzeně ukončeno; receiver/cesta vypnuté, Serve přesně obnovený,
  Funnel vypnutý a syntetický důkaz zachovaný.

Rozhodnutí:
- Bez změny kritérií: syntetický mobilní průchod je úspěšný, plné T049 se
  skutečně nově pořízeným videem zůstává otevřené. Samotná shoda s návrhem
  nevyžaduje opravu kódu.

Další krok:
- Při dostupné cizí Wi-Fi provést oddělený T048 podle připraveného postupu.

Navrhované další kroky:
- Není-li cizí Wi-Fi dostupná, po samostatném zadání připravit T050 se
  zadrženým serverovým ověřením; nic z něj zatím nespouštět.
- Plné T049 s novým skutečným videem vrátit až do integrované aplikace.

Technický důkaz:
- Registrovaný audit po stopu: `phase=stopped`, `receiver_alive=false`,
  `private_route_exact=false`, `funnel_enabled=false`, `session_count=1`,
  `session_verified_count=1`, `latest_session_chunks=13/13`, `object_count=1`,
  `receipt_count=1`, `verified_match=true`, `verified_byte_count=100663553`.
  Úplné znění fyzického dialogu nebylo opsáno; spotřeba operátora nebyla měřena.
