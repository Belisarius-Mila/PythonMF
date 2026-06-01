Nazev: Email Processing - rozhodovaci okno v Cockpitu
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-01

Co se resilo:
- Po ztrate e-mailoveho prehledu v chatu Mila navrhl, aby se e-mailove
  zpracovani neresilo v CLI/chat radce, ale v samostatnem okne Cockpitu.
- Vzniklo okno `Email Processing` na `http://127.0.0.1:8770/email-processing/`.
- Okno nacita posledni soukromy 7denni read-only prehled z:
  `data/private/email_session_handoffs/weekly_email_overview_2026_06_01_private.md`.
- Nasledne bylo doplneno prakticke rozhodovani u kazdeho e-mailu:
  `Zpracovat`, `Ulozit`, `Ignorovat` a tlacitko `Kos`.

Co je hotove:
- Cockpit ma tlacitko `Email Processing` v horni liste i dashboardu.
- API `/api/email-processing/overview` vraci strukturovane polozky z posledniho
  soukromeho prehledu.
- API `/api/email-processing/decision` uklada pracovni rozhodnuti do soukromeho
  JSON souboru mimo git.
- Parser z realneho prehledu 2026-06-01 vytahl 16 kandidatu.
- Testy `tests.test_cockpit` prochazeji: 17 testu OK.
- Cockpit server byl restartovan a aktualizovane okno bylo otevreno.

Co neni hotove:
- `Kos` zatim e-mail fyzicky nemaze; jen uklada stav `trash_requested`.
- `Zpracovat` a `Ulozit` zatim necte tela e-mailu ani nestahuje PDF.
- Chybi navazujici potvrzene akce pro konkretni UID: nacist e-mail, stahnout
  prilohu, ulozit PDF do document vaultu, nebo potvrzene smazat e-mail.

Dalsi krok:
- Nechat Milu v okne oznacit prvni sadu e-mailu.
- Potom pridat navazujici tlacitko nebo workflow, ktere ze soukromych rozhodnuti
  vytvori bezpecnou frontu dalsich kroku.

Navrhovane dalsi kroky:
- Pro `Zpracovat`: po potvrzeni nacist konkretni e-mail podle zdroje a UID.
- Pro `Ulozit`: po potvrzeni najit PDF prilohy a ulozit je pres document vault
  workflow.
- Pro `Ignorovat`: ponechat jen pracovni stav, bez zmen ve schrance.
- Pro `Kos`: vyzadovat samostatne potvrzeni pred jakymkoliv skutecnym smazanim
  nebo presunem e-mailu ve schrance.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `data/private/email_session_handoffs/weekly_email_overview_2026_06_01_private.md`
- `data/private/email_session_handoffs/email_processing_decisions.json`

Bezpecnost / neukladat:
- Do git-safe memory neukladat konkretni UID, e-mailove adresy, cela tela
  e-mailu, plne URL, prilohy ani obsah PDF.
- Soukrome resume a rozhodovaci JSON zustavaji mimo git v `data/private/`.
- Zadna akce v okne nesmi fyzicky mazat e-maily, cist tela ani stahovat prilohy
  bez samostatneho potvrzeni.
