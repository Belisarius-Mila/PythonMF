# Vocabulary image generation workflow

Zalozeno 2026-05-20 po uspesnem dogenerovani obrazku pro `VocabularyIT`.

Tento dokument je kanonicky postup pro tvorbu novych obrazku ke slovnikovym
projektum v `PythonMF`. Plati hlavne pro:

- `VocabularyFR/`
- `VocabularyIT/`
- budouci nebo podobne slovniky `VocabularyES/`, `VocabularyLA/`, `VocabularyEN/`
- sdilenou obrazkovou knihovnu `Pict/`
- pracovni prostor `PictNew/`

## Proc je workflow dulezite

Postup se osvedcil na `VocabularyIT`: vzniklo 125 novych obrazku v davkach,
nejdrive bezpecne do `PictNew/generated/`, po vizualni kontrole byly zkopirovany
do `Pict/` a az dalsi samostatny krok smi resit `Pict/mapping.json`.

Hlavni zasada:

```text
Audit / request -> dry-run -> potvrzene placene generovani -> review -> kopie do Pict -> mapping az po dalsim potvrzeni -> git checkpoint
```

## Spolecny FR/IT aktualizacni trigger

Od 2026-07-31 znamena zapis novych slovicek do kterekoli oblasti `FR - Mila`,
`FR - Jana` nebo `IT - Mila` povinny spolecny audit vsech soucasnych zdroju.
Presny seznam zdroju a distribucni kontrakt je kanonicky popsany v
`memory/projects/pictnew_vocabulary_image_pipeline.md` v sekci
`Povinny aktualizacni kontrakt od 2026-07-31`.

Prakticke pravidlo pro Codex:

- nezpracovavat izolovane jen prave zmeneny CSV,
- vzdy znovu overit jeden FR zdroj Mily, iCloud FR Jany a IT Mily,
- u Jana FR vzdy zkontrolovat vsechny dvojice `Sentence` a `SentenceT`,
  chybejici jednoduche prikladove vety a ceske preklady doplnit; Milovy FR a IT
  vety automaticky nedoplnovat, protoze si je Mila pise sam,
- kontrolu Jana FR spustit nejprve bez zapisu prikazem
  `.venv/bin/python scripts/jana_vocabularyfr_fill_sentences.py`; nenulovy
  vysledek kvuli chybejicim vetam je povinny podnet k jejich doplneni,
- udrzovat jeden cesky a abecedne razeny obsah `Pict/mapping.json`,
- drzet Milovu a Janinu distribucni kopii bajtove shodnou,
- pri chybejicim obrazku nejdrive hledat existujici vhodny asset,
- generovani, presun schvalenych obrazku a mapping apply dal podlehaji svym
  potvrzovacim hranicim,
- pred dokoncenim dolozit audit `CSV -> mapping -> Pict` pro vsechny zdroje.

## Role slozek

```text
Pict/
```

Sdilena knihovna schvalenych obrazku, kterou pouzivaji slovnikove aplikace.
Sem patri az obrazky, ktere Mila vizualne schvalil.

```text
PictNew/
```

Pracovni prostor pro audit, request JSON, review HTML a vygenerovane batche.
Sem patri mezivystupy a kontrolni reporty.

```text
PictNew/generated/YYYYMMDD_<language>_batchNNN/
```

Bezpecny vystup jedne generovaci davky. Kazdy batch ma obsahovat:

- `.webp` obrazky,
- `generation_report.json`,
- `review.html`.

## Faze 1: audit a priprava requestu

Vstupy se lisi podle jazyka a aktualni architektury, ale cilem je vytvorit
request JSON ve tvaru:

```text
PictNew/NewPicturesRequestDDMMYYYY.json
```

Pro aktualni italsky workflow byl pouzit:

```bash
python3 pict_new_prepare.py --language it --date YYYY-MM-DD --batch-size 10 --batch-index 1
```

V teto fazi se nema:

- volat placene API,
- menit `Pict/`,
- menit `Pict/mapping.json`,
- mazat existujici obrazky.

Vystupem je seznam obrazku k vytvoreni, rozdeleny do davek.

## Faze 2: dry-run pred kazdou davkou

Pred placenym generovanim se vzdy spusti dry-run:

```bash
python3 image_generator.py --request-json PictNew/NewPicturesRequestDDMMYYYY.json --batch-index N
```

Dry-run musi ukazat:

- cislo batchu,
- pocet polozek,
- cilove soubory,
- model, format a limity velikosti,
- informaci `Dry run only. No API calls and no files written.`

Pokud dry-run nesedi, generovani se nespousti.

## Faze 3: potvrzene placene generovani

Skutecne generovani vola OpenAI image API a muze stat penize. Proto musi byt
vyslovne potvrzene Milou.

Minimalni potvrzeni pro jednu davku:

```text
Potvrzuji generovani obrazku.
```

Pro vice davek je lepsi presne potvrzeni rozsahu:

```text
Potvrzuji placene generovani VocabularyIT batchu 012 a 013.
Nepresouvej do Pict, nic nemaz, pri selhani zastav.
```

