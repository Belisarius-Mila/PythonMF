Nazev: Email Work Queue - davkove zpracovani, PDF prilohy a potvrzeny kos
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-01

Co se resilo:
- Navazani na Email Processing v Cockpitu a priprava skutecneho zpracovani e-mailu po triage.
- Mila upresnil cil: v Email Work Queue ma byt po kliknuti videt cele telo e-mailu, prilohy, volby ulozit/neukladat/kos a davkove zpracovani.
- Navazujici cil 2026-06-01: skutecne `Zpracovat davku`, ukladani e-mailu a PDF priloh, kos pres potvrzeni a fulltextova dohledatelnost.
- Matysek zmeny v repozitari resi jina session a tato prace je nema menit ani commitovat.

Co je hotove:
- Pridan read-only backend endpoint `/api/email-processing/read-message`.
- Endpoint umi podle `provider`, `folder` a `uid` nacist detail e-mailu z iCloud nebo Seznam provideru bez mazani, odesilani nebo stahovani priloh.
- Email Work Queue ma klikaci seznam, detail e-mailu, telo e-mailu, metadata priloh, checkboxy `Ulozit e-mail`, `Neukladat`, `Ulozit` u priloh a tlacitko `Kos`.
- Po otevreni Work Queue se hlavni okno Email Processing vyprazdni, aby se neslo zpracovavat stejny seznam dvakrat.
- `Obnovit nove` je v prazdnem okne vypnute a bez seznamu uz nespousti omylem nacitani starsich hlavicek.
- Pridano tlacitko `Nacti rozpracovane`, ktere vrati do hlavniho seznamu e-maily se statusem `Zpracovat` nebo `Kos`; 2026-06-01 vratilo 3 rozpracovane polozky `process`.
- Opraveno nezive popup okno Email Work Queue: seznam a detail se uz neplni vnitrnim skriptem popupu, ale primo z rodicovskeho okna pres `initializeWorkQueueWindow`.
- Explicitne otevreny e-mail ve Work Queue ma limit zvednuty z 2 MB na 25 MB, aby pojistne e-maily s PDF prilohami nepadaly na zavadejici hlasku `Zprava je prilis velka`. Hromadne skenovani zustava opatrne na 2 MB.
- Detail v otevrenem Work Queue okne se cachuje; opakovane kliknuti na stejny e-mail uz znovu nevola IMAP.
- Pri nacitani detailu je videt stav `Nacitam cely e-mail read-only`; u PDF je jasne napsano, ze to muze trvat.
- Tlacitko u priloh bylo prejmenovane z `Rozkliknout` na `Metadata`, protoze zatim neotevira soubor, jen ukazuje metadata a informaci, ze otevreni PDF prijde po potvrzenem ulozeni prilohy.
- Pridan backend endpoint `/api/email-processing/process-batch`.
- `Zpracovat davku` v popupu uz vola serverovy endpoint misto pouheho vycisteni fronty.
- Pro `Ulozit e-mail` se e-mail uklada do lokalniho `EmailArchiveVault` pres stavajici `save_email_archive`.
- Vybrane PDF prilohy se z puvodniho EML vytahnou podle `part_id` a pres `apply_document_import_file` se ulozi do private document vaultu, vcetne `documents_index.jsonl` a `text_index.jsonl`, tedy jsou fulltextove dohledatelne v dokumentovem hledani.
- Pro `Neukladat` se polozka uzavre bez provider callu a smaze se jen lokalni pracovni rozhodnuti.
- Pro `Kos` existuje presna potvrzovaci veta `Potvrzuji, přesuň e-mail UID ... do koše.`; server bez ni vraci `trash_pending`.
- iCloud i Seznam provider maji metodu `move_message_to_trash`; pouziva IMAP `MOVE`, pripadne fallback `COPY` do kose + `STORE \Deleted`, ale nepouziva `EXPUNGE`.
- Batch zapisuje audit do lokalniho ignorovaneho JSONL `data/private/email_session_handoffs/email_work_queue_actions.jsonl`.
- Testy `tests.test_cockpit`, `tests.test_email_archive_tools`, `tests.test_email_icloud_archive_provider`, `tests.test_seznam_provider`, `tests.test_payment_case_documents` a `tests.test_email_activity_state` pokryvaji read-only detail, rozpracovane polozky, popup UI, batch archivaci, PDF import, skip, potvrzovaci branu kose a provider parsovani.
- Lokalni Cockpit byl po upravach restartovan a bezi na `http://127.0.0.1:8770`.

Co neni hotove:
- Realny move-to-trash pres iCloud/Seznam je implementovany, ale jeste nebyl rucne otestovan na konkretni bezpecne vybrane zprave.
- PDF prilohy po ulozeni zatim nejdou primo otevrit z Work Queue; jsou ulozene ve vaultu a dohledatelne pres document search.
- Work Queue zatim nezobrazuje detailni vysledek ulozeni jednotlivych priloh v detail pane, jen stav fronty.
- Fulltext celeho tela ulozeneho e-mailu je v EmailArchiveVault souborech, ale dokumentove fulltextove hledani zatim prohledava hlavne ulozene PDF prilohy; sjednocene hledani e-mail archive + document vault je dalsi navazujici krok.

Dalsi krok:
- Rucne otestovat jednu malou davku v Cockpitu: jeden e-mail ulozit, jednu PDF prilohu ulozit, jednu polozku neukladat; potom overit hledani ve `Documenty` a lokalni `EmailArchiveVault`.

Navrhovane dalsi kroky:
- Okamzite: rucni realny test batch ulozeni bez mazani a overeni fulltextu PDF prilohy.
- Potom: rucni realny test presunu jedne zcela bezpecne zpravy do kose pres presnou potvrzovaci vetu; overit, ze neni trvale expungovana.
- Navazujici zlepseni: v detailu Work Queue zobrazit ulozene `archive_id`, `document_id` a odkaz/cestu k ulozene PDF priloze; sjednotit vyhledavani nad EmailArchiveVault a document vaultem.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/email/icloud_provider.py`
- `app/email/seznam_provider.py`
- `tests/test_cockpit.py`
- `tests/test_email_archive_tools.py`
- `tests/test_email_icloud_archive_provider.py`
- `tests/test_seznam_provider.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do handoffu nejsou ulozene zadne predmety realnych e-mailu, tela e-mailu, adresy, UID, tokeny ani hesla.
- Realna tela e-mailu zustavaji pouze lokalne v Cockpit UI po explicitnim kliknuti.
- Batch uklada plny e-mail a PDF prilohy jen do lokalnich soukromych slozek; tyto runtime soubory necommitovat.
- Kos vyzaduje presnou potvrzovaci vetu a kod nepouziva `EXPUNGE`.
- Soukrome runtime soubory v `data/private/` a `data/session_autosave/` necommitovat.
