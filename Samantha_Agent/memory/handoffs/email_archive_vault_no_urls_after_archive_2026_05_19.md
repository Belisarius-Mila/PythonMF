Nazev: EmailArchiveVault - archivace uz nevypisuje plne URL
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Po realnem testu archivace UID 13964 se upresnilo pravidlo vystupu.
- Samotny tool `archive_email_by_uid` nesmi po archivaci nikdy vypisovat plne URL.
- Plne URL z archivu maji byt dostupne az pres samostatny budouci tool, napr. `show_archive_links`, po samostatnem potvrzeni.

Co je hotove:
- Upravene instrukce v `app/samantha_agent.py`.
- Upravena bezpecnostni poznamka vystupu v `app/email/archive_tools.py`.
- Zesilen regresni test v `tests/test_email_archive_tools.py`.
- Test ted overuje, ze vystup `archive_email_by_uid_text` neobsahuje:
  - cele telo e-mailu,
  - `https://`,
  - `http://`,
  - neredigovanou e-mailovou adresu,
  - domeny ulozenych odkazu.
- Archivni JSON muze stale obsahovat plne URL uvnitr lokálního citliveho archivu; nesmi se ale vypsat jako vysledek archivace.

Co neni hotove:
- Neni implementovan samostatny `show_archive_links` tool.
- Neni implementovana samostatna prace s ulozenym archivem.

Dalsi krok:
- Navrhnout a implementovat `show_archive_links` jako samostatne potvrzovany tool nad lokalnim archivem.
- Tool musi vyzadovat konkretni archive id nebo UID a jasny souhlas se zobrazenim plnych odkazu.
- Bez potvrzeni nesmi cist/vypisovat `links.json`.

Zmenene nebo relevantni soubory:
- `app/samantha_agent.py`
- `app/email/archive_tools.py`
- `tests/test_email_archive_tools.py`
- `app/email/archive_service.py`
- `data/email/archive/` je lokalni citlive uloziste a nesmi se commitovat.

Overeni:
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: 113 testu OK.

Bezpecnost / neukladat:
- Neukladat obsah archivovanych e-mailu do memory.
- Neukladat ani nevypisovat plne URL z archivace automaticky.
- Nevypisovat neredigovane e-mailove adresy ve vystupu archivace.
- Neotevirat odkazy.
- Nespoustet ani samostatne nestahovat prilohy.
- Nic neodesilat, nemazat, nepresouvat ani neoznacovat jako prectene.
- `show_archive_links` musi byt samostatny budouci potvrzovany krok.
