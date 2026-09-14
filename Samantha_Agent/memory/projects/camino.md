# Camino

Aktualizováno: 2026-09-14 23:26 CEST
Pracovní proud: `project-camino` · typ Project · režim active · priorita 1.

## Cíl a hranice

Soukromý offline deník na iPhonu, bezpečné originály a osobní deník na Macu;
volitelný rodinný výběr a film až v dalších etapách. Jeden autor a jeden hlavní
editující iPhone. Web v P0 slouží pro čtení a stav, bez veřejného publikování.

## Aktuální stav

- C00 dokončeno v dostupném rozsahu; audit, rozhodnutí a zadání C01a jsou připravené.
- Xcode 26.3 Universal / build 17C529 nainstalovaný po samostatném souhlasu; první nastavení dokončené, iPhone SDK 26.2 ověřené.
- Místní Intel MacBook Pro 2020 / macOS 15.7.9 / 16 GiB RAM plní podle Míly vývojovou i domácí serverovou roli.
- Cílový iPhone 14 Plus / iOS 26.6.1 potvrzen Mílou; párování, signing, build/install/run a audio přejímka NEPROVEDENO.
- C01a NEZAHÁJENO. Další krok: po výslovném zadání připojit odemčený iPhone a ověřit vývojovou cestu pro malý audio prototyp.

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

- G0/G1 nejsou splněné; přítomnost SDK neprokazuje instalaci ani nahrávání na telefonu.
- Služby, úložiště a obnova provozních dat Camino zůstávají NEOVĚŘENO; neblokují offline C01a.
- Recovery záloha zdrojů Samanthy není přejímka budoucí zálohy médií Camino.
- T001–T080 jsou zadání akceptace, nikoli provedené testy. Osobní média, texty, GPS a klíče nepatří do Gitu; placené AI nezadáno.

## Další krok

Po výslovném zadání C01a připojit iPhone a ověřit cestu pro prototyp. C01a nezahájeno.

Historický doklad založení:
Ověření založení: 56/56 testů integrace (54 + 2 profilové testy) a rychlá statická brána OK.
Publikační plná brána a finální nasazení se ověřují registrovaným živým auditem;
tento zápis předchází schválenému push a nasazení.

### 2026-09-14 23:26 CEST — C00, Xcode a checkpoint po recovery záloze

Hotovo:

- C00 a samostatně schválená instalace Xcode dokončeny; projektové předání dorovnáno na skutečný stav.
- Před úklidem vznikla ověřená recovery záloha `20260914_231439`; dokumenty Camina zachované a porovnané pomocí SHA-256.

Rozhodnutí:

- Míla zadal nejdřív ostrou zálohu, potom úklid repozitáře. Úklid tvoří lokální dokumentační checkpoint bez mazání; push ani nasazení nejsou součástí tohoto kroku.
- U01–U11 beze změny. C01a se automaticky nezahajuje.

Další krok:

- Po výslovném zadání C01a připojit odemčený iPhone a ověřit rozpoznání, kompatibilitu a podpis pro malý audio prototyp.

Navrhované další kroky:

- Nahrát, bezpečně dokončit a přehrát krátký neutrální vzorek na skutečném telefonu; server není vstupní podmínka.

Technický důkaz:

- `camino/docs/ENVIRONMENT_AUDIT.md`, `DECISIONS.md`, `XCODE_INSTALLATION.md` a `camino/tasks/C01a_AUDIO_PROTOTYPE.md`.
- Instalační kontroly Xcode/first launch/iPhone SDK prošly; build a fyzické audio testy NEPROVEDENO.
- Recovery: 63 295 souborů, 28 892 kopírováno, 34 360 hardlinků, 43 symlinků, 0 přeskočeno; zkušební obnova AGENTS.md se shodným SHA-256.
- Závěrečná plná kontrolní brána checkpointu: 1684/1684 testů OK; syntaxe a Git safety check OK. Nejde o testy aplikace Camino.
