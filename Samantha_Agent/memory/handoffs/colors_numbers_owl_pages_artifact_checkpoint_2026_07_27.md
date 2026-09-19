Nazev: ColorsAndNumbers sova - aktuální publikace 2026-09-19
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-09-19

Co se resilo:
- Nová denní promluva podle přesně dodaného textu Míly.

Co je hotove:
- Jediný CSV řádek pro 2026-09-19, lokální MP3 náhled a veřejná publikace.
- Dodaný text je zachovaný znak po znaku, bez stylistické opravy; v handoffu se
  záměrně neopakuje.
- 17 cílených testů denní rutiny prošlo; lokální preview má 117 648 B.
- Produkční zdrojový commit je `009fa2d8` a obsahuje pouze tento CSV řádek;
  lokální pracovní commit je `b24bd9b7`.
- Pages workflow `35432115685` nad `009fa2d8` a deploy job `105868609077`
  uspěly.
- Veřejný `app.js` a `owl_190926.mp3` jsou ověřené 19. září v 10:30 CEST:
  `app.js` HTTP 200, výběr `owl_190926.mp3?v=20260919a`; audio HTTP 200,
  `audio/mp3`, 117 648 B.
- Pages artifact zůstal publikační autoritou a workflow nezměnilo `main`.
- Pages artifact je publikační autorita; historický blok níže je uzavřený.

Co neni hotove:
- Ruční poslech v prohlížeči neproběhl; HTTP, MIME, velikost a výběr dnešního
  souboru jsou ověřené.

Dalsi krok:
- Bez dalšího zásahu; nový text až na Mílův pokyn.

Navrhovane dalsi kroky:
- Žádné nové.

Zmenene nebo relevantni soubory:
- `OwlSpeech.csv`, `automated_recurring_tasks.md`, `ACTIVE_PROJECTS.md`.
- Produkční zdrojový commit `009fa2d8`; Pages workflow `35432115685`.

Bezpecnost / neukladat:
- Soukromý obsah ani audio se do tohoto handoffu nekopírují.
- Souběžné změny Camina zachované; do produkčního `main` byl odeslán pouze
  čistý owl commit z izolovaného checkoutu. Workflow oznámilo neblokující
  upozornění na vynucený Node.js 24 pro některé Actions.

## Historický checkpoint 2026-07-27 (nasazení dokončeno 2026-07-30)

Nazev: ColorsAndNumbers sova - publikace bez zapisu do main
Priorita: 1
Stav: ceka na nasazeni
Pripomenout pri startu: ano
Datum: 2026-07-27

Co se resilo:
- Denni sovi GitHub Actions workflow zapisoval generovane audio primo do
  vyvojove vetve `main` a mohl se pretlacit s dokoncenim Human-Adam vyvoje.
- Pro 2026-07-27 bylo na Miluv pokyn znovu vygenerovano audio z noveho textu;
  samotny text se v tomto handoffu neopakuje.

Co je hotove:
- Obe webove kopie dnesniho MP3 jsou platne a maji shodny SHA-256.
- Workflow uz nema `contents: write` a neobsahuje `git add`, `git commit` ani
  `git push`.
- Vygenerovana slozka `docs` se nahrava jako GitHub Pages artifact a samostatny
  job ji nasazuje pres oficialni Pages Actions.
- Cilenych 14 testu `test_daily_3am` a 8 testu `test_workflow_commands` proslo.
- Python syntaxe, YAML parse a `git diff --check` prosly.

Co neni hotove:
- GitHub Pages stale pouziva legacy zdroj `main/docs`; novy workflow proto jeste
  neni aktivni publikacni autoritou.
- Nebyl proveden prvni rucni GitHub Actions beh ani kontrola verejne stranky.

Dalsi krok:
- Samostatne potvrzene prepnout GitHub Pages z legacy `main/docs` na GitHub
  Actions, spustit workflow rucne a overit dnesni audio i to, ze `main` po behu
  zustal na stejnem commitu.

Navrhovane dalsi kroky:
- Po zivem overeni odstranit sovu jako zvlastni pripad z diagnostiky soubehu.
- Nasledne navrhnout lokalni vyvoj s jednim davkovym GitHub pushem denne.

Zmenene nebo relevantni soubory:
- `samantha-daily-3am.yml`
- `OwlSpeech.csv`
- `test_daily_3am.py`
- obe publikacni kopie dnesniho MP3

Bezpecnost / neukladat:
- Do handoffu, logu ani testu neprenaset soukrome texty, tajemstvi nebo private
  data; Pages artifact smi obsahovat pouze verejnou slozku `docs`.
