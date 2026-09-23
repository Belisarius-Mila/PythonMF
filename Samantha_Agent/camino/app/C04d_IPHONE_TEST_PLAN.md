# C04d — cílený test detailu a revizí na iPhonu

Stav 2026-09-23: C04d je podepsaná a aktualizací stejného bundle ID
nainstalovaná na iPhonu 14 Plus / iOS 26.6.1 jako Camino 0.1.0 (2). Starší
C04b Momenty a média zůstaly dostupné. Míla dokončil cílený fyzický průchod
se syntetickým obsahem; žádný obsah audia, fotografií ani textu se nekopíroval
do Gitu.

## Výsledek 2026-09-23

| Test | Výsledek a hranice důkazu |
|---|---|
| Zachování dat | **PASS** — instalace proběhla bez odinstalace; starší C04b záznamy i média zůstaly dostupné a přehratelné. |
| T010 | **PASS** — lidská textová revize přežila uložení a znovuotevření; původní audio zůstalo přehratelné. |
| T019 | **PASS** — zvlášť ignorovaný i přijatý příchozí hovor zachovaly dosavadní část, jasně přerušily záznam, nezachytily hovor a samy nepokračovaly. |
| T020 | **PASS** — změna aktivního vstupu z mikrofonu iPhonu na AirPods zachovala první část; pokračování bylo vědomé, ve stejné Úvaze, a obě části šly přehrát. |
| T021 | **PASS** — video, přehrávač ani druhá Úvaha nevytvořily soupeřící session; původní session zůstala zachovaná. |
| T026 | **PASS** — v režimu Letadlo fungovaly místní dny, filtry, detail, uložený text a místní média bez vymyšleného souhrnu či serverového potvrzení. |
| T030 | **PASS** — soukromý dovětek zůstal samostatnou zamčenou Úvahou s vazbou `Patří k`; změna kapitoly zachovala původní čas, soukromí i přehrávání. |
| T038 | **ČÁSTEČNĚ / fyzicky NEOVĚŘENO** — přednost lidské revize je doložená synteticky a automatizovaně; bez produkční AI nevznikl pozdější automatický text pro fyzický end-to-end test. |
| T039 | **PASS** — po nuceném ukončení aplikace se obnovil přesný koncept bez publikování; nová lidská revize vznikla až po `Uložit` a audio zůstalo přehratelné. |
| T040 | **PASS v lokálním rozsahu** — zamknutí, skrytí a obnovení zachovaly soukromí, text i audio; dialog nesliboval uvolnění místa. Serverová invalidace zůstává C05/C08. |
| T041 | **PASS** — běžná fotografie zůstala samostatná a `Do deníku`; soukromý dovětek byl oddělená propojená Úvaha `Jen pro mě`. |
| T096 | **PASS v lokálním rozsahu** — Úvaha začala `Jen pro mě`, varování popsalo budoucí text a povolené původní audio, vložení ukázalo `Do deníku` a `Místní revize · čeká na server`; návrat na `Jen pro mě` byl místně okamžitý a audio zůstalo přehratelné. Serverové přijetí ani Viewer se netvrdí. |

C04d je tím fyzicky přijaté v dostupném lokálním a zařízení ověřitelném
rozsahu. T038 zůstává otevřené pro pozdější integrační důkaz s produkční AI;
serverové přijetí, konflikt druhého editoru, Viewer a invalidace odvozenin
patří C05/C08.

## Před startem

1. Zachovat současná data aplikace a nainstalovat C04d přes stejné bundle ID;
   aplikaci předem neodinstalovávat. Po startu ověřit, že starší C04b Momenty a
   média zůstaly dostupné.
2. Vytvořit jeden nový neosobní Moment s krátkým komentářem nebo fotografií a
   jednu novou Úvahu. Server C05 není připojený, proto se žádná místní revize
   nesmí tvářit jako serverem potvrzená.
3. T019–T021 opakovat jen nad integrovanou aplikací. Dřívější C01b důkaz
   samotného audio prototypu zůstává užitečný, ale tuto integraci nedokazuje.

## Průchod

| Test | Úkon a pozorování pro PASS |
|---|---|
| T010 | V detailu upravit syntetický text, uložit a znovu otevřít. Nová lidská revize je aktuální; původní audio nebo médium se stále přehrává a jeho technická identita se nezměnila. |
| T019 | Během Úvahy jednou ignorovat a jednou přijmout příchozí hovor. Zachované části jsou pravdivě označené, hovor se nenahraje a záznam se sám znovu nespustí. |
| T020 | Během Úvahy změnit skutečně aktivní audio vstup. Dosavadní část zůstane zachovaná; případné pokračování je vědomé a patří stejné session. |
| T021 | Při aktivní Úvaze zkusit otevřít video, přehrávač a druhou Úvahu. Nevznikne soupeřící session; návrat zachová nebo pravdivě ukončí původní záznam. |
| T026 | Bez sítě otevřít dnešní i jiný místní den, filtry, detail, stažená média a uložený text. Neexistující souhrn se nevymyslí a nic nehlásí serverové potvrzení. |
| T030 | Z běžného Momentu vytvořit **Soukromý dovětek**, dokončit audio a změnit den kapitoly. Dovětek je samostatná zamčená Úvaha s vazbou `Patří k`; původní čas obou záznamů zůstává beze změny. |
| T038 | Po uložené lidské revizi nesmí případný pozdější automatický text změnit čtenářský text. V C04d je doloženo synteticky; bez produkční AI nejde o fyzický end-to-end PASS. |
| T039 | Rozepsat koncept, aplikaci úplně ukončit a znovu otevřít. Editor nabídne stejný koncept, předchozí revize zůstane čtenářská; až **Uložit** vytvoří novou revizi. |
| T040 | Nastavit `Jen pro mě`, skrýt Moment a otevřít **Nabídka → Skryté**. Skrytí výslovně neuvádí uvolnění místa; obnovení vrátí Moment se stejným soukromím a originály. Serverová invalidace čeká na C05/C08. |
| T041 | U běžné fotografie vytvořit **Soukromý dovětek**. Fotografie a dovětek mají dvě různé identity; fotografie si zachová své soukromí, dovětek je `Jen pro mě`. |
| T096 | U samostatné Úvahy zvolit **Vložit Úvahu do deníku**. Před změnou se ukáže varování o textu a povoleném původním audiu; po potvrzení detail ukazuje `Do deníku` a `Místní revize · čeká na server`, nikoli serverové přijetí. Přepnutí zpět na `Jen pro mě` je místně okamžité. |

## Hranice výsledku

- Automatické testy používají jen syntetická data a mohou doložit persistence,
  pořadí revizí, restart, skrytí, vazby a UI. Nedokazují fyzický mikrofon,
  telefonní hovor, změnu audio route, přehrávání skutečných médií ani UX na
  iPhonu.
- C04d frontu lokálních operací neodesílá. Serverové přijetí, Viewer, konflikt
  druhého editoru a invalidace odvozenin patří C05/C08.
- Zdrojový checkpoint `e3868100` prošel před pushnutím plnou projektovou
  bránou 1740/1740 a byl pushnut na `origin/main`. Podepsaný build 0.1.0 (2)
  prošel strict kontrolou podpisu, instalací a spuštěním. Cockpit nebyl v tomto
  kroku nasazen.
- Další vývojový krok je C05a. Místní fronta C04d stále není synchronizace,
  serverové přijetí ani druhá záloha.
