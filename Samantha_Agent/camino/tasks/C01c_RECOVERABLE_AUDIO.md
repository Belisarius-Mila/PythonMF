# C01c — obnovitelné audio části a journal

Zahájeno 2026-09-17 výslovným pokynem Míly po přijetí C01b. Tento krok je
stále izolovaný audio prototyp; neotvírá síť, AI, galerii ani finální datový
model Camina.

## Cíl

Splnit prototypový rozsah F18/F42 a připravit fyzické T022/T023 a syntetické
T061:

- již spuštěný fyzický vstup zůstane aktivní, zatímco se průběžně uzavírají
  samostatné CAF části;
- checkpoint má pracovní cíl 55 sekund a žádná přijatá vstupní dávka nesmí
  posunout část přes návrhový strop 60 sekund;
- journal vznikne před spuštěním mikrofonu a dokončené části se po uzavření
  přesunou z `.partial.caf` na stabilní jméno;
- po pádu se při dalším startu načtou všechny ověřitelně dekódovatelné části,
  případná mezera a neznámý konec se přiznají;
- restart aplikace nikdy sám nezapne mikrofon;
- C01a/C01b soubory a JSON se nemigrují ani nepřepisují.

Limit 60 sekund je cíl ztráty posledního neuzavřeného úseku při testovaných
chybách. Není to garance proti poruše úložiště, ztrátě zařízení nebo chybě
operačního systému.

## Malý technický návrh

`AVAudioEngine` drží jeden input tap. Z něj zapisovač vytváří soubory
`segment-000000.partial.caf`, `segment-000001.partial.caf` atd. Při checkpointu
se aktuální soubor zavře a v téže složce přejmenuje na stabilní `.caf`; input
tap se neodstraňuje a audio session se znovu neaktivuje.

Každý pokus má neměnný `started.json`, `journal.json`, složku `segments/` a po
normálním konci `completed.json` plus `journal-completed.json`. Při startu
úložiště se bez dokončovacího záznamu:

1. zkontrolují stabilní i otevřené části úplným dekódováním,
2. platná otevřená část se povýší na stabilní,
3. neplatný soubor zůstane beze změny,
4. z platných částí vznikne pouze pravdivě označená **Obnovená částečná
   nahrávka** s neznámým koncem,
5. stejné zotavení se při dalším startu nesmí zdvojit.

Přehrávač přehrává ověřené části za sebou jako jeden uživatelský záznam.
Originální části zůstávají archivním zdrojem; spojený soubor se zde nevyrábí.

## Automatizované přijetí

- původní C01a/C01b testy zůstávají zelené a legacy JSON se načte bez přepisu;
- model checkpointu doloží části pod 60 sekundami;
- normální dokončení zapíše všechny části právě jednou;
- pád s platnou otevřenou částí ji obnoví a nezapne mikrofon;
- poškozený konec zůstane zachovaný, dřívější uzavřené části jsou přehratelné;
- platný osiřelý soubor po mezeře se neztratí, ale mezera je označená;
- opakovaný start nevytvoří duplicitní dokončené médium;
- podepsaný build a strict podpis projdou, UI test přehraje dvě syntetické části.

## Fyzické přijetí

### T022 — první předávka

Na novém buildu nahrávat neutrální souvislý test alespoň 2:15. Po hlasových
značkách okolo 00:50, 01:00, 01:45, 01:55 a 02:10 aplikaci za běžícího záznamu
nuceně ukončit. Po otevření se nesmí spustit mikrofon a musí být nabídnuta
obnovená částečná nahrávka. Poslechem se ověří začátek, uzavřené části a pravdivě
přiznaný možný chybějící konec. T022 se následně zopakuje s pádem v jiné fázi
otevřené části; jeden průchod není důkaz všech fází.

### T023 — až po vyhodnocení T022

Souvislý zvuk a časové značky kolem několika 55s hranic ověří, že se na
přechodech nic neopakuje a nevzniká nevysvětlená díra. Existence několika
souborů ani součet jejich délek samy PASS nedokládají.

### T061 — rozsah C01c

Synteticky se pokryjí pády mezi otevřeným zápisem, stabilním přesunem a
dokončovacím JSON. Fyzický test pouze doplní důkaz skutečných CAF; plný
databázový a serverový T061 se zopakuje v C05a.

## Zastavení

C01c není přijaté jen na základě buildu a unit testů. Dokud neprojdou fyzické
T022 a T023 na skutečném telefonu, kontinuita, skutečný checkpoint i rozsah
ztráty zůstávají NEOVĚŘENO. Žádný push, nasazení, síť nebo ostrá osobní média
nejsou součástí tohoto kroku.
