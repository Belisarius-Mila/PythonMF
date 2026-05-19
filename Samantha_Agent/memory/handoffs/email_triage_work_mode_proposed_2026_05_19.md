Nazev: Email Triage and Work Mode - navrh workflow
Priorita: 1
Stav: ceka na implementaci
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Navrh noveho praktickeho workflow `Email Triage and Work Mode`.
- Cil: Mila nechce potvrzovat kazdou mikroakci. Jednim souhlasem chce projit e-maily za poslednich 7 dni, najit dulezite zpravy, deadliny a ukoly, vybrane e-maily ulozit jako bezpecne pracovni pripady a pak pracovat s jednim pripadem.

Co je hotove:
- Navrzen `TriageSession` pro poslednich 7 dni.
- Navrzen `EmailCaseVault` v `data/email/cases/`.
- Navrzen `WorkMode` pro jeden ulozeny pripad.
- Navrzena pravidla, co smi byt v jednom souhlasu:
  - nacist hlavicky za poslednich 7 dni,
  - cist tela kandidatnich e-mailu v omezenem rozsahu,
  - klasifikovat dulezitost,
  - hledat deadliny a akcni kroky,
  - vytvorit bezpecne case soubory,
  - ulozit bezpecne cases do vaultu,
  - pripravit reminder drafty,
  - zobrazit metadata priloh,
  - zobrazit domeny odkazu.
- Navrzena pravidla, co vzdy vyzaduje dalsi potvrzeni:
  - znovu cist zdrojovy e-mail podle UID,
  - zobrazit plne URL,
  - otevrit URL v browseru,
  - vyplnit nebo odeslat formular,
  - stahnout prilohu,
  - odeslat e-mail,
  - smazat/presunout/mark-read,
  - ulozit citlive udaje nebo cele telo do memory.
- Navrzeno, ze browser automation bude az samostatna pozdejsi vrstva, nikdy primo soucast triage.

Minimalni architektura:
- `app/email/triage_models.py`
- `app/email/triage_service.py`
- `app/email/case_vault.py`
- `app/email/work_mode_models.py`
- `app/email/work_mode_service.py`
- `tests/test_email_triage_service.py`
- `tests/test_email_case_vault.py`
- `tests/test_email_work_mode_service.py`

Dalsi krok:
- Implementovat nejdriv cisty `EmailCaseVault` a modely/service nad fake daty:
  - bez IMAPu,
  - bez provideru,
  - bez browser automation,
  - bez ukladani celeho tela e-mailu,
  - bez plnych URL ve vaultu,
  - bez neredigovanych e-mailovych adres.

Zmenene nebo relevantni soubory:
- `app/email/work_session_models.py`
- `app/email/work_session_service.py`
- `app/email/action_case_models.py`
- `app/email/action_case_service.py`
- `app/reminders/store.py`
- `app/reminders/query_tools.py`
- `data/reminders/reminders.json`
- budoucne `data/email/cases/`

Bezpecnost / neukladat:
- Neukladat cela tela e-mailu do memory ani do case vaultu.
- Neukladat plne URL do memory ani do case vaultu.
- Neukladat neredigovane e-mailove adresy do memory ani do case vaultu.
- Neukladat hesla, tokeny, app-specific passwords ani API klice.
- Triage nesmi automaticky otevirat odkazy.
- Triage nesmi stahovat prilohy.
- Triage nesmi odesilat e-mail, mazat, presouvat ani oznacovat jako prectene.
- Browser automation pozdeji vyzadovat samostatne potvrzeni pro otevreni URL a dalsi samostatne potvrzeni pred odeslanim formulare.
