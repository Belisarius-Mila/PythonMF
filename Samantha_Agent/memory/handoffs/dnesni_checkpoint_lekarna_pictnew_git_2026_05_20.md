Nazev: Dnesni checkpoint - Lekarna, image resize a PictNew batche
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Lekarna: foto import, vyrazeni leku a zmenseni fotek krabicek.
- Obecna media utilita: zmensovani obrazku podle cilove velikosti v kB.
- PictNew / VocabularyIT: priprava `IT_Pict.csv`, request JSON a generovani obrazku.
- Bezpecny git checkpoint: pridat dnesni rozpracovanou praci do gitu bez `git add .`.

Co je hotove:
- Lekarna ma navazujici read/write workflow pro potvrzovane operace a samostatne handoffy.
- Media utilita pro zmenseni obrazku je hotova, otestovana a prvne pouzita na lekarne.
- `VocabularyIT/IT_Pict.csv` je doplneny a `PictNew/NewPicturesRequest20052026.json` obsahuje 125 unikatnich obrazku v 13 davkach.
- `image_generator.py` a `image_generator_config.json` jsou pripraveny pro bezpecne davkove generovani bez ulozeneho API klice.
- PictNew batche 001 az 004 jsou vygenerovane do `PictNew/generated/20260520_it_batch001/` az `batch004/`.
- Batch 001 Mila vizualne pochvalil; batche 002 az 004 jsou technicky hotove a cekaji na vizualni kontrolu.
- Batch 005 je pripraveny jen jako dry-run a nesmi se spoustet bez dalsiho potvrzeni.

Co neni hotove:
- Vizualne zkontrolovat review HTML pro batche 002 az 004.
- Rozhodnout, ktere obrazky se prijmou, ktere se budou regenerovat a kdy se budou presouvat do `Pict/`.
- Batch 005 a dalsi davky zatim nespoustet bez dalsiho potvrzeni.

Dalsi krok:
- Dokoncit git checkpoint dnesni prace: cilene `git add`, kontrola staged diffu, commit.
- Po commitu lze pokracovat vizualni kontrolou `PictNew/generated/20260520_it_batch002/review.html` az `batch004/review.html`.
- Pokud Mila potvrdi dalsi generovani, spustit batch 005.

Zmenene nebo relevantni soubory:
- `Samantha_Agent/app/lekarna/`
- `Samantha_Agent/app/media/`
- `Samantha_Agent/scripts/resize_images.py`
- `Samantha_Agent/tests/test_lekarna_service.py`
- `Samantha_Agent/tests/test_media_image_resize.py`
- `Samantha_Agent/requirements.txt`
- `Samantha_Agent/memory/`
- `VocabularyIT/IT_Pict.csv`
- `pict_new_prepare.py`
- `image_generator.py`
- `image_generator_config.json`
- `PictNew/NewPicturesRequest20052026.json`
- `PictNew/NewPicturesReview20052026_batch001.html`
- `PictNew/generated/20260520_it_batch001/`
- `PictNew/generated/20260520_it_batch002/`
- `PictNew/generated/20260520_it_batch003/`
- `PictNew/generated/20260520_it_batch004/`
- `Samantha_GIT_PUSH.txt`

Bezpecnost / neukladat:
- Neukladat API klice, tokeny, hesla, app-specific passwords ani `.env`.
- Nekommitovat `Samantha_Agent/data/session_autosave/`.
- Nepresouvat obrazky do `Pict/` bez samostatneho potvrzeni.
- Nespoustet dalsi placene generovani bez potvrzeni `Potvrzuji generovani obrazku`.
