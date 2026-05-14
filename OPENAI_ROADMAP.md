# OpenAI roadmap pro PythonMF

## Shrnutí

Tento dokument není archiv novinek OpenAI. Je to pracovní roadmapa pro PythonMF: co z nových OpenAI/Codex možností dává praktický smysl pro naše jazykové aplikace, weby, obrázky ke slovíčkům a vývojový workflow.

Nejdůležitější směr pro nás je:

- hlasové cvičení v `docs/colors-numbers/`,
- budoucí živý učitel pro jazykové tréninky,
- jednotná pipeline pro obrázky ke slovíčkům,
- lepší zadávání a kontrola práce v Codexu,
- později automatizované pipeline přes Agents SDK.

Před skutečnou implementací OpenAI API je vždy nutné ověřit aktuální oficiální dokumentaci, názvy modelů, dostupnost, ceny a bezpečnostní požadavky.

## Nejvíc relevantní pro nás

### Realtime voice a `gpt-realtime-whisper`

Nejbližší praktické použití je prototyp hlasového cvičení pro `docs/colors-numbers/`.

Možný scénář:

- uživatel vidí barvu nebo číslo,
- řekne odpověď nahlas,
- backend přepíše krátký hlasový vstup přes Realtime transcription / Whisper,
- aplikace vyhodnotí správně nebo špatně,
- API klíč zůstane pouze na backendu, nikdy ve frontendu.

To je pro nás relevantnější než jen přehrávání statických MP3 souborů, protože aplikace začne aktivně poslouchat a hodnotit odpověď.

### `gpt-realtime-2` jako budoucí živý učitel

`gpt-realtime-2` dává smysl jako další krok po jednoduchém přepisu řeči.

Možný budoucí scénář:

- uživatel odpoví nahlas,
- agent rozpozná, co řekl,
- opraví výslovnost nebo význam,
- vysvětlí chybu česky,
- nabídne další příklad anglicky, francouzsky nebo italsky,
- reaguje přirozeně v živém dialogu.

Tohle patří až po menším prototypu. Nejdřív potřebujeme ověřit jednoduchý hlasový vstup a vyhodnocení.

### GPT Image 2 pro slovníkové obrázky

GPT Image 2 je relevantní pro pipeline okolo `PictNew`, `Pict/` a `Pict/mapping.json`.

Praktický směr:

- generovat jednotné obrázky ke slovíčkům,
- držet konzistentní dětský a čistý styl,
- ukládat nové obrázky nejdřív do `PictNew/`,
- ručně je zkontrolovat,
- teprve potom je přesunout do `Pict/`,
- API klíč držet pouze v proměnné prostředí.

To navazuje na plán popsaný v paměti `Samantha_Agent/memory/projects/pictnew_vocabulary_image_pipeline.md`.

### Codex workflow a GPT-5.5 pro vývoj

Pro běžný vývoj v PythonMF je nejdůležitější lepší práce s Codexem:

- zadávat cíl, omezení a očekávaný výstup,
- vyjmenovat konkrétní soubory, kterých se úkol týká,
- říct, co se nesmí měnit,
- požadovat ověření testem nebo spuštěním,
- při gitu přidávat jen konkrétní soubory, ne `git add .`.

GPT-5.5 a novější modely jsou relevantní hlavně pro delší úkoly: refaktoring, migrace, audit větší části repozitáře, složitější webové nebo agentní změny.

### Agents SDK později pro automatizované pipeline

Agents SDK je relevantní pro budoucí opakovatelné procesy, ne jako první krok pro všechno.

Možné použití později:

- audit slovníků a obrázků,
- příprava návrhů do `mapping.json`,
- synchronizace dat do `docs/`,
- kontrola webových exportů,
- dlouhodobější Samantha agent s lokální pamětí.

Aktuálně má větší smysl držet jednoduché skripty a ruční kontrolu.

## Možné experimenty

### Experiment 1: hlasové cvičení pro `docs/colors-numbers/`

Vytvořit malý prototyp:

- uživatel řekne barvu nebo číslo,
- backend přijme krátký audio vstup,
- OpenAI Realtime / Whisper přepíše řeč,
- aplikace porovná odpověď s očekávanou hodnotou,
- web zobrazí správně/špatně.

Bezpečnostní pravidlo: API klíč nesmí být nikdy ve statickém GitHub Pages frontendu.

### Experiment 2: jednotné obrázky ke slovíčkům

Navázat na `PictNew` workflow:

- vybrat malou dávku pěti slovíček,
- připravit prompt a request JSON,
- vygenerovat obrázky přes aktuální Images API,
- uložit je do `PictNew/`,
- ručně zkontrolovat styl, velikost a použitelnost,
- teprve potom řešit přesun do `Pict/`.

### Experiment 3: Codex prompt šablony

Připravit krátké šablony pro zadávání práce Codexu:

- úkol na úpravu webu,
- úkol na úpravu slovníku,
- úkol na audit obrázků,
- úkol na commit a push,
- úkol na bezpečnou práci s API.

Šablony mají Codexu říkat: cíl, soubory, omezení, ověření a git postup.

### Experiment 4: Samantha Agent

Pokračovat v `Samantha_Agent/`:

- udržovat lokální markdown paměť,
- používat jednoduché `search_memory`,
- zatím bez vektorové databáze,
- později přidat RAG nad exporty z ChatGPT,
- Agents SDK používat jako základ, ale postupovat po malých krocích.

## Co zatím neřešit

- Nepřidávat Realtime API přímo do statického frontendu bez backendu.
- Neřešit složitou vektorovou databázi dřív, než budou dobře připravené zdrojové texty a exporty.
- Nestavět plně automatické generování obrázků bez ruční kontroly.
- Nespoléhat na staré názvy modelů bez ověření v oficiální dokumentaci.
- Nepřidávat API klíče do Python souborů, JSON konfigurací, markdownů ani commitu.
- Neautomatizovat git operace stylem `git add .`.

## Zdroje

- `gpt-realtime-2`: https://developers.openai.com/api/docs/models/gpt-realtime-2
- `gpt-realtime-translate`: https://developers.openai.com/api/docs/models/gpt-realtime-translate
- `gpt-realtime-whisper`: https://developers.openai.com/api/docs/models/gpt-realtime-whisper
- Realtime API overview: https://platform.openai.com/docs/guides/realtime/overview
- GPT-5.5 guide: https://developers.openai.com/api/docs/guides/latest-model
- Codex Chrome extension: https://developers.openai.com/codex/app/chrome-extension
- Sandbox agents: https://developers.openai.com/api/docs/guides/agents/sandboxes
- OpenAI Docs MCP: https://developers.openai.com/learn/docs-mcp
- Image generation: https://developers.openai.com/api/docs/guides/image-generation
- API deployment checklist: https://developers.openai.com/api/docs/guides/deployment-checklist

## Další kroky

1. Ověřit aktuální OpenAI dokumentaci k Realtime API a image generation před jakoukoliv implementací.
2. Navrhnout nejmenší backend pro hlasové cvičení v `docs/colors-numbers/`.
3. Připravit bezpečný experiment pro přepis krátké řeči bez ukládání API klíče do frontendu.
4. Připravit malý GPT Image 2 experiment pro pět slovíček v `PictNew/`.
5. Sepsat Codex prompt šablony pro opakovatelné úkoly v PythonMF.
6. Pokračovat v `Samantha_Agent/` postupně: markdown paměť, jednoduché nástroje, později RAG.
