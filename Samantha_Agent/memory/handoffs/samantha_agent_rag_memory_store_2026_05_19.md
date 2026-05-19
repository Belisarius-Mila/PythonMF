Nazev: Samantha Agent/RAG - prvni lokalni markdown memory store
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Pokracovani na priorite `Samantha Agent/RAG`.
- Cilem byl nejmensi prakticky krok od velke vlozene markdown pameti k jednoduche lokalni RAG-like vrstve.

Co je hotove:
- Pridan `app/memory_store.py`:
  - nacitani full markdown pameti,
  - kompakni startup kontext jen z `samantha_core.md`, `ACTIVE_PROJECTS.md` a `MEMORY_INDEX.md`,
  - textove vyhledavani v markdown pameti podle dotazu,
  - formatovany vystup pro tool `search_memory`.
- `app/samantha_agent.py` zachovava kompatibilni `load_memory()`, ale live agent v `ask_samantha()` pouziva `load_agent_memory()`.
- Instrukce agenta jsou upravene: startup kontext je kompakni a konkretni kontext se ma dohledavat pres `search_memory`.
- Doplnene testy v `tests/test_memory_store.py`.
- README obsahuje zakladni spusteni agenta a testu.
- Kratky live test pres `.venv/bin/python -m app.samantha_agent "Na cem mame pokracovat v Samantha Agent/RAG?"` probehl; agent odpovedel, ale spis navrhl dalsi metatest/checklist, coz ukazalo potrebu diagnostickeho toolu.
- Pridan tool `memory_status`, ktery bez cteni e-mailu a bez tajemstvi vraci pocet markdown souboru, velikost markdown/startup/plneho kontextu, projekty priority 1 a `[PRIPOMENOUT]` polozky.
- Live test `memory_status` pres Samanthu probehl prikazem `.venv/bin/python -m app.samantha_agent "Ukaz stav lokalni pameti Samanthy a aktivni priority. Pouzij memory_status."`.
- Pridan jednoduchy in-memory index/cache v `app/memory_store.py`: indexuje markdown snippety, termy ze snippetů a názvů souborů, počet souborů a velikost markdown paměti. Ve stejném procesu se znovu použije, dokud se nezmění seznam, velikost nebo `mtime_ns` `.md` souborů.

Co neni hotove:
- Zatim nejde o vektorovou databazi ani embeddings.
- `unittest discover` bez `-s tests` v tomto rozlozeni nenasel testy; spravny prikaz je `.venv/bin/python -m unittest discover -s tests`.

Dalsi krok:
- Dalsi technicky krok je zlepsit ranking/vystup `search_memory`, napr. limity delky snippetů, lepsi vahy pro nazvy souboru a filtrovani starych handoffu.
- Embeddings resit az po rozhodnuti, ze textove vyhledavani s cache nestaci.

Zmenene nebo relevantni soubory:
- `app/memory_store.py`
- `app/samantha_agent.py`
- `tests/test_memory_store.py`
- `README.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Overeni:
- `.venv/bin/python -m unittest tests.test_memory_store` proslo.
- `.venv/bin/python -m unittest tests.test_reminders_due tests.test_email_activity_state` proslo.
- `.venv/bin/python -m unittest discover -s tests` proslo: 97 testu OK.
- Po doplneni `memory_status` proslo `.venv/bin/python -m unittest discover -s tests`: 98 testu OK.
- Po doplneni index/cache proslo `.venv/bin/python -m unittest discover -s tests`: 100 testu OK.
- `.venv/bin/python -m compileall app tests/test_memory_store.py` proslo.
- Lokalni build agenta bez volani API ukazal 15 toolu vcetne `memory_status`.
- `load_agent_memory()` ma zhruba 17 KB, `load_memory()` zhruba 216 KB.
- Live `memory_status` pres Samanthu vratil 60 markdown souboru, startup kontext zhruba 17.5 KB a priority 1.
- Lokalni kontrola cache ukazala opakovane pouziti stejneho index objektu (`True`) a 1801 markdown snippetů.

Bezpecnost / neukladat:
- Neukladat API klice, tokeny ani `.env`.
- Neukladat plny obsah e-mailu ani plne URL z e-mailu do memory.
