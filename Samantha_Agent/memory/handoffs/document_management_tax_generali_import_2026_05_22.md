Nazev: Dokumentovy vault - Generali penzijni podklady pro tax
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-05-22

Co se resilo:
- Do dokumentoveho inboxu byly vlozeny ctyri PDF podklady z klientského portalu
  Generali penzijni spolecnosti.
- Cilem bylo ulozit je do private document vaultu v oblasti `tax`, po importu
  presunout zdrojove kopie do `inbox/processed/` a zkontrolovat statistiku.

Co je hotove:
- Vsechny 4 PDF byly po Milove potvrzeni importovany do
  `data/private/documents/vault/tax/`.
- Vsechny 4 zdrojove kopie byly po potvrzeni presunuty z
  `data/private/documents/inbox/incoming/` do `data/private/documents/inbox/processed/`.
- `inbox/incoming/` je po akci prazdny.
- Dokumenty jsou dohledatelne pres `search_private_documents`.
- Auditni stopa presunu je v `data/private/documents/index/inbox_actions.jsonl`.

Statistika po akci:
- Dokumentu v indexu celkem: 11.
- Oblast `tax`: 5 dokumentu.
- Oblast `insurance`: 6 dokumentu.
- Zdrojove kopie v `processed`: 5.
- Cekajici soubory v `incoming`: 0.
- Trvale smazano z inboxu: 0.
- Datumovych/due-date kandidatu celkem: 46.
- Kandidatu vhodnych na pripominku: 1.

Co neni hotove:
- Jedno PDF smlouvy nema dostupnou textovou vrstvu; je ulozene a indexovane
  metadata-only. Pokud bude potreba obsahove vyhledavani, dodat lepsi/OCR kopii.
- Z nalezenych datumovych kandidatu zatim nebyla ulozena zadna nova pripominka.

Dalsi krok:
- Pri danich pracovat s dokumenty ve vaultu pres `search_private_documents`.
- Pokud Mila bude chtit připominku z konkretniho due-date kandidata, ulozit ji
  az samostatnym potvrzenim.

Zmenene nebo relevantni soubory:
- `data/private/documents/vault/tax/` (soukrome, necommitovat)
- `data/private/documents/inbox/processed/` (soukrome, necommitovat)
- `data/private/documents/index/documents_index.jsonl` (soukrome, necommitovat)
- `data/private/documents/index/text_index.jsonl` (soukrome, necommitovat)
- `data/private/documents/index/due_dates.jsonl` (soukrome, necommitovat)
- `data/private/documents/index/inbox_actions.jsonl` (soukrome, necommitovat)
- `app/documents/vault.py` - potvrzovaci kontrola nově normalizuje Unicode a
  whitespace v nazvech souboru.
- `tests/test_document_vault_tools.py` - doplnen test pro zalomeny nazev s
  diakritikou.

Overeni:
- `scan_document_inbox_text`: incoming prazdny.
- `document_vault_status_text`: 11 dokumentu celkem, 5 v tax, 5 processed kopii.
- `search_private_documents_text('Generali penzijni tax 2025')`: nove tax
  dokumenty dohledatelne.
- `.venv/bin/python -m unittest tests.test_document_vault_tools`: OK.

Bezpecnost / neukladat:
- Neukladat do memory rodna cisla, cisla smluv, cele texty dokumentu, adresy,
  castky z dokumentu ani PDF obsah.
- `data/private/documents/` je soukrome uloziste mimo git.
