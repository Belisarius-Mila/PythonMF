Nazev: VocabularyIT IT_Pict.csv - audit obrazku a rucni kontrola
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Mila potrebuje pripravit italsky slovnik pro pozdejsi doplneni chybejicich obrazku.
- Pracovni soubor je `VocabularyIT/IT_Pict.csv`.
- Sloupce: `ITP` italske slovicko, `CZP` cesky vyznam, `ENP` anglicky nazev obrazku, `PD` stav doplneni, `PE` existence obrazku.
- Obrazky jsou ve spolecnem adresari `Pict/`.

Co je hotove:
- V `VocabularyIT/IT_Pict.csv` bylo doplneno 127 prazdnych hodnot `ENP`.
- Pro nove doplnene radky bylo `PD` nastaveno podle fyzicke existence obrazku v `Pict/`:
  - `add`, pokud obrazek podle `ENP` chybi,
  - `Obrazek existuje zkontroluj`, pokud odpovidajici soubor existuje.
- Pro nove doplnene radky bylo `PE` srovnano na `ano` nebo `ne`.
- Opraveno 7 starsich nesrovnalosti mezi `ENP`/`PE` a fyzickou existenci obrazku:
  - `brioche`: `bakery`, stav na existujici obrazek.
  - `esercizio`: preklep `excercise` -> `exercise`, stav na existujici obrazek.
  - `viale`: preklep `evenue` -> `avenue`, stav na existujici obrazek.
  - `scheda`: `card`, stav na existujici obrazek.
  - `telefonico`: `call`, stav na existujici obrazek.
  - `di`: Mila rozhodl zmenit pouze `ENP` z `from` na `fromwhere`; `PD=json ok` a `PE=ano` zustaly.
  - `bravo`: `good`, stav na existujici obrazek.
- Finalni kontrola po upravach:
  - prazdne `ENP`: 0,
  - rozpor mezi `PE` a fyzickou existenci obrazku v `Pict/`: 0.
- Pridan pripraveny root-level skript `pict_new_prepare.py`.
- Skript umi z `IT_Pict.csv` vybrat radky, kde `PD` obsahuje `add`, seskupit je podle unikatniho ciloveho obrazku a vytvorit:
  - `PictNew/NewPicturesRequest20052026.json`,
  - `PictNew/NewPicturesReview20052026_batch001.html`.
- Aktualni pocet je 128 zdrojovych radku, ale 125 unikatnich cilovych obrazku; duplicity jsou sloucene, aby se stejny obrazek negeneroval vicekrat.
- Syntaxe skriptu byla overena pres `PYTHONPYCACHEPREFIX=/tmp python3 -m py_compile ../pict_new_prepare.py`.
- Overena aktualni oficialni OpenAI image generation dokumentace: pro jednorazove generovani z promptu se pouzije Image API, aktualni guide uvadi `gpt-image-2`; vystup je base64 obrazek.
- Pridan root-level skript `image_generator.py` a konfigurace `image_generator_config.json`.
- Vychozi generator:
  - model `gpt-image-2`,
  - velikost `1024x1024`,
  - kvalita `low`,
  - format `webp`,
  - cil `250 kB`, maximum `300 kB`,
  - vystup jen do `PictNew/generated/YYYYMMDD_it_batchNNN/`.
- Generator je bezpecne defaultne dry-run; skutecne API volani vyzaduje `--execute` a potvrzeni `Potvrzuji generovani obrazku`.
- Dry-run batch 001 prosel a naplanoval 10 souboru do `PictNew/generated/20260520_it_batch001/`.
- Lokální kompresni testy pro `webp` i `jpeg` prosly; syntaxe `image_generator.py` prosla pres `PYTHONPYCACHEPREFIX=/tmp python3 -m py_compile`.
- Po Milove potvrzeni `potvrzuji generovani obrazku` byl spusten prvni placeny batch 001.
- Batch 001 vytvoril 10/10 obrazku ve slozce `PictNew/generated/20260520_it_batch001/`:
  - `a.webp`
  - `perJulia.webp`
  - `inorderto.webp`
  - `sothenwell.webp`
  - `often.webp`
  - `tolikepleasure.webp`
  - `painevil.webp`
  - `month.webp`
  - `usual.webp`
  - `go.webp`
- Vznikly take:
  - `PictNew/generated/20260520_it_batch001/generation_report.json`
  - `PictNew/generated/20260520_it_batch001/review.html`
- Kontrola reportu: `generated=10`, maximum velikosti cca `74.6 kB`, tedy pod limitem `300 kB`.
- `image_generator.py` byl po batchi doplnen o prubezne logovani `Generating X/Y...` pro dalsi davky.
- Mila zkontroloval styl batch 001: nebyl spatny, ale byl moc detsky, sterilni a nektere metafory byly spatne.
- Konkretni problem: `a.webp` vysel jako jablko, pravdepodobne kvuli asociaci `A is for apple`; to je spatne pro neurcity clen `una/un`.
- Stary batch 001 byl na Milovo prani smazan ze slozky `PictNew/generated/20260520_it_batch001/`.
- Prompt v `pict_new_prepare.py` a `image_generator_config.json` byl upraven:
  - mene sterilni a mene baby styl,
  - vice prostredi, detailu, stinu a male scenky,
  - stridat postavy, ne porad stejny kluk a holka,
  - pro `a` specialni pravidlo: nekreslit pismeno A ani jablko, ale metaforu jedne neurcite veci,
  - cesky napis nebo cedule jsou povolene, pokud pomahaji pochopeni obrazku,
  - nahodne texty, cizi slova, dekorativni pismena a nesmyslne popisky stale zakazat.
