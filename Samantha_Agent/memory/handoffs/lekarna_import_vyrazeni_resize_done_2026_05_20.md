Nazev: Lekarna - import fotek, umisteni, vyrazeni leku a zmenseni fotek hotovo
Priorita: 1
Stav: hotovo, cekaji jen navazujici provozni kroky
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Pokracovani projektu Lekarna po doplneni novych fotek leku.
- Import 8 opravenych JPEG fotek a 4 WhatsApp JPEG fotek do evidence.
- Doplnovani umisteni leku v CSV.
- Dotazy nad inventarem: osobni leky na zaludek/tlak a co je doma na bolest zad.
- Navrh a implementace bezpecneho workflow pro vyrazeni leku bez mazani radku.
- Zmenseni fotek v lekarne pres novou obecnou media utilitu.

Co je hotove:
- `data/lekarna/domaci_leky.csv` obsahuje 56 polozek.
- Import 8 JPEG fotek byl proveden a zdokumentovan v
  `data/lekarna/photo_import_20260520_015239.md`.
- Import 4 WhatsApp fotek byl proveden a zdokumentovan v
  `data/lekarna/photo_import_20260520_020238.md`.
- Foto zdroje po importech i po zmenseni obrazku byly validovane: `missing_sources=0`.
- Pro umisteni bylo v CSV nastaveno:
  - osobni denni leky Mily do `U léků - Míla (osobní denní léky)`,
  - osobni leky Jany do `U léků - Jana (osobní léky)`,
  - ostatni leky do `Horní koupelna`.
- Doplnil se Miluv vecerni lek Agomelatin do Milova umisteni.
- Odpoved na Milovy leky k objednani:
  - Omeprazol Teva Pharma - 20 mg,
  - Tonarssa - 4 mg / 5 mg.
- Dotaz na bolest zad vratil inventarni kandidaty bez davkovani a s bezpecnostnim upozornenim.
- Implementovan soft-delete workflow pro vyrazeni leku:
  - `preview_vyrazeni_leku`,
  - `apply_vyrazeni_leku`,
  - potvrzovaci veta `Potvrzuji vyrazeni leku`,
  - radek se nemaze, ale nastavi se `mnozstvi=vyradeno`, `umisteni=vyradeno`,
    `nutno_overit=ano` a prida se poznamka s datem a duvodem.
- Bezna evidence/hledani vyrazene polozky nenabizi.
- Lékárenské fotky byly zmenseny na cca 100 kB:
  - pred zmensovanim cca 46.14 MB,
  - po zmenseni cca 3.70 MB,
  - 40 obrazku, 0 kandidatu nad 100 kB.

Co neni hotove:
- Neni zatim commit/push aktualnich zmen.
- Cely `unittest discover -s tests` mel drive 1 nesouvisejici fail v e-mailovem
  testu kvuli ocekavanemu datu `2026-05-19` vs aktualni `2026-05-20`.
- `../Samantha_GIT_PUSH.txt` je Miluv vlastni soubor pro postup pri sekani Codexu;
  zatim se ho nedotykat, dokud Mila nerekne dalsi krok.

Dalsi krok:
- Navazat na Milovu zadost a podivat se na `../Samantha_GIT_PUSH.txt`.
- Pokud se bude pracovat s git publikaci, nebrat `git add .`; pridavat jen
  vedome vybrane soubory.
- Pri dalsim vyrazeni leku pouzit preview a apply az po potvrzeni
  `Potvrzuji vyrazeni leku`.
- Pri dalsich fotkach leku pouzit stavajici foto import workflow pres manifest.

Zmenene nebo relevantni soubory:
- `app/lekarna/service.py`
- `app/lekarna/tools.py`
- `app/lekarna/__init__.py`
- `app/samantha_agent.py`
- `tests/test_lekarna_service.py`
- `memory/projects/lekarna_domaci_leky.md`
- `data/lekarna/domaci_leky.csv`
- `data/lekarna/Leky_v_Krabickach/`
- `data/media/image_resize_backups/20260520_025659/`
- `data/media/image_resize_backups/20260520_030427/`

Overeni:
- `.venv/bin/python -m py_compile ...` pro dotcene moduly proslo.
- `.venv/bin/python -m unittest tests.test_lekarna_service` proslo.
- Po zmenseni obrazku proslo:
  `.venv/bin/python -m unittest tests.test_media_image_resize tests.test_lekarna_service`
  s vysledkem 24 testu OK.
- `scripts/lekarna_photo_import.py validate` vratil `missing_sources=0`.

Bezpecnost / neukladat:
- Do memory neukladat dalsi osobni zdravotni detaily nad ramec tohoto technickeho
  handoffu.
- Neuvadet davkovani leku; evidence je inventar, ne lekarske doporuceni.
- Nemazat fotky ani zalohy bez vyslovneho Milova souhlasu.
