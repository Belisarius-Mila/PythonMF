Nazev: Document vault / e-mailove prilohy / ScanDocu checkpoint
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-16

Co se resilo:
- Dokonceni dnesni vlny prace kolem Document Vaultu, Email Work Queue a ScanDocu Review.
- Prakticky problem: nektere e-mailove prilohy nebyly jen PDF, ale i obrazky/JPEG, a potrebovaly jit ulozit do private document vaultu.
- Prakticky problem: dokument vraceny rucne zpet do stavu `needs_review` se nemel ve ScanDocu Review ztratit kvuli drivejsimu auditnimu zaznamu `reviewed`.
- Prakticky problem: oblast `petkovy-65` byla vecne spatne a mela byt sjednocena na `petkovy-56`.

Co je hotove:
- Email Work Queue umi vybrane podporovane prilohy uklada jako PDF i obrazky.
- Nahled prilohy v e-mailove fronte podporuje PDF i obrazkove prilohy a umi dohledat prilohu i podle nazvu, kdyz se lisi technicke `part_id`.
- Obrazkove prilohy ve vaultu dostanou text extraction stav `image-no-text`, OCR zustava dalsi faze.
- ScanDocu Review zohlednuje manualni zmenu reading statusu: `needs_review` dokument znovu otevre, `ok` / `unreadable` / `superseded` ho bere jako uzavreny.
- V private datech byla aktivni oblast `petkovy-65` prejmenovana na `petkovy-56` v registru oblasti, aktivnich dokumentech, indexech a ulozenych cestach.
- Aktivni klasifikace dokumentu po opravach hlasi `167/167` kompletni metadata.

Co neni hotove:
- OCR pro obrazkove prilohy neni implementovane; obrazky jsou ulozene, ale bez fulltextove textove vrstvy.
- Historicke zalohy a auditni logy se zamerne neprepisovaly; mohou obsahovat stare oznaceni `petkovy-65`.
- Restart Cockpitu pres stary restart worker neumi restartovat `cockpit_launchd_runner.py`; aktualni API ale vraci nova data a v UI staci obnovit stranku.

Dalsi krok:
- Pri dalsi realne praci v Cockpitu otestovat jeden e-mail s kombinaci PDF + JPEG priloh a overit, ze se vse ulozi do vaultu a v ScanDocu Review se daji metadata doplnit bez zaseknuti fronty.

Navrhovane dalsi kroky:
- Kratkodobe: pokud se znovu objevi obrazkova priloha bez textu, ulozit ji a metadata doplnit rucne.
- Navazujici: navrhnout OCR workflow pro JPEG/PNG prilohy jako samostatny potvrzovany krok.
- Technicky: rozsirit bezpecny restart Cockpitu tak, aby rozpoznal i launchd runner a restartoval child server nebo supervisor kontrolovane.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/documents/scandocu.py`
- `app/documents/vault.py`
- `app/email/icloud_provider.py`
- `app/email/seznam_provider.py`
- `tests/test_cockpit.py`
- `tests/test_document_vault_tools.py`
- `data/private/documents/` mimo git: upravena metadata a registr oblasti `petkovy-56`

Bezpecnost / neukladat:
- Do gitu nepatri `data/private/`, PDF, obrazkove prilohy, plne texty dokumentu, e-maily, adresy, variabilni symboly ani jina soukroma data.
- Handoff je zamerne redigovany a neobsahuje obsah dokumentu ani plne osobni udaje.
