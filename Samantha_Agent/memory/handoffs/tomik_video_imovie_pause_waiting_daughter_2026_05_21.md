Nazev: Tomik video iMovie - pauza pred odsouhlasenim s dcerou
Priorita: 1
Stav: ceka na rozhodnuti
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Pokracovalo se v priprave rodinneho iMovie filmu Tomik druhy rok.
- Po hotovem auditu a vyberech vznikly prakticke review vystupy pro Milu a dceru.
- Projekt se ted pozastavuje, dokud Mila neodsouhlasi dalsi postup s dcerou.

Co je hotove:
- Short vyber pro iMovie:
  `data/private/tomik_rok_2/05_imovie_vyber_short/`
  - 35 MP4 klipu
  - surova delka cca 15:12
  - cil po strihu cca 3-5 minut
- Family vyber pro iMovie:
  `data/private/tomik_rok_2/06_imovie_vyber_family/`
  - 82 MP4 klipu
  - surova delka cca 32:11
  - cil po strihu cca 12-18 minut
- Short HTML review:
  `data/private/tomik_rok_2/03_audit/review_short.html`
- Family HTML review:
  `data/private/tomik_rok_2/03_audit/review_family.html`
- Short PDF pro poslani:
  `data/private/tomik_rok_2/03_audit/review_short.pdf`
  - 11 stran
  - cca 1,7 MB
- Family PDF pro poslani:
  `data/private/tomik_rok_2/03_audit/review_family.pdf`
  - 23 stran
  - cca 3,9 MB
- Lokální review server byl spusten pro pohodlne prohlizeni:
  `http://localhost:8765/03_audit/review_short.html`
  `http://localhost:8765/03_audit/review_family.html`
- HTML bylo upraveno tak, aby se kliknute video oteviralo do nove karty a review
  stranka zustala otevrena.

Co neni hotove:
- Dcera jeste neodsouhlasila postup.
- Neni rozhodnuto, jestli strihat short, family, nebo obe verze.
- Neni provedena finalni rucni selekce klipu podle dcery.
- Neni import do iMovie, hudba, titulky ani export.

Dalsi krok:
- Poslat dceri PDF, pravdepodobne nejdriv `review_short.pdf`, pripadne i
  `review_family.pdf`.
- Po jejim vyjadreni upravit vyber: vyhodit/pridat/preskladat klipy podle
  poznamek.
- Az potom importovat vybranou slozku do iMovie a strihat podle storyboardu.

Zmenene nebo relevantni soubory:
- `scripts/tomik_video_select_imovie.py`
- `scripts/tomik_video_review_pages.py`
- `scripts/tomik_video_review_pdf.py`
- `data/private/tomik_rok_2/05_imovie_vyber_short/`
- `data/private/tomik_rok_2/06_imovie_vyber_family/`
- `data/private/tomik_rok_2/03_audit/review_short.html`
- `data/private/tomik_rok_2/03_audit/review_family.html`
- `data/private/tomik_rok_2/03_audit/review_short.pdf`
- `data/private/tomik_rok_2/03_audit/review_family.pdf`

Bezpecnost / neukladat:
- Rodinna videa a detailni vystupy jsou v `data/private/`, ktera je ignorovana
  gitem.
- Nic z rodinnych videi necommitovat.
- Originaly nemazat ani neupravovat bez vyslovneho souhlasu.
