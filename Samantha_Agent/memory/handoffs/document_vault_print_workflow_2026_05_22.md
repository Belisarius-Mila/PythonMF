Nazev: Dokumentovy vault - workflow pro tisk dokumentu
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-05-22

Co se resilo:
- Mila chce umet rict napriklad: vyhledej puvodni smlouvu o penzijnim
  pripojisteni a vytiskni ji.
- Soucasny dokumentovy vault umel vyhledat a ulozit dokument, ale nemel bezpecny
  workflow pro pripravu a potvrzeny tisk.

Co je hotove:
- Pridan dvoukrokovy tiskovy workflow:
  - `prepare_document_print_job`
  - `run_document_print_job`
- `prepare_document_print_job` najde jednoznacny dokument podle `document_id`
  nebo dotazu, zkopiruje pracovni kopii do
  `data/private/documents/print_queue/` a vytvori zaznam v
  `data/private/documents/index/print_jobs.jsonl`.
- `run_document_print_job` vyzaduje samostatne potvrzeni s `print_job_id`, spusti
  macOS tiskovy prikaz `lp` a po uspesnem predani tisku smaze jen kopii z
  `print_queue`.
- Pri chybe tisku kopii v `print_queue` ponecha a vrati zpravu, ze tisk se
  nedari.
- Originál ve vaultu se tiskem nikdy nemaze.
- Samantha instrukce jsou doplnene o pravidlo pro tisk dokumentu.
- Testy pokryvaji pripravu tisku, chybejici potvrzeni, uspesny tisk s mazanim
  kopie a neuspesny tisk s ponechanim kopie.

Co neni hotove:
- Nebyl spusten realny tisk na tiskarne; testy pouzivaji fake print runner.
- Neni hotova pokrocila kontrola realne tiskove fronty po odeslani; aktualne se
  za uspech bere navratovy kod systemoveho prikazu `lp`.

Dalsi krok:
- Pri prvnim realnem tisku nejdriv spustit `prepare_document_print_job` pro
  jednoznacny dokument, potom po potvrzeni `run_document_print_job`. Pokud tisk
  selze, zkontrolovat tiskarnu/frontu a zkusit job znovu.

Zmenene nebo relevantni soubory:
- `app/documents/vault.py`
- `app/documents/tools.py`
- `app/documents/__init__.py`
- `app/samantha_agent.py`
- `tests/test_document_vault_tools.py`
- `memory/technical/private_document_vault_workflow.md`
- `memory/projects/document_management_private_vault.md`

Overeni:
- `.venv/bin/python -m unittest tests.test_document_vault_tools` - OK, 24 testu.
- `.venv/bin/python -m py_compile app/documents/vault.py app/documents/tools.py app/documents/__init__.py app/samantha_agent.py tests/test_document_vault_tools.py` - OK.

Bezpecnost / neukladat:
- `data/private/documents/print_queue/` je soukroma pracovni slozka mimo git.
- Mazani po tisku smi smazat pouze pracovni kopii z `print_queue`, nikdy original
  ve vaultu.
- Netisknout bez samostatneho potvrzeni s `print_job_id`.
