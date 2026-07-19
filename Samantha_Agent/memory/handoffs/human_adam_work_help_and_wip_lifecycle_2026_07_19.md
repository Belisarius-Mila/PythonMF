Nazev: Human-Adam Prace - napoveda semaforu a zivotniho cyklu WIP vetvi
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-07-19

Co se resilo:

- Mila rucne potvrdil, ze nasazena napoveda `Plan -> ?` je v poradku.
- Stejnou pametovou berlicku potrebuje okno `Prace`, kde se potkava globalni
  vyvojovy semafor, profilovy checkpoint/nasazeni a read-only audit WIP vetvi.
- Návod ma zjednodusit bezny provoz bez pridavani nove automatizace.

Co je hotove:

- Schvaleny rozsah navodu:
  - rozdil mezi semaforem, WIP vetvi, worktree a Codex vlaknem;
  - bezny vyvoj z r-Adama;
  - vyvoj z terminaloveho Adama;
  - vyznam stavu zivotniho cyklu vetvi;
  - reseni blokace semaforu, checkpointu, nasazeni a zastaraleho workspace;
  - nouzove pravidlo bez mazani, resetu, rebase a force push.
- Vyvoj je izolovany ve vetvi `wip/human-adam-work-help-20260719` a globalni
  semafor vlastni terminal.
- Tlacitko `?` a staticka rolovatelna karta jsou implementovane v hlavicce
  okna `Prace`; otevreni a zavreni meni jen `hidden` a `aria-expanded`.
- Plan i Prace sdileji stejne male CSS komponenty napovedy; nevznikla nova
  backendova ani API vrstva.
- Cilenych 50 UI testu proslo.
- Cela Cockpit quality gate prosla: Python, JavaScript a shell syntaxe a 826 testu.
- Tento handoff je soucasti jedineho WIP checkpointu na vetvi
  `wip/human-adam-work-help-20260719`.
- Checkpoint `e1bc193` byl potvrzenym fast-forwardem prevzaty do `main`, pushnuty
  na GitHub a Cockpit byl rizene restartovany.
- Nova instance bezi pod novym PID; petibodovy smoke test prosel a nasazene HTML
  obsahuje tlacitko `?`, oba vyvojove postupy, stavy vetvi i nouzove pravidlo.

Co neni hotove:

- Rucni vizualni retest na Macu nebo iPhonu je mozny az po nasazeni.

Dalsi krok:

- Rucne otevrit `Prace -> ?` a overit citelnost napovedy na Macu nebo iPhonu
  bez zmeny semaforu.

Navrhovane dalsi kroky:

- Po nasazeni rucne overit citelnost a spravnost postupu bez zmeny semaforu.
- Potom soucasne ovladani nekolik dni bezne pouzivat; nepridavat dalsi ochranu
  handoffu driv, nez bude workflow zazite.

Zmenene nebo relevantni soubory:

- `app/communication/human_adam_ui.py`
- `tests/test_human_adam_ui.py`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:

- Otevreni nebo zavreni napovedy nesmi volat API ani menit semafor, profil,
  workspace, checkpoint, nasazeni, vetev, worktree nebo Git.
- Kandidat k uklidu nesmi byt popsan jako automaticky mazana vetev.
- Navod nesmi obsahovat soukrome texty, identifikatory vlaken, absolutni cesty,
  tokeny nebo tajemstvi.
