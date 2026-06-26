Nazev: Capability registry - prioritni mezery zavrene a audit rozdeleny podle rizika
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-26

Co se resilo:
- Navazovalo se na robustnejsi vyvoj Samanthy bez zbytecne byrokracie.
- Cilem bylo mit maly skutecny capability registry v kodu a zavrit nejrizikovejsi
  mezery, aby audit rozlisoval schopnosti podle rizika, potvrzeni a provozniho
  rozsahu.

Co je hotove:
- Capability datovy model a registry existuji v kodu.
- Registry ma 28 zaznamu a capability audit hlasi `Priority missing capability records: None`.
- Capability audit je rozdeleny podle rizikove vrstvy:
  - kriticke/action-write mezery,
  - action/review mezery,
  - read-only nebo nizkorizikove mezery.
- Pokryte jsou hlavni rizikovejsi schopnosti:
  - git guard / push guard,
  - email/SMS odesilani a archivace,
  - dokumentovy vault import/reindex/final import/tisk/inbox cleanup,
  - backup restore a registrovane workflow prikazy,
  - Lekarna write flows,
  - image resize,
  - Downloads -> private knowledge inbox copy,
  - email triage reporty.
- Posledni relevantni commity na `main`:
  - `8e758b5 Add capability record model`
  - `7391c54 Add initial capability registry`
  - `2bb412b Report capability registry in audit`
  - `b371e44 Show capability registry coverage in audit`
  - `da99317 Register confirmed outbound capabilities`
  - `0e5c468 Register document reminder capabilities`
  - `c0c7cf6 Register document vault cleanup capabilities`
  - `f7728d9 Register workflow utility capabilities`
  - `daf29b8 Register priority inbox triage capabilities`

Co neni hotove:
- Registry zatim hlavne dokumentuje a audituje; neni jeste jednotne runtime
  rozhodovaci centrum pro vsechny tooly.
- Zbyva mnoho read-only nebo nizkorizikovych toolu bez samostatneho capability
  zaznamu.
- Zbyva postupne doplnit 14 action/review a 42 read-only nebo nizkorizikovych
  registry zaznamu, pokud bude davat smysl je pokryvat po malych davkach.

Dalsi krok:
- Rozhodnout, zda dalsi davka ma byt action/review registry, nebo read-only
  registry pro pamet/system reporty.

Navrhovane dalsi kroky:
- Dalsi prakticka davka muze byt action/review:
  `prepare_iphone_shortcut`, `build_email_case_from_uid`, `prepare_document_import`
  a podobne.
- Alternativne lze nejdriv doplnit read-only zaklad:
  `search_memory`, `memory_status`, `samantha_health_check`,
  `samantha_capability_audit`.
- Az potom zvazit runtime napojeni registry na jednotne rozhodovani o potvrzeni.

Zmenene nebo relevantni soubory:
- `app/capabilities/models.py`
- `app/capabilities/registry.py`
- `app/capability_audit.py`
- `tests/test_capability_models.py`
- `tests/test_capability_registry.py`
- `tests/test_capability_audit.py`
- `scripts/git_push_guard.py`

Bezpecnost / neukladat:
- Capability registry nesmi obsahovat tokeny, hesla, cele e-maily, soukrome texty
  ani konkretni citliva data.
- Registry popisuje tridy schopnosti, cesty a rizika, ne obsah soukromych souboru.
- Push bez dalsiho dotazu plati jen pro rutinni `git push origin main` po zelenem
  push guardu; force push, jine vetve a mazani zustavaji mimo tuto vyjimku.
