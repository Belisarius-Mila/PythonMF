Nazev: Document management - Cockpit command inbox a hlasove ovladani z iPhonu
Priorita: 1
Stav: ceka na implementaci
Pripomenout pri startu: ne
Datum: 2026-05-29

Co se resilo:
- Mila navrhl ovladat nektere funkce cockpitu hlasem z iPhonu pres presne definovanou zkratku.
- iPhone zkratka by po diktovani ulozila textovy/JSON prikaz do iCloud inboxu.
- Cockpit na Macu by periodicky kontroloval inbox, prikaz nacetl, bezpecne ho naroutoval a vysledek ukazal v panelu cockpitu.
- Priklady read-only prikazu: hledani dokumentu, hledani e-mailovych hlavicek, status e-mailove komunikace, status PDF ve Downloads, stav zalohy.

Co je hotove:
- Koncept potvrzen jako technicky proveditelny.
- Bezpecnostni hranice jsou vymezene:
  - read-only akce lze po zpracovani prikazu spoustet automaticky,
  - zapisujici/rizikove akce musi zustat potvrzovane v cockpitu.
- Navrzeny obecny tok:
  `iPhone Shortcut -> iCloud command inbox -> Cockpit poller -> intent router -> safe tool -> result panel`.

Co neni hotove:
- Neni implementovan command inbox.
- Neni implementovan intent router.
- Neni vytvorena iPhone zkratka pro diktovani a ulozeni prikazu.
- Neni napojene e-mailove read-only hledani do cockpitu.
- Neni definovan finalni JSON schema prikazu a stavove soubory `pending/processing/processed/failed`.

Dalsi krok:
- Implementovat textovy command inbox MVP bez iPhonu: rucne vlozeny JSON do lokalni/iCloud slozky, cockpit ho najde, spusti pouze povolenou read-only akci a vysledek ukaze v panelu.

Navrhovane dalsi kroky:
- Okamzite:
  - zalozit slozku typu `SamanthaCockpitInbox` mimo git,
  - definovat JSON schema prikazu,
  - v cockpitu pridat poller a panel `Prikazy z iPhonu`,
  - podporovat prvni intent `document_search`.
- Navazujici:
  - pridat read-only intent `email_search`,
  - pridat read-only intent `email_status`,
  - pridat `backup_status` a `downloads_status`,
  - az potom vyrobit iPhone Shortcut s diktovanim.
- Bezpecnost:
  - hlas nesmi sam mazat, archivovat, tisknout, odesilat e-mail/SMS ani menit metadata,
  - pro tyto akce smi jen pripravit navrh a cockpit musi vyzadovat kliknuti/potvrzeni.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `projects/document_management_private_vault.md`
- `technical/iphone_shortcuts_playground.md`
- `projects/email_readonly_oauth.md`

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, cele e-maily, cele dokumenty, SPZ/RZ, VIN, rodna cisla, adresy ani jine citlive osobni udaje do memory nebo gitu.
- iCloud inbox smi obsahovat jen kratky prikaz uzivatele; vysledky citlivych hledani zustavaji lokalne v cockpitu a private datech mimo git.
