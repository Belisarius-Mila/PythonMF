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
