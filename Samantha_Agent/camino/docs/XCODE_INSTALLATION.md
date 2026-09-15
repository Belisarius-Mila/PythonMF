# Xcode 26.3 — instalační doklad

Aktualizace 2026-09-15 08:19 CEST: C01a ověřilo spárovaný iPhone, zapnutý Developer Mode
a DDI. Skutečný Xcode build však blokuje platform support iOS 26.2 navzdory
přítomnému SDK. [Aktuální důkaz a rozsah](C01a_AUDIO_PROTOTYPE_REPORT.md).

Datum: 14. září 2026, aktualizováno po prvním nastavení v 23:05 CEST.
Navazuje na C00 a následný výslovný Mílův pokyn ověřit místo a nainstalovat Xcode.

## Výsledek

**Instalace Xcode 26.3 Universal i první nastavení jsou dokončené.**
Licence již použití SDK neblokuje. iPhone SDK 26.2 a nástroje jsou dostupné.
Xcode je také aktuálně vybraným vývojovým prostředím. Build a instalace aplikace
na cílovém iPhonu dosud neproběhly; C01a zůstává nezahájené.

## Ověřené kroky instalace — původní stav před dokončením licence

| Kontrola | Důkaz / výsledek |
|---|---|
| Zdroj | Míla stáhl z přihlášeného Apple Developer katalogu `Xcode_26.3_Universal.xip`. |
| Velikost archivu | 2 871 807 039 bajtů, přibližně 2,67 GiB. |
| SHA-256 archivu | `cf87232e0419785170edcfa070b750f28808ec00b489ab540c08b7d197c79ae4` |
| Podpis archivu | `pkgutil --check-signature`: `signed Apple Software`; řetězec Software Update → Apple Software Update Certification Authority → Apple Root CA. |
| Velikost po rozbalení podle metadat XIP | `UncompressedSize=12179714548`, přibližně 11,34 GiB; metadata přečtena bez rozbalení celého payloadu. |
| Kapacita před rozbalením | 25,95 GiB volných již se staženým archivem; dost na deklarovanou velikost aplikace, případný mezisoubor a provozní rezervu. Simulátory nebyly zahrnuty do instalace. |
| Instalace | `/usr/bin/xip --expand` z `/Applications`, až po ověření neexistence cílového `Xcode.app`; exit 0. |
| Poznámka k XIP | Samotný expander vypsal `validation not attempted`; proto doklad nestojí jen na něm. Podpis byl nezávisle kontrolován předem přes pkgutil a po rozbalení přes codesign a Gatekeeper. |
| Verze aplikace | Přímý `Contents/Developer/usr/bin/xcodebuild -version`: **Xcode 26.3, build 17C529**, exit 0. |
| Minimum macOS | Info.plist: 15.6; místní Mac má 15.7.9. |
| Architektury | Hlavička Mach-O skutečného Xcode executable: **x86_64 a arm64**. Universal obsahuje Intel. |
| Podpis aplikace | `codesign --verify --deep --strict --verbose=2`: exit 0, valid on disk, satisfies its Designated Requirement. |
| Gatekeeper | `spctl --assess --type execute --verbose=2`: exit 0, accepted, source Apple System. |
| iPhone SDK v aplikaci | Balíček obsahuje `iPhoneOS26.2.sdk` a odkaz `iPhoneOS.sdk`. |
| Aktivní použití SDK | `xcrun --no-cache --sdk iphoneos --show-sdk-version` s procesovým `DEVELOPER_DIR` skončil exit 69: nepřijatá licence Xcode. Přítomnost SDK není zatím doklad použitelné build cesty. |
| První nastavení | `xcodebuild -checkFirstLaunchStatus`: exit 69. |
| Oprávnění správce | `sudo -n true`: vyžaduje heslo. Hesla ani Keychain nebyly čteny; oprávnění se neobcházela. |
| Otevření pro uživatele | `open -a /Applications/Xcode.app`: exit 0. Obsah dialogu nebyl agentem vizuálně ověřen. |
| Volno po instalaci a kontrolách | Přibližně **21,41 GiB**, okamžitý stav. APFS komprese znamená, že deklarované nekomprimované bajty nejsou totožné s fyzickým obsazením. |

## Zachovaný rozsah

Archiv ve Stahování zůstal zachovaný. Žádné soubory se nemazaly, systém se
neaktualizoval a globální `xcode-select` se nepřepínal; kontroly používaly
procesový `DEVELOPER_DIR`. Cílový iPhone 14 Plus / iOS 26.6.1 nebyl párován,
nenahrávalo se audio a nevznikl zdrojový kód Camino. Placené AI, členství,
veřejný přístup ani serverové služby se nezřizovaly.

## Dokončení prvního nastavení — 23:05 CEST

Míla poskytl nový snímek úvodní obrazovky Xcode 26.3 s nabídkou vytvoření,
klonování a otevření projektu. Následné příkazy nezávisle potvrdily dokončení:

| Kontrola | Aktuální výsledek |
|---|---|
| `xcodebuild -version` přímo z instalované aplikace | Exit 0, Xcode 26.3 / 17C529. |
| `xcodebuild -checkFirstLaunchStatus` | **Exit 0**, první nastavení dokončené. |
| `xcrun --no-cache --sdk iphoneos --show-sdk-version` | **Exit 0, 26.2**. |
| `xcrun --no-cache --sdk iphoneos --find clang` | Exit 0, compiler v XcodeDefault.xctoolchain. |
| `xcrun --no-cache --find devicectl` | Exit 0, nástroj v instalovaném Xcode. |
| Samostatný `xcode-select -p` bez procesového override | `/Applications/Xcode.app/Contents/Developer`. Aktivní volba po uživatelském prvním nastavení; agent nepoužil globální přepínací příkaz. |
| Volné místo | Přibližně **20,91 GiB**. |

Předchozí blokace licence je vyřešená. Z těchto kontrol neplyne, že byl
proveden build, signing, párování nebo audio test iPhonu 14 Plus / iOS 26.6.1.
Další projekt se v uvítacím okně nezakládal; pokračování C01a vyžaduje nový pokyn.

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
