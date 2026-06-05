# Family Memory Films

Zalozeno: 2026-06-04
Priorita: 1
Stav: obecna platforma pro trideni rodinnych fotek/videi a pripravu
vzpominkovych filmu; prvni prakticky dataset je USA 2019 na plose Macu

## Smysl

Projekt ma zobecnit zkusenosti z `Tomik video iMovie` / `FamilyVideoOrganizer`
na opakovatelny workflow pro velke rodinne akce, dovolene a cesty.

Cil neni hned strihat film. Cil prvni faze je bezpecne projit velky archiv,
udelat katalog, nahledy, casove a tematicke bloky, vybrat reprezentativni
material a teprve potom pripravit storyboard pro iMovie nebo podobny strihovy
nastroj.

## Prvni dataset: USA 2019

Pracovni kopie je na Macu:

```text
/Users/miloslavfalta/Desktop/USA
```

Soukrome vystupy patri mimo git do:

```text
data/private/family_memory_films/usa_2019/
```

## Bezpecnost

- Originaly nemazat, neprejmenovavat a nepresouvat bez samostatneho potvrzeni.
- Prvni kroky jsou read-only nad zdrojovymi soubory.
- Do gitu nepatri fotky, videa, nahledy, GPS metadata, realne manifesty ani
  rodinne poznamky nad konkretnimi soubory.
- Do git-safe memory patri jen workflow, stav a obecna rozhodnuti.

## Vztah k Tomik video / FamilyVideoOrganizer

Pouzit se da:

- princip soukromeho katalogu mimo git,
- generator nahledu,
- webove rozhodovaci UI,
- export rozhodnuti do JSON,
- oddeleni originalu od vyberu.

Rozsirit je potreba:

- z videi na fotky + videa,
- z jednoho casoveho proudu na vice zdroju/pristroju,
- o bloky podle dne/mista/tematu,
- o hledani duplicit a podobnych fotek,
- o storyboard pro film do 30 minut.

## Workflow

1. Read-only intake katalog:
   - manifest vsech souboru,
   - casova osa,
   - souhrn podle zdrojovych slozek,
   - zakladni metadata fotek/videi.
2. Nahledy a kontaktni listy:
   - male nahledy fotek,
   - video snimky,
   - prvni galerie pro rychle prochazeni.
   - k dennim contact sheetum rovnou vytvorit lidsky editovatelny formular
     `day_review_form.html` nad `day_review.csv`.
3. Bloky:
   - automaticke bloky podle casu,
   - rucni nazvy mist/temat,
   - velikost materialu v kazdem bloku.
4. Cisteni:
   - podobne fotky,
   - nepouzitelne zaberove serie,
   - A/B/C vyber bez mazani originalu.
5. Storyboard:
   - max 30 minut,
   - 8-12 kapitol,
   - mix fotek, kratkych videi, titulku a mapy cesty.

## Aktualni stav k 2026-06-04

Read-only intake pro `/Users/miloslavfalta/Desktop/USA` je hotovy.

Soukrome vystupy mimo git:

```text
data/private/family_memory_films/usa_2019/01_intake/
data/private/family_memory_films/usa_2019/02_review/
```

Souhrn intake:

- 2742 medialnich souboru.
- 1642 fotek.
- 1100 videi.
- 33.10 GiB podle katalogu.
- 4 zdrojove skupiny: `JanaFotak`, `Nikond60`, `iphonejana`, `iphonemila`.

Review prep je po obnoveni po ukoncenem terminalu take hotovy:

- 2742 ocekavanych nahledu existuje.
- Vytvoreno 81 blokovych contact sheetu a 29 dennich contact sheetu.
- `blocks.csv` obsahuje 81 casovych bloku.
- Pro denni kontrolu vznikl lidsky formular `02_review/day_review_form.html`
  a editacni soubor `02_review/day_review.csv`.
- Po Milove rucni editaci denniho review vznikl take blokovy review soubor
  `02_review/block_review.csv` a formular `02_review/block_review_form.html`.
  `block_review.csv` ma 81 bloku, prenesene opravy datumu z poznamek,
  predvyplnene kratke nazvy a stav `use_in_film` pro rychle rozhodovani po
  mensich blocich.
- Smesne bloky `2019-08-05_B01` a `2019-08-05_B02` se nemaji pouzivat jako
  celek. Pro ne vzniklo samostatne item-level review
  `02_review/mixed_2019_08_05/mixed_2019-08-05_review.csv` a formular
  `02_review/mixed_2019_08_05/mixed_2019-08-05_form.html`. Prvni konzervativni
  pruchod priradil 226 z 280 videi ke zrejmym dnům/mistum a 54 nechal mimo
  zpracovani.
- `thumbnail_errors.csv` hlasi 10 problemovych videonahledu; skript pro ne
  vytvoril placeholdery.
- Vedlejsi duplicitni JPG soubory s koncovkou typu ` 2.jpg` byly po Milove
  potvrzeni smazany; kontrola po uklidu hlasi 2742 JPG, 0 chybejicich a
  0 prebyvajicich oproti manifestu.

Relevantni git-safe skripty:

- `scripts/family_memory_intake.py`
- `scripts/family_memory_prepare_review.py`
- `scripts/family_memory_prepare_block_review.py`
- `scripts/family_memory_prepare_mixed_review.py`

## Aktualni stav k 2026-06-05

- Cisty seznam 15 filmu pouzitelnych dnu USA 2019 je odsouhlaseny:
  `2019-07-20` az `2019-08-03`.
- Den `2019-08-05` neni samostatny den filmu; je to smesny zdroj, jehoz
  videa se pouzivaji jen podle item-level review.
- Prvni celkovy prehled ve stylu `Tomik 2` je ulozen mimo git v
  `data/private/family_memory_films/usa_2019/03_overview/usa_2019_tomik2_overview.md`.
  Obsahuje ciste dny, pocty fotek/videi, navrh kratkeho filmu, navrh dlouheho
  filmu a doporuceni pro zarazeni fotografii.
- Dalsi prakticky krok uz neni oprava datumu, ale vyber kandidatu do filmu:
  pripravit review formular pro foto/video vyber po kapitolach nebo dnech,
  s autosave, CSV exportem a prehravanim videi.

## Aktualni dalsi krok

Pripravit druhy rozhodovaci formular pro predstrihovy vyber:

- radek = den nebo kapitola,
- sloupce = kandidat do kratkeho filmu, kandidat do dlouheho filmu, fotky A,
  videa A, poznamka pro strih,
- zachovat autosave do prohlizece a CSV export,
- u videi zachovat tlacitko `Prehrat video`,
- vystup brat jako podklad pro iMovie import/organizaci, ne jako prikaz k mazani
  originalu.

Pokud se bude jeste vracet ke smesnemu dni `2019-08-05`, pouzivat novejsi
lokalni formular s videoprehravanim a ne stary port z drivejsiho handoffu.
Pri dalsi uprave brat nejnovejsi stazene
`~/Downloads/mixed_2019-08-05_review*.csv` jako zdroj pravdy.
