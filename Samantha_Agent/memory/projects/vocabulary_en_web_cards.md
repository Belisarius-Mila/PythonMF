# VocabularyEN web: obrazové kartičky pro opakování slovíček

## Stav

Vznikl nový malý webový projekt na bázi `VocabularyEN/vocab_trainer_en.py`.

Cílová skupina jsou mentálně postižení studenti, které Míla učí anglická slovíčka.

Původní desktopová aplikace `vocab_trainer_en.py` je bohatá, ale pro tuto skupinu je příliš hustá a textová. Webová verze má být jednodušší: jeden obrázek, jedno slovíčko, velká tlačítka, minimum textu.

Hlavní vytvořené nebo dotčené soubory:

- `VocabularyEN/sync_vocabulary_en_to_docs.py`
- `docs/vocabulary-en/index.html`
- `docs/vocabulary-en/styles.css`
- `docs/vocabulary-en/app.js`
- `docs/data/vocabulary-en.json`
- `docs/assets/vocabulary-en/`
- `Pict/VocabularyEN_missing_nouns_plan.md`
- `Pict/mapping.json`

## Cíl

Cílem je vytvořit jednoduchou webovou learner aplikaci pro opakování anglických slovíček z `VocabularyEN.csv`.

Web nemá být editor slovníku. Má sloužit studentům k procvičování.

Autoring obsahu má zůstat mimo learner web:

1. Míla přidá slovíčko do `VocabularyEN/VocabularyEN.csv`.
2. Přidá obrázek do `Pict/`.
3. Pokud obrázek nemá přímý název podle slovíčka, doplní mapování do `Pict/mapping.json`.
4. Spustí synchronizační skript.
5. Web načte vygenerovaný JSON a obrázky z `docs/`.

## Důležité poznatky

### Co šlo převést z desktopu

Z `vocab_trainer_en.py` je webově dobře přenositelný:

- datový model `EN, CZ, Order, Sentence, SentenceT, L, HT`,
- filtrace slov podle `All / Last / Interval / Not known / HT`,
- náhodné vybírání bez opakování,
- logika mapování obrázků přes `Pict/mapping.json`,
- základní stav `learned` a `hardTraining`,
- hlas přes browser speech nebo později hotová audio data.

### Co nepřenášet 1:1

Do learner webu se nemá přenášet celé desktopové UI:

- hustý panel nastavení,
- editor CSV,
- psací režim jako výchozí režim,
- macOS `say`,
- export PNG do Apple Photos,
- příliš rychlý turbo režim.

Pro cílovou skupinu je lepší:

- jeden úkol na obrazovce,
- velký obrázek,
- velké tlačítko pro přehrání,
- 2–4 velké odpovědi nebo jednoduché odhalení odpovědi,
- minimum checkboxů a vysvětlovacího textu.

## Rozhodnutí

### Sync skript

Vznikl skript:

```text
VocabularyEN/sync_vocabulary_en_to_docs.py
```

Co dělá:

- načte `VocabularyEN/VocabularyEN.csv`,
- použije stejnou nebo obdobnou logiku výběru obrázků jako desktopová aplikace,
- zkopíruje použité obrázky do `docs/assets/vocabulary-en/`,
- vygeneruje manifest `docs/data/vocabulary-en.json`.

Spuštění:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py
```

Volitelně umí zapisovat i do dalšího web rootu:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py \
  --extra-output-root MatysekANJ/web_mmtx
```

Ověření při vzniku:

```bash
python3 -m py_compile VocabularyEN/sync_vocabulary_en_to_docs.py
python3 VocabularyEN/sync_vocabulary_en_to_docs.py
```

Výsledek tehdy:

- 152 položek v JSON,
- 63 zkopírovaných unikátních obrázků,
- JSON obsahuje mimo jiné `learned`, `hardTraining`, `sentenceEn`, `sentenceCz`, `image`, `imageSource`.

### Webová stránka

Vznikla první learner stránka:

- `docs/vocabulary-en/index.html`
- `docs/vocabulary-en/styles.css`
- `docs/vocabulary-en/app.js`

Stránka:

- načítá `docs/data/vocabulary-en.json`,
- ukazuje velký obrázek,
- podporuje režim CZ -> EN a EN -> CZ,
- má akce `Nové slovo`, `Ukaž odpověď`,
- umí přehrát zadání i odpověď přes browser speech,
- ukládá `Umím` a `Těžké` do `localStorage`,
- není editor obsahu.

Lokální spuštění:

```bash
python3 -m http.server 8811 -d docs
```

URL:

```text
http://127.0.0.1:8811/vocabulary-en/
```

### Úprava hlavičky

Po prvním náhledu byla stránka vizuálně upravena:

- nadpis je jen `Obrazkove karticky EN`,
- odstraněn text pro opakovani slovicek,
- odstraněn vysvětlující šedý text,
- hlavička byla zmenšena na výšku,
- font nadpisu byl mírně zmenšen, aby držel v jedné řádce.

### Obrázky a fallbacky

