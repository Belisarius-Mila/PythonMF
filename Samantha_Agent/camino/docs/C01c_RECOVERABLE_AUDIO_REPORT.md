# C01c — report obnovitelných audio částí

Zahájeno 2026-09-17 po výslovném pokynu Míly. C01a a C01b byly před zahájením
přijaté v prototypovém rozsahu.

**Stav: C01c přijato v prototypovém rozsahu ve verzi 0.3.0 (4). Pád při prvním
Start je opravený; automatické ověření, krátký fyzický smoke, oba průchody T022
a poslechová kontrola segmentových přechodů T023 prošly.**

## Implementace

- Jeden `AVAudioEngine` input tap zapisuje obnovitelné CAF části bez vědomého
  restartu vstupu mezi checkpointy.
- Cíl checkpointu je 55 sekund, návrhový strop části 60 sekund. Nadměrná vstupní
  dávka selže uzavřeně místo tichého překročení stropu.
- Journal vzniká před aktivací audio driveru. Stabilní části jsou neměnné a
  normální dokončení má create-only metadata.
- Start úložiště opraví journalovaný pokus z platných částí, neplatný konec
  zachová a označí výsledek jako obnovenou částečnou nahrávku. Mikrofon přitom
  není aktivován.
- Osiřelá platná část se nezahodí; neznámá mezera je viditelná. Opakovaná obnova
  nevytváří druhou položku.
- Přehrávání ověřených částí je sekvenční. Legacy C01a/C01b `audio.caf` a JSON
  se čtou v původním formátu bez migrace či přepisu.

### Oprava pádu při Start

- Pět shodných systémových crash reportů ukázalo `SIGTRAP` v
  `_swift_task_checkIsolatedSwift` uvnitř tap callbacku. Nešlo o neplatný
  hardwarový formát ani první zápis CAF.
- `IOSAudioDriver` je `@MainActor`; původní inline closure proto zdědila
  izolaci hlavního aktoru, přestože ji `AVAudioEngine` volá na real-time audio
  frontě.
- Build 4 vytváří callback v explicitně `nonisolated` helperu a předává mu
  interně zamčený `SegmentedCaptureWriter`. Přísné kontroly Swift 6 zůstaly
  zapnuté; audio architektura, checkpointy ani formát dat se nemění.

## Ověření

- Swift XCTest po opravě: **52/52 PASS**. Pět testů C01c pokrývá strop checkpointu,
  obnovu platné otevřené části bez aktivace mikrofonu, poškozený konec,
  osiřelou část po mezeře, idempotenci a normální vícečástové dokončení.
- Nepodepsaný i podepsaný iOS Debug build po opravě: **PASS**. Strict podpis: **PASS**;
  profil platí do 22. září 2026 18:16 CEST.
- UI testy po opravě: **2/2 PASS** na simulátoru iPhone 14 Plus / iOS 26.3.1. Fixture
  obsahuje dvě navazující 15s části; prošel průběh, Stop, opakování i relaunch
  bez automatického přehrání. Snímek byl vizuálně zkontrolovaný bez vady
  rozložení. Opravný průchod proběhl čistě.
- Instalace a spuštění 0.3.0 (4) na připojeném iPhonu: **PASS**, bez
  odinstalace. Všech 136 položek před instalací zůstalo po instalaci i launchi
  shodných v relativní cestě, typu a velikosti. Jde o původních 111 položek a
  25 zachovaných technických položek z pěti neúspěšných pokusů; nic se
  nemazalo a audio nebylo kopírováno ani posloucháno.
- Plná projektová brána před opravou: **PASS, 1685/1685 testů**. První běh měl jediné
  časovací selhání nesouvisejícího Human–Adam worker testu; cílené opakování
  prošlo 1/1 a následný celý průchod prošel čistě. Po opravě prošla rychlá
  statická brána; změněná audio cesta je krytá výše uvedenými cílenými testy a
  oběma arm64 buildy.
- Krátký fyzický Start/Stop buildu 4: **PASS podle Míly**. Aplikace nespadla,
  čas i ukazatel rostly a nový záznam šel přehrát. Technická účtenka potvrzuje
  jeden normálně dokončený Komentář 10,7 s, 2 058 496 B, 48 kHz mono, jeden
  segment, bez přerušení, recovery a mezery. Všech 136 předchozích položek
  zůstalo beze změny; přibylo sedm očekávaných položek nového pokusu. Žádný CAF
  se nekopíroval ani neposlouchal nástrojem.
- T022: **PASS podle Míly ve dvou odlišných fázích otevřené části**. Po nuceném
  ukončení se mikrofon sám nespustil, aplikace nabídla pravdivě označenou
  obnovenou částečnou nahrávku a zachovaný rozsah šel celý přehrát. Snímek
  prvního průchodu ukazuje `Připraveno 00:00`, tři obnovitelné části a 02:18
  zachovaného přehratelného rozsahu; druhý průchod prošel stejnými kritérii při
  pádu v pozdější fázi otevřené části.
- T023: **PASS podle Míly**. V souvislém nejméně čtyřminutovém testu byly
  poslechem ověřeny značky před a po čtyřech 55s hranicích; všechny zazněly
  jednou, ve správném pořadí, bez opakování, nevysvětlené mezery či useknutí.

Automatizace používá jen syntetická data v dočasných složkách. Neprokazuje
skutečný mikrofon, zámek, spotřebu, přechod CAF částí bez slyšitelné vady ani
záchranu po reálném nuceném ukončení na iPhonu.

## Otevřeno a rizika

- `AVAudioEngine` nahrazuje v prototypu dosavadní `AVAudioRecorder`; skutečný
  mikrofon, background běh a segmentové přechody prošly prototypovou fyzickou
  přejímkou. Dlouhodobá terénní spotřeba zůstává mimo rozsah C01c.
- Otevírání dalšího souboru probíhá v tap callbacku. T023 na fyzickém zařízení
  neodhalil slyšitelnou mezeru ani opakování na čtyřech přechodech.
- Platná poslední otevřená CAF část může být po pádu dekódovatelná, ale vždy se
  označí jako zotavená s možným chybějícím koncem. Nic se nedomýšlí.
- C01c neřeší síťovou finalizaci ani produkční databázi; plný T061 se vrátí v C05a.

## Další krok

C01c dále nerozšiřovat. Další plánovanou etapou je po výslovném pokynu C02a;
plný databázový a serverový T061 se zopakuje v C05a.
