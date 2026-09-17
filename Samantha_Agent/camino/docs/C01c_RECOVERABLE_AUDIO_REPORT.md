# C01c — report obnovitelných audio částí

Zahájeno 2026-09-17 po výslovném pokynu Míly. C01a a C01b byly před zahájením
přijaté v prototypovém rozsahu.

**Stav: pád při prvním Start opraven ve verzi 0.3.0 (4), automaticky ověřeno,
podepsáno, nainstalováno a spuštěno na iPhonu bez změny dosavadních dat.
Krátký fyzický Start/Stop a T022/T023 zatím NEPROVEDENO.**

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
- Krátký fyzický Start/Stop buildu 4 a T022/T023: **NEPROVEDENO**.

Automatizace používá jen syntetická data v dočasných složkách. Neprokazuje
skutečný mikrofon, zámek, spotřebu, přechod CAF částí bez slyšitelné vady ani
záchranu po reálném nuceném ukončení na iPhonu.

## Otevřeno a rizika

- `AVAudioEngine` nahrazuje v prototypu dosavadní `AVAudioRecorder`; skutečná
  route, formát, background běh a spotřeba se musí znovu ověřit na telefonu.
- Otevírání dalšího souboru probíhá v tap callbacku. Teprve T023 rozhodne, zda
  na fyzickém zařízení nevzniká slyšitelná mezera nebo opakování.
- Platná poslední otevřená CAF část může být po pádu dekódovatelná, ale vždy se
  označí jako zotavená s možným chybějícím koncem. Nic se nedomýšlí.
- C01c neřeší síťovou finalizaci ani produkční databázi; plný T061 se vrátí v C05a.

## Další krok

Nejdřív na buildu 4 provést krátký neutrální Start/Stop a celý poslech. Pokud
aplikace nespadne, čas i ukazatel rostou a záznam je přehratelný, pokračovat
T022 podle zadání: alespoň 2:15, časové značky, nucené ukončení během otevřené
části, relaunch bez automatického mikrofonu a celý poslech zachovaného rozsahu.
Teprve po jeho vyhodnocení následuje T023.
