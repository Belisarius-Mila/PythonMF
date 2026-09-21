Nazev: ColorsAndNumbers sova - výchozí publikace 2026-09-21
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-09-21

Co se resilo:
- Nová výchozí promluva pro každý den bez vlastní připravené položky a oprava
  návratu starého červencového audia.

Co je hotove:
- Přesně dodaný text je v jediném řádku `default`; v handoffu se neopakuje.
- Konkrétní datum má přednost, jinak se pro každý den vytvoří nová denní MP3.
- Cílené testy 19/19, lokální brána 1740/1740 a čistá produkční brána
  1719/1719 prošly. Náhled má 78 624 B a 13,104 s.
- Lokální commit `f71bc5d4`; produkční commit `b16cae26` byl z čistého
  izolovaného checkoutu odeslán fast-forward bez čekajících commitů Camina.
- Pages workflow `35567028291` nad `b16cae26` a deploy job `106230984887`
  uspěly.
- Veřejný `app.js` vybírá `owl_210926.mp3?v=20260921a`; audio vrací HTTP 200,
  `audio/mp3`, 78 624 B a 13,104 s.

Co neni hotove:
- Ruční poslech v prohlížeči neproběhl; HTTP, MIME, velikost a výběr dnešního
  souboru jsou ověřené.

Dalsi krok:
- Bez dalšího zásahu. Vlastní denní řádek příště automaticky přebije `default`.

Navrhovane dalsi kroky:
- Žádné nové.

Zmenene nebo relevantni soubory:
- `OwlSpeech.csv`, `daily_3am.py`, `test_daily_3am.py`, `daily_3am.md`.
- Produkční zdrojový commit `b16cae26`; Pages workflow `35567028291`.

Bezpecnost / neukladat:
- Soukromý obsah ani audio se do tohoto handoffu nekopírují.
- Souběžné změny Camina zachované; do produkčního `main` byl odeslán pouze
  čistý owl commit z izolovaného checkoutu. Workflow oznámilo neblokující
  upozornění na vynucený Node.js 24 pro některé Actions.

## Historický checkpoint 2026-09-19

- Denní promluva 19. 9. byla publikována workflow `35432115685` nad
  `009fa2d8`; veřejné audio mělo 117 648 B. Tento stav byl 21. 9. nahrazen
  výchozí promluvou popsanou výše.

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
