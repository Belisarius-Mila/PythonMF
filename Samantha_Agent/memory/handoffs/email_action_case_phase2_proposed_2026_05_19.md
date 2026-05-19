# Handoff: Email Action Case Phase 2 navrzena

Nazev: Email Action Case Phase 2 - navrh ulozitelne pripominky z e-mailu
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-19

## Co se resilo

Po testu read-only workflow nad potvrzene prectenym e-mailem od NIBE byl navrzen
novy smer `Email Action Case Phase 2`.

Cil Phase 2:

- z jednoho potvrzene precteneho e-mailu vytvorit redigovany ukol,
- pripravit ho jako navrh pro lokalni reminders JSON,
- nic automaticky neukladat bez samostatneho potvrzeni,
- nezapisovat cele telo e-mailu do memory.

Test NIBE ukazal prakticky use case: marketingovy nebo servisni e-mail muze byt
newsletter, ale presto z nej muze vzniknout uzitecny ukol typu "objednat
preventivni servisni prohlidku". Konkretni UID, plne URL, cele predmety ani telo
realneho e-mailu nejsou v tomto handoffu ulozene.

## Co je hotove

- Existuje funkcni Phase 1 pro `EmailCaseDraft` z jednoho potvrzeneho UID.
- Existuje funkcni Phase 1 pro agregovany `RIXO Insurance Case` z vice UID.
- Byl navrzen novy `EmailActionCase` nad jednim potvrzene prectenym e-mailem.
- Byly navrzeny dva oddelene kroky:
  - vytvorit navrh ukolu,
  - ulozit navrh do reminders JSON az po druhem vyslovnem potvrzeni.

## Co neni hotove

- Nejsou implementovane modely `EmailActionCase` / `ReminderDraft`.
- Neni implementovana cista service nad fake `EmailMessage`.
- Neni implementovany formatter navrhu ukolu pro Samanthu.
- Neni implementovany tool pro vytvoreni navrhu z UID.
- Neni implementovane bezpecne ulozeni do `data/reminders/reminders.json`.
- Neni hotovy test pro NIBE-like e-mail bez realneho IMAPu.

## Navrzeny rozsah Phase 2

Navrzene soubory:

```text
app/email/action_case_models.py
app/email/action_case_service.py
app/email/action_case_tools.py
tests/test_email_action_case_service.py
data/reminders/reminders.json
```

`EmailActionCase` ma obsahovat:

- UID zdroje,
- datum,
- redigovaneho odesilatele,
- predmet,
- redigovane shrnuti,
- akcni kroky,
- nalezeny deadline nebo doporuceny termin,
- metadata priloh,
- metadata odkazu pouze jako domeny a pocty,
- navrh titulku ukolu,
- redigovane poznamky k ukolu,
- prioritu ukolu,
- `source_type = "email"`,
- bezpecnostni poznamku.

Navrzeny reminders JSON zaznam:

```json
{
  "id": "email-safe-slug",
  "title": "Strucny navrh ukolu",
  "notes": "Kratke redigovane shrnuti a prakticky dalsi krok.",
  "due_date": "YYYY-MM-DD",
  "priority": "normal",
  "status": "open",
  "source": {
    "type": "email",
    "uid": "[neukladat realne UID do memory]",
    "date": "datum zdroje",
    "sender": "redigovany odesilatel"
  },
  "links": [
    {
      "domain": "example.com",
      "count": 1
    }
  ],
  "attachments": [],
  "created_at": "YYYY-MM-DD"
}
```

## Dalsi krok

Implementovat Phase 2 konzervativne:

1. Pridat `app/email/action_case_models.py`.
2. Pridat `app/email/action_case_service.py` jako ciste funkce nad
   `EmailMessage`, bez IMAPu.
3. Pridat `tests/test_email_action_case_service.py` s fake NIBE-like e-mailem.
4. Overit, ze vystup neobsahuje cele telo e-mailu, plne URL ani neredigovane
   e-mailove adresy.
5. Pridat tool pro vytvoreni navrhu z jednoho potvrzeneho UID.
6. Az potom pridat samostatny tool pro ulozeni do `data/reminders/reminders.json`
   za druhou potvrzovaci branou.

## Zmenene nebo relevantni soubory

- `app/email/case_models.py`
- `app/email/case_service.py`
- `app/email/case_tools.py`
- `app/email/link_tools.py`
- `app/email/insurance_case_models.py`
- `app/email/insurance_case_service.py`
- `app/email/insurance_case_tools.py`
- `app/email/safety.py`
- `app/samantha_agent.py`
- `tests/test_email_case_service.py`
- `tests/test_insurance_case_service.py`

## Bezpecnost / neukladat

Do memory ani gitu neukladat:

- konkretni UID realnych zprav,
- plne hlavicky realnych zprav,
- plne e-mailove adresy,
- cele predmety realnych zprav,
- obsah e-mailu,
- plne URL z e-mailu,
- prilohy,
- tokeny,
- app-specific password,
- iCloud adresu,
- hesla.

Workflow stale nesmi odesilat, mazat, presouvat, oznacovat jako prectene,
automaticky otevirat odkazy, stahovat prilohy ani ukladat cele telo e-mailu do
memory.
