Nazev: Human-Adam - faze 0 a 0.1 pro registraci projektu a handoffu
Priorita: 1
Stav: ceka na prevzeti
Pripomenout pri startu: ano
Datum: 2026-07-19

Co se resilo:

- Odstraneni nutnosti zahajovat kazdy dosud nezaregistrovany projekt v terminalu.
- Bezpecna faze 0 primo v okne `Human-Adam -> Prace` pro registraci projektu,
  vychoziho handoffu a souvisejici projektove vazby vyvojoveho semaforu.
- Rozsireni velke napovedy pod otaznikem o postup faze 0 az 4.
- Faze 0.1 odstranuje nepravdivy predpoklad, ze registrovany projekt jeste nema
  zadnou existujici implementaci, bez pridani dalsi volby nebo kroku do UI.

Co je hotove:

- Pri volnem semaforu a cistem zarovnanem workspace muze aktivni profil otevrit
  formular `+ Zaregistrovat projekt / handoff`.
- Formular prijima jen kratky git-safe nazev, prioritu 1-3, cil a nejblizsi krok;
  odmita vice radku a znaky, ktere by mohly porusit Markdown registr.
- Prvni operace je read-only nahled. Nic nezapisuje a vraci presne dve cilove
  cesty spolu s potvrzovaci vetou
  `POTVRZUJI REGISTRACI PROJEKTU`.
- Potvrzena operace atomicky vytvori standardni vychozi handoff a prida projekt do
  `ACTIVE_PROJECTS.md` pouze v izolovanem workspace aktivniho profilu.
- Cockpit pro operaci docasne prevezme volny semafor a po uspesnem zapisu jej
  pripne ke stejnemu registrovanemu projektu a handoffu.
- Pri cizim WIP, aktivnim tahu, obsazenem semaforu, nezarovnanem workspace,
  kolizi nazvu nebo zmene revize operace selze uzavrene.
- Pomocny lock registru je ignorovany Gitem, takze skutecna faze 0 zanecha jen
  ocekavany projektovy registr a novy handoff.
- Faze 0 umi zaregistrovat uplne novy i jiz rozpracovany projekt, pokud jeste
  neni v registru. Vygenerovany handoff neutralne uvadi, ze dalsi planovana
  etapa nezacala; netvrdi, ze drivejsi implementace neexistuje.
- Napoveda `Prace -> ?` vysvetluje, ze projekt se registruje jen jednou a dalsi
  funkce, opravy a male etapy uvnitr nej nejsou nove projekty. Faze 0 sama
  nedela commit, push, prevzeti do `main` ani nasazeni.
- Puvodni faze 0 je nasazena v commitu `dcdbbdd`; faze 0.1 je pripravena v
  samostatne izolovane WIP vetvi.
- Pro fazi 0.1 proslo 98 cilenych testu. Cela kanonicka Cockpit quality gate
  prosla vcetne Python, JavaScript a shell syntaxe, `git diff --check` a 862 testu.

Co neni hotove:

- Oprava faze 0.1 zatim neni prevzata do `main`, nasazena ani zive proklikana.
- Faze 0 zamerne nevytvari commit ani push registrovaneho projektu; nasleduje bezny
  postup checkpointu a nasazeni ve fazich 1 az 4.
- Faze 0 nenahrazuje vyber jiz registrovaneho projektu. Pouziva se jen kdyz
  dlouhodobejsi projekt v nabidce jeste chybi.

Dalsi krok:

- Provest cerstvy audit jedineho WIP checkpointu, potvrzene prevzeti do `main`,
  push, rizeny restart a petibodovy smoke test.

Navrhovane dalsi kroky:

- Po nasazeni z profilu Knihovna rucne otevrit `Prace`, proverit napovedu a
  zaregistrovat existujici projekt `Rodinny kalendar / rodinna upozorneni`.
- Overit, ze se registrovany projekt a handoff okamzite objevi ve vazbe semaforu a ze
  tlacitko checkpointu pracuje se stejnym profilem.
- Zadnou automatickou tvorbu projektu z volneho chatoveho textu nepridavat bez
  nove provozni potreby a samostatneho navrhu.

Zmenene nebo relevantni soubory:

- `.gitignore`
- `app/project_continuity.py`
- `app/communication/development_semaphore.py`
- `app/communication/human_adam_profiles.py`
- `app/communication/human_adam_ui.py`
- `app/cockpit.py`
- `tests/test_project_continuity.py`
- `tests/test_development_semaphore.py`
- `tests/test_human_adam_profiles.py`
- `tests/test_human_adam_ui.py`
- `tests/test_cockpit.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/handoffs/human_adam_project_bootstrap_phase0_wip_2026_07_19.md`

Bezpecnost / neukladat:

- Do poli faze 0 ani do Git handoffu neukladat hesla, tokeny, API klice,
  soukrome texty, osobni udaje ani absolutni private cesty.
- Pri chybe zachovat semafor a workspace; nepouzivat reset, rebase, force push
  ani rucni mazani vytvorenych souboru bez samostatne kontroly.
