# Handoff: iCloud Mail a RIXO Insurance Case Phase 1

Nazev: iCloud Mail read-only - RIXO Insurance Case Phase 1 připravený k implementaci
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-19

## Co se resilo

Navazovalo se na iCloud Mail read-only workflow pro Samanthu. Byly ověřené
jednotlivé bezpečné kroky nad konkrétně potvrzenými e-maily a následně byl
navržen směr Phase 1 pro `RIXO Insurance Case`.

Cíl nového směru:

- z více potvrzeně přečtených e-mailů vytvořit jeden pracovní případ typu
  `InsuranceCase`,
- nic neodesílat,
- nestahovat přílohy,
- neotevírat odkazy,
- neukládat celé e-maily do memory.

## Co je hotove

- Samantha umí read-only vypsat e-mailové hlavičky.
- Hlavičkový výstup rediguje e-mailovou adresu odesílatele.
- `build_email_case_from_uid` umí po aktuálním výslovném potvrzení vytvořit
  redigovaný pracovní případ z jednoho e-mailu.
- `show_email_case_links` umí po samostatném výslovném potvrzení vypsat plné URL
  z jednoho e-mailu.
- Průchod pracovního případu i URL toolu byl ověřen přes Samanthu.
- Lokální testy e-mailové vrstvy prošly.
- Byl navržen Phase 1 pro `RIXO Insurance Case`:
  - nové modely v `app/email/insurance_case_models.py`,
  - čistá služba v `app/email/insurance_case_service.py`,
  - tool pro více UID v `app/email/insurance_case_tools.py`,
  - testy nad fake `EmailMessage` bez IMAPu.

## Co neni hotove

- `InsuranceCase` modely zatím nejsou implementované.
- Není hotový service pro agregaci více e-mailů do jednoho případu.
- Není hotový Samantha tool pro více UID.
- Není hotový ruční end-to-end test s více potvrzenými UID.
- Není hotová perzistence redigovaného shrnutí do memory po samostatném souhlasu.
- Není hotový workflow pro přílohy; zatím jen metadata, žádné stahování.

## Dalsi krok

Implementovat Phase 1 konzervativně v tomto pořadí:

1. Přidat `app/email/insurance_case_models.py`.
2. Přidat `app/email/insurance_case_service.py` jako čisté funkce nad fake
   `EmailMessage`, bez IMAPu a bez Samanthy.
3. Přidat `tests/test_insurance_case_service.py`.
4. Ověřit, že výstup rediguje adresy, neukazuje plné URL automaticky, uvádí
   přílohy jen jako metadata a obsahuje bezpečnostní poznámku.
5. Teprve potom přidat `app/email/insurance_case_tools.py` pro více UID s
   potvrzovací bránou.

Navržený potvrzovací text pro budoucí reálný test:

```text
Potvrzuji, že chceš přečíst těla e-mailů UID <UID1>, <UID2>, <UID3> a vytvořit jeden RIXO Insurance Case.
```

Tool nesmí akceptovat neurčité „vezmi ty předchozí“ bez explicitního seznamu UID.

## Navrzeny vystup pro uzivatele

Výstup `InsuranceCase` má být praktický a redigovaný:

- název a stav případu,
- priorita,
- počet potvrzeně přečtených zdrojů,
- redigované shrnutí,
- účastníci a jejich role,
- pojistka / škoda, pokud jde rozumně určit,
- časová osa,
- akční kroky se zdrojovým UID,
- přílohy pouze jako metadata,
- odkazy pouze jako domény a počty,
- otevřené otázky,
- bezpečnostní poznámka.

## Zmenene nebo relevantni soubory

- `app/email/models.py`
- `app/email/case_models.py`
- `app/email/case_service.py`
- `app/email/case_tools.py`
- `app/email/link_tools.py`
- `app/email/safety.py`
- `app/email/tools.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `tests/test_email_case_service.py`
- `memory/handoffs/email_url_tool_e2e_ok_2026_05_19.md`
- `memory/handoffs/email_samantha_headers_redacted_waiting_uid_2026_05_19.md`

## Bezpecnost / neukladat

Do memory ani gitu neukládat:

- konkrétní UID reálných zpráv,
- plné hlavičky reálných zpráv,
- plné e-mailové adresy,
- celé předměty reálných zpráv,
- obsah e-mailů,
- plné URL z e-mailů,
- přílohy,
- tokeny,
- app-specific password,
- iCloud adresu,
- hesla.

Workflow stále nesmí:

- odesílat e-maily,
- mazat e-maily,
- přesouvat e-maily,
- označovat e-maily jako přečtené,
- otevírat odkazy,
- stahovat přílohy bez dalšího výslovného potvrzení,
- ukládat obsah e-mailů do memory bez výslovného souhlasu.
