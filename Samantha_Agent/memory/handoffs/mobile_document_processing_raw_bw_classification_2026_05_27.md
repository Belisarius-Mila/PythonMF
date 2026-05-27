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
- Po Milove redefinici se hlavni workflow zjednodusilo na cestu C:
  - Mila nafoti dokument a v GPT z nej udela PDF;
  - PDF se stahne do Downloads;
  - ScanDocu vezme nejmladsi nezpracovane PDF z Downloads, vytvori pracovni kopii, udela OCR/navrh metadat a zobrazi lokalni webovou kontrolu;
  - klik `Ulozit` ve ScanDocu je potvrzenim finalniho ulozeni do vaultu.
- Procesor ScanDocu je implementovany v `app/documents/scandocu.py`, spousteci skript je `scripts/scandocu_server.py`.
- Testy po posledni zmene prosly:
  - `test_normalize_mobile_document_page_crops_borders`
  - `test_normalize_mobile_document_page_raw_profile_preserves_geometry`
  - `test_prepare_mobile_document_batch_creates_working_pdf_without_deleting_source`
  - `test_process_mobile_document_inbox_creates_pdf_analysis_and_marks_request`
- `py_compile` proslo pro `app/documents/vault.py` a `tests/test_document_vault_tools.py`.

Co neni hotove:
- Neni hotova zkratka pro spusteni ScanDocu z iPhonu/Macu.
- Stara mobilni scan cesta je ponechana jako zaloha, ale uz neni hlavni workflow.

Dalsi krok:
- Otestovat ScanDocu na novem realnem GPT PDF v Downloads.

Navrhovane dalsi kroky:
- Okamzite: vlozit nove GPT PDF do Downloads, otevrit `http://127.0.0.1:8766`, zkontrolovat PDF/metadata a potvrdit ulozeni.
- Potom: vytvorit zkratku, ktera spusti ScanDocu nebo vytvori jednoduchy request pro Samanthu; uz nema fotit ani skladat PDF.
- Pozdeji: rozhodnout, jestli po importu PDF z Downloads automaticky oznacovat jako zpracovane, presouvat, nebo nechavat beze zmeny.

Aktualizace po navazani 2026-05-27:
- Pricina spatne klasifikace byla falesna shoda `stk` uvnitr slova jako `kostky`.
- `STK` se nově bere jen jako samostatny token, ne jako libovolna cast slova.
- Pridany typy/domény `recipe` / `food` a `diet_guidance` / `health`.
- Realny reprocess `scan_D` i `scan_F` vratil `food / recipe`.
- Testovaci scany byly uklizeny: lokalni `data/private/documents/mobile_inbox/processing` ma jen `.DS_Store`, iCloud `SamanthaDocumentInbox` je prazdny.
- Finalni import byl dodelan vcetne `case_id`; test `tests.test_document_vault_tools` prosel cely s 34 testy.
- ScanDocu procesor byl dodelan:
  - `scan_downloaded_pdfs` vypise PDF v Downloads a jejich stav;
  - `prepare_next_scandocu_document` vytvori pracovni kopii nejmladsiho noveho PDF;
  - `scripts/scandocu_server.py` poskytuje lokalni web s nahledem PDF a editaci metadat;
  - test `tests.test_document_vault_tools` prosel cely s 35 testy.
