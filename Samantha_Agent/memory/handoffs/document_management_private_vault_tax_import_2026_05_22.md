Nazev: Document private vault - prvni realny tax import
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-05-22

Co se resilo:
- Pri navazani pres Samanthu mel byt Milovi aktivne oznamen novy dokument v
  `data/private/documents/inbox/incoming/`.
- Read-only scan nasel jeden PDF soubor a po Milove potvrzeni byl importovan do
  private document vaultu.
- Overilo se, ze `search_private_documents` dokument najde podle dotazu k Centru
  83, prijmum, roku 2025 a oblasti `tax`.
- Pri overeni se nasla a opravila bezpecnostni mezera: snippety ve vyhledavani
  dokumentu redigovaly URL a e-mail, ale ne ceske rodne cislo.
- Do workflow bylo doplneno pravidlo, ze pri zapisu ma Codex Milovi pripravit
  presnou potvrzovaci vetu.

Co je hotove:
- Dokument je ulozeny v private vaultu jako oblast `tax`, typ
  `tax_income_confirmation`.
- `document_id`: `centrum-83-potvrzeni-prijmy-2025`.
- Manifest a index private vaultu vznikly v `data/private/documents/`.
- Vyhledavani dokumentu funguje a citlive identifikatory ve snippetu jsou
  redigovane.
- Cileny test `tests.test_document_vault_tools` prosel.

Co neni hotove:
- V ramci tohoto konkretniho dokumentu neni nic otevrene.
- Obecne zustava dalsi rozvoj dokumentoveho vaultu podle budoucich dokumentu.

Dalsi krok:
- Pri dalsim novem dokumentu pouzit stejne workflow: import do private vaultu,
  overeni vyhledavani a nasledne `propose_document_inbox_cleanup`.
- Pokud bude Mila pokracovat v danich, pouzit private vault read-only hledani a
  nevypisovat cele dokumenty ani citlive identifikatory.

Zmenene nebo relevantni soubory:
- `app/documents/vault.py`
- `tests/test_document_vault_tools.py`
- `memory/technical/private_document_vault_workflow.md`
- `data/private/documents/vault/tax/centrum-83-potvrzeni-prijmy-2025/`
- `data/private/documents/index/`
- `data/private/documents/inbox/processed/potvrzeni_scan_zarovnany.pdf`

Bezpecnost / neukladat:
- Neukladat do memory rodne cislo, adresu, cele potvrzeni, cely OCR text ani
  presne citlive castky z dokumentu.
- `data/private/documents/` je soukromy obsah mimo git.
- Soubor byl po potvrzeni presunut z `inbox/incoming/` do `inbox/processed/`.

Dodatek 2026-05-22 rano:
- Doplneny cleanup workflow podle Milova navrhu:
  `Dokument xy zpracovan, presunout do slozky processed? 1. presunout,
  2. smazat.`
- Volba 2 musi vzdy vest na druhou otazku:
  `Opravdu chcete dokument xy smazat z inboxu?`

Dodatek 2026-05-22 po potvrzeni:
- Mila zvolil ne mazani, ale ulozeni zdrojove kopie.
- Po potvrzeni vetou `Potvrzuji, presunout dokument ... do processed.` byl
  soubor presunut do `data/private/documents/inbox/processed/`.
- `data/private/documents/inbox/incoming/` je prazdny.

Dodatek 2026-05-22 k dohledatelnosti:
- Doplnil se auditni index `data/private/documents/index/inbox_actions.jsonl`.
- Presun do `processed` je zapsany s akci `move_to_processed`, `document_id`,
  SHA a puvodni/cilovou cestou.
- Diky tomu lze pozdeji propojit fyzickou zdrojovou kopii v `processed` s
  importovanym dokumentem ve vaultu.
- `search_private_documents` pri nalezu dokumentu ukazuje i `Zdrojova kopie`,
  pokud je k dokumentu zaznam v `inbox_actions.jsonl`.
