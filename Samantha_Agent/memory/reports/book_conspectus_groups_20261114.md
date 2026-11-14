# Jemnější skupiny Konspektu —14.11.2026

Stav: místně dokončené a ověřené; bez nového push/nasazení.
Proud: project-knowledge-library. Nové p+n není součástí zadání.

## Výsledek

- Katalogové MARC072 ze stejného vybraného záznamu ukládá kód$a, název$x
  a nadřazený obor. Neznámý kód, nejasný název, rozporný$9 ani jiné schéma
  skupinu nevytváří. Hlavní obor, žánr/forma, témata a jazyk zůstávají samostatné.
- Karta/detail, rychlé ISBN, podrobné přidání i editace zobrazují skupiny.
  Ruční výběr závisí na oboru a funguje také bez ISBN/katalogového záznamu.
  Přehled má filtr s počty i Podle skupin; identitou je kód, nikoli proměnný název.
  OR v poli, AND mezi poli, zvolená nulová hodnota zůstává viditelná.
- Ruční skupiny mají samostatný původ; katalogový důkaz se nepřepisuje.
  Prázdný ruční seznam výslovně potlačí katalogové skupiny. Změna ISBN
  skupiny zneplatní; bez změny se uchovají. Skupina mimo účinný obor se nezobrazí.
- Žádná migrace starých knih. Staré snapshoty v1 bez groups zůstanou bez klíče;
  payload fingerprint a dokončení původního zápisu jsou zachované. Nový
  nepovinný book_groups_manual vstupuje do identity jen při přítomnosti.

## Primární zdroje a omezení

MARC072: https://prirucky.ipk.nkp.cz/katalogizace/monografie/072 .
Kódy/obory: dosavadní přesná mapa RecordManager2 MZK v book_conspectus.json.
Názvy: https://raw.githubusercontent.com/moravianlibrary/RecordManager2/master/cz.mzk.recordmanager.server/src/main/resources/mapping/conspectus_subcategory_name.map .
SHA2569af28c8fceab1e386dc20068705e0a1b0520c6effb7191fea5c5cb546cf7b681.
Dnešní audit:606 pojmenovaných kódů z616 známých. Všechna doložená slovní
záhlaví jsou zachovaná; pro ruční volbu se používá první varianta ve zdroji.
Deset kódů bez názvu se ručně nenabízí; z katalogu lze převzít jejich přesné$x.
Název konkrétního katalogového snapshotu se nenahrazuje názvem nabídky.
Živý veřejný kontrolní záznam potvrdil821.162.3-3 / Česká próza.

## Důkazy

-394 cílených testů PASS: katalog, persistence/replay, archiv, HTTP adaptéry,
  frontendový kontrakt a Node regrese. Log book_conspectus_targeted_20261114.log.
-101 backendových/archivních PASS v book_conspectus_backend_20261114.log.
- Skutečný izolovaný browser390/1280: převzetí katalogové skupiny, ruční výběr,
  filtry i editace; odděleně celý sestavený COCKPIT_HTML a skutečné options API,
  úplná karta bez ISBN, explicitní vyprázdnění skupiny a rychlé přidání.
  Celkem2+3 testovací zápisy,0 produkčních POST,0 neodchycených výjimek,
  šířka dokumentu390/1280 bez přetékání. Screenshoty vizuálně přečtené.
  Full-page příprava ostatní POST pouze lokálně stubuje; žádný jiný backend nevolá.
  Soukromé důkazy: data/private/book_conspectus_groups_20261114/.
- Plná brána PASS:3918 testů,31 SKIP,767,493s unit část;0 chyb/selhání.
  Zmrazených14 zdrojových/testových otisků při dokončení přesně souhlasilo.
  Log book_conspectus_full_gate_20261114.log, privátní unit_timings.json.
- Po ní pouze jedna UI podmínka pro Podle skupin u víceoborové knihy:
  respektovat vybraný hlavní obor stejně jako filtr. Backend/persistence
  zůstaly beze změny. Finální browser390/1280 tento případ ověřil,
  frontendový kontrakt24 testů PASS. Původní plnou bránu neoznačujeme jako
  běh nového UI otisku; rozdíl přesně2 souborů (app.js + kontrakt) je doložený
  ve final_validation.json. Finální statická brána ověřena před commitem.

## Stav a další krok

Dosavadní ruční obory24096145 a jednorázové čištění jsou dokončené a kanonicky
dorovnané; neopakovat apply ani vydání. Cizí Vocabulary EN4e5e18a7 dokončené,
3912 PASS/push+Pages confirmed/HTTP200; main se během aktivity neměnil.
Tento krok je pouze místní vývoj. Fyzická iPhone přejímka a případné budoucí
samostatně schválené p+n zůstávají otevřené. Soukromé knihy se testem neměnily.
Další pořadí Míly: konkrétní iPhone UI (podrobnosti dosud chybí), pak poštovní
přejímka A+C podle Downloads; před ní nový čtecí audit běhu a zdrojových vazeb.
Vnější watchdog, poštovní aktivace ani Mac sleep nejsou zadané zásahy.

Aktualizováno: 2026-11-14 20:05 CET.
