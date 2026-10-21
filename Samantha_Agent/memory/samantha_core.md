# Samantha Core Memory

## Mila

Mila je uzivatel tohoto projektu. Buduje osobniho AI agenta jmenem Samantha, ktery mu ma dlouhodobe pomahat s praci, projekty a osobnim kontextem.

## Samantha Agent

Samantha Agent je pripravovany osobni AI agent. Cil je postupovat po malych praktickych krocich:

1. Nejdrive vytvorit lokalni pamet.
2. Potom postavit agenta nad OpenAI Agents SDK.
3. Pozdeji doplnit RAG nad exporty z ChatGPT.

## Prakticka kotva

Projekt neni o technologii pro efekt, ale o praktickem pomocnikovi pro konkretni
lidske agendy. Kulturni metafora `samyce/samice` je ulozena v
`technical/samantha_cultural_metaphors.md`: stary pocitac by nerozumel
preklepu, ale Samantha ma hledat zamer, kontext a rozumny dalsi krok i pri
nepresnem lidskem vstupu.

## Milova pracovni preference: jednoduche funkcni reseni

Mila chce prednostne jednoducha funkcni reseni. Rizika se maji vecne a primerene
posoudit, ale nema se automaticky hledat idealni nebo maximalne pojistene reseni,
pokud by dalsi vrstvy, brany, fallbacky a infrastruktura neumerne prodluzovaly
vyvoj bez konkretniho uzitku.

Pri vice bezpecnych variantach ma Adam doporucit nejjednodussi variantu, ktera
dany cil spolehlive splni, otevrene pojmenovat zbyvajici realne riziko a
nepridavat kod jen pro hypotetickou dokonalost. Duvod je lidsky a prakticky:
zivot je kratky.

Tato preference nerusi ochranu tajemstvi a private dat ani zvlastni potvrzeni
pro mazani, nevratne zasahy, odesilani ven a skutecne systemove riziko.

## Aktualni technicky stav

- Codex CLI uz funguje.
- Node.js je pripraveny.
- npm je pripraveny.
- Python 3.12 je pripraveny.
- OpenAI API key je pripraveny lokalne, ale nesmi se zapisovat do gitu ani do pametovych souboru.

## Aktualni kanonicky stav 2026-10-21

Samantha Agent/RAG je prakticky agent nad OpenAI Agents SDK a lokalni git-safe
Markdown pameti. Toto je kompaktní startup kontext; podrobný stav, rozhodnutí a
bezprostřední další krok jsou v kanonickém handoffu a TVBCP.

- Startup nacita hlavne `samantha_core.md`, `ACTIVE_PROJECTS.md` a
  `MEMORY_INDEX.md`; konkretni kontext dohledava pres `search_memory`.
- `app/memory_store.py` poskytuje textove hledani s cache, typem zdroje a
  autoritou vysledku (`canonical`, `aggregate`, `aggregate_unverified`,
  `reference`, `historical`). Vyhledavani nepouziva embeddings.
- P0-P7 jsou hotove. P7 vyzaduje pro proměnlivá tvrzení registrovaný redigovaný
  live audit, případně přiznání stáří a nejistoty snapshotu.
- P8 rozšířilo read-only audit o kandidáta na ruční revizi, pokud je datum
  aktuálního odstavce zde starší než datum v označeném aktuálním stavu handoffu.
  Samotné datum není důkaz obsahového rozporu a audit nic neopravuje.
- Nové milníky a provozně proměnlivý stav ověřuj v
  `handoffs/workstreams/project-samantha-agent-rag.md` a
  `tvbcp/workstreams/project-samantha-agent-rag.md`; nepřebírej další krok ze
  staršího historického záznamu.
- Embeddings zvažovat pouze po praktickém důkazu, že textové hledání nestačí.

## Historicke handoffy Samantha Agent/RAG

- `handoffs/samantha_agent_rag_memory_store_2026_05_19.md` - prvni lokalni
  markdown memory store, `search_memory`, `memory_status`, in-memory index/cache
  a zakladni testy.
- `handoffs/samantha_agent_rag_search_memory_ranking_2026_05_19.md` - vylepseny
  ranking a vystup `search_memory`; tento handoff zustava poslednim technickym
  mezistavem pred lokalnim smoke testem 2026-05-23.

## Bezpecnost

- Do pameti se nezapisuji zadne citlive udaje.
- API klice patri pouze do lokalniho `.env`.
- `.env.example` smi obsahovat jen ukazkovou hodnotu.
