Nazev: Dokumentovy vault - navazani po tisku a intake ze Stazenych
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-22

Co se resilo:
- Dokumentovy vault ma hotovy dvoukrokovy tiskovy workflow:
  `prepare_document_print_job` a `run_document_print_job`.
- Realny test penzijni smlouvy prosel az po predani do macOS tiskove fronty:
  tiskovy prikaz uspel, pracovni kopie z `print_queue` byla smazana a original
  zustal ve vaultu.
- Codex ale neumi fyzicky overit, ze papir skutecne vyjel z tiskarny.
- Mila chce pri dalsim vstupu do projektu dokumenty povinne fyzicky overit tisk.
- Mila navrhl dalsi vstupni variantu: misto rucniho vkladani do inboxu rict, ze
  dokument je ve slozce Stazene/Downloads; Samantha ho najde, ukaze nazev a cas
  ulozeni/zmeny a az po potvrzeni ho presune do inboxu.

Co je hotove:
- Tiskovy workflow je implementovany a testovany:
  - priprava kopie do `data/private/documents/print_queue/`,
  - potvrzeny tisk pres macOS `lp`,
  - automaticke smazani jen pracovni kopie po uspesnem predani tisku,
  - ponechani kopie pri chybe tisku,
  - audit v `data/private/documents/index/print_jobs.jsonl`.
- Memory workflow doplneno o pravidlo, ze intake ze Stazenych/Downloads ma byt
  dvoukrokovy a potvrzovany.

Povinny ukol pri pristim navazani v projektu dokumenty:
- Napsat Milovi presne:
  `Domluvili jsme se, že pro další vývoj projektu je nutné fyzicky ověřit tisk alespoň jednoho dokumentu. Jestli souhlasíš napiš: Ok.`

Co neni hotove:
- Neni implementovany tool pro read-only vyhledani dokumentu ve Stazenych.
- Neni implementovany potvrzeny presun dokumentu ze Stazenych do
  `data/private/documents/inbox/incoming/`.
- Neni implementovana detailni kontrola tiskove fronty po odeslani dokumentu.

Dalsi krok:
1. Pri jakemkoli dalsim vstupu do projektu dokumenty nejdriv napsat Milovi
   presnou vetu:
   `Domluvili jsme se, že pro další vývoj projektu je nutné fyzicky ověřit tisk alespoň jednoho dokumentu. Jestli souhlasíš napiš: Ok.`
2. Potom implementovat downloads intake workflow:
   - `prepare_document_inbox_from_downloads` jako read-only vyhledani kandidatu,
   - `move_document_from_downloads_to_inbox` jako potvrzeny presun do inboxu,
   - auditni zaznam intake akce,
   - testy na nejednoznacny vyber, potvrzeni a zakaz prace mimo Downloads/inbox.

Navrhovane potvrzovaci vety:
- Pro presun ze Stazenych do inboxu:
  `Potvrzuji, presunout dokument <nazev_souboru> ze Stazenych do document inboxu.`
- Pro dalsi import po presunu do inboxu:
  `Potvrzuji, uloz dokument <nazev_souboru> do oblasti <oblast>.`

Zmenene nebo relevantni soubory:
- `app/documents/vault.py`
- `app/documents/tools.py`
- `app/documents/__init__.py`
- `app/samantha_agent.py`
- `tests/test_document_vault_tools.py`
- `memory/technical/private_document_vault_workflow.md`
- `memory/projects/document_management_private_vault.md`

Bezpecnost / neukladat:
- Neukladat do memory obsah dokumentu, rodna cisla, cisla smluv, adresy ani plne
  citlive texty.
- Ze slozky Stazene/Downloads nic nepresouvat bez potvrzeni.
- Pri tisku nikdy nemazat original ve vaultu; mazat smi jen pracovni kopie v
  `print_queue` po uspesnem predani tisku systemu.
