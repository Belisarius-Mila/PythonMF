Nazev: Globalni vyvojovy semafor a blokace nasazeni pri cizim WIP
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-07-19

Co se resilo:

- Bezpecny soubeh vyvoje mezi profilem Human-Adam, profilem Knihovna a
  terminalovym Adamem.
- Jeden trvaly vlastnik zapisu, zatimco ostatni profily mohou zustat read-only.
- Fail-closed checkpoint a nasazeni pri cizim nebo neoverenem WIP.

Co je hotove:

- Soukromy globalni development lease ma revizi, vlastnika, tema, zakladni commit
  a rezimy `active`, `paused` a `free`; samovolne nevyprsi.
- Atomicky souborovy zamek brani dvema procesum soucasne prevzit stejnou revizi.
- Cockpit umi semafor prevzit pro aktivni profil nebo terminal, pozastavit,
  obnovit a uvolnit.
- Human-Adam i Knihovna dostavaji pred kazdym tahem autoritativni blok
  `writable=true|false`; bez vlastnictvi maji zustat striktne read-only.
- Checkpoint vyzaduje aktivni vlastnictvi semaforu zvolenym profilem.
- Audit a nasazeni kontroluji aktivni vlastnictvi a cizi dirty workspace,
  lokalni WIP checkpoint i rozvetveny workspace.
- Uvolneni je povolene jen pri cistych profilovych workspaces a cistem zdrojovem
  `main`; po uspesnem cistem nasazeni se lease uvolni automaticky.
- Cela Cockpit quality gate prosla: Python, JavaScript a shell syntaxe a 815 testu.

Co neni hotove:

- WIP v `wip/global-development-semaphore-20260719` zatim neni prevzaty do
  `main`, nasazeny ani zive otestovany v Cockpitu.
- V teto Codex relaci nebyl dostupny prohlizec pro klikaci a obrazovou kontrolu.
- Rucne spusteny primy `git push` z terminalu muze Cockpitovy deployment guard
  technicky obejit.

Dalsi krok:

- Po samostatnem potvrzeni auditovat a prevzit tuto WIP vetev do `main`, rizene
  nasadit Cockpit a zive overit prevzeti, pozastaveni, read-only druhy profil,
  checkpoint, blokaci ciziho WIP a ciste uvolneni.

Navrhovane dalsi kroky:

- Samostatne navrhnout verzovany terminalovy deployment guard, ktery pred
  commitem/pushem/nasazenim overi stejnou soukromou lease a vsechny registrovane
  workspaces.
- Jako prisnejsi variantu posoudit kontrolovany Git `pre-push` hook. Hook se nema
  instalovat automaticky ani potichu; nejdriv musi mit instalacni/auditni workflow,
  fail-closed chovani, testy a jasny nouzovy postup bez mazani nebo resetu WIP.
- Nezavadet automaticky rebase, merge, reset, takeover ciziho WIP ani automaticke
  vyprseni vlastnika.

Zmenene nebo relevantni soubory:

- `app/communication/development_semaphore.py`
- `app/communication/human_adam_profiles.py`
- `app/communication/human_adam_service.py`
- `app/communication/human_adam_deploy.py`
- `app/communication/human_adam_ui.py`
- `app/cockpit.py`
- `scripts/cockpit_quality_gate.py`
- `tests/test_development_semaphore.py`
- `tests/test_human_adam_profiles.py`
- `tests/test_human_adam_ui.py`
- `tests/test_cockpit.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:

- Do Gitu neukladat obsah konverzaci, plna vlaknova ID, soukrome cesty, tokeny,
  tajemstvi ani soukromy stav lease.
- Semafor ani cizi WIP neprepisovat automaticky.
- Git hook neinstalovat a zadny primy push neblokovat mimo samostatne potvrzeny
  a otestovany navazujici krok.
