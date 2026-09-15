# TVBCP: Camino

Pracovni proud: `project-camino`
Typ: `Project`
Rezim: `active`
Priorita: 1

## Cíl a hranice

Samostatný soukromý cestovní deník podle v0.4. Založení a napojení na Human–Adam
je první organizační krok; aplikace ani audit prostředí tím nevznikají.

## Aktuální stav a další krok

- C01a rozpracováno: izolovaný audio prototyp, 25 testů logiky a syntetického CAF audia OK; přímá kompilace/linkování pro arm64 iOS 17 / SDK 26.2 prošly.
- iPhone 14 Plus při aktuální kontrole odpojený; dřívější párování a Developer Mode ověřeny, živé spojení je nutné obnovit.
- Xcode 26.3 / iOS SDK 26.2: podepsaný Debug build CaminoAudio pro iPhone prošel (exit 0), `codesign --verify --deep --strict` exit 0. Jedna platná vývojová identita; profil platí do 2026-09-22 18:16 CEST. Výběr týmu je pouze v ignorovaném LocalSigning.xcconfig.
- Celý C01a BLOCKED: instalace, ruční UI/poslech a fyzické T015/T017/T025 NEPROVEDENO. C01b nezahájeno.
- Restart a následný schválený úklid dokončeny. Před zahájením instalace bylo na SSD 85,79 GiB volných. Dřívější přesun USA neopakovat.
- P+n ověřeno pro `e4e667b5`: 1684/1684 testů, nový Cockpit, smoke 5/5.
  Tento dodatečný handoff předchozí p+n nezahrnovalo.


Připojit a odemknout iPhone, ověřit dostupnost zařízení a nainstalovat podepsaný CaminoAudio.app. Potom provést fyzickou přejímku T015/T017/T025; nahrávání zahajuje uživatel vědomým Start.

## Rizika

- Bez funkčního Xcode buildu, podpisu a fyzické přejímky nelze prototyp označit za přijatý; G0/G1 nesplněné.
- Pouze krátké foreground audio; žádná segmentace, záchrana po pádu během zápisu ani pokračování pod zámkem.
- Vzorky v telefonu mají jen místní kopii, nejsou určeny pro ostrá média; žádná AI, síť, export nebo automatické mazání.
- Podepsaný build není instalace ani fyzická přejímka; vývojový profil je časově omezený. U01–U11 se neotevírají.

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
