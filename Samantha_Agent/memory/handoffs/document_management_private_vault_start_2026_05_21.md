Nazev: Sprava dokumentu - soukromy dokumentovy trezor
Priorita: 1
Stav: MVP implementovane, realne PDF/OCR testy provedene, ostrý intake test ceka na potvrzeny import
Pripomenout pri startu: ano
Datum: 2026-05-21

## Co se resilo

Mila chce zalozit novy priorita 1 projekt pro systemovou spravu dulezitych
dokumentu mimo git. Nejde jen o pojistky, ale i smlouvy, faktury, revizni a
servisni protokoly, dokumentaci ke kotli, fotovoltaice, domu, autu a dalsim
zarizenim.

Cil: dokumenty budou ulozene v `data/private/documents/`, Samantha v nich bude
umet hledat, navrhne zarazeni a automaticky vytahne kandidaty na due date.
Reminder vznikne az po potvrzeni spravneho data.

## Co je hotove

- Zalozen projektovy memory soubor:
  `memory/projects/document_management_private_vault.md`
- Zalozen technicky workflow:
  `memory/technical/private_document_vault_workflow.md`
- Navrzena struktura private uloziste a indexu.
- Implementovany a napojeny MVP tooly:
  `prepare_document_import`, `inspect_document_text`,
  `apply_document_import`, `search_private_documents`,
  `save_document_due_reminder`.
- Pridan modul `app/documents/`.
- Pridany testy `tests/test_document_vault_tools.py`.
- Cile testy prosly: dokumentovy vault, payment case documents, payment SMS a
  reminders store/tools/query.
- Realny read-only test na trech pojistovacich PDF ze Seznam priloh ukazal, ze
  jde o sifrovana/uzamcena PDF; vsechny jsou `pdf-encrypted`.
- Po realnem testu byla opravena logika extrakce, aby nouzove dekodovani bajtu
  neoznacovalo obrazova PDF jako textove zpracovana.
- Tri testovana PDF byla metadata-only importovana do
  `data/private/documents/vault/insurance/` a jsou dohledatelna pres
  `search_private_documents`.
- OCR vrstva byla doplnena pres `poppler` + `tesseract` + `tesseract-lang` a
  overena na neuzamcenem obrazkovem PDF.
- Dalsi hledani v pojistovacich PDF naslo 32 nezamcenych PDF. Jedno PDF bez
  textove vrstvy bylo realne zpracovane pres `tesseract-ocr`:
  `metlife-akciove-fondy-ocr`.
- Dve dalsi nezamcene textove pojistovaci PDF byla importovana do vaultu:
  `kooperativa-pojisteni-vozidla-6300720621-2023` a
  `kooperativa-upomenuti-platby-6391193598-2025`.
- Dalsi tri nezamcene PDF byly precteny read-only:
  `09_Zhodnocen_investice_World_index_21-_akcie_sv_tov_.pdf` pres
  `tesseract-ocr`, `05_Zelen_karta.pdf` pres `pdftotext` a
  `08_potvrzeni_odpovednosti.pdf` pres `pdftotext`.
- OCR nastaveni bylo doladeno: `--psm 3` zustava default, render byl zmenen
  z 250 DPI na 200 DPI, protoze na testovanem tabulkovem MetLife PDF daval
  cistsi text a mensi docasne obrazky.
- Na dalsich tabulkovych PDF bylo OCR vynuceno:
  `21_Oce_ovac_tabulky.pdf`, `25_Kompletn_porovn_n_nab_dek.pdf` a
  `06_Tabulka_asisten_n_ch_slu_eb.pdf`.
- Nalezen a opraven dulezity edge case: samotna PDF znacka `/Encrypt` nesmi byt
  automaticka stopka, protoze nektera PDF jsou presto citelna pres `pdftotext`
  nebo OCR. `pdf-encrypted` se vraci az po neuspesnem pokusu o extrakci.
- Doplnen volitelny `pdfplumber` parser tabulek:
  `requirements.txt` obsahuje `pdfplumber`, lokalni `.venv` ma `pdfplumber 0.11.9`.
  Standardni extrakce PDF s textovou vrstvou umi pripojit nalezene tabulky jako
  `pdftotext+pdfplumber-tables`.
- Realny test `pdfplumber`:
  `21_Oce_ovac_tabulky.pdf` -> 8 tabulek z prvnich 8 stran,
  `25_Kompletn_porovn_n_nab_dek.pdf` -> 6 tabulek,
  `06_Tabulka_asisten_n_ch_slu_eb.pdf` -> 6 tabulek.
- Doplnen user-friendly intake:
  `scan_document_inbox` read-only kontroluje
  `data/private/documents/inbox/incoming/`, vypise cekajici soubory a navrhne
  `prepare_document_import`. Startup kontext obsahuje jen pocet cekajicich
  dokumentu, ne nazvy souboru.
