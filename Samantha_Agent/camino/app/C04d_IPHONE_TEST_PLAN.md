# C04d — cílený test detailu a revizí na iPhonu

Stav 2026-09-22: C04d je lokálně implementovaná a automatizovaně ověřená,
ale není podepsaná ani nainstalovaná na iPhone. Tento průchod proto není PASS.
Instalace je samostatný potvrzený krok. Použij cestu **Zkouška**, neosobní
média a syntetický text; do chatu stačí ID testu a PASS/FAIL bez hlasu,
fotografií nebo textového obsahu.

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
- Po průchodu zapiš model/iOS, verzi buildu, jednotlivé výsledky a všechny
  odchylky. Bez tohoto fyzického průchodu zůstávají T010/T019–T021/T026/T030/
  T039–T041/T096 pro integrovanou aplikaci otevřené nebo jen částečné.
