Nazev: Lekarna - read-only tool pro domaci leky
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Implementace prvni bezpecne read-only schopnosti pro projekt Lekarna.
- Cilem bylo, aby Samantha dokazala nad lokalni evidenci `data/lekarna/domaci_leky.csv`
  najit domaci leky podle bezneho dotazu, symptomu nebo kategorie.

Co je hotove:
- Pridana cista Python vrstva `app/lekarna/`:
  - `models.py` - modely `DomaciLek` a `DomaciLekMatch`.
  - `service.py` - nacitani CSV, heuristicke hledani a formatovani ceskeho vystupu.
  - `tools.py` - `function_tool` `search_domaci_leky`.
  - `__init__.py` - export verejnych funkci.
- Tool je registrovany v `app/samantha_agent.py`.
- Samantha instrukce rikaji, ze tool je pouze read-only inventar:
  - nic nezapisuje,
  - nedoporucuje davkovani,
  - nenahrazuje lekare, lekarnika ani pribalovy letak,
  - zvyraznuje nejistoty.
- Vyhledavani pokryva zakladni dotazy/synonyma typu:
  - bolest,
  - horecka,
  - kasel,
  - alergie,
  - prujem,
  - nachlazeni,
  - traveni,
  - modriny.
- Vystup ukazuje:
  - co je doma evidovane,
  - souvislost podle evidence,
  - umisteni,
  - expiraci,
  - mnozstvi,
  - proc se polozka nasla,
  - bezpecnostni nejistoty.
- Nejistoty zvyraznene ve vystupu:
  - `nutno_overit=ano`,
  - chybejici nebo nezjistena expirace,
  - `ZBYTKY_BEZ_KRABICKY`,
  - neovereny nebo nejisty nazev,
  - nizka/stredni jistota cteni,
  - neovereno z pribaloveho letaku.
- Pridany unit testy nad malym fake CSV v `tests/test_lekarna_service.py`.

Co neni hotove:
- Nebyl proveden live test pres skutecneho Samanthu agenta s OpenAI API.
- Synonyma a ranking jsou zatim jednoduche heuristiky.
- Zatim neexistuje zapisovy workflow pro doplnovani evidence, expiraci nebo umisteni.

Dalsi krok:
- Spustit rucni live test pres Samanthu, napr.:
  - "Co mame doma na bolest?"
  - "Najdi neco evidovaneho na horecku."
  - "Co je doma na modriny?"
- Podle vysledku doladit aliasy, ranking a format vystupu.
- Jakykoli zapis do evidence navrhnout az jako samostatny potvrzovany workflow.

Zmenene nebo relevantni soubory:
- `app/lekarna/__init__.py`
- `app/lekarna/models.py`
- `app/lekarna/service.py`
- `app/lekarna/tools.py`
- `app/samantha_agent.py`
- `tests/test_lekarna_service.py`
- `data/lekarna/domaci_leky.csv`
- `data/lekarna/README.md`
- `memory/projects/lekarna_domaci_leky.md`

Overeni:
- `.venv/bin/python -m py_compile app/lekarna/__init__.py app/lekarna/models.py app/lekarna/service.py app/lekarna/tools.py app/samantha_agent.py`
- `.venv/bin/python -m unittest tests.test_lekarna_service`
- `.venv/bin/python -m unittest discover -s tests`
- Vysledek: `Ran 151 tests ... OK`.

Bezpecnost / neukladat:
- Neukladat zdravotni citlive udaje nad ramec lokalni evidence bez vyslovneho souhlasu.
- Tool nesmi doporucovat davkovani.
- Tool nesmi tvrdit, ze lek je vhodny pro konkretniho cloveka bez overeni.
- U deti, tehotenstvi, chronickych nemoci, alergii, kombinaci leku a silnych/trvajicich
  potizi vzdy smerovat na pribalovy letak, lekarnika nebo lekare.
- Polozky bez expirace, bez krabicky, s nejistym nazvem nebo `nutno_overit=ano`
  brat jen jako inventarni kandidaty, ne jako doporuceni k pouziti.
