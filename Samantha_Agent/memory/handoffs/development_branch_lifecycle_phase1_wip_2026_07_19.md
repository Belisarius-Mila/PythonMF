Nazev: Rizeni zivotniho cyklu WIP vetvi - prvni read-only faze
Priorita: 1
Stav: ceka na prevzeti
Pripomenout pri startu: ano
Datum: 2026-07-19

Co se resilo:

- Prvni programovatelna faze prevence zapomenutych a "suchych" vyvojovych vetvi.
- Bezpecne rozliseni aktivniho WIP, integrovane historie, patchoveho ekvivalentu,
  vedomeho archivu a vetve vyzadujici rucni kontrolu.
- Minimalni read-only ovladani v panelu `Prace` bez nafouknuti `cockpit.py`.

Co je hotove:

- Samostatne auditni jadro cte lokalni a `origin` reference, vztah k `main`,
  pripojene worktrees a aktivni archiv; zadny `fetch` samo nespousti.
- Pripojena nebo rozpracovana vetev je vzdy chranena a neni kandidat k uklidu.
- Kandidatem k pozdeji potvrzenemu uklidu muze byt pouze odpojena vetev, jejiz
  historie je v `main` nebo jejiz commity maji patchovy ekvivalent v `main`.
- Neoveritelny stav selhava uzavrene a vyzaduje rucni revizi.
- Verejny API vystup neobsahuje absolutni cesty worktrees.
- Existuje read-only CLI a registrovana workflow schopnost bez potvrzovaci brany.
- Cockpit ma samostatny GET endpoint a v panelu `Prace` tlacitko
  `Proverit WIP vetve`; UI nema zapisovou ani uklidovou akci.
- Sedm realnych Git scenaru a integracni kontrakty jsou pokryte testy.
- Cela Cockpit quality gate prosla: Python, JavaScript a shell syntaxe a 824 testu.
- Tento handoff je soucasti jedineho WIP checkpointu na vetvi
  `wip/development-branch-lifecycle-audit-20260719`.

Co neni hotove:

- WIP jeste neni prevzaty do `main`, nasazeny ani zive otestovany v Cockpitu.
- Prvni faze nic nemaze, neslucuje, nerebasuje ani automaticky nearchivuje.
- Audit zamerne neobnovuje sitove reference; uvadi, ze pracovuje s lokalnim
  stavem `origin/*`.
- Neni implementovana potvrzovana uklidova faze, grace period ani Git hook.

Dalsi krok:

- Provest potvrzene prevzeti tohoto jedineho WIP checkpointu do `main`, push,
  rizeny restart Cockpitu a read-only smoke test endpointu a panelu `Prace`.

Navrhovane dalsi kroky:

- Po zivem overeni navrhnout druhou fazi: stav `pozorovat`, grace period a
  dvoukrokovy uklid pouze pro znovu overene kandidaty.
- Terminalovy deployment guard nebo kontrolovany `pre-push` hook drzet jako
  samostatny navazujici ukol; neinstalovat jej automaticky.
- Automaticky rebase, reset, merge ani mazani vetvi nepridavat.

Zmenene nebo relevantni soubory:

- `app/development_branch_lifecycle.py`
- `scripts/development_branch_audit.py`
- `app/workflows/commands.py`
- `app/cockpit.py`
- `app/communication/human_adam_ui.py`
- `scripts/cockpit_quality_gate.py`
- `tests/test_development_branch_lifecycle.py`
- `tests/test_workflow_commands.py`
- `tests/test_cockpit.py`
- `tests/test_human_adam_ui.py`
- `tests/test_cockpit_quality_gate.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:

- Do Gitu neukladat soukrome cesty, obsah konverzaci, private stav semaforu,
  tokeny, tajemstvi ani soubory z `data/session_autosave/`.
- Zadnou vetev ani worktree nemenit nebo mazat bez samostatneho presneho
  potvrzeni a cerstveho auditu.