- `PictNew/NewPicturesRequest20052026.json` a `PictNew/NewPicturesReview20052026_batch001.html` byly znovu vygenerovany s novymi prompty.
- Vystupni slozka `PictNew/generated/20260520_it_batch001/` byla po smazani stareho batch 001 cista.
- Po Milove potvrzeni `Potvrzuji generovani obrazku` byl batch 001 znovu vygenerovan s novym promptem:
  - `generated=10/10`,
  - vystupni soubory jsou `webp`,
  - nejvetsi soubor je `go.webp` cca `237 kB`, tedy pod limitem `300 kB`,
  - vznikly nove `generation_report.json` a `review.html`.
- Mila vizualne zkontroloval batch 001 a potvrdil, ze obrazky jsou velmi povedene.
- Po dalsim Milove potvrzeni `potvrzuji generovani obrazku` byl spusten batch 002.
- Batch 002 vytvoril 10/10 obrazku ve slozce `PictNew/generated/20260520_it_batch002/`:
  - `favor.webp`
  - `then2.webp`
  - `pray.webp`
  - `remember.webp`
  - `immediately.webp`
  - `usually.webp`
  - `when.webp`
  - `enemy.webp`
  - `occupied.webp`
  - `permission.webp`
- Vznikly take:
  - `PictNew/generated/20260520_it_batch002/generation_report.json`
  - `PictNew/generated/20260520_it_batch002/review.html`
- Kontrola reportu batch 002: `generated=10/10`, nejvetsi soubor cca `185.2 kB`, tedy pod limitem `300 kB`.
- Dry-run batch 003 byl overen bez API volani; planuje obrazky `beforeawhile`, `which`, `this`, `russian`, `likeable`, `surprise`, `findoneself`, `wine`, `who`, `mynamecall`.
- Po Milove potvrzeni `Potvrzuji generovani obrazku` byl spusten batch 003.
- Batch 003 vytvoril 10/10 obrazku ve slozce `PictNew/generated/20260520_it_batch003/`:
  - `beforeawhile.webp`
  - `which.webp`
  - `this.webp`
  - `russian.webp`
  - `likeable.webp`
  - `surprise.webp`
  - `findoneself.webp`
  - `wine.webp`
  - `who.webp`
  - `mynamecall.webp`
- Vznikly take:
  - `PictNew/generated/20260520_it_batch003/generation_report.json`
  - `PictNew/generated/20260520_it_batch003/review.html`
- Kontrola reportu batch 003: `generated=10/10`, nejvetsi soubor cca `240.1 kB`, tedy pod limitem `300 kB`.
- Dry-run batch 004 byl overen bez API volani; planuje obrazky `meet`, `after`, `hereyouare`, `fountain`, `french`, `postalstamp`, `italian`, `less`, `mixed`, `room`.
- Po Milove potvrzeni `Potvrzuji generovani obrazku` byl spusten batch 004.
- Batch 004 vytvoril 10/10 obrazku ve slozce `PictNew/generated/20260520_it_batch004/`:
  - `meet.webp`
  - `after.webp`
  - `hereyouare.webp`
  - `fountain.webp`
  - `french.webp`
  - `postalstamp.webp`
  - `italian.webp`
  - `less.webp`
  - `mixed.webp`
  - `room.webp`
- Vznikly take:
  - `PictNew/generated/20260520_it_batch004/generation_report.json`
  - `PictNew/generated/20260520_it_batch004/review.html`
- Kontrola reportu batch 004: `generated=10/10`, nejvetsi soubor cca `210.0 kB`, tedy pod limitem `300 kB`.
- Dry-run batch 005 byl overen bez API volani; planuje obrazky `swim`, `amongin`, `menrucksacks`, `pig`, `postcard`, `unfortunatelly`, `sick`, `weak`, `prefere`, `enough`.

Co neni hotove:
- Mila chce `IT_Pict.csv` jeste rucne projit.
- Batch 001 je vizualne schvaleny Milou.
- Batch 002, batch 003 a batch 004 jsou technicky hotove a cekaji na vizualni kontrolu.
- Polozky z `NewPicturesRequest20052026.json` jsou kandidati pro pozdejsi tvorbu obrazku.

Dalsi krok:
- Mila spusti italsky vocabulary trainer v samostatnem terminalu nebo z VS Code, aby neshodil aktualni Codex relaci.
- Zkontrolovat `PictNew/generated/20260520_it_batch002/review.html`, `PictNew/generated/20260520_it_batch003/review.html` a `PictNew/generated/20260520_it_batch004/review.html`.
- Batch 005 nebo presun do `Pict/` nespoustet bez dalsiho Milova potvrzeni.

Zmenene nebo relevantni soubory:
- `VocabularyIT/IT_Pict.csv`
- `Pict/`
- `pict_new_prepare.py`
- `image_generator.py`
- `image_generator_config.json`
- `PictNew/NewPicturesRequest20052026.json`
- `PictNew/NewPicturesReview20052026_batch001.html`
- `PictNew/generated/20260520_it_batch001/`
- `PictNew/generated/20260520_it_batch002/`
- `PictNew/generated/20260520_it_batch003/`
- `PictNew/generated/20260520_it_batch004/`
- `memory/projects/pictnew_vocabulary_image_pipeline.md`

Bezpecnost / neukladat:
- Neukladat API klice, tokeny ani jina tajemstvi.
- Negenerovat ani nepresouvat obrazky bez dalsiho Milova potvrzeni.
- Nemazat existujici obrazky v `Pict/`.
