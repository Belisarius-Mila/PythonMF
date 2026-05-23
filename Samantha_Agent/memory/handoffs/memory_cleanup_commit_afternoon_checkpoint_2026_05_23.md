Nazev: Memory cleanup - checkpoint rozdelaneho commitoveho odpoledne
Priorita: A1+
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-05-23

Co se resilo:
- Navazuje se na commitove odpoledne a pravidlo handoff compression per project.
- Cilem je uklidit `MEMORY_INDEX.md`, projektove memory soubory a aktivni
  navazovani tak, aby Samantha/Codex pri startu neskakal do starych mezistavu.
- Nejde o mazani handoffu; stare handoff soubory zustavaji fyzicky v
  `memory/handoffs/` jako auditni historie.
- Tato davka byla commitnuta a pushnuta jako
  `ef15589 Clean up Samantha memory handoffs and RAG search`.

Co je hotove v teto rozpracovane davce:
- Dokumenty / private vault:
  - v indexu zustal aktivni aktualni handoff k fyzickemu tisku a Downloads intake;
  - stare dokumentove handoffy jsou shrnute jako historicke v
    `projects/document_management_private_vault.md`.
- Lekarna:
  - stare importni/webove mezistavy byly odstranene z aktivnich pripominek;
  - historicke handoffy byly doplneny do `projects/lekarna_domaci_leky.md` a
    `projects/lekarna_web_app.md`.
- PictNew / VocabularyIT:
  - stare batch mezistavy byly odstranene z aktivnich pripominek;
  - `projects/pictnew_vocabulary_image_pipeline.md` ma kanonicky stav, ze
    VocabularyIT vlna je hotova, 125 obrazku je v `Pict/`, mapping je aplikovany,
    audit je cisty a git checkpoint existuje jako
    `851b347 Apply VocabularyIT picture mapping updates`;
  - `ACTIVE_PROJECTS.md` uz neobsahuje neaktualni krok "udelat git checkpoint".
- Tomik video / FamilyVideoOrganizer:
  - stare iMovie/PDF mezistavy byly odstranene z aktivnich pripominek;
  - `projects/tomik_video_imovie.md` ma kanonicky stav, ze aktualni smer je
    `FamilyVideoOrganizer` a dalsi krok je soukromy realny `videos-data.js` a
    balicek mimo git.
- E-mail read-only / Email Cases:
  - stare iCloud, case, triage, archive a fulltext mezistavy byly odstranene z
    aktivnich pripominek;
  - `projects/email_readonly_oauth.md` ma kanonicky stav se soucasnymi iCloud,
    triage/case/archive/fulltext a Seznam read-only schopnostmi;
  - lokalni Seznam `.env` je vyplneny mimo git a memory;
  - read-only Seznam smoke test hlavicek 2026-05-23 prosel bez vypisu predmetu,
    adres, tel nebo URL.
- Samantha Agent/RAG:
  - `samantha_core.md` ma aktualni kanonicky stav RAG vrstvy, `search_memory`,
    `memory_status`, cache/index a dalsi realny krok;
  - stare RAG mezistavy uz nejsou aktivni `[PRIPOMENOUT]` polozky v
    `MEMORY_INDEX.md`, zustavaji jen historicky dohledatelne;
  - `search_memory` ma doplneny typ zdroje ve vystupu a volitelny filtr
    `source_type` pro `core`, `projects`, `handoffs`, `technical` a dalsi
    slozky;
  - lokalni smoke test `search_memory_text` 2026-05-23 bez OpenAI API prosel
    pro RAG, `core`, `projects`, `handoffs` i `email read-only workflow`;
  - `.venv/bin/python -m unittest tests.test_memory_store` proslo: 15 testu OK;
  - `.venv/bin/python -m compileall app tests/test_memory_store.py` proslo;
  - `.venv/bin/python -m unittest discover -s tests` proslo: 233 testu OK;
  - pri full suite byl opraven casove krehky test
    `tests/test_email_archive_tools.py`, ktery cekal pevne datum 2026-05-19
    misto dnesniho data archivace.
