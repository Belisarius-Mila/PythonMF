# C01b — audio pod zámkem, přerušení a pokračování

Zahájeno 2026-09-15 po výslovném pokynu Míly. C01a bylo před zahájením přijaté.
**Stav: 0.2.0 (2) nainstalováno a spuštěno; krátký test zámku a T016/T018–T021/T024 PASS v dosavadním rozsahu, čeká T059.**
V0.5 + U15 byly přijaty 2026-09-16; význam tohoto izolovaného audio prototypu
a zbývající T059 se tím nemění. Finální soukromí Momentu patří do C03/C04.

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
- Fyzické T016, T018–T020 a T024: **PASS podle Míly**; T021: **PASS v rozsahu C01b prototypu**, plná integrace se zopakuje v C04; T059: **NEPROVEDENO**.

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

Krátký funkční test zámku a T016/T018–T021/T024 v dosavadním rozsahu Míla potvrdil. Následuje T059 podle
[C01b_BACKGROUND_AUDIO.md](../tasks/C01b_BACKGROUND_AUDIO.md). Bez zbývajících výsledků
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

### 2026-09-16 13:43 CEST — T016 potvrzen na fyzickém telefonu

Hotovo / důkaz:
- Míla potvrdil přibližně 30:16 nahrávání, převážně pod zámkem, v režimu Letadlo. Nahrávání proběhlo bez problému a celý záznam se přehrál bez hlášeného výpadku. T016: PASS podle uživatele.
- Pokus o přehrávání při zamčené obrazovce neběžel. T016 ověřuje nahrávání pod zámkem, nikoli background přehrávání; toto pozorování proto T016 nemění na FAIL.

Hranice důkazu a rizika:
- Velikost souboru nebyla sdělena. Dnešní zpráva znovu nečetla verzi aplikace, model telefonu ani iOS; výsledek navazuje na evidovaný kontext Camino Audio 0.2.0 (2) na iPhone 14 Plus / iOS 26.6.1.
- Jediný nepřerušený soubor C01b není důkaz segmentace, journalu ani 60s obnovy C01c. Audio zůstává pouze na telefonu.

Další krok:
- T018 s dostupnými sluchátky: ověřit skutečný aktivní vstup, stání/chůzi a zámek. Potom T019–T021/T024/T059; C01c nezahajovat.

Ověření:
- Kód se neměnil; automatické testy se neopakovaly. Změněn je pouze zápis fyzického výsledku a navazující projektový stav.

### 2026-09-16 19:46 CEST — T018 PASS a technická kontrola přerušení

Hotovo / důkaz:
- Míla potvrdil AirPods jako zobrazený aktivní mikrofon, několikaminutové záznamy ve stoje i za chůze pod zámkem, bez výpadků a s úspěšným celým poslechem. T018: PASS pro ověřené podmínky; vítr nebyl přítomen.
- Snímek v Downloads ukázal T016 30:24 a jednu session rozdělenou na Část 1, pauzu a Část 2. Soukromý obsah snímku ani audia se do projektu nekopíroval.
- Živý CoreDevice inventář na připojeném iPhone 14 Plus potvrdil Camino Audio 0.2.0 (2). T016 má 1824,406 s, 175 147 072 B, 48 kHz mono a `interrupted=false`.
- Telefonát dokončil první samostatný CAF/JSON po 188,555 s s `interrupted=true`. Vědomé Pokračovat vytvořilo nový samostatný CAF/JSON o 293,571 s, navázaný na stejnou session a předchozí část, s evidovanou pauzou 145,130 s. Grafické seskupení je očekávané; média se neslepila do jednoho souboru.
- Pozdější záznam přes mikrofon iPhonu je podle metadat samostatná nová session bez continuation. Nešlo o automatické pokračování rozpracované session.

Hranice důkazu a rizika:
- Odchozí hovor je dílčí důkaz T019, nikoli úplný předepsaný scénář příchozího hovoru jednou ignorovaného a jednou přijatého. Obsah hovoru nebyl nástrojem poslouchán.
- Samostatný nový záznam po odpojení AirPods není T020; odpojení a opětovné připojení skutečně aktivního mikrofonu během běžícího záznamu čeká.
- Mikrofon iPhonu v kapse byl podle Míly výrazně tišší a méně kvalitní. To je očekávatelné praktické omezení, nikoli důkaz chyby zápisu. Výkon AirPods ve větru nebyl ověřen.

Další krok:
- Dokončit T019 příchozím hovorem: jednou ignorovat, jednou přijmout; ověřit zachovanou část, žádný zvuk hovoru a žádné samovolné pokračování. Potom T020–T021/T024/T059; C01c nezahajovat.

Ověření:
- Přečteny pouze malé technické JSON účtenky a inventář velikostí; žádný CAF se nekopíroval ani neposlouchal. Kód beze změn, automatické testy se neopakovaly.

### 2026-09-16 20:25 CEST — T019 PASS

Hotovo / důkaz:
- Míla potvrdil PASS ignorovaného i přijatého příchozího běžného telefonního hovoru: části před a po přerušení jsou přehratelné, nic z hovoru v audu není a nahrávání se samo neobnovilo.
- Technická metadata potvrzují dvě první části označené `interrupted=true`: 44,410 s a 26,798 s. Jejich vědomá pokračování jsou samostatné části stejné session: 21,551 s po pauze 43,153 s a 20,999 s po pauze 112,272 s. Všechny čtyři části jsou 48 kHz mono.
- Jeden dřívější běžně ukončený záznam bez přerušení a bez continuation byl od T019 oddělen.

