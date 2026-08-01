<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-01 14:52 CEST

### Hotovo
- Samantha před aktuálním provozním tvrzením použije dostupný bezpečný live audit a bez něj přizná stáří i nejistotu paměti.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- V Cockpitu vytvořit jeden čistý checkpoint bez nasazení.

### Rozhodnutí
- Dostupný bezpečný live audit má přednost; bez něj se uvádí stáří a nejistota snapshotu.

### Navrhované další kroky
- Po případném pozdějším nasazení ověřit kalendářní routing krátkým read-only dotazem.

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `d1ffd4c0bc56`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `d1ffd4c0bc56` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-01T12:25:16+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Samantha Agent / RAG

Nazev: Samantha Agent / RAG
Pracovni proud: project-samantha-agent-rag
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-07-30

Co se resilo:
- Pravdivost projektove pameti a textoveho RAG nad git-safe Markdown zdroji.
- Ochrana proti tomu, aby stary agregat nebo historicky handoff prebil
  soucasny kanonicky stav.

Co je hotove:
- P0 zavedlo deterministicky read-only audit 30 pracovnich proudu bez cteni
  private obsahu a bez oprav pameti.
- P1 pridalo do `search_memory` autoritu zdroju `canonical`, `aggregate`,
  `aggregate_unverified`, `reference` a `historical`.
- Autorita P1 se uplatni jen pro pracovni proud jednoznacne rozpoznany z dotazu;
  nesouvisejici kanonicke dokumenty neziskavaji falesnou vyhodu.
- P2 zalozilo tuto jedinou kanonickou dvojici handoff + TVBCP po vyslovnem
  souhlasu Mily.
- P0 audit po P2 hlasi tento proud jako `registry_consistent` a prakticky dotaz
  vraci nejprve oba kanonicke dokumenty.
- P3 opravilo jediny prokazany formalni rozpor: Mobile Input je nyni shodne v
  katalogu i agregatu `paused`.
- P4 read-only overilo sedm roadmapovych proudu. Samotny textovy RAG umel
  vybrat spravny proud a autoritu, ale Samantha pri aktualnim stavu opakovane
  vnucovala `source_type=projects` a tim vyrazovala kanonicke handoffy.
- P5a meni prvni hledani aktualniho stavu na nefiltrovane porovnani autorit.
  Relevantni `canonical` vysledek dalsi zuzeni zastavi; slabsi
  `aggregate_unverified` a `reference` se priznaji jako fallback.
- P5b pridalo pouze query aliasy `R2 Adam` a `Kalendář`. Alias nemeni runtime
  binding a samotny `Cockpit` zustava zamerne nejednoznacny.
- P5 bylo potvrzene nasazeno na `20180e2`; deployment uctenka i opakovany
  Cockpit smoke potvrzuji 5/5.
- P6a obsahove porovnalo sedm roadmapovych proudu se zivymi dukazy,
  kanonickymi dokumenty, projektovymi referencemi a agregaty.
- P6b narovnalo pouze aktivni souhrny a dalsi kroky; historicke bloky zustaly
  zachovane a zadna nova lazy kanonicka dvojice nebyla materializovana.

Co neni hotove:
- Obsahova pravdivost vsech 30 pracovnich proudu nebyla plosne prepisovana ani
  automaticky prohlasena za overenou.
- Proudy bez materializovane kanonicke dvojice zustavaji poctive oznacene jako
  `aggregate_unverified`.
- Obecny dotaz `Cockpit` zustava nejednoznacny mezi hlavnim Cockpitem a
  Janicka Cockpitem; nema dostat tichy alias.
- P6 neřeší proměnlivé runtime stavy. Aktivace rodinného kalendáře proběhla po
  implementačním checkpointu, ale redigovaná provozní účtenka se nepropsala do
  kanonické git-safe paměti. P6 pak bez čtení private konfigurace stav poctivě,
  ale neúplně snížilo na `neověřeno`.

Dalsi krok:
- P7: navrhnout a otestovat úzkou ochranu proměnlivého provozního stavu.
  Dotaz typu `aktivní`, `běží` nebo `připraveno` má použít registrovaný
  redigovaný live audit; pokud není dostupný, musí uvést stáří a nejistotu
  paměťového snapshotu.

Navrhovane dalsi kroky:
- Nejprve read-only zmapovat existující live-status capability a místa, kde
  agent rozhoduje jen z paměti. Potom přidat nejmenší synteticky testovatelnou
  ochranu bez čtení private obsahu.
- U obecneho `Cockpit` zachovat explicitni doptani, ne automaticky vyber.
- Pri dalsi praci sledovat, zda se znovu neobjevi obsahovy drift aktivniho
  souhrnu proti novejsimu dukazu.
- Embeddings resit pouze pokud textove hledani ani po techto krocich nestaci.

Zmenene nebo relevantni soubory:
- `app/samantha_agent.py`
- `app/memory_truth_audit.py`
- `app/memory_store.py`
- `app/communication/human_adam_workstream_catalog.py`
- `scripts/samantha_memory_truth_audit.py`
- `memory/samantha_core.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/tvbcp/workstreams/project-samantha-agent-rag.md`
- `tests/test_capability_runtime_policy.py`
- `tests/test_human_adam_workstream_catalog.py`
- `tests/test_memory_store.py`

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice, private obsah, cele e-maily ani obsah
  soukromych dokumentu.
- Historicke handoffy zachovat jako historii; nemazat je kvuli novemu rankingu.

### Automatický checkpoint 2026-08-01 14:52 CEST

- Pracovní proud: `project-samantha-agent-rag`
- Hotovo: Samantha před aktuálním provozním tvrzením použije dostupný bezpečný live audit a bez něj přizná stáří i nejistotu paměti.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.8 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/samantha_agent.py`, `Samantha_Agent/tests/test_capability_runtime_policy.py`
- Commit: `Upřednostnit živý stav před paměťovým snapshotem`
- Další krok: V Cockpitu vytvořit jeden čistý checkpoint bez nasazení.
