# C05c — report stavového UX

Datum lokální implementace: 2026-09-24

## Výsledek

Obrazovka **Uložení a přenosy** zobrazuje čtyři samostatné sekce: **Telefon**,
**Mac**, **Další záloha** a **AI**. Každá má vlastní stav, vysvětlení a barevný
tón. Neexistuje jeden souhrnný zelený symbol, který by zakryl čekající originál,
neověřenou zálohu nebo nedokončenou AI úlohu.

Stav Telefonu vychází z místních Momentů. Stav Macu počítá úplné a čekající
Momenty; počet čekajících změn metadat, médií a jejich bajtů zůstává zvláštní
provozní údaj. Moment je úplný až tehdy, když Mac přijal všechny jeho známé
operace a ověřil všechna známá média.

Produkční C05c si nevymýšlí schopnosti dalších etap. Bez C06b zobrazuje
**Další záloha zatím není ověřená** a vysvětluje, že kopie na Macu není další
záloha. Bez C07 zobrazuje **AI zatím není zapnutá** a výslovně říká
**Přepis není záloha**.

## Chyby a mezistavy

- Přijaté bajty nejsou úspěch: při serverové finalizaci zůstává Mac ve stavu
  **Ověřuji**.
- Nedostupná cesta říká jen, že Mac není dostupný a příčinu nelze spolehlivě
  určit.
- Stav čekání na Wi-Fi potvrzuje, že data jsou uložená v telefonu.
- Odmítnutý přístup, nedostatek místa, neověřitelná odpověď, konflikt epochy a
  přerušení mají oddělené bezpečné texty; interní kód serveru se uživateli
  nevydává jako vysvětlení.
- Pouhé uložení připojení ani připravená fronta nejsou zelené ověření.

## T054 a T055

Datový model podporuje nezávislé kombinace všech čtyř os. T054 ověřuje AI bez
zálohy i zálohu s čekající AI. T055 ověřuje stav
**Média zálohována, novější změny ještě čekají** po novější změně textu nebo
soukromí.

Tyto dva scénáře jsou zatím syntetické. Simulátorový ladicí fixture je uzavřený
pod `DEBUG` a `targetEnvironment(simulator)`; fyzický produkční build jím nelze
přepnout do falešného stavu. Reálná záloha patří C06b a reálná AI C07.

## Automatický důkaz

- Swift Core: 33/33 PASS, včetně počítání Momentů odděleně od operací a
  segmentů, nezávislých os T054, čerstvosti metadat T055 a bezpečných textů.
- Nepodepsaný generic iOS build: PASS.
- Cílený UI test čtyř os a syntetického T054: 1/1 PASS.
- Regresní UI test trvalého pause a místního záznamu po relaunchi: PASS.
- Plná projektová brána: 1770/1770 PASS.

## Zbývající hranice

Zdrojový checkpoint `f0f714f4` je pushnutý. Podepsané Camino 0.1.0 (4) prošlo
strict kontrolou, kontrolou týmu a profilu, instalací stejného bundle ID bez
odinstalace a spuštěním. Fyzický průchod C05c zatím neproběhl; zachování dat,
čitelnost a skutečné UX se přijmou podle `C05c_IPHONE_TEST_PLAN.md`.

Tento krok nenasadil Cockpit a neměnil server, token, Serve ani Funnel. Fyzický
průchod může přijmout pouze produkční výchozí stavy a skutečné C05b stavy Macu;
skutečnou zálohu a AI nelze přijmout před C06b/C07.
Závěrečný registrovaný read-only audit potvrdil C05b `phase=stopped`, neběžící
server, nepřítomnou privátní cestu, vypnutý Funnel a nula aktivních tokenů.
