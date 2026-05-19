Nazev: Email Triage Session tool - realna read-only triage hotova
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Implementoval se Samantha tool `run_email_triage_session` pro realnou read-only triage session nad iCloud e-maily za poslednich N dni.
- Tool navazuje na hotovy cisty `Email Triage and Work Mode` core.

Co je hotove:
- Pridan `app/email/triage_tools.py`.
- Doplnen export v `app/email/__init__.py`.
- Doplnena registrace toolu v `app/samantha_agent.py`.
- Doplneny instrukce do `app/samantha_agent.py`.
- `ICloudReadOnlyEmailProvider` ma novou konzervativni read-only metodu `list_recent_messages(days, limit, max_chars)`.
- Provider pouziva `select("INBOX", readonly=True)` a `BODY.PEEK[]`.
- Tool bez jasneho potvrzeni nevola provider.
- Potvrzeni musi obsahovat triage/Email Triage, pocet dni nebo frazi typu poslednich 7 dni, souhlas se ctenim hlavicek a tel kandidatnich e-mailu a explicitni zakazy:
  - neotevirat odkazy,
  - nestahovat prilohy,
  - nic neodesilat,
  - nemazat,
  - nepresouvat,
  - neoznacovat jako prectene.
- Po potvrzeni tool nacte omezene mnozstvi zprav read-only, preda je do `triage_email_messages` a vrati bezpecny souhrn:
  - dulezite e-maily,
  - deadline e-maily,
  - action e-maily,
  - newslettery / nizka priorita,
  - case kandidaty.
- Vystup ukazuje jen UID, datum, redigovaneho odesilatele, bezpecny predmet, prioritu a doporuceny dalsi krok.
- Pridany testy v `tests/test_email_triage_tools.py`.

Co neni hotove:
- Neni provedena realna end-to-end triage pres Samanthu nad iCloud Mail.
- Tool zatim automaticky neuklada case kandidaty do `EmailCaseVault`.
- Neni samostatny tool pro potvrzene ulozeni vybranych case kandidatu do vaultu.
- Neni WorkMode Samantha tool nad ulozenym case.

Dalsi krok:
- Rucne otestovat `run_email_triage_session` pres Samanthu s jasnym potvrzenim.
- Potom navrhnout samostatne potvrzovane ulozeni vybranych case kandidatu do `EmailCaseVault`.

Zmenene nebo relevantni soubory:
- `app/email/triage_tools.py`
- `app/email/icloud_provider.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `tests/test_email_triage_tools.py`
- `app/email/triage_service.py`
- `app/email/case_vault.py`
- `app/email/work_mode_service.py`

Overeni:
- `.venv/bin/python -m compileall app app/samantha_agent.py`
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: 71 testu OK.

Bezpecnost / neukladat:
- Neukladat cela tela e-mailu do memory, vaultu ani reminders.
- Neukladat plne URL.
- Neukladat neredigovane e-mailove adresy.
- Neukladat hesla, tokeny, app-specific passwords ani API klice.
- Tool nesmi automaticky otevirat URL.
- Tool nesmi stahovat prilohy.
- Tool nesmi odesilat e-mail, mazat, presouvat ani oznacovat jako prectene.
- Tool nesmi automaticky zapisovat do EmailCaseVault, reminders ani memory.
