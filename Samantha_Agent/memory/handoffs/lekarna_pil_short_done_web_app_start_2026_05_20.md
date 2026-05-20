Nazev: Lekarna PIL_Short hotovo a start webove aplikace
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Doplnit k domaci lekarne kratke vytahy z pribalovych informaci do `PIL_Short`.
- Zdokumentovat opakovatelny postup pro budouci nove leky.
- Zalozit novy projekt "Webova aplikace Lekarna" pro sdileni vybranych informaci
  s Janickou.

Co je hotove:
- `data/lekarna/domaci_leky.csv` ma pro vsech 56 radku vyplneny `PIL_Short`
  nebo vysvetlujici status.
- Pouzite sloupce:
  - `PIL_Short`
  - `PIL_Source`
  - `PIL_Checked_Date`
  - `PIL_Match_Status`
- Statusy k 2026-05-20:
  - `overeno_sukl_dlp_pil`: 26
  - `overeno_sukl_dlp_ema_pil`: 1
  - `pravdepodobne_sparovano_sukl_pil`: 1
  - `nejista_varianta_sukl`: 4
  - `nejisty_nazev_pravdepodobne_sukl`: 3
  - `nejisty_nazev`: 4
  - `nenalezeno_sukl_overit_obal`: 7
  - `neni_lek_nebo_bez_sukl_pil`: 8
  - `neni_lek`: 2
- Vytvorena zaloha:
  - `data/lekarna/domaci_leky.backup_before_pil_short_all_20260520_152331.csv`
- Vytvoren report:
  - `data/lekarna/pil_short_report_20260520_152331.md`
- Testy prosly:
  - `.venv/bin/python -m unittest tests.test_lekarna_service`
- Kanonicky postup je zdokumentovan:
  - `memory/technical/lekarna_pil_short_workflow.md`
- Novy projekt zalozen:
  - `memory/projects/lekarna_web_app.md`

Co neni hotove:
- Webova aplikace jeste neni implementovana.
- Neni rozhodnuto, zda bude web verejny pres GitHub Pages, soukromy, nebo jen lokalni.
- Neni rozhodnuto, ktera pole se smi ukazat Janicce.
- Neni hotovy git-safe export z lokalniho soukromeho CSV do weboveho datasetu.

Dalsi krok:
- Nez se zacne kodovat web, potvrdit rozsah exportu pro Janicku:
  - zda ukazat umisteni leku,
  - zda ukazat fotky,
  - zda ukazat osobni leky,
  - zda web muze byt verejny v gitu/GitHub Pages.
- Potom vytvorit export skript, ktery z `data/lekarna/domaci_leky.csv` vyrobi
  omezeny JSON/CSV pro web.

Zmenene nebo relevantni soubory:
- `app/lekarna/models.py`
- `tests/test_lekarna_service.py`
- `memory/projects/lekarna_domaci_leky.md`
- `memory/technical/lekarna_pil_short_workflow.md`
- `memory/projects/lekarna_web_app.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `data/lekarna/domaci_leky.csv` lokalne, ignorovano gitem
- `data/lekarna/pil_short_report_20260520_152331.md` lokalne, ignorovano gitem

Bezpecnost / neukladat:
- `data/lekarna/` je soukroma evidence a je ignorovana v gitu.
- Plny inventar leku, osobni leky, umisteni a fotky nepublikovat bez vyslovneho
  rozhodnuti.
- Web nesmi pusobit jako davkovaci nebo lecba doporucujici nastroj.