Spusteni jedne davky:

```bash
python3 image_generator.py --request-json PictNew/NewPicturesRequestDDMMYYYY.json --batch-index N --execute --confirm "Potvrzuji generovani obrazku"
```

Bezpecnostni pravidla:

- Generovat postupne po davkach, ne nekontrolovane vse najednou.
- Pri chybe dalsi batch nespoustet.
- API klic smi byt jen v prostredi, nikdy v repo souboru, dokumentaci ani memory.
- Neexistujici nebo neuplny batch nejdrive overit dry-runem.
- Neprenaset obrazky do `Pict/` automaticky po generovani.

## Faze 4: technicka kontrola po batchi

Po dobehnuti batchu zkontrolovat:

- proces skoncil bez chyby,
- pocet `.webp` odpovida poctu polozek v batchi,
- existuje `generation_report.json`,
- existuje `review.html`,
- vsechny polozky v reportu maji status `generated`,
- nejvetsi soubor je pod `max_size_kb`, aktualne 300 kB.

Prakticka kontrola:

```bash
python3 -c "import json; from pathlib import Path; ..."
```

Neni nutne si pamatovat presny jednorazovy prikaz; dulezite je overit body vyse.

## Faze 5: vizualni kontrola Milou

Mila kontroluje `review.html` v kazde davce.

Dokud Mila obrazky neschvali:

- nekopirovat do `Pict/`,
- neupravovat `Pict/mapping.json`,
- necommitovat je jako schvalenou knihovnu, pokud to neni vyslovne chtene jako
  rozpracovany checkpoint.

## Faze 6: kopie do `Pict/`

Po Milove schvaleni lze obrazky zkopirovat do `Pict/`.

Pred kopirovanim overit:

- kolik `.webp` souboru je v planovanych batchich,
- zda se nazvy mezi sebou neduplikuji,
- zda v `Pict/` uz neexistuji stejne nazvy.

Kopirovat bez mazani zdroju:

```bash
find PictNew/generated -path 'PictNew/generated/YYYYMMDD_<language>_batch*/*.webp' -type f -exec cp -n {} Pict/ \;
```

Po kopirovani overit, ze v `Pict/` existuje 100 % cilovych souboru.

Poznamka: `cp -n` nema prepsat existujici soubory. Pokud jsou kolize, zastavit a
zeptat se Mily.

## Faze 7: `Pict/mapping.json`

`Pict/mapping.json` je citlivejsi nez samotna kopie obrazku, protoze ovlivnuje,
ktere slovicko pouzije ktery obrazek.

Pred upravou mappingu:

1. Ziskat samostatne potvrzeni.
2. Vytvorit zalohu mappingu.
3. Pripravit preview zmen.
4. Aplikovat az po potvrzeni.

Bez potvrzeni:

- neupravovat mapping,
- neprepisovat existujici vazby,
- nemazat obrazky ani stare mapping zaznamy.

## Faze 8: git checkpoint

Po schvalenem kopirovani a/nebo mapping zmenach udelat cilene git operace.

Nikdy nepouzivat slepe:

```bash
git add .
```

Pouzit cilene cesty, typicky:

```bash
git add Pict PictNew/generated/YYYYMMDD_<language>_batchNNN ... Samantha_Agent/memory/...
git commit -m "Add VocabularyIT generated image batches"
```

Po commitu zkontrolovat:

```bash
git status --short
git log -1 --oneline --stat
```

## Co je uz overene

Overeno 2026-05-20 na `VocabularyIT`:

- request mel 125 unikatnich obrazku,
- batch 001 byl po uprave promptu Milou vizualne pochvalen,
- batche 002 az 013 byly technicky hotove,
- batch 013 mel poslednich 5 polozek,
- po Milove schvaleni bylo 125/125 obrazku zkopirovano do `Pict/`,
- vznikl git commit `20825ad Add VocabularyIT generated image batches`.

## Stav automatizace

Tento workflow je zatim zdokumentovana schopnost a rucne overeny postup.
Neni jeste plne registrovany jako Samantha shell workflow v:

```text
Samantha_Agent/app/workflows/commands.py
```

Dokud nebude registrovany:

- Samantha ho nema spoustet jako volny ad hoc shell podle jedne vety,
- Codex muze postup provest rucne podle teto karty,
- pro kazde placene generovani a mapping zmenu je potreba jasne potvrzeni.

## Dalsi doporucena automatizace

V dalsim kroku stoji za to registrovat samostatne workflow nebo tooly:

1. `pictnew_prepare_request` - audit/priprava requestu bez API volani.
2. `pictnew_generate_batch_preview` - dry-run batchu.
3. `pictnew_generate_batch_confirmed` - placene generovani jedne davky po potvrzeni.
4. `pictnew_copy_approved_to_pict` - kopie schvalenych obrazku bez prepisu.
5. `pictnew_update_mapping_preview/apply` - preview a potvrzena aktualizace `mapping.json` se zalohou.
