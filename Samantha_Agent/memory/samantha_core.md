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

## Aktualni technicky stav

- Codex CLI uz funguje.
- Node.js je pripraveny.
- npm je pripraveny.
- Python 3.12 je pripraveny.
- OpenAI API key je pripraveny lokalne, ale nesmi se zapisovat do gitu ani do pametovych souboru.

## Aktualni kanonicky stav 2026-05-23

Samantha Agent/RAG ma prvni praktickou verzi nad OpenAI Agents SDK a lokalni
markdown pameti.

- Startup kontext je kompaktní: nacita hlavne `samantha_core.md`,
  `ACTIVE_PROJECTS.md` a `MEMORY_INDEX.md`.
- Konkretni dlouhodoby kontext se dohledava pres `search_memory`.
- Diagnostika pameti je dostupna pres `memory_status`.
- `app/memory_store.py` ma textovy RAG-like index nad markdown pameti, in-memory
  cache, tokenizaci nazvu souboru, podporu variant `read-only`/`readonly`,
  jeden nejlepsi snippet za soubor a zkraceny textovy vystup.
- `search_memory_text` ve vystupu ukazuje typ zdroje (`core`, `projects`,
  `handoffs`, `technical`, `infrastructure`, `stories`) a podporuje volitelny
  filtr `source_type`, aby historicke handoffy neprebijely kanonicky stav.
- Vyhledavani zatim neni vektorova databaze a nepouziva embeddings.
- Lokalni smoke test 2026-05-23 bez OpenAI API po doplneni `source_type`:
  - dotaz `Samantha Agent RAG search_memory ranking` vraci vysledky oznacene
    typem zdroje a mezi prvnimi je kanonicky `core` kontext;
  - `source_type='core'` omezi vysledky na `MEMORY_INDEX.md`,
    `samantha_core.md` a `ACTIVE_PROJECTS.md`;
  - `source_type='projects'` pro `email read-only workflow` vraci jako prvni
    `projects/email_readonly_oauth.md`;
  - `source_type='handoffs'` umi cilene najit historicke RAG handoffy.

Aktualni dalsi krok:

- Udelat pristi live retest pres Samanthu/OpenAI a sledovat, jestli agent sam
  vhodne pouziva `source_type`.
- Embeddings resit az po overeni, ze vylepsene textove vyhledavani s cache
  nestaci.

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
