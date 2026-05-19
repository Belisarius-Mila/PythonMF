# Handoff: iCloud Mail URL tool end-to-end OK

Nazev: iCloud Mail read-only - URL tool end-to-end ověřený
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

## Co se resilo

Navázalo se na iCloud Mail read-only workflow pro Samanthu. Cílem bylo dokončit
bezpečný tok:

- vypsat e-mailové hlavičky read-only,
- vytvořit redigovaný pracovní případ po výslovném potvrzení,
- přidat samostatný tool pro plné URL jen po samostatném výslovném potvrzení,
- ověřit, že odkazy se pouze vypíšou a neotevírají.

## Co je hotove

- Samantha umí read-only vypsat hlavičky e-mailů.
- Výstup hlaviček rediguje e-mailovou adresu odesílatele.
- `build_email_case_from_uid` prošel end-to-end přes Samanthu po aktuálním
  výslovném potvrzení s konkrétním UID.
- Byl přidán nový tool `show_email_case_links`.
- `show_email_case_links` prošel end-to-end přes Samanthu po samostatném
  výslovném potvrzení s konkrétním UID a výslovnou žádostí o URL/odkazy.
- Tool vypsal plné URL, ale nic neotevřel, nestáhl, neupravil ani neuložil
  do memory.
- Lokální testy prošly.

## Co neni hotove

- Není hotová pohodlnější prezentace URL, například seskupení podle domény,
  popisky podle okolního textu nebo kopírovatelný blok.
- Není hotová perzistence redigovaného pracovního shrnutí do memory po samostatném
  výslovném souhlasu.
- Není hotový workflow pro přílohy; zatím jen metadata, žádné stahování.

## Dalsi krok

Pokud se bude pokračovat v iCloud Mail workflow, nejpraktičtější další krok je
zlepšit prezentaci odkazů:

- seskupit URL podle domény,
- přidat krátký popis z okolního textu,
- zachovat pravidlo, že plné URL se vypíšou jen po samostatném potvrzení,
- plné URL dál neukládat do memory.

## Zmenene nebo relevantni soubory

- `app/email/tools.py`
- `app/email/safety.py`
- `app/email/case_service.py`
- `app/email/link_tools.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `tests/test_email_case_service.py`
- `memory/handoffs/email_samantha_headers_redacted_waiting_uid_2026_05_19.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

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
