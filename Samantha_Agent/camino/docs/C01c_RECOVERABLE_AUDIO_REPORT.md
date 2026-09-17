# C01c — report obnovitelných audio částí

Zahájeno 2026-09-17 po výslovném pokynu Míly. C01a a C01b byly před zahájením
přijaté v prototypovém rozsahu.

**Stav: implementace 0.3.0 (3) automaticky ověřená, podepsaná, nainstalovaná
a spuštěná na iPhonu; fyzické T022/T023 zatím NEPROVEDENO.**

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

## Ověření

- Swift XCTest: **52/52 PASS**. Pět nových testů pokrývá strop checkpointu,
  obnovu platné otevřené části bez aktivace mikrofonu, poškozený konec,
  osiřelou část po mezeře, idempotenci a normální vícečástové dokončení.
- Nepodepsaný i podepsaný iOS Debug build: **PASS**. Strict podpis: **PASS**;
  profil platí do 22. září 2026 18:16 CEST.
- UI testy: **2/2 PASS** na simulátoru iPhone 14 Plus / iOS 26.3.1. Fixture
  obsahuje dvě navazující 15s části; prošel průběh, Stop, opakování i relaunch
  bez automatického přehrání. Snímek byl vizuálně zkontrolovaný bez vady
  rozložení. První běh se kvůli systémovému `signal kill` test runneru nedostal
  k bootstrapu; po čistém restartu dedikovaného simulátoru opakování prošlo.
- Instalace a spuštění 0.3.0 (3) na připojeném iPhonu: **PASS**, bez odinstalace.
  Inventář Application Support před/po je přesně shodný: 111 položek,
  28 `started.json`, 27 `completed.json` a 28 původních `audio.caf`; shoduje se
  i SHA-256 seznamu relativních cest, velikostí a typu položky. Jde jen o
  technická metadata, audio nebylo kopírováno ani posloucháno.
- Plná projektová brána: **PASS, 1685/1685 testů**. První běh měl jediné
  časovací selhání nesouvisejícího Human–Adam worker testu; cílené opakování
  prošlo 1/1 a následný celý průchod prošel čistě.
- Fyzické T022/T023: **NEPROVEDENO**.

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

Provést T022 podle zadání: neutrální souvislý záznam alespoň 2:15, několik
časových značek, nucené ukončení během další otevřené části, relaunch bez
automatického mikrofonu a celý poslech nabídnutého zachovaného rozsahu. Teprve
po jeho vyhodnocení následuje T023.
