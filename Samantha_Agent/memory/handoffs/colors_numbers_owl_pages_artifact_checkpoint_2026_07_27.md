Nazev: ColorsAndNumbers sova - aktuální publikace 2026-09-14
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-09-14

Co se resilo:
- Nová denní promluva studentkám podle přesně dodaného textu.

Co je hotove:
- Jediný CSV řádek pro 2026-09-14, lokální MP3 náhled a veřejná publikace.
- 25 cílených testů a plná brána 1 656 testů prošly.
- Commit `8db5cd81`, Pages workflow `34820248317` nad stejným commitem.
- Veřejný app.js a owl_140926.mp3 ověřené 14. září v 09:59 CEST:
  HTTP 200, audio/mp3, 111 312 B, přibližně 18,6 s.
- Pages artifact je publikační autorita; historický blok níže je uzavřený.

Co neni hotove:
- Žádný otevřený implementační krok; ruční poslech v prohlížeči neproběhl.

Dalsi krok:
- Bez dalšího zásahu; nový text až na Mílův pokyn.

Navrhovane dalsi kroky:
- Žádné nové.

Zmenene nebo relevantni soubory:
- OwlSpeech.csv, automated_recurring_tasks.md, ACTIVE_PROJECTS.md.
- Technická účtenka mimo Git: data/daily_3am/receipts/20260914_publication.json.

Bezpecnost / neukladat:
- Soukromý obsah ani audio se do tohoto handoffu nekopírují.
- Souběžné změny Cockpitu zachované; publikován jen ověřený soví commit.

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