- Ostrý intake test 2026-05-22:
  - v inboxu je `data/private/documents/inbox/incoming/potvrzeni_scan_zarovnany.pdf`;
  - `scan_document_inbox` ho vidi jako cekajici soubor;
  - `prepare_document_import` a `inspect_document_text` ho read-only precetly pres
    `tesseract-ocr`;
  - podle obsahu jde o danove potvrzeni o zdanitelnych prijmech za cast roku 2025,
    ne o pojistku;
  - navrh zarazeni: oblast `tax`, typ `tax_income_confirmation`, document_id
    `centrum-83-potvrzeni-prijmy-2025`;
  - protistrana: `Centrum 83, poskytovatel socialnich sluzeb`;
  - nalezene datum 2026-01-27 vypada jako datum vystaveni/podpisu, ne due date,
    proto nevytvaret reminder.

## Co neni hotove

- Uzamcena PDF potrebuji odemcenou kopii nebo heslo; OCR samotne neprecte zamek.
- Obsahove hledani u tri metadata-only pojistovacich PDF zatim neni, protoze
  nejsou odemcena.
- Robustni extrakce castek, identifikatoru a protistran je zatim jednoducha
  heuristika.
- Search je zatim JSONL fulltext, ne SQLite FTS ani embedding index.
- Dokument `potvrzeni_scan_zarovnany.pdf` zatim NENI ulozeny ve vaultu ani
  zaindexovany; probehlo jen read-only cteni. Import ceka na Milovo samostatne
  potvrzeni pres `apply_document_import`.

## Dalsi krok

Navazujici krok:

1. Ziskat odemcenou kopii nebo heslo k pojistovacim PDF, pokud je Mila chce
   obsahove indexovat.
2. Znovu obohatit tri metadata-only dokumenty v insurance vaultu.
3. U novych nezamcenych PDF pokracovat importem pres `prepare_document_import`
   a `apply_document_import`.
4. Zkontrolovat due date kandidaty u Kooperativa dokumentu a pripadne samostatne
   ulozit reminder.
5. Pokud bude treba dale ladit OCR pro tabulky, testovat hlavne oddeleni
   "datum zaplaceno do" vs. skutecna splatnost; aktualni OCR text je pro hledani
   pouzitelny, ale due date heuristika je u tabulek stale opatrne k rucnimu
   potvrzeni.
6. Pro presne tabulky zvazit dalsi fazi: Camelot/Tabula/pdfplumber pro PDF s
   textovou vrstvou a az potom OCR layout parser pro skeny.
7. Dalsi prakticky krok: pridat samostatny `inspect_document_tables` tool, aby
   Samantha umela ukazat jen tabulky bez dlouheho plneho textu dokumentu.
8. Pri startu Samanthy a pri dotazech typu "mam nove dokumenty" pouzit
   `scan_document_inbox`; pokud jsou soubory v inboxu, pokracovat read-only
   preview pres `prepare_document_import`.
9. Po restartu pro ostrý test nejdriv overit, ze startup kontext hlasi 1 cekajici
   dokument v inboxu. Potom na dotaz k dokumentu pouzit `scan_document_inbox`.
10. Pokud Mila chce dokument ulozit, vyzadat/akceptovat potvrzeni:
    `Potvrzuji, ulož dokument potvrzeni_scan_zarovnany.pdf do oblasti tax.`
    Pak volat `apply_document_import` s `target_domain="tax"`,
    `document_type="tax_income_confirmation"`, `counterparty="Centrum 83, poskytovatel socialnich sluzeb"`
    a `document_id="centrum-83-potvrzeni-prijmy-2025"`.
11. Po potvrzenem importu otestovat `search_private_documents` dotazy typu:
    "potvrzeni o prijmech 2025", "Centrum 83", "danove potvrzeni".

## Zmenene nebo relevantni soubory

- `memory/projects/document_management_private_vault.md`
- `memory/technical/private_document_vault_workflow.md`
- `memory/handoffs/document_management_private_vault_start_2026_05_21.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `app/documents/__init__.py`
- `app/documents/vault.py`
- `app/documents/tools.py`
- `tests/test_document_vault_tools.py`
- `app/samantha_agent.py`

## Bezpecnost / neukladat

- Necommitovat dokumenty ani extrahovany text.
- Dokumenty patri do `data/private/documents/`.
- Do memory ukladat jen pravidla, stav a redigovane shrnuti.
- Do memory neukladat plny text danoveho potvrzeni, rodne cislo, adresu,
  castky ani dalsi osobni/danove udaje z dokumentu.
- Neprepisovat ani nemazat originalni soubory bez vyslovneho potvrzeni.