- Automaticke opakujici se ukoly:
  - `projects/automated_recurring_tasks.md` ma aktualni kanonicky stav
    scheduleru, GitHub Actions a jednorazoveho ColorsAndNumbers sovího TTS
    tasku;
  - stare automatizacni mezistavy uz nejsou aktivni `[PRIPOMENOUT]` handoffy v
    `MEMORY_INDEX.md`, zustavaji historicky dohledatelne v projektove karte;
  - lokalni historie ukazuje commit `a640c05 Schedule ColorsAndNumbers owl TTS`;
  - lokalni HEAD ani pracovni strom neobsahuji
    `ColorsAndNumbers/web_colors_numbers/owl_230526.mp3`, takze vysledek GitHub
    Actions neni z lokalniho stavu potvrzeny;
  - lokalni dry-run `scripts/daily_3am.py --run-date 2026-05-23 --dry-run`
    prosel s runtime cestami v `/private/tmp`.

Git stav pri puvodnim checkpointu pred commitem:
- Branch tehdy: `main...origin/main`
- Zmenene soubory tehdy:
  - `Samantha_Agent/memory/ACTIVE_PROJECTS.md`
  - `Samantha_Agent/memory/MEMORY_INDEX.md`
  - `Samantha_Agent/memory/projects/document_management_private_vault.md`
  - `Samantha_Agent/memory/projects/lekarna_domaci_leky.md`
  - `Samantha_Agent/memory/projects/lekarna_web_app.md`
  - `Samantha_Agent/memory/projects/pictnew_vocabulary_image_pipeline.md`
  - `Samantha_Agent/memory/projects/tomik_video_imovie.md`
  - `Samantha_Agent/memory/projects/email_readonly_oauth.md`
  - `Samantha_Agent/memory/samantha_core.md`
  - `Samantha_Agent/memory/technical/project_capability_map.md`
  - `Samantha_Agent/app/memory_store.py`
  - `Samantha_Agent/app/samantha_agent.py`
  - `Samantha_Agent/tests/test_memory_store.py`
  - `Samantha_Agent/tests/test_email_archive_tools.py`
  - `Samantha_Agent/memory/projects/automated_recurring_tasks.md`
  - tento handoff

Co neni hotove:
- Puvodni memory cleanup davka je hotova, commitnuta a pushnuta.
- Infrastructure/network cleanup se dela navazujicim krokem po tomto commitu.

Dalsi krok:
- Tento checkpoint brat jako historickou auditni stopu k commitu `ef15589`.
- Pro dalsi praci navazovat z `ACTIVE_PROJECTS.md`, `MEMORY_INDEX.md` a
  konkretni projektove/infrastrukturni karty.

Navrhovane dalsi kroky:
- Dalsi audit po `ef15589`: infrastruktura/network reconnect.
- Po infrastructure cleanupu udelat samostatny maly commit, pokud vzniknou zmeny.

Zmenene nebo relevantni soubory:
- `Samantha_Agent/memory/MEMORY_INDEX.md`
- `Samantha_Agent/memory/ACTIVE_PROJECTS.md`
- `Samantha_Agent/memory/projects/document_management_private_vault.md`
- `Samantha_Agent/memory/projects/lekarna_domaci_leky.md`
- `Samantha_Agent/memory/projects/lekarna_web_app.md`
- `Samantha_Agent/memory/projects/pictnew_vocabulary_image_pipeline.md`
- `Samantha_Agent/memory/projects/tomik_video_imovie.md`
- `Samantha_Agent/memory/projects/email_readonly_oauth.md`
- `Samantha_Agent/memory/samantha_core.md`
- `Samantha_Agent/memory/technical/project_capability_map.md`
- `Samantha_Agent/app/memory_store.py`
- `Samantha_Agent/app/samantha_agent.py`
- `Samantha_Agent/tests/test_memory_store.py`
- `Samantha_Agent/tests/test_email_archive_tools.py`
- `Samantha_Agent/memory/projects/automated_recurring_tasks.md`

Bezpecnost / neukladat:
- Neukladat zadna soukroma data z dokumentu, lekarny, rodinnych videi, e-mailu,
  tokeny, hesla ani API klice.
- Handoff je jen navigacni a provozni checkpoint.
- Stare handoff soubory nemazat bez vyslovneho Milova souhlasu.
