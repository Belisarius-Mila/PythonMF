Nazev: Mobilni dokumenty - RAW/BW zpracovani a klasifikace
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-27

Co se resilo:
- Pokracovalo se v mobilnim intake dokumentu pres iPhone zkratku `Skenovat dokument pro Samanthu`.
- V iCloud inboxu `SamanthaDocumentInbox` se testovaly batche `scan_B`, `scan_D` a `scan_F`.
- Byl dopsan procesor `process_mobile_document_inbox`, ktery reaguje na `process_request.json`, pripravi pracovni PDF, udela OCR/analyzu a zapise `process_result.json`; finalni import do vaultu stale neprovede.
- Resila se kvalita fotek/scanu:
  - `scan_B` byl spatna/tmava fotka, pomohlo cernobile cisteni.
  - `scan_D` a `scan_F` byly lepsi fotky, agresivni cernobile cisteni je zhorsovalo.

Co je hotove:
- `process_mobile_document_inbox` je implementovany v `app/documents/vault.py`, wrapper je v `app/documents/tools.py`, export v `app/documents/__init__.py` a tool je registrovany v `app/samantha_agent.py`.
- `requirements.txt` obsahuje `opencv-python-headless` pro obrazove cisteni.
- Zpracovani ma rezimy pres `SAMANTHA_DOCUMENT_CLEAN_PROFILE`:
  - vychozi `raw`: jen EXIF orientace + ulozeni do PDF, bez cisteni;
  - `bw`: nouzove cernobile cisteni pro spatne dokumenty;
  - `color`/`rgb`: konzervativni barevny rezim bez BW thresholdingu.
- `SAMANTHA_DOCUMENT_OPENCV_RECTIFY` je defaultne vypnute; perspektivni narovnani se nema pouzivat bez vyslovneho testu, protoze varianta `scan_b-6` byla nepouzitelna.
- Realne vystupy pred uklidem:
  - `data/private/documents/mobile_inbox/processing/scan_b-11/scan_b.pdf` - cernobile nouzove vylepseni spatneho `scan_B`;
  - `data/private/documents/mobile_inbox/processing/scan_d-2/scan_d.pdf` - RAW varianta receptu, lepsi nez BW;
  - `data/private/documents/mobile_inbox/processing/scan_f/scan_f.pdf` - RAW varianta, dobra pro kvalitni fotky.
- Testovaci scany byly pozdeji smazany z lokalniho processing adresare i z iCloud `SamanthaDocumentInbox`, aby nezabiraly misto.
- Finalni mobilni import je dodelany jako dvoukrokovy proces:
  - `prepare_mobile_document_final_import` ukaze PDF, navrzena metadata, `case_id` a potvrzovaci vetu;
  - `apply_mobile_document_final_import` ulozi jeden zpracovany mobilni dokument do vaultu az po samostatnem potvrzeni.
- Testy po posledni zmene prosly:
  - `test_normalize_mobile_document_page_crops_borders`
  - `test_normalize_mobile_document_page_raw_profile_preserves_geometry`
  - `test_prepare_mobile_document_batch_creates_working_pdf_without_deleting_source`
  - `test_process_mobile_document_inbox_creates_pdf_analysis_and_marks_request`
- `py_compile` proslo pro `app/documents/vault.py` a `tests/test_document_vault_tools.py`.

Co neni hotove:
- Neni hotove automaticke rozhodovani RAW vs LIGHT vs BW podle kvality vstupu.
- Neni hotova zkratka pro import hotoveho GPT PDF z Downloads do `SamanthaDocumentInbox`.

Dalsi krok:
- Otestovat cely pruchod na novem realnem dokumentu: scan/zpracovani -> kontrola PDF/metadat -> potvrzeny finalni import.

Navrhovane dalsi kroky:
- Okamzite: u noveho dokumentu pouzit `process_mobile_document_inbox`, potom `prepare_mobile_document_final_import`, zkontrolovat PDF a potvrdit nebo zmenit metadata.
- Potom: zavest `LIGHT` rezim jako jemne barevne vylepseni mezi RAW a BW, ale nepouzit ho jako default bez dalsich testu.
- Pozdeji: vytvorit iPhone zkratku pro hotove GPT PDF: vybrat PDF z Downloads, zadat nazev, ulozit do `SamanthaDocumentInbox`, vytvorit manifest a spustit request pro zpracovani.

Aktualizace po navazani 2026-05-27:
- Pricina spatne klasifikace byla falesna shoda `stk` uvnitr slova jako `kostky`.
- `STK` se nově bere jen jako samostatny token, ne jako libovolna cast slova.
- Pridany typy/domény `recipe` / `food` a `diet_guidance` / `health`.
- Realny reprocess `scan_D` i `scan_F` vratil `food / recipe`.
- Testovaci scany byly uklizeny: lokalni `data/private/documents/mobile_inbox/processing` ma jen `.DS_Store`, iCloud `SamanthaDocumentInbox` je prazdny.
- Finalni import byl dodelan vcetne `case_id`; test `tests.test_document_vault_tools` prosel cely s 34 testy.

Zmenene nebo relevantni soubory:
- `app/documents/vault.py`
- `app/documents/tools.py`
- `app/documents/__init__.py`
- `app/samantha_agent.py`
- `tests/test_document_vault_tools.py`
- `requirements.txt`
- `data/private/documents/mobile_inbox/processing/` (soukrome vystupy, necommitovat)

Bezpecnost / neukladat:
- Necommitovat obsah `data/private/`, fotky, PDF, OCR texty ani recepty/dokumenty.
- Do memory neukladat plne texty dokumentu, jen kratke technicke shrnuti.
- Zdrojove fotky v iCloud inboxu nemazat bez vyslovneho Milova souhlasu.
- Zaloha Samantha je k 2026-05-27 starsi nez 3 dny; jen pripominat, nic automaticky nekopirovat.
