# Handoff: ChatGPT -> Codex a novy chat

## Ucel

Tento soubor slouzi jako kompaktní predani kontextu po dlouhem ChatGPT vlakne.

Ma dva cile:

1. Dat Codexu jasny seznam toho, co uz bylo zpracovano do memory.
2. Umoznit Mílovi zalozit novy ChatGPT chat, ktery navaze bez kopirovani cele dlouhe historie.

## Aktualni stav prostredi

- Projekt: `PythonMF`
- Samantha Agent slozka: `Samantha_Agent/`
- Codex CLI je nainstalovany globalne a funguje jako `/usr/local/bin/codex`.
- Node.js a npm jsou nainstalovane.
- Python 3.12 je dostupny.
- OpenAI API klic existuje, ale nesmi se zapisovat do repozitare ani do memory souboru.
- `Samantha_Agent` ma vlastni `.venv`.

## Memory soubory vytvorene nebo pripravene v tomto vlakne

Projektove memory:

- `projects/tax_priznani_2025.md`
- `projects/pictnew_vocabulary_image_pipeline.md`
- `projects/tts_edge_audio_tools.md`
- `projects/matysek_english_game_concept.md`
- `projects/mmtx_story_hotspot_app.md`
- `projects/multilo_stabilization_cleanup.md`

Core memory:

- `samantha_core.md`
- `MEMORY_INDEX.md`

Tento handoff:

- `handoffs/chatgpt_handoff_2026_05_14.md`

## Strucny obsah memory

### Tax

Soubor `projects/tax_priznani_2025.md` zachycuje:

- danove priznani 2025,
- vypocty z prijmu ze zamestnani a najmu,
- checklist radku formulare,
- upozorneni neukladat rodne cislo a adresu do gitu.

### PictNew / obrazky pro slovicka

Soubor `projects/pictnew_vocabulary_image_pipeline.md` zachycuje:

- budoucí pipeline pro opakovane doplnovani obrazku ke slovickum,
- zdroj pravdy: `VocabularyFR.csv`, `VocabularyIT.csv`, `Pict/mapping.json`, `Pict/`,
- rozhodnuti nepovazovat `FR_Pict.csv` a `IT_Pict.csv` za nutny zdroj pravdy,
- spolecny audit FR a IT,
- postup: audit -> protokol -> request JSON -> image generator -> kontrola v `PictNew/` -> presun do `Pict/`,
- pravidlo neukladat OpenAI API klic do souboru.

### TTS

Soubor `projects/tts_edge_audio_tools.md` zachycuje:

- `scripts/generate_tts.py`,
- `scripts/tts_gui.py`,
- pouziti `edge-tts`,
- hlas `cs-CZ-AntoninNeural`,
- rozdil mezi davkovym CSV rezimem a rucnim GUI.

### Matysek koncept

Soubor `projects/matysek_english_game_concept.md` zachycuje:

- ze hra je pro Matyska, 5 let, bez cteni a bez anglictiny,
- ze hlavni komunikace ma byt obrazem, hlasem a kliknutim,
- ze V3 byla stabilni technicka zkouska, ale ne finalni smer,
- ze hlavni smer ma byt pribehova aplikace.

### MMTX

Soubor `projects/mmtx_story_hotspot_app.md` zachycuje:

- novou aplikaci `MatysekANJ/MMTX.py`,
- pouziti pozadi `MatysekANJ/NumCol1.JPG`,
- hotspoty nad houbami,
- rezim barvy,
- rezim cisla,
- dynamicke cislovani hub podle poradi kliknuti v ramci barvy,
- potrebu dale ladit geometrii hotspotu.

### MultiLO

Soubor `projects/multilo_stabilization_cleanup.md` zachycuje:

- zamrzani pri navratu do kokpitu,
- pravdepodobny problem `CTkEntry` v psacich rezimech,
- prechod na `tk.Entry`,
- cleanup lifecycle screenu,
- ruseni pending `after(...)` callbacku,
- fix `MonthsScreen._back()`,
- retest seznam.

## Pravidla pro Codex

Codex ma pred praci:

1. Precist `Samantha_Agent/AGENTS.md`.
2. Precist `Samantha_Agent/memory/MEMORY_INDEX.md`.
3. Podle tematu precist relevantni memory soubor.
4. Nemenit soubory mimo zadany rozsah.
5. Nikdy neukladat API klice, rodne cislo, adresy ani jine citlive udaje do repozitare.
6. Pri git operacich nepouzivat slepe `git add .`.
7. U UI zmen poctive overovat syntaxi a pokud mozno smoke test.

## Prompt pro Codex po navratu k praci

```text
Nejdrive si precti Samantha_Agent/AGENTS.md, Samantha_Agent/memory/MEMORY_INDEX.md a Samantha_Agent/memory/handoffs/chatgpt_handoff_2026_05_14.md.

Potom mi strucne rekni, jake hlavni projektove oblasti jsou v memory zachycene a navrhni dalsi nejbezpecnejsi krok. Zatim nic neupravuj.
```

## Prompt pro novy ChatGPT chat

```text
Navazuji na predchozi dlouhy chat o projektu PythonMF a Samantha_Agent.

Mame lokalni projekt:
/Users/miloslavfalta/Desktop/PythonMF

V nem vznikla slozka:
Samantha_Agent/

Dulezite memory soubory:
- Samantha_Agent/memory/MEMORY_INDEX.md
- Samantha_Agent/memory/samantha_core.md
- Samantha_Agent/memory/projects/tax_priznani_2025.md
- Samantha_Agent/memory/projects/pictnew_vocabulary_image_pipeline.md
- Samantha_Agent/memory/projects/tts_edge_audio_tools.md
- Samantha_Agent/memory/projects/matysek_english_game_concept.md
- Samantha_Agent/memory/projects/mmtx_story_hotspot_app.md
- Samantha_Agent/memory/projects/multilo_stabilization_cleanup.md
- Samantha_Agent/memory/handoffs/chatgpt_handoff_2026_05_14.md

Chci pokracovat tak, ze ChatGPT bude pomahat delat strukturovane memory souhrny, navrhovat presne prompty pro Codex a kontrolovat architekturu.

Codex ma delat fyzicke upravy souboru v projektu.

Zasadni pravidla:
- odpovidat cesky,
- postupovat krok za krokem,
- neukladat citlive udaje do projektu,
- Codexu davat uzce vymezene ukoly,
- u rozsahlejsich zmen nejdrive plan, potom implementace.

Prosim navaz na tento stav.
```

## Doporučeny dalsi prakticky krok

Nejdrive nechat Codex pouze zkontrolovat a shrnout memory:

```text
Nejdrive si precti Samantha_Agent/AGENTS.md, MEMORY_INDEX.md a handoff soubor. Nic neupravuj. Rekni, jestli je memory struktura konzistentni a co bys doporucil jako dalsi krok.
```

Az potom pokracovat jednim konkretnim smerem:

- PictNew pipeline,
- MMTX hotspoty,
- MultiLO retest/stabilizace,
- TTS nastroje,
- ChatGPT export importer,
- Agents SDK Samantha agent.

## Poznamka

Tento soubor neni nahrada detailnich memory souboru. Je to rozcestnik pro navazani po dlouhem chatu.
