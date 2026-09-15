# Camino

Aktualizováno: 2026-09-15 10:33 CEST
Pracovní proud: `project-camino` · typ Project · režim active · priorita 1.

## Cíl a hranice

Soukromý offline deník na iPhonu, bezpečné originály a osobní deník na Macu;
volitelný rodinný výběr a film až v dalších etapách. Jeden autor a jeden hlavní
editující iPhone. Web v P0 slouží pro čtení a stav, bez veřejného publikování.

## Aktuální stav

- C01a rozpracováno: izolovaný audio prototyp, 25 testů logiky a syntetického CAF audia OK; přímá kompilace/linkování pro arm64 iOS 17 / SDK 26.2 prošly.
- iPhone 14 Plus / iOS 26.6.1 build 23G83 přímo ověřen: paired, wired, tunnel connected, Developer Mode enabled, DDI available.
- Xcode 26.3 je nainstalovaný, ale standardní build blokuje chybějící platform support iOS 26.2; samotné SDK nestačí. Platných podpisových identit je 0.
- Celý C01a BLOCKED: instalace, ruční UI/poslech a fyzické T015/T017/T025 NEPROVEDENO. C01b nezahájeno.
- Před restartem 2026-09-15 10:33 CEST: SSD volno 18,81 GiB, CloudKit
  cache 14,75 GiB; Falta odpojený. USA přesunuto a ověřeno, neopakovat.
  Podrobný restartový vzkaz je v kanonickém handoffu Camina.
- P+n ověřeno pro `e4e667b5`: 1684/1684 testů, nový Cockpit, smoke 5/5.
  Tento dodatečný handoff předchozí p+n nezahrnovalo.


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

- Bez funkčního Xcode buildu, podpisu a fyzické přejímky nelze prototyp označit za přijatý; G0/G1 nesplněné.
- Pouze krátké foreground audio; žádná segmentace, záchrana po pádu během zápisu ani pokračování pod zámkem.
- Vzorky v telefonu mají jen místní kopii, nejsou určeny pro ostrá média; žádná AI, síť, export nebo automatické mazání.
- Před velkou instalací iOS komponent znovu posoudit diskovou kapacitu. U01–U11 se neotevírají.

## Další krok

Po skutečném restartu Macu nejprve jen čtením ověřit nový boot, stav Cockpitu, volné místo SSD a velikost cache CloudKit. Nic nemazat ani neinstalovat; teprve podle výsledku navázat na chybějící iOS Platform Support.

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

### 2026-09-15 08:19 CEST — C01a: první prototyp, telefon připraven, build blokován

Hotovo:

- Malý prototyp Start/Stop, skutečný vstup, místní evidence a přehrání; 25 testů logiky a syntetického audia prošlo.
- Míla připravil důvěru a Developer Mode; přímý audit potvrdil párování, spojení a vývojové služby telefonu.

Rozhodnutí:

- Na Mílův pokyn pokračovat ve vývoji zahájeno pouze C01a. Žádná placená AI ani další etapa.
- Přímá kompilace není náhrada Xcode buildu, instalace nebo fyzického poslechu. Celý krok zůstává BLOCKED.

Další krok:

- V Xcode → Settings → Components ověřit a zpřístupnit Platform Support iOS 26.2, potom zopakovat build připraveného CaminoAudio projektu.

Navrhované další kroky:

- Po sestavení připravit podpis, nainstalovat prototyp a ručně ověřit neutrální vzorky Komentář/Úvaha. Žádná automatická aktivace mikrofonu.

Technický důkaz:

- `camino/docs/C01a_AUDIO_PROTOTYPE_REPORT.md`, `camino/prototypes/audio/README.md`.
- 25/25 XCTest OK; arm64/iOS kompilace/link exit 0, bez warnings; project.pbxproj lint OK.
- Xcode build exit 70: platform support iOS 26.2 chybí; platné signing identity 0. Fyzické testy NEPROVEDENO.
- Plná společná brána před checkpointem: 1684/1684 testů OK; nové Swift testy jsou samostatných 25/25 výše.
