# Handoff: RIXO Insurance Case Phase 1 implementovana

Nazev: iCloud Mail read-only - RIXO Insurance Case Phase 1 implementovana
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-05-19

## Co se resilo

Navazovalo se na plan pro agregovany `RIXO Insurance Case` z vice potvrzene
prectenych e-mailu. Cilem bylo pridat konzervativni Phase 1 bez realneho IMAP
testu: ciste modely, cistou sluzbu nad `EmailMessage`, testy nad fake zprávami
a Samantha tool s potvrzovaci branou pro vice UID.

## Co je hotove

- Pridane modely v `app/email/insurance_case_models.py`.
- Pridana sluzba `app/email/insurance_case_service.py`.
- Pridan tool `build_rixo_insurance_case_from_uids` v
  `app/email/insurance_case_tools.py`.
- Tool je exportovany pres `app/email/__init__.py`.
- Samantha ma novy tool registrovany v `app/samantha_agent.py` a instrukce
  vysvetluji, ze musi byt potvrzena vsechna konkretni UID v aktualni zprave.
- Bezpecnostni helper `has_explicit_multi_uid_read_confirmation` vyzaduje alespon
  dve unikatni UID, jejich explicitni pritomnost v potvrzovacim textu a potvrzovaci
  slovo.
- Testy jsou v `tests/test_insurance_case_service.py`.

## Co neni hotove

- Neni proveden realny end-to-end test pres Samanthu nad vice skutecnymi UID.
- Neni hotova perzistence redigovaneho shrnuti do memory po samostatnem souhlasu.
- Neni hotovy workflow pro prilohy; vystup ukazuje pouze metadata, nic nestahuje.

## Dalsi krok

1. Najit RIXO e-maily pouze pres read-only hlavicky.
2. Nechat Milu vybrat konkretni UID.
3. Vyžadat potvrzeni v aktualni zprave ve tvaru podobnem:

```text
Potvrzuji, ze chci precist tela e-mailu UID <UID1>, UID <UID2> a vytvorit jeden RIXO Insurance Case.
```

4. Otestovat `build_rixo_insurance_case_from_uids` primo pres Samanthu.
5. Overit, ze vystup neukazuje plne URL automaticky, nestahuje prilohy a nic
   neuklada do memory.

## Zmenene nebo relevantni soubory

- `app/email/insurance_case_models.py`
- `app/email/insurance_case_service.py`
- `app/email/insurance_case_tools.py`
- `app/email/safety.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `tests/test_insurance_case_service.py`

## Overeni

```bash
.venv/bin/python -m compileall app/email app/samantha_agent.py
.venv/bin/python -m unittest tests.test_email_case_service tests.test_insurance_case_service
.venv/bin/python -m unittest discover -s tests
```

Vysledek: vsechny dostupne testy prosly, `unittest discover -s tests` spustil
19 testu a skoncil `OK`.

## Bezpecnost / neukladat

Do memory ani gitu neukladat konkretni UID realnych zprav, plne hlavicky, plne
e-mailove adresy, cele predmety realnych zprav, obsah e-mailu, plne URL, prilohy,
tokeny, app-specific password, iCloud adresu ani hesla.

Workflow stale nesmi odesilat, mazat, presouvat, oznacovat jako prectene, otevirat
odkazy, stahovat prilohy ani ukladat obsah e-mailu do memory bez vyslovneho
souhlasu.