- Opravena dalsi falesna klasifikace `car`: kratke markery `auto`, `VIN`, `SPZ` se uz berou jen jako samostatne tokeny. Duvod: slova typu `automaticky` nebo `vitamin` nemaji dokument radit mezi auta. ScanDocu kandidati byli prepocitani a `Lekarna_v_Neuberku_pro_Janicku.pdf` uz vraci `other / document`; testy prosly s 36 testy.
- Do ScanDocu byla doplnena pravdepodobnostni kontrola duplicit: pokud nove PDF vypada podle nazvu/metadat jako uz ulozeny dokument, UI ukaze pravdepodobnou shodu vcetne nazvu/adresare a bez zaskrtnuti `Presto ulozit jako dalsi dokument` import odmitne. Prvni verze byla moc volna a hlasila nesouvisejici smlouvy; aktualni verze je zprisnena na rozlisovaci termy z nazvu/metadat, aby se minimalizovaly falesne poplachy. Realna kontrola aktualni najemni smlouvy nenasla v ulozenych metadatech jasnou shodu a ScanDocu ted nehlasi duplicitu. Testy prosly s 37 testy.
- Na Milovu zadost byly smazany ulozene testovaci dokumenty: finalni vault dokument `test-scandocu` byl odstranen vcetne indexoveho textu/due-date radku a byla vycistena pracovni ScanDocu cache `data/private/documents/scandocu/processing`. Realne dokumenty se slovem `scan` v nazvu, zejmena danovy scan, nebyly mazany. ScanDocu server po uklidu znovu bezi na `http://127.0.0.1:8766`; aktualne je na rade realna najemni smlouva bez pravdepodobne duplicity.
- Pri testu realne najemni smlouvy se potvrdilo, ze problem byl v klasifikaci a tagach: dokument padal do `other / contract` a do tagu se pridavaly roky. Byla doplnena detekce najemni smlouvy jako `home / lease`, tagy `najem` a `bydleni`, odstraneno automaticke tagovani let a zprisneno cteni protistrany tak, aby se nebraly nadpisy typu `Prava najemce`. Aktualni navrh ve ScanDocu spravne vyplnuje domenu, typ a najemni tagy; protistranu lze doplnit rucne, pokud ji parser nevyplni. Testy prosly s 38 testy.
- Parser najemnich smluv byl dale zlepsen pro blokovy format stran: umi vytahnout osoby uvedene v radcich `Titul, jmeno a prijmeni` pred markerem `jako najemce`, ale zacina az za blokem `jako pronajimatel`, aby nevzal pronajimatele jako protistranu. `related_asset` se bere z OCR nebo konzervativne z nazvu souboru. Aktualni realny navrh ve ScanDocu spravne vyplnil oblast `home`, typ `lease`, protistranu, souvisejici vec a najemni tagy; duplicity 0. Testy prosly s 39 testy.
- Byla vytvorena macOS zkratka `Spustit ScanDocu.shortcut` v `/Users/miloslavfalta/Documents/Shortcuts Playground/`. Zkratka vola projektovy skript `scripts/start_scandocu.sh`, ktery spusti nebo otevře lokalni ScanDocu na `http://127.0.0.1:8766`. XML validace prosla a podepsany `.shortcut` ma nenulovou velikost. Dalsi krok: Mila musi zkratku importovat do aplikace Zkratky dvojklikem ve Finderu a rucne otestovat.
- Po rozhodnuti, ze macOS zkratka neprinasi dostatecne zjednoduseni, byl vytvoren prvni prototyp `Samantha Cockpit`: `app/cockpit.py`, `scripts/cockpit_server.py` a `scripts/start_cockpit.sh`. Cockpit bezi lokalne na `http://127.0.0.1:8770`, ukazuje PDF ve Downloads, stav ScanDocu, stav zalohy a agregovany document-vault status; umi spustit/otevrit ScanDocu a otevrit Terminal v projektu. Prototyp zatim nedela rizikove akce typu mazani nebo finalni import bez ScanDocu potvrzeni.
- Vecerni checkpoint 2026-05-28: Mila potvrdil, ze prototyp cockpitu bezi a vypada dobre. Byl opraven problem, kdy zavreni ScanDocu zaviralo i cockpit: `app/cockpit.py` uz servíruje HTML/JSON s `Cache-Control: no-store` a tlacitko ScanDocu okamzite otevre samostatne okno `SamanthaScanDocu`, do ktereho se po startu nacte `http://127.0.0.1:8766`. Mila potvrdil, ze oprava funguje. Rano navazat testem dalsiho dokumentu pres cockpit/ScanDocu.

Zmenene nebo relevantni soubory:
- `app/documents/vault.py`
- `app/documents/scandocu.py`
- `app/documents/tools.py`
- `app/documents/__init__.py`
- `app/samantha_agent.py`
- `scripts/scandocu_server.py`
- `app/cockpit.py`
- `scripts/cockpit_server.py`
- `scripts/start_cockpit.sh`
- `tests/test_document_vault_tools.py`
- `requirements.txt`
- `data/private/documents/mobile_inbox/processing/` (soukrome vystupy, necommitovat)

Bezpecnost / neukladat:
- Necommitovat obsah `data/private/`, fotky, PDF, OCR texty ani recepty/dokumenty.
- Do memory neukladat plne texty dokumentu, jen kratke technicke shrnuti.
- Zdrojove fotky v iCloud inboxu nemazat bez vyslovneho Milova souhlasu.
- Zaloha Samantha je k 2026-05-27 starsi nez 3 dny; jen pripominat, nic automaticky nekopirovat.
