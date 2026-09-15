# C01b — audio pod zámkem, přerušení a pokračování

Zahájeno 2026-09-15 po výslovném pokynu Míly. C01a bylo před zahájením přijaté.
**Stav: 0.2.0 (2) nainstalováno a spuštěno; krátká zkouška zámku zadána, fyzická přejímka čeká na výsledek.**

## Co se změnilo

- UIBackgroundModes obsahuje pouze audio. Běžící recorder se při přechodu
  aplikace do pozadí nezastaví. Nový Start/Pokračovat povolí controller i iOS
  adaptér pouze při aktivní aplikaci; neověřená příprava se při odchodu zruší.
- Timer i pozorování AVAudioSession vlastní model, nikoli viditelná obrazovka.
  Čas zůstává odvozený od média, nikoli od dopočtu nástěnnými hodinami.
- Hovor, změna skutečné vstupní route, reset/ztráta audio služby nebo zastavený
  recorder okamžitě pozastaví vstup a zahájí uzavření. Omezený background task
  poskytuje čas na dokončení; jeho vypršení nikdy nevytváří falešné Uloženo.
- Přerušeno nabízí Pokračovat/Ukončit. Pokračovat založí novou část stejné
  session, uchová typ a předchozí ID. Původní CAF a JSON se nepřepisují.
  Konec hovoru, návrat aplikace ani připojení sluchátek automaticky nepokračují.
- Části jsou v seznamu seskupené; každá je samostatně přehratelná. Pauza je
  interval od pozorované události k vědomému pokračování, nikoli přesná mezera
  mezi audio vzorky. Změna/neplatný clock dává neznámou délku, nikoli odhad.
- Bluetooth HFP je povolen jako dostupný vstup. Skutečný vstup určuje currentRoute;
  existence či připojení sluchátek se nevydává za důkaz použití jejich mikrofonu.
- Místní upozornění při přerušení se zkusí pouze při již uděleném oprávnění,
  s obecným textem bez obsahu nahrávky. Nová žádost o oznámení se nezobrazuje.

## Ochrana dat a kompatibilita

Nový adresář pokusu, CAF i nové JSON používají
completeUntilFirstUserAuthentication: po prvním odemknutí po restartu jsou
přístupné také při dalším zamčení. Ochrana je stále zapnutá. Původním souborům
C01a se atributy nemění a nic se nemigruje. Staré JSON bez volitelného
continuation se načítají beze změny; regression test kontroluje původní bajty.
Při načítání knihovny za zámku by staré soubory s Complete nebyly dostupné,
proto se knihovna po background dokončení obnovuje až po návratu do popředí.

Po restartu procesu se mikrofon nikdy nespustí. Dokončené části se načtou,
neověřené pokusy zůstanou viditelné jako neúplné; rozpracované in-memory
Pokračovat se automaticky neobnovuje. To není journal ani záchrana C01c.

Zůstává jeden soubor na nepřerušený úsek. Bez automatických segmentů zatím
není doložen 60s limit ztráty ani G1. Soubory nejsou pro ostrá média a nemají
ověřenou další kopii; audio se v tomto kroku z telefonu nestahuje.

## Ověření

- Swift XCTest: **47/47 PASS**, z toho 15 nových testů pro C01b; 32 původních prošlo.
  Zahrnuje modelový background/return bez restartu, zákaz Start v pozadí,
  okamžité a opakované přerušení, route před prvním mediálním tickem, explicitní
  navazování částí, chybu pokračování, revokaci oprávnění, neověřené dokončení,
  přehrávání při přerušení, neplatný clock, druhé přerušení a legacy JSON.
  Pořadí částí sleduje uložené vazby i při posunu systémových hodin dozadu.
- Podepsaný iOS Debug build 0.2.0 (2): finální build PASS, strict podpis PASS; profil do 22. září 18:16 CEST.
- Info.plist finálního buildu: UIBackgroundModes = [audio], správný hlavní bundle;
  codesign --verify --deep --strict exit 0.
- UI testy simulátoru: **2/2 PASS**, 0 přeskočeno, asi 42,6 s. Snímek průběhu
  00:03 / 00:30 vizuálně zkontrolován, bez problémů s rozložením.
- Plná projektová brána: **PASS, 1684/1684 testů**, asi 385 s; jde o společné
  projektové testy, nikoli testy audia.
- Finální balíček odpovídá SHA-256 všech aktuálních zdrojů; neobsahuje
  simulator-only testovací launch flags. Dedikovaný simulátor byl po testu vypnut.
- Instalace/spuštění 0.2.0: **PASS**, živě ověřeno přes devicectl.
- Původní soubory: inventář všech 15 cest/velikostí před/po shodný; bez čtení audia.
- Fyzické T016/T018–T021/T024/T059: **NEPROVEDENO**.

Příkazy:

```sh
swift test --package-path camino/prototypes/audio --scratch-path /private/tmp/camino-c01b-swift
xcodebuild -project camino/prototypes/audio/CaminoAudio.xcodeproj -scheme CaminoAudio -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath '<private tmp>' -allowProvisioningUpdates build
xcodebuild -project camino/prototypes/audio/CaminoAudio.xcodeproj -scheme CaminoAudioUITests -configuration Debug -destination 'platform=iOS Simulator,id=<private>' -derivedDataPath '<private tmp>' -resultBundlePath '<private>/UIResults.xcresult' test
.venv/bin/python -B scripts/cockpit_quality_gate.py
```

Podrobné účtenky jsou pouze v ignorované soukromé složce uvedené ukazatelem
latest_c01b.txt, zdrojové testy jsou syntetické. Žádný účet ani identifikátor
telefonu není součástí reportu/Gitu. Testy simulátoru nejsou důkaz mikrofonu,
zámku, hovoru, Bluetooth nebo ochrany dat před prvním odemknutím.

## Další krok

Aktualizace je nainstalovaná a spuštěná. Nejdřív krátká zkouška zámku asi 30 sekund se slyšitelnými značkami před,
pod zámkem a po něm. Potom samostatně 30minutový T016 a další scénáře podle
[C01b_BACKGROUND_AUDIO.md](../tasks/C01b_BACKGROUND_AUDIO.md). Bez výsledků
nelze C01b přijmout; C01c ani G0/G1 nejsou tímto uzavřeny.

## Technické podklady

- [Apple: audio recording apps a background režim](https://developer.apple.com/library/archive/documentation/Audio/Conceptual/AudioSessionProgrammingGuide/AudioGuidelinesByAppType/AudioGuidelinesByAppType.html)
- [Apple: přerušení audio session](https://developer.apple.com/documentation/avfaudio/handling-audio-interruptions)
- [Apple: změny route](https://developer.apple.com/documentation/avfaudio/responding-to-audio-route-changes)
- [Apple: ochrana po prvním odemknutí](https://developer.apple.com/documentation/foundation/fileprotectiontype/completeuntilfirstuserauthentication)
- [Apple: Bluetooth HFP](https://developer.apple.com/documentation/avfaudio/avaudiosession/categoryoptions-swift.struct/allowbluetoothhfp)
- Zadání: F16–F18/F42 a T016/T018–T021/T024/T059 z původního balíčku v0.4,
  který zůstává beze změny.

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
