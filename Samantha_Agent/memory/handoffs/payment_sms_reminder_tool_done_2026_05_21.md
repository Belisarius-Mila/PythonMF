Nazev: Platebni SMS reminder tool
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Mila chce posilat Samanthě platebni SMS typu pojistka/faktura a mit jistotu,
  ze se ulozi prakticka pripominka bez plnych URL a bez unahleneho "zaplatit dnes".
- Konkretni motivace byl RIXO pripad: SMS tlacila na rychlou uhradu, ale overena
  splatnost byla 2026-07-31 a nova pojistka zacina 2026-08-01.

Co je hotove:
- Pridan Samantha tool `save_payment_sms_reminder`.
- Tool umi ze SMS vytahnout cislo pojistky/smlouvy/faktury, castku a domenu
  odkazu.
- Pokud neni overena skutecna splatnost, uklada jen ukol `Overit splatnost...`.
- Pokud je overena skutecna splatnost, uklada platebni pripominku s
  `verified_due_date` a volitelne `verified_start_date`.
- Tool vyzaduje samostatne potvrzeni s id pripominky a souhlasem s ulozenim.
- Plne URL ani tokeny se neukladaji; reminder store je navic odmita validaci.
- Pridan navazujici read-only tool `inspect_payment_page_for_reminder`.
- Inspektor vyzaduje potvrzeni s domenou odkazu, nacte pouze HTTPS text/HTML,
  hleda splatnost, pocatek pojisteni/sluzby, castku a cislo smlouvy/pojistky.
- Inspektor ve vystupu nevraci plnou URL ani token a nic neuklada.
- RIXO realny test probehl: API detail vraci pojistku 3275111280, castku 4956 Kc,
  produkt Autopojisteni Combi Plus IV, pojistovnu CPP, platbu kartou/branou do
  2026-07-31, bankovni prevod do 2026-07-30 a pocatek pojisteni 2026-08-01.
- Pridan tool `save_payment_case_document` pro ulozeni lokalni faktury/prilohy
  k platebnimu pripadu do `data/private/payment_cases/<case_id>/documents/`.
- Testy pro RIXO scenar prosly.

Co neni hotove:
- Inspektor zatim neumi cist text z PDF faktur; PDF lze zatim jen soukrome
  ulozit k pripadu jako dokument.
- RIXO API v realnem testu nevratilo fakturu jako dokument/prilohu, jen platebni
  udaje a branu.
- Neni hotove prime predani vysledku inspektoru do ulozeni bez lidske kontroly;
  spravne zustava dvoukrokove potvrzeni.

Dalsi krok:
- Pri pristim platebnim SMS testu pouzit Samanthu:
  1. `inspect_payment_page_for_reminder` overi splatnost z odkazu,
  2. pokud najde `verified_due_date`, dalsim potvrzenym krokem ulozit
     `save_payment_sms_reminder`,
  3. pokud existuje lokalni faktura/priloha, dalsim potvrzenym krokem ulozit
     `save_payment_case_document`,
  4. pokud splatnost nenajde, ulozit jen overovaci pripominku.
- Pozdeji zvazit extrakci textu z PDF faktur, ale jen read-only a s limity.

Zmenene nebo relevantni soubory:
- `app/reminders/payment_page_inspector.py`
- `app/reminders/payment_case_documents.py`
- `app/reminders/payment_sms_tools.py`
- `app/reminders/__init__.py`
- `app/samantha_agent.py`
- `tests/test_payment_page_inspector.py`
- `tests/test_payment_case_documents.py`
- `tests/test_payment_sms_reminders.py`
- `memory/technical/general_reminders_workflow.md`

Bezpecnost / neukladat:
- Neukladat plne platebni URL, tokeny, cele SMS ani citlive platebni detaily.
- SMS urgence neni sama o sobe splatnost.
