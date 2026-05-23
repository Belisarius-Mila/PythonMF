Nazev: Document private vault - inbox cleanup a auditni dohledatelnost hotove
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-05-22

Co se resilo:
- Po prvnim realnem importu dokumentu do private vaultu zustala zdrojova kopie
  v `data/private/documents/inbox/incoming/`.
- Mila navrhl, ze po zpracovani ma Samantha nabidnout:
  `Dokument xy zpracovan, presunout do slozky processed? 1. presunout,
  2. smazat.`
- Pri volbe smazani musi nasledovat druha otazka:
  `Opravdu chcete dokument xy smazat z inboxu?`
- Resila se take dohledatelnost za rok: fyzicka zdrojova kopie v `processed`
  musi byt propojena s importovanym dokumentem ve vaultu pres index.

Co je hotove:
- Doplneny tooly `propose_document_inbox_cleanup` a
  `resolve_document_inbox_item`.
- Presun z `inbox/incoming/` do `inbox/processed/` je povoleny jen po potvrzeni.
- Mazani z inboxu vyzaduje druhe vyslovne potvrzeni s presnym nazvem souboru.
- Doplnen `data/private/documents/index/inbox_actions.jsonl` pro auditni stopu:
  akce, cas, `document_id`, nazev, SHA, puvodni cesta a cilova cesta.
- `search_private_documents` pri nalezu dokumentu ukazuje i `Zdrojova kopie`,
  pokud existuje auditni zaznam v `inbox_actions.jsonl`.
- Doplnen read-only tool `document_vault_status`: agregovane pocty dokumentu,
  oblasti, typy, inbox, processed, due date kandidati a auditni akce bez obsahu
  dokumentu.
- Status byl zpresnen: presun do `processed` se pocita jako vyreseni souboru z
  `inbox/incoming/`, ne jako trvale smazani. Auditni pocty jsou celkove v danem
  auditnim obdobi, ne od posledniho spusteni statusu; status ukazuje i pocet za
  poslednich 30 dni.
- Realna zdrojova kopie z prvniho tax importu byla po potvrzeni presunuta do
  `data/private/documents/inbox/processed/`.
- `data/private/documents/inbox/incoming/` je prazdny.
- Cileny test `tests.test_document_vault_tools` prosel: 19 testu OK.

Co neni hotove:
- Nic blokujiciho v dokumentovem projektu.
- Zmeny zatim nejsou git checkpointnute; pri budoucim commitu pridavat cilene,
  ne pres `git add .`.

Dalsi krok:
- Muzeme prejit na dalsi projekt.
- Pri dalsim dokumentu pouzit standardni workflow: scan inboxu, read-only preview,
  potvrzeny import, overeni vyhledavani, potom cleanup dotaz a auditni zapis.

Navrhovane dalsi kroky:
- Pridat read-only sumarizaci dokumentu podle `document_id`, ktera vrati jen
  bezpecna metadata, kratke snippety, due date kandidaty a cestu ke zdrojove
  kopii, bez celeho OCR textu.
- Dodelat workflow pro hromadny import vice dokumentu: nejdrive jen scan a
  navrh metadata pro vsechny, potom potvrzovat po jednom.
- Zlepsit klasifikaci oblasti/typu dokumentu pro dane, pojistky, faktury,
  zaruky a servisni protokoly podle dosavadnich realnych dokumentu.
- Zvážit samostatny `document_id` katalog/report pro danove priznani 2025, aby
  bylo jasne, ktere podklady uz jsou zalozene a ktere jeste chybi.
- Pred git checkpointem zkontrolovat, ze se necommitnou soukroma data z
  `data/private/documents/`; pridavat jen kod, testy a memory soubory cilene.

Zmenene nebo relevantni soubory:
- `app/documents/vault.py`
- `app/documents/tools.py`
- `app/documents/__init__.py`
- `app/samantha_agent.py`
- `tests/test_document_vault_tools.py`
- `memory/technical/private_document_vault_workflow.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/document_management_private_vault_tax_import_2026_05_22.md`
- `data/private/documents/index/inbox_actions.jsonl`
- `data/private/documents/inbox/processed/`

Bezpecnost / neukladat:
- Do memory neukladat rodne cislo, adresu, cele potvrzeni, cely OCR text ani
  presne citlive castky z dokumentu.
- `data/private/documents/` je soukromy obsah mimo git.
- Mazani dokumentu z inboxu vzdy vyzaduje druhou potvrzovaci otazku.
