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

## Bezpecnost

- Do pameti se nezapisuji zadne citlive udaje.
- API klice patri pouze do lokalniho `.env`.
- `.env.example` smi obsahovat jen ukazkovou hodnotu.
