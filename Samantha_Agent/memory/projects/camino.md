# Camino

Aktualizováno: 2026-09-14 21:22 CEST
Pracovní proud: `project-camino` · typ Project · režim active · priorita 1.

## Cíl a hranice

Soukromý offline deník na iPhonu, bezpečné originály a osobní deník na Macu;
volitelný rodinný výběr a film až v dalších etapách. Jeden autor a jeden hlavní
editující iPhone. Web v P0 slouží pro čtení a stav, bez veřejného publikování.

## Aktuální stav

- Projekt Camino je založený jako samostatný proud Human–Adam `project-camino`.
- Podklady v0.4 a původní ZIP jsou zachované; žádná funkce aplikace není hotová.
- Nejdřív meziúkol podle Míly, potom výslovný návrat ke Caminu a C00.
- C00 znamená read-only audit vývojového Macu, iPhonu a samostatně domácího serveru.
- Priorita 1 odpovídá Mílovu pořadí: Camino je další projekt hned po meziúkolu.

## Zdroje a návaznost

- Kořen projektu: `camino/`, instrukce `camino/AGENTS.md`.
- Autoritativní podklady: `camino/CAMINO_podklady_v0.4/README_v0.4.md`,
  `CAMINO_funkcni_specifikace_v0.4.md`, `CAMINO_Codex_v0.4.md` a akceptační scénáře.
- Kanonický handoff: `memory/handoffs/workstreams/project-camino.md`.
- Kanonický TVBCP: `memory/tvbcp/workstreams/project-camino.md`.
- Původní balíček se nemění; nové auditní a vývojové výsledky patří mimo něj.
- Katalogové přidání samo neotevírá soukromé vlákno. To vznikne až při otevření projektu.

## Pevná pravidla

Originály jsou neměnné, bez automatického mazání. Offline záznam nečeká na síť,
GPS ani AI. „Do deníku“ je stále soukromé; „Jen pro mě“ vylučuje všechny filmy
a rodinné výstupy. Externí přepis není důkaz zálohy. Lidskou revizi AI nepřepíše.

## Rizika a otevřeno

- Zařízení, instalace, mikrofon, přenosy a zálohy pro Camino dosud NEOVĚŘENO.
- T001–T080 jsou zadání akceptace, nikoli provedené testy aplikace.
- Reálná média, osobní texty, přesná GPS a klíče zůstávají mimo Git a logy.
- Rozpočet AI dosud neurčen; vývoj se syntetickými daty a mock AI.

## Další krok

Nejdřív meziúkol podle Míly. Potom C00 podle plánu v0.4; žádná instalace,
platba ani implementace celé aplikace v auditním kroku.

Ověření založení: 54/54 testů integrace a rychlá statická brána OK.
Publikační plná brána a finální nasazení se ověřují registrovaným živým auditem;
tento zápis předchází schválenému push a nasazení.
