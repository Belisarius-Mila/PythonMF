Nazev: Dokumentovy vault - navazani po tisku a intake ze Stazenych
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-05-22

Co se resilo:
- Dokumentovy vault ma hotovy dvoukrokovy tiskovy workflow:
  `prepare_document_print_job` a `run_document_print_job`.
- Realny test penzijni smlouvy prosel az po predani do macOS tiskove fronty:
  tiskovy prikaz uspel, pracovni kopie z `print_queue` byla smazana a original
  zustal ve vaultu.
- Puvodne zustalo otevrene fyzicke overeni tisku, protoze Codex umi potvrdit jen
  predani do macOS tiskove fronty.
- Mila dodatecne potvrdil, ze fyzicky tisk uz byl vyzkouseny na TXT dokumentu o
  zkratkach a vysledek je ulozeny.
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
- Fyzicky tisk papiru byl Milou overen na TXT dokumentu o zkratkach; startovni
  pripominka k overeni tisku uz neni potreba.

Co neni hotove:
- Neni implementovany tool pro read-only vyhledani dokumentu ve Stazenych.
- Neni implementovany potvrzeny presun dokumentu ze Stazenych do
  `data/private/documents/inbox/incoming/`.
- Neni implementovana detailni kontrola tiskove fronty po odeslani dokumentu.
- Neni implementovany vztahovy prehled dokumentu podle case/asset/protistrany.

Dalsi krok:
1. Pokracovat v navrhu klasifikace/vazeb dokumentu:
   - pouzivat `case_id` nebo podobny vztahovy klic pro dokumenty, ktere patri k
     jednomu pripadu napric typy,
   - zachovat `domain`, `document_type`, `counterparty`, `related_asset` a `tags`
     jako samostatne osy klasifikace,
   - doplnit read-only prehled skupin podle souvislosti.
2. Implementovat downloads intake workflow:
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
