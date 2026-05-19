Nazev: Email Triage and Work Mode - cisty core hotovy
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Implementovala se prvni cista cast `Email Triage and Work Mode` nad fake `EmailMessage` objekty.
- Rozsah byl omezeny na modely/service/testy bez IMAPu, provideru, browser automation a bez Samantha toolu.

Co je hotove:
- Pridan `app/email/triage_models.py`.
- Pridan `app/email/triage_service.py`.
- Pridan `app/email/case_vault.py`.
- Pridan `app/email/work_mode_models.py`.
- Pridan `app/email/work_mode_service.py`.
- Pridany testy:
  - `tests/test_email_triage_service.py`,
  - `tests/test_email_case_vault.py`,
  - `tests/test_email_work_mode_service.py`.
- Triage umi z predaneho seznamu fake `EmailMessage` vytvorit:
  - dulezite e-maily,
  - e-maily s deadlinem,
  - e-maily s akcnim krokem,
  - newslettery / nizkou prioritu,
  - kandidaty k ulozeni jako case.
- `EmailCaseVault` uklada bezpecny case JSON do explicitne predane slozky a udrzuje jednoduchy `index.json`.
- Vault odmita plne URL a neredigovane e-mailove adresy a nepridava duplicitni case id.
- `WorkMode` pracuje jen nad ulozenym safe case JSON, umi zobrazit bezpecny detail a vypsat dalsi mozne akce.
- U e-mailoveho zdroje WorkMode pripomina, ze znovu cist zdrojovy e-mail, zobrazit plne URL, otevrit URL nebo stahnout prilohu vyzaduje dalsi samostatne potvrzeni.

Co neni hotove:
- Neni pridan Samantha tool pro triage session.
- Neni napojeni na realny iCloud/IMAP provider.
- Neni browser automation.
- Neni realny `data/email/cases/` workflow ani rucni end-to-end test pres Samanthu.

Dalsi krok:
- Navrhnout a implementovat samostatny Samantha tool pro spusteni triage nad realnymi e-mailovymi hlavickami/tely az po jednom jasnem triage potvrzeni.
- Pred tim zvazit exporty v `app/email/__init__.py` a udrzet potvrzovaci pravidla pro realny IMAP/provider oddelene od ciste core vrstvy.

Zmenene nebo relevantni soubory:
- `app/email/triage_models.py`
- `app/email/triage_service.py`
- `app/email/case_vault.py`
- `app/email/work_mode_models.py`
- `app/email/work_mode_service.py`
- `tests/test_email_triage_service.py`
- `tests/test_email_case_vault.py`
- `tests/test_email_work_mode_service.py`
- `app/email/action_case_service.py`
- `app/email/models.py`

Overeni:
- `.venv/bin/python -m compileall app/email`
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: 66 testu OK.

Bezpecnost / neukladat:
- Neukladat cela tela e-mailu do memory ani do case vaultu.
- Neukladat plne URL do memory ani do case vaultu.
- Neukladat neredigovane e-mailove adresy do memory ani do case vaultu.
- Neukladat hesla, tokeny, app-specific passwords ani API klice.
- Core nevola IMAP/provider a nectenim realnych e-mailu nema zadne side efekty.
- Core neotevira odkazy, nestahuje prilohy, nepouziva browser automation.
- Core neodesila e-mail, nemaze, nepresouva ani neoznacuje jako prectene.
