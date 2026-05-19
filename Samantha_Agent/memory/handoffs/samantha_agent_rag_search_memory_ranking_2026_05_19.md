Nazev: Samantha Agent/RAG - vylepsene search_memory ranking a vystup
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Navazani na prioritu `Samantha Agent/RAG`.
- Cilem bylo zlepsit textove RAG-like vyhledavani nad markdown pameti bez embeddings.

Co je hotove:
- `search_memory` uz vraci nejlepsi snippet jednou za soubor, aby jeden soubor nezaplavil vysledky vice odstavci.
- Tokenizace lepe pracuje s nazvy souboru a podtrzitky, napr. `search_memory`, `email_readonly_oauth`.
- `read-only` a `readonly` se pri hledani potkavaji pres jednoduchy alias.
- Ranking vic vazi shody v nazvu souboru a miri na konkretnejsi vysledky.
- Stare handoffy jsou utlumeny, pokud se Mila vyslovne nepta na handoff.
- Markdown tabulky a delsi odrazkove bloky se pri indexaci deli po radcich, takze `ACTIVE_PROJECTS.md` vraci konkretni radek projektu misto cele tabulky.
- Vystup `search_memory_text` zkracuje dlouhe snippety.
- Doplneny testy v `tests/test_memory_store.py`.

Co neni hotove:
- Nejde o vektorovou databazi ani embeddings.
- Neprobehl live API test pres `.venv/bin/python -m app.samantha_agent ...` v teto relaci.

Dalsi krok:
- Udelat rucni/live retest pres Samanthu: dotazy typu `Pouzij search_memory a najdi kontext k Samantha Agent/RAG` a `Najdi email read-only workflow`.
- Pokud budou vysledky porad sumet, dalsi krok je pridat typ zdroje do vystupu a volitelny filtr `projects`, `handoffs`, `technical`.
- Embeddings resit az po rozhodnuti, ze vylepsene textove vyhledavani nestaci.

Zmenene nebo relevantni soubory:
- `app/memory_store.py`
- `tests/test_memory_store.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Overeni:
- `.venv/bin/python -m unittest tests.test_memory_store` proslo: 13 testu OK.
- `.venv/bin/python -m unittest discover -s tests` proslo: 106 testu OK.
- `.venv/bin/python -m compileall app tests/test_memory_store.py` proslo.
- Rucni kontrola `search_memory_text('Samantha Agent RAG search_memory ranking')` vraci konkretni RAG polozky z `MEMORY_INDEX.md`, noveho/starsiho RAG handoffu a konkretni radek `ACTIVE_PROJECTS.md`.
- Rucni kontrola `search_memory_text('email read-only')` dava pred starymi handoffy `projects/email_readonly_oauth.md`.

Bezpecnost / neukladat:
- Neukladat API klice, tokeny ani `.env`.
- Neukladat plny obsah e-mailu ani plne URL z e-mailu do memory.
