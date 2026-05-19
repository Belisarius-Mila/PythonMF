Nazev: Email Action Case - reminders Phase 3B hotova
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Navazani na hotovy reminders store a due reminders.
- Implementace Samantha toolu pro rucni praci s lokalnimi pripominkami.
- Bezpecnost: zadne cteni e-mailu, zadny IMAP/provider, zadne otevirani odkazu, zadne stahovani priloh, zadne odesilani a zadny zapis do memory.

Co je hotove:
- Pridan modul `app/reminders/query_tools.py`.
- Pridan tool `list_open_reminders` pro vypis otevrenych pripominek.
- Pridan tool `show_reminder_detail` pro bezpecny detail jedne pripominky.
- Pridan tool `mark_reminder_done` pro samostatne potvrzene oznaceni pripominky jako hotove.
- Tooly jsou exportovane z `app/reminders/__init__.py`.
- Tooly jsou registrovane v `app/samantha_agent.py`.
- Instrukce Samanthy popisuji bezpecne pouziti reminder toolu a samostatne potvrzeni pro `mark_reminder_done`.
- Pridane testy pokryvaji vypis, detail, potvrzovaci branu, zapis statusu `done`, chybejici id a redakci plnych URL / neredigovanych e-mailu.

Co neni hotove:
- Nebyl delan rucni end-to-end test pres bezici Samanthu.
- Zatim neni implementovana editace existujicich pripominek mimo oznaceni jako hotove.

Dalsi krok:
- Rucne otestovat pres Samanthu:
  - vypsani otevrenych pripominek,
  - detail konkretni pripominky,
  - samostatne potvrzene oznaceni jedne pripominky jako hotove.

Zmenene nebo relevantni soubory:
- `app/reminders/query_tools.py`
- `app/reminders/__init__.py`
- `app/samantha_agent.py`
- `tests/test_reminders_query_tools.py`
- `app/reminders/store.py`
- `app/reminders/due.py`
- `data/reminders/reminders.json`

Overeni:
- `.venv/bin/python -m compileall app app/samantha_agent.py`
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: 48 testu OK.

Bezpecnost / neukladat:
- Neukladat cela tela e-mailu.
- Neukladat plne URL.
- Neukladat neredigovane e-mailove adresy.
- Neukladat hesla, tokeny, app-specific passwords ani API klice.
- Pri praci se zdrojovym e-mailem vzdy vyzadovat samostatne potvrzeni konkretniho UID.
