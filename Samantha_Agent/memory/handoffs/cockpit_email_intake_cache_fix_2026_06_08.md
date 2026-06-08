Nazev: Cockpit e-mail intake cache fix po T-Mobile zpracovani
Priorita: 1
Stav: hotovo / ceka na rucni UI retest
Pripomenout pri startu: ano
Datum: 2026-06-08

Co se resilo:
- V Dokumentovem intake se zobrazil e-mailovy kandidat T-Mobile vyuctovani.
- Mila jej zpracoval pres Email Processing.
- Backend ulozeni probehlo spravne, ale v hlavnim Cockpit okne kandidat zustal
  videt jako nezpracovany az do zavreni a znovuotevreni Cockpitu.

Co je hotove:
- Overeno lokalne bez provider zmen:
  - Seznam UID `155808` je ulozeny v `data/email/archive/`.
  - Telo e-mailu i original `.eml` jsou ulozene.
  - PDF `Vyuctovani_40580553_2606.pdf` je importovane do private document vaultu
    jako `doc-2026-06-08-other-email-attachment-pdf-vyuctovani_40580553_2606-e97259c3`.
- Opravena cache chyba v `Samantha_Agent/app/cockpit.py`:
  - backend `new_email_headers_overview` vraci `suppressed_known_ids`,
  - `document_intake_email_scan_status` tuto informaci propousti do odpovedi,
  - frontend `runEmailIntakeMonitor` posila aktualni kandidatni ID a odstrani
    z lokalni cache jen ty, ktere backend oznaci jako rozhodnute nebo zpracovane,
  - stale slucuje nove e-mailove kandidaty, aby se neztratil jiny dosud
    nezpracovany kandidat.
- Pridany regresni testy v `Samantha_Agent/tests/test_cockpit.py`.
- Testy prosly:
  - cileny vyber 4 testu,
  - `.venv/bin/python -m unittest tests.test_cockpit` -> 106 testu OK.
- Restartovan lokalni i Tailscale Cockpit:
  - `http://127.0.0.1:8770`
  - `http://100.89.150.6:8770`
- Smoke test po restartu:
  - `/api/status` odpovida,
  - `document_intake_count` byl 0,
  - read-only e-mail intake scan zobrazil 0 kandidatu.

Co neni hotove:
- Neni jeste udelany rucni UI retest pres realny prohlizec: zpracovat dalsi
  e-mailovy dokumentovy kandidat a overit, ze po navratu/refreshi z hlavniho
  Cockpitu zmizi bez rucniho zavirani celeho Cockpitu.
- Dne 2026-06-08 zustavaji v repu dalsi rozpracovane zmeny mimo tento bug:
  slovnikove/Pict zmeny a nove obrazky v `Pict/` a `PictNew/`.

Dalsi krok:
- Pokud bude cas, udelat rucni UI retest pri nejblizsim bezpecnem dokumentovem
  e-mail kandidatu.
- Commitovat Cockpit fix oddelene od slovnikovych/Pict zmen:
  - `Samantha_Agent/app/cockpit.py`
  - `Samantha_Agent/tests/test_cockpit.py`
  - tento handoff a pripadny index.

Navrhovane dalsi kroky:
- Okamzite:
  - udelat oddeleny git checkpoint jen pro Cockpit e-mail intake fix.
- Potom:
  - samostatne se vratit ke slovnikovym/Pict zmenam, zkontrolovat review
    `PictNew/generated/20260608_itfr_replacement_batch001/review.html`,
    rozhodnout, co patri do commitu, a nemichat to s Cockpit opravou.

Zmenene nebo relevantni soubory:
- `Samantha_Agent/app/cockpit.py`
- `Samantha_Agent/tests/test_cockpit.py`
- `Samantha_Agent/memory/handoffs/cockpit_email_intake_cache_fix_2026_06_08.md`
- `data/private/email_session_handoffs/email_work_queue_actions.jsonl`
- `data/email/archive/email-155808-vyuctovani-sluzeb-od-t-mobile-za-obdobi-6-5-2026-5-6-2026-fakturacni-skupina-40580553/`
- `data/private/documents/` private vault

Bezpecnost / neukladat:
- Neukladat do memory plne e-mailove adresy, cela tela e-mailu, prilohy,
  cele PDF ani soukrome dokumenty.
- `data/private/`, `data/email/archive/`, `data/email/outbox_drafts/` a provider
  konfigurace zustavaji lokalni a necommituji se.
- Pri git checkpointu nepouzit `git add .`; pridat jen explicitni soubory
  souvisejici s Cockpit fixem.