Hranice důkazu a rizika:
- Poslech a nepřítomnost hovoru v audu potvrzuje Míla; nástroj četl pouze malé technické JSON účtenky. Žádný CAF se nekopíroval ani neposlouchal.
- T020–T021/T024/T059, C01b/G0/G1 zůstávají otevřené. C01c nezahájeno.

Další krok:
- Provést T020 změnou skutečně aktivního vstupu během běžícího záznamu; ověřit přerušení, zachování staré části, žádné samovolné pokračování a novou navazující část stejné session.

Ověření:
- Kód aplikace se neměnil; aktualizuje se pouze výsledek fyzické přejímky a navazující projektový stav.

### 2026-09-16 20:39 CEST — T020 PASS

Hotovo / důkaz:
- Míla potvrdil, že odpojení skutečně aktivních AirPods přerušilo záznam, první část je přehratelná, vědomé pokračování zobrazilo mikrofon iPhonu, nic se samo neobnovilo a všechny části jsou přehratelné.
- Po opětovném připojení se AirPods staly aktivním vstupem až při dalším vědomém spuštění. Technická metadata přitom potvrzují, že druhá část byla také systémově přerušena a třetí vznikla až jako její explicitní continuation.
- Session obsahuje tři samostatné části: 34,776 s s `interrupted=true`, pokračování 25,944 s po pauze 28,002 s opět s `interrupted=true` a závěrečné pokračování 18,215 s po pauze 90,312 s s `interrupted=false`. Všechny jsou 48 kHz mono.

Vyhodnocení a rizika:
- T020 PASS. Pouhé Bluetooth připojení není totéž jako aktivní vstup; skutečná route AirPods se potvrdila až po vědomé reaktivaci audio session. To odpovídá F17 a neznamená samovolné pokračování.
- Poslech potvrzuje Míla; nástroj četl jen technické JSON účtenky. Žádný CAF se nekopíroval ani neposlouchal. T021/T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.

Další krok:
- Provést T021 v prototypovém rozsahu: za běžící Úvahy ověřit zákaz přehrávače a druhého recorderu a návrat z jiné aplikace bez zrušení aktivního záznamu. Video/Moment patří až do C04.

### 2026-09-16 21:27 CEST — T021 PASS v rozsahu C01b prototypu

Hotovo / důkaz:
- Míla potvrdil neaktivní volbu typu i Přehrát, nemožnost spustit druhý recorder, pokračování stejné Úvahy po návratu z jiné aplikace, růst času, jednu část bez přerušení a celý poslech v pořádku.
- Nejnovější technická Úvaha má 56,350 s, 5 413 696 B, 48 kHz mono, `interrupted=false` a nemá continuation. Předchozí samostatná Úvaha 31,717 s je oddělena jako přípravný pokus, nikoli druhá část testované session.

Vyhodnocení a rizika:
- T021 PASS v rozsahu C01b prototypu. Video a integrace Momentu zde nejsou implementované; úplný původní scénář se musí zopakovat v C04, aby pozdější galerie/přehrávač nezavedly soupeřící session.
- Poslech potvrzuje Míla; nástroj četl jen technické JSON účtenky. Žádný CAF se nekopíroval ani neposlouchal. T024/T059, C01b/G0/G1 zůstávají otevřené; C01c nezahájeno.

Další krok:
- T024: po dokončené části vědomě pokračovat, za běžícího pokračování nuceně ukončit aplikaci a po otevření ověřit žádný aktivní mikrofon, zachovanou dokončenou část a pravdivě přiznaný neověřený pokus. Potom T059.

### 2026-09-16 22:41 CEST — T024 PASS

Hotovo / důkaz:
- Míla potvrdil očekávané chování po nuceném ukončení aplikace za rozpracovaného audia. Snímek po relaunchi ukazuje klidový stav `Připraveno` 00:00, vědomý `Start`, jednu neověřenou nebo neúplnou položku a zachované části s dostupným přehráním.
- Živý CoreDevice inventář a pouze malé technické JSON účtenky potvrzují dokončenou session: první část 25,093 s, `interrupted=true`, pokračování 2,254 s po pauze 25,729 s, 48 kHz mono. Novější samostatná Úvaha má `started.json` a audio soubor, ale žádný `completed.json`; aplikace ji proto pravdivě započítala jako neověřenou.

Vyhodnocení a rizika:
- T024 PASS. Nuceně ukončený pokus byl samostatná nová Úvaha, nikoli continuation předchozí session. Kanonický T024 vyžaduje pád s rozpracovaným audiem, žádnou automatickou aktivaci mikrofonu a nabídku zachovaného přehratelného rozsahu; tyto podmínky jsou splněné.
- Nejde o důkaz záchrany otevřeného CAF, segmentového journalu ani omezení ztráty na 60 s; to patří do C01c. Žádný CAF se nekopíroval ani neposlouchal. Oprava ani nový build nejsou potřeba.

Další krok:
- Provést T059. C01c nezahajovat před uzavřením C01b.
