Nazev: Email Processing v Cockpitu - koš, trvalé mazání, deduplikace a navázání na dokumenty
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-06-03

Co se resilo:
- Dokonceni praktickeho workflow pro `Email Processing` a `Email Work Queue` v Samantha Cockpitu.
- Mila realne zpracovaval davky e-mailu a narazil na tri provozni problemy:
  - e-maily oznacene jako kos se po presunu do Work Queue znovu potvrzovaly jednotlive,
  - hromadne tlacitko pro smazani melo neergonomicke textove potvrzeni,
  - nektere uz zpracovane e-maily se znovu vracely pri nacteni dalsi davky.
- Vedle toho se overovalo zpracovani PDF priloh do dokumentoveho vaultu a odemykani drive zamcenych PDF.
- Na konci Mila potvrdil, ze e-maily uz funguji uspokojive a priste se ma pokracovat obecnym zpracovanim dokumentu.

Co je hotove:
- `Email Work Queue` ma oddelene kroky:
  - `Zpracovat dávku` pro ukladani/ignorovani,
  - `Emaily určené ke smazání smazat` pro presun oznacenych e-mailu do kose,
  - `Trvale smazat e-maily v koši` pro samostatny nevratny IMAP EXPUNGE krok.
- Presun do kose uz nevyzaduje po Mile potvrzovat kazdy e-mail jednotlive.
- Trvale smazani je na tlacitko a standardni potvrzovaci dialog, bez opisovani potvrzovaci fraze.
- iCloud i Seznam provider po presunu do kose vraci metadata pro navazujici trvale smazani:
  - `trash_folder`,
  - `trash_uid`,
  - `message_id`.
- iCloud i Seznam provider maji metodu pro trvale smazani zpravy z kose s fallbackem pres `Message-ID`.
- Seznam trash kandidati doplneni o lowercase `trash`, protoze realna slozka takto existovala.
- `Email Processing` pri nacitani novych hlavicek filtruje nejen aktualni rozhodnuti, ale i historicky dokoncene Work Queue polozky z action logu:
  - `saved`,
  - `skipped`,
  - `trashed`,
  - `purged`.
- Po oprave nacitani poslednich 10 dni:
  - puvodne se vracelo 59 hlavicek,
  - po filtrovani se vratilo 50,
  - `skipped_completed_count` bylo 16,
  - konkretni drive zpracovane UID se uz nevracely.
- Odemcene PDF kopie z Downloads byly vymeneny za zamcene aktivni varianty ve vaultu a znovu fulltextove indexovane.
- Aktivni kontrola uz nenasla zadne aktivni `pdf-encrypted`; zustava jen jeden zero-text PDF pripad bez textove vrstvy/OCR.
- Booking/Ville Verdi komunikace byla dohledana, shrnuta a odeslana Janicce jako informacni e-mail; handoff neuklada cele e-maily ani PINy.
- Cockpit byl po upravach restartovan na `http://127.0.0.1:8770`.

Co neni hotove:
- Historicke e-maily zpracovane jinymi workflow nez `Email Work Queue` se zatim filtrujou jen tehdy, pokud maji stopu v action logu nebo rozhodnutich.
- Obecne dokumentove zpracovani je dalsi samostatna etapa.
- Trvale mazani z kose je implementovane opatrne, ale dalsi realne pouzivani ma pokracovat po malych davkach a s kontrolou vysledku.
- Zaloha Samanthy je stale starsi nez 3 dny: posledni uspesna zaloha byla 2026-05-29.

Dalsi krok:
- Pri dalsim navazani otevrit dokumentovy cockpit / dokumentove zpracovani a zamerit se na obecny workflow dokumentu:
  - prehled fronty dokumentu,
  - klasifikace,
  - fulltext/OCR,
  - vazby mezi dokumenty,
  - ergonomie ulozeni, archivace a revize.

Navrhovane dalsi kroky:
- Okamzity krok: zacit dokumentovou etapou, ne dalsim ladnim e-mailu, pokud Mila neprinese novy konkretni e-mailovy problem.
- Prakticky dokumentovy start:
  - zkontrolovat aktualni document vault dashboard,
  - najit zero-text/OCR pripady,
  - navrhnout jednotny postup pro nove dokumenty z Downloads, e-mailu a mobilniho skenu,
  - oddelit bezpecne read-only kroky od potvrzovanych akci.
- Volitelne e-mailove doladeni:
  - rozsirit filtr historicky zpracovanych e-mailu i na dalsi archivni zdroje mimo Work Queue,
  - pridat report poslednich e-mailovych akci bez otevirani schranky,
  - po vetsi realne davce dodelat audit, jestli `purged` polozky korektne mizi i z UI.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/email/icloud_provider.py`
- `app/email/seznam_provider.py`
- `tests/test_cockpit.py`
- `tests/test_seznam_provider.py`
- `data/private/documents/vault/` - soukrome PDF vystupy a indexy mimo git
- `data/private/email_session_handoffs/` - soukrome e-mailove mezistavy mimo git

Overeni:
- `.venv/bin/python -m py_compile app/cockpit.py`
- `.venv/bin/python -m unittest tests.test_cockpit`
- Targeted test drive pred posledni upravou probehl uspesne pro relevantni e-mailove testy.
- Plny test suite mel drive jeden nesouvisejici znamy fail v `test_email_triage_service` kvuli priorite NIBE.
- Live read-only overeni nacitani hlavicek poslednich 10 dni po restartu Cockpitu proslo a uz vynechalo drive zpracovane Work Queue polozky.

Bezpecnost / neukladat:
- Do pameti ani gitu neukladat cele e-maily, PINy, booking odkazy, app-specific passwords, tokeny ani cele soukrome dokumenty.
- `data/private/` a `data/session_autosave/` nikdy necommitovat.
- Mazani e-mailu zustava citliva akce:
  - presun do kose je samostatny krok,
  - trvale smazani z kose je samostatny nevratny krok,
  - pri nejistote nejdrive maly test a kontrola vysledku.
