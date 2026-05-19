Nazev: Lekarna - read-only audit domaci lekarny
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Navazalo se na hotovy read-only tool `search_domaci_leky`.
- Cilem bylo pridat druhou bezpecnou read-only schopnost: kontrolni audit evidence
  domaci lekarny jako prakticky checklist pro fyzickou kontrolu krabicek/blistru.

Co je hotove:
- V `app/lekarna/service.py` pribyly funkce:
  - `audit_domaci_lekarna_records`
  - `format_domaci_lekarna_audit`
- Audit seskupuje polozky podle kontrolnich kategorii:
  - chybejici nebo nezjistena expirace,
  - neurcene umisteni,
  - `nutno_overit=ano`,
  - `ZBYTKY_BEZ_KRABICKY`,
  - nizka/stredni jistota cteni,
  - antibiotika,
  - leciva souvisejici s redenim krve.
- V `app/lekarna/tools.py` pribyl `function_tool`:
  - `audit_domaci_lekarna`
- Exporty jsou doplnene v `app/lekarna/__init__.py`.
- `app/samantha_agent.py` ma doplnene instrukce a tool registraci.
- `tests/test_lekarna_service.py` ma unit testy nad fake CSV:
  - auditni kategorie,
  - checklist format,
  - zakaz davkovani / vhodnosti pro konkretni osobu,
  - read-only chovani.
- Reálný CSV audit byl ručně ověřen přes service. Výsledek ukazuje, že aktuálně všech
  21 evidovaných položek má nevyřešenou expiraci a neurčené umístění, což odpovídá
  dosavadnímu stavu evidence.

Co neni hotove:
- Nebyl proveden live test přes skutečného Samanthu agenta s OpenAI API.
- Zatím není žádný zapisový workflow pro doplnění expirace, umístění, síly nebo poznámek.
- Audit zatím jen vypisuje checklist, negeneruje návrh oprav CSV.

Dalsi krok:
- Udělat live test přes Samanthu:
  - "Udělej audit domácí lékárny."
  - "Co mám fyzicky zkontrolovat v lékárničce?"
- Podle výstupu případně zkrátit audit pro chat nebo doplnit volitelné filtry.
- Další fáze může být samostatně potvrzovaný návrh aktualizace evidence, ale ne automatický zápis.

Zmenene nebo relevantni soubory:
- `app/lekarna/__init__.py`
- `app/lekarna/service.py`
- `app/lekarna/tools.py`
- `app/samantha_agent.py`
- `tests/test_lekarna_service.py`
- `data/lekarna/domaci_leky.csv`
- `memory/projects/lekarna_domaci_leky.md`
- `memory/handoffs/lekarna_readonly_tool_done_2026_05_19.md`

Overeni:
- `.venv/bin/python -m py_compile app/lekarna/__init__.py app/lekarna/models.py app/lekarna/service.py app/lekarna/tools.py app/samantha_agent.py tests/test_lekarna_service.py`
- `.venv/bin/python -m unittest tests.test_lekarna_service`
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: `Ran 155 tests ... OK`.

Bezpecnost / neukladat:
- Audit nesmi zapisovat do CSV ani jiných dat.
- Audit nesmi doporucovat davkovani.
- Audit nesmi posuzovat vhodnost pro konkretni osobu.
- Antibiotika a leky souvisejici s redenim krve brat jako citlive polozky pro overeni
  u lekare/lekarnika, ne jako navod k pouziti.
- Polozky bez expirace, bez krabicky, s nejasnym nazvem nebo `nutno_overit=ano`
  brat jako inventarni kandidaty k fyzicke kontrole.