Analýza ukázala, že některá podstatná jména a noun-like fráze padají do obecných fallbacků typu `proverbs`, `others`, `man`, `preposition`, `woman`.

Dobří kandidáti na dokreslení obrázků:

- airport
- animal
- baby elephant
- bus station
- cat
- cow
- crocodile
- doctor
- document
- duck
- elephant
- eyes
- field
- film
- giraffe
- goat
- horse
- lake / pond
- lion
- monkey
- name
- office
- popcorn
- rabbit
- rhino
- teacher
- ticket
- zebra
- orange
- pound

Sporné, ale možné:

- cook
- drawing
- English
- help
- something

Vznikl plánovací soubor:

- `Pict/VocabularyEN_missing_nouns_plan.md`

Obsahuje doporučené názvy souborů do `Pict/`.

Byly také doplněny návrhy mapování do:

- `Pict/mapping.json`

Příklad workflow:

- `Pict/bus_station.png`
- a v `mapping.json` mapování pro:
  - `bus station`
  - `autobusové nádraží`
  - `autobusove nadrazi`

Po přidání nových obrázků je potřeba spustit:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py
```

## Otevřené otázky

- Přidat druhý režim s 2–4 obrázkovými možnostmi místo pouhého odhalení odpovědi.
- Rozhodnout, zda bude stránka napojená z hlavního webového rozcestníku.
- Zlepšit heuristiku výběru obrázků, aby podstatná jména nepadala do obecných fallbacků.
- Po dokreslení obrázků znovu spustit sync a zkontrolovat, kolik položek ještě padá do fallbacku.
- Rozhodnout, zda pro některé slovníkové položky vytvořit hotové audio soubory místo browser speech.
- Později zvážit backend, pokud bude potřeba editace obsahu přes web.

## Další kroky pro Codex

Před prací na tomto projektu číst:

- `VocabularyEN/vocab_trainer_en.py`
- `VocabularyEN/sync_vocabulary_en_to_docs.py`
- `VocabularyEN/VocabularyEN.csv`
- `Pict/mapping.json`
- `Pict/VocabularyEN_missing_nouns_plan.md`
- `docs/vocabulary-en/index.html`
- `docs/vocabulary-en/styles.css`
- `docs/vocabulary-en/app.js`
- tento memory soubor

Pravidla:

- Neudělat z learner webu editor obsahu.
- Autoring dál držet v CSV, `Pict/` a `mapping.json`.
- Po změně CSV nebo obrázků spustit sync skript.
- Nezapisovat z prohlížeče přímo do CSV bez backendu.
- Pro cílovou skupinu držet UI velmi jednoduché.
- Při změně webu testovat přes lokální HTTP server nad `docs/`.
- Při git operacích nepoužívat slepě `git add .`, protože v repozitáři bývá hodně rozpracovaných souborů.

## Okruh Benji z MMTX - 2026-08-25

- Všech 120 položek importovaných z MMTX, tedy pořadí 187 až 306, má v poli
  `WS` přidanou hodnotu `Benji`.
- Původní okruhy zůstávají zachované. Více okruhů se v CSV odděluje znakem `|`,
  například `Actions|Benji`.
- Web vytváří seznam okruhů dynamicky z manifestu, proto nebyla potřebná změna
  HTML ani JavaScriptu. Po synchronizaci nabízí checkbox `Benji` a jeho filtr
  obsahuje právě 120 nových položek.
- Budoucí import přes `import_mmtx_vocabulary.py` přidá `Benji` automaticky.
- Pro bezpečné doplnění existujících importovaných řádků slouží
  `tag_mmtx_benji_word_set.py`; bez `--apply` pouze audituje.
- Webový export se obnovuje příkazem:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py --preserve-extra-assets
```

## Oprava výslovnosti cat — 2026-09-05 21:40 CEST

- Hotovo: pro `cat` (Order 20) je připravená MP3 hlasu Jenny. Text kartičky,
  české audio i ostatních 305 položek zůstaly stejné.
- Rozhodnutí: generátor má úzkou hlasovou výjimku pro anglické `cat`, takže
  další sestavení opravu zachová. Nový hlas mění adresu MP3 a obchází cache
  původní nahrávky. Staré soubory se nemažou.
- Další krok: push a samostatná publikace GitHub Pages, potom poslech na
  cílovém zařízení. Oprava zatím není doložená na veřejném webu.
- Technický důkaz: veřejná původní MP3 byla bajtově shodná s lokální;
  automatický anglický přepis původního Aria audia vrátil `Kate.`, nového
  Jenny audia `Cat.`. Jde o strojovou kontrolu, nikoli lidský poslech.
  Cílené audio testy prošly 11/11, knihovna má 608 aktivních MP3 pro 306 slov.

## Zdroj

Souhrn ChatGPT/Codex konverzace k převodu části `vocab_trainer_en.py` do jednoduché webové learner aplikace pro mentálně postižené studenty, vytvoření sync skriptu `VocabularyEN -> docs`, prvního webového MVP, zmenšení hlavičky a přípravě seznamu chybějících obrázků v `Pict/`.
