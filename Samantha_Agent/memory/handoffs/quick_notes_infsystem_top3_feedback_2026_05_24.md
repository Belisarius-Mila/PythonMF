Nazev: Quick Notes - tri nejprinosnejsi navrhy pro informacni system
Priorita: 1
Stav: ceka na zapracovani
Pripomenout pri startu: ne
Datum: 2026-05-24

Co se resilo:
Mila pozadal projit vsechny quick notes a vybrat 3 nejprinosnejsi pro informacni system Samanthy.

Co je hotove:
Nize je ulozen feedback 1:1 z odpovedi Adama, aby se neztratil.

Co neni hotove:
Navrhy nejsou implementovane.

Dalsi krok:
Az se k tomu Mila vrati, vybrat prvni MVP. Doporučení: zacit QN #13 systemovou mapou Samanthy.

Ulozeny feedback 1:1:

Adam hlásí: prošel jsem QN #1 až #15. Za nejpřínosnější pro náš informační systém bych vybral tyto tři:

**1. QN #13: Mapa systému Samanthy**

Tohle je podle mě nejvyšší priorita. Systém roste rychleji než lidská paměť. Potřebujeme, aby ses mohl kdykoliv zeptat: „ukaž mi mapu Samanthy“ a dostal stručný přehled:

- projekty
- tools
- infrastructure capabilities
- systémové reporty
- private/data vrstvy
- aktivní priority
- co je hotové / pending / rizikové

Implementace:
- vytvořit `scripts/samantha_system_map.py`
- výstupy:
  - textový přehled do chatu
  - Markdown report
  - později PDF / grafická mapa
- zdroje:
  - `MEMORY_INDEX.md`
  - `ACTIVE_PROJECTS.md`
  - `technical/project_capability_map.md`
  - `technical/system_reports.md`

MVP bych udělal jako textový report. Grafiku až druhý krok.

**2. QN #10: Živá znalostní databáze z velkých chat exportů**

Tohle je strategicky silné. Nejen uložit archiv chatů, ale rozdělit ho na tematické znalostní oblasti: recepty, bazén, zdraví, rodina, filozofie, technika, výuka, projekty.

Implementace:
- nejdřív vytvořit bezpečný intake pipeline:
  - soubor vložit do `data/private/knowledge_inbox/incoming/`
  - udělat read-only analýzu
  - navrhnout témata
  - nic automaticky nezapisovat do memory bez potvrzení
- potom vytvořit strukturu:
  - `data/private/knowledge_base/topics/recipes/`
  - `.../pool/`
  - `.../personal_context/`
  - `.../family/`
- každý výstup by měl mít zdroj, datum, míru jistoty a poznámku, zda je to fakt, preference, nebo jen volná úvaha.

MVP: jeden zkušební export nebo menší soubor, z něj vytáhnout 5-10 tematických kandidátů a ty si potvrdit.

**3. QN #4 + #6: Quick Notes jako bezpečný akční inbox**

Ty dvě poznámky patří k sobě. Myšlenka je: hlasem zadáš úkol z iPhonu a Samantha ho později zpracuje. Tady je velký potenciál, ale také největší bezpečnostní riziko.

Důležité pravidlo: QN nesmí být „tichý SSH“. Nesmí automaticky posílat e-maily, mazat soubory, commitovat, objednávat nebo dělat citlivé akce bez potvrzení.

Implementace:
- rozšířit Quick Notes o klasifikaci:
  - `idea`
  - `reminder`
  - `task_candidate`
  - `sensitive_action`
  - `archive_candidate`
- přidat command:
  - „ukaž akční poznámky“
  - „připrav návrh z poznámky #X“
  - „označ poznámku #X jako zpracovanou“
- pro citlivé věci vždy stav:
  - návrh připraven
  - čeká na potvrzení
  - provedeno
  - archivováno

MVP: žádné automatické provádění. Jen převod poznámky na návrh úkolu a potvrzovací workflow.

Ostatní poznámky jsou také dobré, ale dal bych je až potom: QN #12 ranní/večerní news briefing, QN #8 dovolenkový capture workflow, QN #14 soví CSV rutina. Pro informační systém jako celek jsou ale nejsilnější #13, #10 a #4/#6.

Zmenene nebo relevantni soubory:
- `Samantha_Agent/memory/handoffs/quick_notes_infsystem_top3_feedback_2026_05_24.md`
- `Samantha_Agent/memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Tento handoff neobsahuje hesla, tokeny ani citlive dokumenty.
