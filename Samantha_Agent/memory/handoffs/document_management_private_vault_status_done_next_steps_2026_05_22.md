Nazev: Document private vault - status hotovy a navrzene dalsi kroky
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-05-22

Co se resilo:
- Po prvnim realnem importu dokumentu do private vaultu se dotahoval konec
  workflow: co se stane se souborem v inboxu, jak se dohleda pozdeji a jak ma
  Samantha citelne vysvetlovat stav dokumentoveho trezoru.
- Mila upresnil, ze "presunout do processed" musi znamenat, ze soubor zmizi z
  `inbox/incoming/`; kdyby zustal i tam, bylo by to kopirovani.
- Resilo se take, ze agregovane pocty ve statusu musi rikat, od kdy jsou
  pocitane, jinak casem ztrati vypovidaci hodnotu.

Co je hotove:
- Zdrojovy soubor z prvniho realneho importu byl po potvrzeni presunut z
  `inbox/incoming/` do `inbox/processed/`; `inbox/incoming/` je prazdny.
- Presun do `processed` se auditne zapisuje do
  `data/private/documents/index/inbox_actions.jsonl` vcetne `document_id`,
  nazvu souboru, puvodni/cilove cesty a SHA otisku.
- `search_private_documents` umi u nalezeneho dokumentu ukazat zdrojovou kopii,
  pokud existuje auditni stopa.
- `document_vault_status` je read-only status bez obsahu dokumentu. Ukazuje:
  aktualni pocet souboru v incoming, pocet zdrojovych kopii v processed,
  auditni obdobi, akce za poslednich 30 dni, presuny do processed, trvala
  smazani po druhem potvrzeni, pocty podle oblasti a typu dokumentu.
- Terminologie statusu byla zpresnena: presun do `processed` je "vyreseni
  souboru z incoming", ne "trvale smazani". Trvale smazani je jen samostatna
  akce po druhem potvrzeni.
- Cileny test `tests.test_document_vault_tools` prosel: 19 testu OK.

Co neni hotove:
- Neni hotovy detailni read-only report jednoho dokumentu podle `document_id`.
- Neni hotovy hromadny import vice dokumentu z inboxu.
- Neni hotovy katalog podkladu pro danove priznani 2025.
- Zmeny zatim nejsou git checkpointnute; pri commitu pridavat jen kod, testy a
  memory soubory, nikdy `data/private/documents/`.

Dalsi krok:
- Projekt dokumentu je v tuto chvili ulozeny a muze se odlozit.
- Pri dalsim novem dokumentu pouzit standardni postup: scan inboxu, read-only
  preview, potvrzeny import, overeni vyhledavani, cleanup dotaz, auditni zapis
  a kontrolni `document_vault_status`.

Navrhovane dalsi kroky:
- Pridat read-only sumarizaci podle `document_id`: metadata, bezpecne kratke
  snippety, due-date kandidaty, zdrojovou kopii a auditni stopu, bez celeho OCR.
- Dodelat hromadny import vice dokumentu: nejdrive navrh metadat pro vsechny,
  potom potvrzovat import a cleanup po jednom.
- Zlepsit klasifikaci typu dokumentu pro dane, pojistky, faktury, zaruky,
  servisni protokoly a zdravotni/rodinne dokumenty.
- Udelat katalog/report pro danove priznani 2025: ktere podklady uz ve vaultu
  jsou, ktere chybi a ktere maji datumove kandidaty k pripomenuti.
- Pred git checkpointem zkontrolovat `git status` a pridat cilene jen
  bezpecne soubory; soukroma data v `data/private/` zustavaji mimo git.

Zmenene nebo relevantni soubory:
- `app/documents/vault.py`
- `app/documents/tools.py`
- `app/documents/__init__.py`
- `app/samantha_agent.py`
- `tests/test_document_vault_tools.py`
- `memory/technical/private_document_vault_workflow.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/document_management_private_vault_cleanup_done_2026_05_22.md`
- `data/private/documents/index/inbox_actions.jsonl`
- `data/private/documents/inbox/processed/`

Bezpecnost / neukladat:
- Do memory neukladat rodna cisla, adresy, cele OCR texty, cele dokumenty ani
  presne citlive castky z dokumentu.
- `data/private/documents/` je soukromy obsah mimo git.
- Mazani dokumentu z inboxu vyzaduje druhou potvrzovaci otazku.
