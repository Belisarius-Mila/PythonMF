# Handoff: Email Action Case Phase 2 core hotovy

Nazev: Email Action Case Phase 2 - cisty core nad fake EmailMessage hotovy
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-19

## Co se resilo

Implementovala se pouze prvni cast Phase 2 pro `Email Action Case`: ciste modely
a service nad existujicim `EmailMessage`, bez IMAPu, bez provideru, bez novych
Samantha toolu a bez zapisu do `memory` nebo `data/reminders`.

Cil teto casti:

- z uz potvrzene precteneho `EmailMessage` vytvorit bezpecny `EmailActionCase`,
- pripravit pouze navrh `ReminderDraft`,
- udrzet vystup redigovany a kratky,
- nikdy neukladat cele telo e-mailu.

## Co je hotove

- Pridan `app/email/action_case_models.py`.
- Pridan `app/email/action_case_service.py`.
- Pridan `tests/test_email_action_case_service.py`.
- Service pracuje jen s predanym `EmailMessage`.
- Service nevola iCloud/IMAP, nic neodesila, nemaze, nepresouva, neoznacuje jako
  prectene, neotevira odkazy a nestahuje prilohy.
- Service negeneruje zapis do `memory` ani do `data/reminders`.
- Vystup drzi odkazy pouze jako domeny a pocty.
- Prilohy jsou pouze metadata.
- NIBE-like fake test overuje, ze e-mail s nabidkou prohlidky fotovoltaiky vytvori
  navrh ukolu a doporuceny termin.
- Test hlida, ze formatovany vystup neobsahuje plne URL, neredigovane e-mailove
  adresy ani umele vlozenou cast simulujici pozdni unik celeho tela.

## Co neni hotove

- Neni pridan Samantha tool pro vytvoreni action case z konkretniho UID.
- Neni pridan tool pro ulozeni navrhu do `data/reminders/reminders.json`.
- Neni implementovana druha potvrzovaci brana pro zapis pripominky.
- Neni proveden end-to-end test pres Samanthu.
- `app/email/__init__.py` zatim nemusi exportovat nove action case typy, pokud to
  dalsi krok nebude vyzadovat.

## Dalsi krok

Implementovat druhou cast Phase 2 v tomto poradi:

1. Rozhodnout, zda exportovat action case modely/service z `app/email/__init__.py`.
2. Pridat `app/email/action_case_tools.py` pro vytvoreni navrhu z jednoho UID po
   stejne potvrzovaci brane jako cteni tela e-mailu.
3. Pridat test, ze tool bez potvrzeni nevola provider.
4. Az potom pridat samostatne potvrzovane ulozeni do
   `data/reminders/reminders.json`.
5. Otestovat pres Samanthu na umelem nebo bezpecne potvrzenem e-mailu.

## Zmenene nebo relevantni soubory

- `app/email/action_case_models.py`
- `app/email/action_case_service.py`
- `tests/test_email_action_case_service.py`
- `app/email/models.py`
- `app/email/case_service.py`
- `app/email/redaction.py`

## Overeni

```bash
.venv/bin/python -m unittest tests.test_email_action_case_service
.venv/bin/python -m unittest discover -s tests
```

Vysledek:

- `tests.test_email_action_case_service`: 2 testy, `OK`.
- `discover -s tests`: 21 testu, `OK`.

## Bezpecnost / neukladat

Do memory ani gitu neukladat:

- konkretni UID realnych zprav,
- plne hlavicky realnych zprav,
- plne e-mailove adresy,
- cele predmety realnych zprav,
- cele telo e-mailu,
- plne URL z e-mailu,
- prilohy,
- tokeny,
- app-specific password,
- iCloud adresu,
- hesla.

Dalsi implementace stale nesmi odesilat, mazat, presouvat, oznacovat jako
prectene, automaticky otevirat odkazy, stahovat prilohy ani ukladat cele telo
e-mailu do memory.
