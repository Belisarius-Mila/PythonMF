Nazev: Email Work Queue - zitrejsi navazani na realny batch test
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-01

Co se resilo:
- Dokonceni prvni ostre implementace `Zpracovat davku` v Email Work Queue.
- Cil: davkove ulozeni e-mailu, ulozeni vybranych PDF priloh, kos pres potvrzeni a fulltextova dohledatelnost.

Co je hotove:
- Cockpit endpoint `/api/email-processing/process-batch` existuje a je napojen na popup `Email Work Queue`.
- `Ulozit e-mail` uklada zpravu do lokalniho `EmailArchiveVault`.
- Vybrane PDF prilohy se vytahnou z EML podle `part_id` a importuji se pres `apply_document_import_file` do private document vaultu vcetne `documents_index.jsonl` a `text_index.jsonl`.
- `Neukladat` uzavre polozku bez provider callu.
- `Kos` vyzaduje presnou potvrzovaci vetu `Potvrzuji, přesuň e-mail UID ... do koše.`
- iCloud i Seznam provider maji `move_message_to_trash`; kod pouziva IMAP `MOVE`, pripadne fallback `COPY` + `STORE \Deleted`, ale nepouziva `EXPUNGE`.
- Batch zapisuje lokalni audit do `data/private/email_session_handoffs/email_work_queue_actions.jsonl`.
- Cockpit byl restartovan a bezi na `http://127.0.0.1:8770`.
- Overeni: `py_compile` proslo; relevantni unittest sada prosla (`tests.test_cockpit`, `tests.test_email_icloud_archive_provider`, `tests.test_seznam_provider`, `tests.test_email_archive_tools`).

Co neni hotove:
- Nebyl jeste proveden rucni realny test na skutecnych e-mailech.
- Nebyl jeste proveden rucni realny test presunu jedne bezpecne zpravy do kose.
- Work Queue zatim v detailu nezobrazuje po davce klikaci vystup `archive_id` / `document_id`.
- Sjednocene hledani pres EmailArchiveVault + document vault zatim neni hotove; document fulltext pokryva hlavne ulozene PDF prilohy.

Dalsi krok:
- Zitra udelat maly realny test bez mazani: v Cockpitu nacist rozpracovane nebo nove e-maily, otevrit Work Queue, jeden e-mail ulozit, jednu PDF prilohu ulozit, jednu polozku dat `Neukladat`, spustit `Zpracovat davku` a overit document fulltext.

Navrhovane dalsi kroky:
- Okamzite: realny batch test bez kose.
- Potom: opatrny test jedne zcela bezpecne zpravy do kose pres presnou potvrzovaci vetu.
- Navazujici zlepseni: zobrazit vysledky batch ulozeni primo ve Work Queue a pridat sjednocene hledani nad EmailArchiveVault i document vaultem.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/email/icloud_provider.py`
- `app/email/seznam_provider.py`
- `tests/test_cockpit.py`
- `memory/handoffs/email_work_queue_detail_checkpoint_2026_06_01.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do handoffu nejsou ulozene zadne predmety realnych e-mailu, tela e-mailu, adresy, UID konkretni realne zpravy, tokeny ani hesla.
- Runtime data v `data/private/`, `data/email/` a `data/session_autosave/` necommitovat.
- Kos nepouziva `EXPUNGE`; test kose delat az na jasne bezpecne zprave.
