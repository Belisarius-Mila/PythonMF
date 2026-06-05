Nazev: USA 2019 - Tomik 2 prehled a navazujici predstrihovy formular
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-05

Co se resilo:
- Navazani na projekt Family Memory Films / USA 2019 po vycisteni dnu,
  obnoveni smesneho CSV a vytvoreni lidskeho review workflow.
- Mila chce celkovy prehled ve stylu `Tomik 2`: navrh kratkeho filmu, navrh
  dlouheho filmu a zpusob, jak do filmu zaradit fotografie.

Co je hotove:
- Cisty seznam 15 filmu pouzitelnych dnu je odsouhlaseny:
  `2019-07-20` az `2019-08-03`.
- Den `2019-08-05` neni samostatny den filmu; je to smesny zdroj a jeho videa
  se pouzivaji jen podle item-level review.
- Prvni celkovy prehled je ulozen mimo git v:
  `data/private/family_memory_films/usa_2019/03_overview/usa_2019_tomik2_overview.md`.
- Predstrihovy formular je vygenerovany mimo git v:
  `data/private/family_memory_films/usa_2019/03_overview/film_selection_form.html`.
  Pracuje s `film_selection_review.csv`, ma 2688 polozek, denni filtr,
  rating `A/B/C/skip`, volby pro kratky/dlouhy film, autosave, CSV export a
  prehravani videi pres read-only lokalni server originalu.
- Git-safe memory byla aktualizovana a pushnuta commitem:
  `c4762f6 Document USA 2019 film overview step`.

Co neni hotove:
- Jeste neni hotovy finalni seznam konkretne vybranych fotek a videi pro iMovie.

Dalsi krok:
- Otevrit `http://127.0.0.1:8792/03_overview/film_selection_form.html`.
- Rucne oznacit kandidaty fotek a videi: hlavne `A`, `B`, `skip`, kandidat
  kratky film, kandidat dlouhy film a poznamka pro strih.
- Po praci stahnout CSV a pri navazani brat nejnovejsi
  `~/Downloads/film_selection_review*.csv` jako zdroj pravdy.

Navrhovane dalsi kroky:
- Okamzite: Mila projde formular, ulozi/stahne CSV a Adam vezme nejnovejsi
  stazene CSV jako zdroj pravdy.
- Dale: podle vyberu pripravit iMovie importni balicek nebo strihovy checklist.

Zmenene nebo relevantni soubory:
- Git-safe:
  - `memory/projects/family_memory_films.md`
  - `memory/handoffs/family_memory_usa_2019_tomik2_overview_checkpoint_2026_06_05.md`
- Private mimo git:
  - `data/private/family_memory_films/usa_2019/01_intake/media_manifest.csv`
  - `data/private/family_memory_films/usa_2019/02_review/day_review.csv`
  - `data/private/family_memory_films/usa_2019/02_review/block_review.csv`
  - `data/private/family_memory_films/usa_2019/02_review/mixed_2019_08_05/mixed_2019-08-05_review.csv`
  - `data/private/family_memory_films/usa_2019/03_overview/usa_2019_tomik2_overview.md`
  - `data/private/family_memory_films/usa_2019/03_overview/film_selection_review.csv`
  - `data/private/family_memory_films/usa_2019/03_overview/film_selection_form.html`

Bezpecnost / neukladat:
- Do gitu nedavat fotky, videa, nahledy, manifesty, GPS metadata, realne rodinne
  poznamky ani exporty rozhodnuti z formulare.
- Originaly z `/Users/miloslavfalta/Desktop/USA` nemazat, neprejmenovavat ani
  nepresouvat bez samostatneho vyslovneho potvrzeni.

Copy/paste handoff:
- Pokracujeme na Family Memory Films / USA 2019.
- Cisty seznam dnu je hotovy, `2019-08-05` je smesny zdroj, ne den filmu.
- Master prehled `Tomik 2` je v
  `data/private/family_memory_films/usa_2019/03_overview/usa_2019_tomik2_overview.md`.
- Predstrihovy formular je v
  `data/private/family_memory_films/usa_2019/03_overview/film_selection_form.html`
  a bezi na `http://127.0.0.1:8792/03_overview/film_selection_form.html`.
- Dalsi krok je rucne oznacit kandidaty fotek/videi a stahnout
  `film_selection_review.csv`.
