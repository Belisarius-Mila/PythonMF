# TVBCP: Camino

Pracovni proud: `project-camino`
Typ: `Project`
Rezim: `active`
Priorita: 1

## Cíl a hranice

Samostatný soukromý cestovní deník podle v0.4. Založení a napojení na Human–Adam
je první organizační krok; aplikace ani audit prostředí tím nevznikají.

## Aktuální stav a další krok

- C00 dokončeno v dostupném rozsahu; audit, rozhodnutí a zadání C01a jsou připravené.
- Xcode 26.3 Universal / build 17C529 nainstalovaný po samostatném souhlasu; první nastavení dokončené, iPhone SDK 26.2 ověřené.
- Místní Intel MacBook Pro 2020 / macOS 15.7.9 / 16 GiB RAM plní podle Míly vývojovou i domácí serverovou roli.
- Cílový iPhone 14 Plus / iOS 26.6.1 potvrzen Mílou; párování, signing, build/install/run a audio přejímka NEPROVEDENO.
- C01a NEZAHÁJENO. Další krok: po výslovném zadání připojit odemčený iPhone a ověřit vývojovou cestu pro malý audio prototyp.

## Rizika

- G0/G1 nejsou splněné; přítomnost SDK neprokazuje instalaci ani nahrávání na telefonu.
- Služby, úložiště a obnova provozních dat Camino zůstávají NEOVĚŘENO; neblokují offline C01a.
- Recovery záloha zdrojů Samanthy není přejímka budoucí zálohy médií Camino.
- T001–T080 jsou zadání akceptace, nikoli provedené testy. Osobní média, texty, GPS a klíče nepatří do Gitu; placené AI nezadáno.

## Chronologické záznamy

### 2026-09-14 21:22 CEST — Založení Camina před meziúkolem

Hotovo:
- Samostatný katalogový projekt, vlastní paměť, handoff a TVBCP; podklady v0.4 uchované.

Rozhodnutí:
- Míla zadal založení projektu a integraci do Human–Adam, commit, push a nasazení.
- Vývoj se dnes tímto krokem nezahajuje; nejdřív meziúkol, potom C00.
- Potvrzené U01–U11 z podkladů se znovu neotevírají. Návrhy D01–D10 nejsou nová uživatelská rozhodnutí.

Další krok:
- Vyřešit Mílův meziúkol; při návratu ke Caminu začít C00.

Navrhované další kroky:
- Po C00 připravit jen malý audio prototyp C01a podle skutečně ověřeného prostředí.

Technický důkaz:
- Manifest 15/15 shodných SHA-256; ZIP odpovídá všem 16 rozbaleným souborům.
- Testy integrace a stav publikace: viz `memory/reports/camino_registration_2026_09_14.md`.
- Testy aplikace a manuální hardware zkoušky NEPROVEDENO.

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
