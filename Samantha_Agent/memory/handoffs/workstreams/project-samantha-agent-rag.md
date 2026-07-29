# Handoff pracovního proudu: Samantha Agent / RAG

Nazev: Samantha Agent / RAG
Pracovni proud: project-samantha-agent-rag
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-07-29

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

Co neni hotove:
- Obsahova pravdivost dalsich pracovnich proudu nebyla plosne prepisovana ani
  automaticky opravovana.
- Prakticke live dotazy pres Samanthu/OpenAI zatim nebyly soucasti P3.
- Exploracni lokalni dotaz `Mobile Input Layer` nerozpoznal proud bez celeho
  katalogoveho nazvu; P4 ma overit bezne varianty dotazu pred zmenou rankingu.

Dalsi krok:
- P4 ma read-only overit prakticke dotazy pro sedm proudu soucasne roadmapy a
  sledovat volbu autority i `source_type`.

Navrhovane dalsi kroky:
- Potom udelat maly obsahovy audit jen nejdulezitejsich aktivnich proudu.
- Prakticky overit, zda Samantha sama dobre pouziva autoritu a `source_type`.
- U zkracenych nazvu overit, zda jsou potreba bezpecne katalogove aliasy.
- Embeddings resit pouze pokud textove hledani ani po techto krocich nestaci.

Zmenene nebo relevantni soubory:
- `app/memory_truth_audit.py`
- `app/memory_store.py`
- `scripts/samantha_memory_truth_audit.py`
- `memory/samantha_core.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/tvbcp/workstreams/project-samantha-agent-rag.md`

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice, private obsah, cele e-maily ani obsah
  soukromych dokumentu.
- Historicke handoffy zachovat jako historii; nemazat je kvuli novemu rankingu.
