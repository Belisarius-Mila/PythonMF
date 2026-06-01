Nazev: Email Work Queue - detail e-mailu a prvni zpracovatelske UI
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-01

Co se resilo:
- Navazani na Email Processing v Cockpitu a priprava skutecneho zpracovani e-mailu po triage.
- Mila upresnil cil: v Email Work Queue ma byt po kliknuti videt cele telo e-mailu, prilohy, volby ulozit/neukladat/kos a davkove zpracovani.
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
- Testy `tests.test_cockpit` a `tests.test_seznam_provider` pokryvaji read-only detail, rozpracovane polozky, popup UI, cache/loading texty a vetsi explicitni limit zpravy.
- Lokalni Cockpit byl po upravach restartovan a bezi na `http://127.0.0.1:8770`.

Co neni hotove:
- Tlacitko `Zpracovat davku` zatim jen vycisti pracovni frontu v popupu; jeste nearchivuje e-mail, neuklada PDF a fyzicky nemaze.
- Fyzicke smazani e-mailu zatim neni implementovane. Musi byt samostatne potvrzovane a otestovane.
- Ukladani vybranych priloh do document vaultu/inboxu zatim neni implementovane. Aktualni archivacni vrstva e-mailu uklada jen metadata priloh.
- PDF prilohy zatim nejdou z Work Queue otevrit; aktualne jde jen zobrazit metadata a zaskrtnout budoucí ulozeni.
- Fulltextove vyhledani ulozeneho e-mailu existuje pres EmailArchiveVault koncept, ale jeste neni propojene s Work Queue davkou a dokumentovym vyhledavanim v Cockpitu.

Dalsi krok:
- Implementovat potvrzene `Zpracovat davku`: pro polozky `Ulozit` ulozit e-mail do EmailArchiveVault a vybrane prilohy do soukromeho document inbox/vault workflow; pro `Neukladat` jen uzavrit bez ulozeni; pro `Kos` nejdrive zobrazit presne potvrzeni a teprve potom resit skutecny delete/move-to-trash.

Navrhovane dalsi kroky:
- Okamzite: udelat batch endpoint bez destruktivniho mazani, ktery ulozi jen e-mailovy archiv a zapise audit vysledek.
- Potom: pridat bezpecne ulozeni vybranych PDF priloh a napojit je na document vault index.
- Nakonec: zvazit fyzicke mazani e-mailu jako oddeleny workflow s presnou potvrzovaci vetou a mozna spise `move to Trash` nez okamzite `EXPUNGE`.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/email/icloud_provider.py`
- `app/email/seznam_provider.py`
- `tests/test_cockpit.py`
- `tests/test_seznam_provider.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do handoffu nejsou ulozene zadne predmety realnych e-mailu, tela e-mailu, adresy, UID, tokeny ani hesla.
- Realna tela e-mailu zustavaji pouze lokalne v Cockpit UI po explicitnim kliknuti.
- Soukrome runtime soubory v `data/private/` a `data/session_autosave/` necommitovat.
