Nazev: Email Work Session pro jedno UID - navrh rezimu
Priorita: 1
Stav: ceka na implementaci
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Navrh rezimu `Email Work Session` pro jedno konkretni UID.
- Cil: jednim potvrzenim povolit sadu bezpecnych akci nad jednim e-mailem:
  - precist telo,
  - vytvorit action case,
  - zobrazit plne URL,
  - ulozit bezpecnou pripominku,
  - zobrazit metadata priloh.

Co je hotove:
- Navrzen jednorazovy permission model pro aktualni beh / aktualni odpoved, ne trvale opravneni.
- Navrzen objekt `EmailWorkSession` s `uid`, `allowed_actions`, `denied_actions`, `confirmation_text` a `created_at`.
- Navrzeno, ze se e-mail ma nacist jen jednou a dalsi vystupy se maji odvozovat z jednoho `EmailMessage` v pameti procesu.
- Navrzeno, ze existujici tooly zustanou zachovane a nad nimi vznikne samostatny orchestrator pro jedno UID.
- Navrzen potvrzovaci text, ktery musi obsahovat `Email Work Session`, konkretni UID, povolene akce a explicitni zakazy.

Co neni hotove:
- Zatim nebyla provedena zadna implementace.
- Zatim nejsou modely, service ani testy pro `EmailWorkSession`.
- Zatim neni Samantha tool pro spusteni work session.
- Zatim neni end-to-end test pres realne UID.

Dalsi krok:
- Implementovat nejdrive cisty model a service nad fake `EmailMessage`, bez IMAPu:
  - validace potvrzeni pro jedno UID,
  - bezpecne slouceni vystupu: redigovane shrnuti, action case, plne URL jako vystup, metadata priloh, safe reminder draft,
  - zadne automaticke otevreni URL,
  - zadne stazeni priloh,
  - zadne odeslani, mazani, presun ani mark-read,
  - zadne ulozeni celeho tela e-mailu do memory.

Zmenene nebo relevantni soubory:
- `app/email/action_case_tools.py`
- `app/email/link_tools.py`
- `app/email/tools.py`
- `app/email/action_case_service.py`
- `app/reminders/store.py`
- `app/reminders/tools.py`
- `app/reminders/query_tools.py`
- `app/samantha_agent.py`

Bezpecnost / neukladat:
- Neukladat cela tela e-mailu do memory.
- Neukladat plne URL do memory.
- Neukladat neredigovane e-mailove adresy do memory.
- Neukladat hesla, tokeny, app-specific passwords ani API klice.
- Work session nesmi automaticky otevirat URL.
- Work session nesmi stahovat prilohy bez dalsiho samostatneho potvrzeni.
- Work session nesmi odesilat e-mail, mazat, presouvat ani oznacovat jako prectene.
