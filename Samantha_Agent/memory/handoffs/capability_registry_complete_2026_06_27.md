Nazev: Capability registry - plne pokryti agent toolu
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-27

Co se resilo:
- Dokoncoval se skutecny capability registry v kodu jako zaklad robustnejsi
  Samanthy bez zbytecne byrokracie.
- Cilem bylo, aby vsechny existujici Samantha `@function_tool` mely registrovany
  capability zaznam s rizikem, ctenim/zapisem, potvrzovaci politikou, voice/mobile
  pravidlem a auditni politikou.
- Prace navazovala na low-friction filozofii: bezne read-only a nizkorizikove
  operace nemaji zbytecne brzdit, ale external send, destructive, private export
  a systemove zmeny zustavaji potvrzovane.

Co je hotove:
- Capability registry je na `main` kompletni pro aktualni agent tooly.
- Finalni capability audit hlasi:
  - `Agent tools: 81`
  - `Capability registry records: 84`
  - `Registry-covered agent tools: 81/81`
  - `Critical/action-write missing records: 0`
  - `Action/review missing records: 0`
  - `Read-only or low-risk missing records: 0`
  - `Agent tools missing capability records: None`
- Runtime uz capability registry pouziva v promptu pres kompaktni runtime policy
  sekci pro potvrzovane schopnosti.
- Doplneny byly postupne davky:
  - pamet a systemove reporty,
  - e-mailova read/private vrstva,
  - action/review registry,
  - knowledge inbox, iPhone shortcuts status a Quick Notes,
  - backup/workflow preview a listing,
  - Lekarna read-only/preview/staging,
  - reminders/media/document-vault read-only tooly.
- Posledni relevantni commity na `main`:
  - `366ef28 Register memory report capabilities`
  - `cd98208 Register email read capabilities`
  - `69adba8 Use capability registry in runtime policy`
  - `9c92bf7 Register inbox and quick note capabilities`
  - `6778ff5 Register backup workflow capabilities`
  - `dc80d32 Register lekarna preview capabilities`
  - `6e041a0 Complete low risk capability registry coverage`
- Overeni pred ukoncenim tematu:
  - `109 tests OK`
  - `git_safety_check` zeleny
  - `git_push_guard.py` zeleny
  - `git status` cisty, `main` synchronni s `origin/main`

Co neni hotove:
- Registry je zatim hlavne auditni a promptova/runtime-policy vrstva.
- Programova enforcement brana pred samotnym volanim toolu jeste neni hotova.
- Workflow command registry a capability registry jeste nejsou jeden spolecny
  zdroj pravdy.
- Zaloha Samanthy je starsi nez 3 dny; posledni uspesna recovery zaloha je
  `2026-06-23`.

Dalsi krok:
- Prejit na recovery zalohu: pripojit externi disk / sifrovany kontejner a spustit
  standardni backup workflow.

Navrhovane dalsi kroky:
- Bezprostredne: udelat recovery zalohu, protoze backup status hlasi stav starsi
  nez 3 dny.
- Udrzovaci pravidlo: pri kazdem novem Samantha toolu pridat ve stejnem PR/commitu
  capability registry zaznam a test.
- Pozdeji pridat test, ktery nedovoli novy `@function_tool` bez registry zaznamu.
- Pozdeji zvazit programovou enforcement branu podle registry pro rizikove tooly.
- Pozdeji sjednotit workflow command registry a capability registry, aby se
  shellove workflow politiky negenerovaly rucne na dvou mistech.

Zmenene nebo relevantni soubory:
- `app/capabilities/models.py`
- `app/capabilities/registry.py`
- `app/capabilities/runtime_policy.py`
- `app/capability_audit.py`
- `app/samantha_agent.py`
- `tests/test_capability_models.py`
- `tests/test_capability_registry.py`
- `tests/test_capability_runtime_policy.py`
- `tests/test_capability_audit.py`
- `scripts/git_push_guard.py`
- `memory/technical/capability_routing_rules.md`
- `memory/infrastructure/git_checkpoint_protocol.md`

Bezpecnost / neukladat:
- Capability registry nesmi obsahovat tokeny, hesla, cele e-maily, soukrome texty
  ani konkretni citliva data.
- Registry popisuje tridy schopnosti, typy cteni/zapisu a rizika, ne obsah
  soukromych souboru.
- Push bez dalsiho dotazu zustava povoleny jen pro rutinni `git push origin main`
  po zelenem `git_push_guard.py`; force push, jina vetev, mazani vetvi/tagu a
  private data zustavaji mimo tuto vyjimku.
