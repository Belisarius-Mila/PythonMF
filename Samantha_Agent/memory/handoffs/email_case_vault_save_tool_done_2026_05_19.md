Nazev: EmailCaseVault save tool hotovy
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Implementoval se samostatne potvrzovany Samantha tool `save_selected_email_cases_from_uids`.
- Tool navazuje na hotovy `run_email_triage_session` a cisty `EmailCaseVault` core.
- Ucel: po triage vybrat konkretni UID a ulozit je jako bezpecne case JSON do `data/email/cases/`.

Co je hotove:
- Pridan `app/email/case_vault_tools.py`.
- Doplnen export v `app/email/__init__.py`.
- Doplnena registrace toolu v `app/samantha_agent.py`.
- Doplneny instrukce do `app/samantha_agent.py`.
- Tool bez potvrzeni nevola provider a nic nezapisuje.
- Potvrzeni musi obsahovat vsechna UID a jasny souhlas s ulozenim jako case.
- Po potvrzeni tool nacte vybrana UID read-only pres `ICloudReadOnlyEmailProvider.read_message_by_uid`.
- Z nactenych `EmailMessage` vytvori triage polozky pres `triage_email_messages`.
- Case recordy vytvori pres `triage_item_to_case_record`.
- Ulozeni probiha pres `save_email_case_record` do `EmailCaseVault`.
- Duplicity podle `case_id` se nepridavaji.
- Pridany testy v `tests/test_email_case_vault_tools.py`.
- Doplnen regresni test potvrzovaci formulace pro triage denial wording v `tests/test_email_triage_tools.py`.

Co neni hotove:
- Neni rucne otestovano pres Samanthu nad realnymi vybranymi UID.
- Neni implementovan Samantha WorkMode tool nad ulozenym case.
- Neni browser automation pro otevreni odkazu nebo formulare; to ma zustat az dalsi samostatne potvrzovana faze.

Dalsi krok:
- Rucne otestovat pres Samanthu napr. s potvrzenim obsahujicim konkretni UID z triage a jasny souhlas s ulozenim jako case do EmailCaseVault.
- Potom navrhnout/implementovat WorkMode Samantha tool nad ulozenym safe case JSON.

Zmenene nebo relevantni soubory:
- `app/email/case_vault_tools.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `tests/test_email_case_vault_tools.py`
- `app/email/triage_tools.py`
- `tests/test_email_triage_tools.py`
- `app/email/case_vault.py`
- `app/email/triage_service.py`

Overeni:
- `.venv/bin/python -m compileall app app/samantha_agent.py`
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: 79 testu OK.

Bezpecnost / neukladat:
- Neukladat cela tela e-mailu do memory, reminders ani EmailCaseVault.
- Neukladat plne URL do memory, reminders ani EmailCaseVault.
- Neukladat neredigovane e-mailove adresy.
- Neukladat hesla, tokeny, app-specific passwords ani API klice.
- Tool nesmi bez potvrzeni volat provider.
- Tool nesmi otevirat odkazy.
- Tool nesmi stahovat prilohy.
- Tool nesmi nic odesilat, mazat, presouvat ani oznacovat jako prectene.
- Tool nesmi zapisovat do memory ani reminders.
