Nazev: Human-Adam Plan - napoveda rotace a postupne zaziti workflow
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-07-19

Co se resilo:

- Mila nechce pridavat dalsi vrstvu automatizace driv, nez bude bezpecne
  zazite soucasne ovladani profilu, kotvy, rotace vlaken, semaforu a WIP vetvi.
- Okno `Plan` a bezpecna rotace profiloveho vlakna jsou funkcni, ale postup je
  uz prilis slozity na zapamatovani bez prime napovedy.
- Schvalena je pametova berlicka dostupna pod tlacitkem `?` primo v okne `Plan`.

Co je hotove:

- Schvalen obsah napovedy: bezna prace s Planem, kdy rotovat, presny postup
  rotace, nejcastejsi blokery, nouzovy postup a upozorneni, ze stare vlakno se
  nemaze.
- Schvaleno poradi dalsi prace:
  1. implementovat napovedu `?` v okne `Plan`;
  2. spolecne podle ni projit jedno cvicne overeni;
  3. nekolik dni pouzivat semafor, rotaci a audit vetvi v beznem provozu;
  4. teprve potom vyvijet kontrolu aktualnosti projektovych handoffu.
- Vyvoj prvniho kroku je izolovany ve vetvi
  `wip/human-adam-plan-help-20260719` a globalni semafor vlastni terminal.
- Napoveda `?` je implementovana jako lokalni rozbalovaci karta v hlavicce
  okna `Plan`; obsahuje beznou praci, duvody rotace, sestikrokovy postup,
  reseni blokeru a nouzovy navrat.
- Otevreni a zavreni meni jen atributy `hidden` a `aria-expanded`; nevola API
  a neobsahuje zadne akcni tlacitko rotace.
- Cilenych 49 UI testu proslo.
- Cela Cockpit quality gate prosla: Python, JavaScript a shell syntaxe a 825 testu.
- Tento handoff je soucasti jedineho WIP checkpointu na vetvi
  `wip/human-adam-plan-help-20260719`.
- Checkpoint `5052a4c` byl potvrzenym fast-forwardem prevzaty do `main`, pushnuty
  na GitHub a Cockpit byl rizene restartovany.
- Po restartu bezi jedina instance pod novym PID; zakladni smoke test vsech peti
  endpointu prosel a nasazene HTML obsahuje tlacitko i cely krokovy navod.
- Mila rucne potvrdil, ze napoveda `Plan -> ?` je v poradku.

Co neni hotove:

- Cvicna rotace a nekolikadenni provozni zaziti jeste neprobehly.
- Audit aktualnosti handoffu je pouze schvaleny budouci smer; nema se nyni
  implementovat ani spojovat s touto malou UI zmenou.

Dalsi krok:

- Stejnym malym zpusobem doplnit napovedu `?` do okna `Prace`, potom soucasne
  workflow nekolik dni bezne pouzivat.

Navrhovane dalsi kroky:

- Doplnit regresni testy obsahu, pristupnosti, mobilniho layoutu a nulovych
  vedlejsich ucinku.
- Po checkpointu a nasazeni projit navod s Milou krok za krokem; nerotovat vlakno
  jen kvuli testu, pokud neni skutecne potreba.
- Kontrolu handoffu otevrit az po provoznim zaziti soucasnych funkci.

Zmenene nebo relevantni soubory:

- `app/communication/human_adam_ui.py`
- `tests/test_human_adam_ui.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:

- Otevreni nebo zavreni napovedy nesmi menit profil, kotvu, vlakno, TVBCP,
  workspace, semafor ani Git stav.
- Napoveda nesmi obsahovat soukrome texty, identifikatory vlaken, absolutni
  cesty, tokeny ani tajemstvi.
- Rotace zustava oddelena auditni a presne potvrzovana akce; napoveda ji nikdy
  nesmi spustit.
