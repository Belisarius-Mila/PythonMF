Nazev: Dokumentovy vault - e-mailove PDF revize, metadata a case workflow
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-06-13

Co se resilo:
- Navazovalo se na auditovy bod `Dokumentovy vault detail case + rozhodnuti dalsiho smeru`.
- Realny e-mailovy PDF dokument ukazal, ze e-mailove prilohy se ukladaji bezpecne k revizi, ale review workflow bylo matouci:
  - technicky typ `email-attachment-pdf` mohl pusobit jako hotovy typ dokumentu,
  - rucne zadana nova oblast se drive mohla ztratit na `other`,
  - klasifikacni panel neumel pohodlne doplnit `case_id`,
  - ScanDocu revize aktualizovala metadata, ale ne vzdy vycistila `reading_status=needs_review`,
  - Cockpit karta `Ulozene dokumenty k revizi` mohla ukazovat dokument, ktery ScanDocu uz povazoval za zrevidovany.

Co je hotove:
- `normalize_domain()` zachova novou rucne zadanou oblast jako bezpecny slug, napriklad `CEZ smlouvy` -> `cez-smlouvy`.
- `email-attachment-pdf` se v Cockpitu bere jako slaby/technicky typ, dokud neni nahrazen skutecnym typem dokumentu.
- Klasifikacni metadata v Cockpitu umi doplnit i `case_id`.
- Rucne zadane ceske hodnoty pro oblast, typ dokumentu a case se slugify normalizuji bez ztraty prvniho pismene.
- ScanDocu revize existujiciho dokumentu nastavuje `reading_status=ok` a auditni poznamku.
- Cockpit fronta ulozenych dokumentu k revizi preskakuje dokumenty, ktere uz maji ve ScanDocu actions `reviewed` nebo `review_skipped`.
- Po Milove potvrzeni byl konkretni zrevidovany dokument UID 14438 oznacen v soukromem vaultu jako `OK`.

Co neni hotove:
- Neni hotovy plnohodnotny editor/seznam existujicich oblasti a case v UI.
- Neni hotove automaticke zpetne cisteni vsech historickych dokumentu se slabym typem; toto musi byt po samostatnem potvrzeni.
- Neni rozhodnuto, jestli dalsi vetsi smer bude OCR/re-review pipeline nebo sjednoceny intake panel.

Dalsi krok:
- Restartovat Cockpit a rucne otestovat realny pruchod:
  1. `Dokumenty k revizi` uz nema nabizet zpracovany dokument.
  2. `Doplnit metadata` dovoli napsat novou oblast a case.
  3. Detail case ukaze dokument pod novou souvislosti, pokud byl case vyplnen.

Navrhovane dalsi kroky:
- Okamzite: UI retest po restartu Cockpitu.
- Volitelne potom: pridat lepsi modal pro metadata misto postupnych `prompt()` oken.
- Vetsi smer potom rozhodnout podle bolesti z retestu: OCR/re-review vs sjednoceny intake Downloads/e-mail/mobilni sken.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/documents/scandocu.py`
- `app/documents/vault.py`
- `tests/test_cockpit.py`
- `tests/test_document_vault_tools.py`

Bezpecnost / neukladat:
- Do handoffu neukladat obsah PDF, text smlouvy, cisla smluv, adresy, osobni udaje ani cele e-maily.
- Soukromy vault v `data/private/documents/` zustava mimo git.
