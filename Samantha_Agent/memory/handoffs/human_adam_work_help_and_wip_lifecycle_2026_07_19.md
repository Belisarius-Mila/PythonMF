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
- Rucni retest potvrdil spravny obsah, ale odhalil, ze napoveda `Prace -> ?`
  rolovala uvnitr maleho vnitrniho okna a byla hur citelna nez napoveda `Plan`.

Co je hotove:

- Schvaleny rozsah navodu:
  - rozdil mezi semaforem, WIP vetvi, worktree a Codex vlaknem;
  - bezny vyvoj z r-Adama;
  - vyvoj z terminaloveho Adama;
  - vyznam stavu zivotniho cyklu vetvi;
  - reseni blokace semaforu, checkpointu, nasazeni a zastaraleho workspace;
  - nouzove pravidlo bez mazani, resetu, rebase a force push.
- Puvodni obsahova verze byla nasazena z vetve
  `wip/human-adam-work-help-20260719` jako commit `e1bc193`.
- Ergonomicka oprava je izolovana ve vetvi
  `wip/human-adam-work-help-layout-20260719` a globalni semafor vlastni terminal.
- Tlacitko `?` a staticka napoveda jsou implementovane v hlavicce okna `Prace`;
  otevreni a zavreni meni jen `hidden` a `aria-expanded`.
- Plan i Prace sdileji stejne male CSS komponenty napovedy; nevznikla nova
  backendova ani API vrstva.
- Napoveda `Prace` uz nema vlastni omezeni `max-height` ani vnitrni scrollbar.
  Ma prirozenou plnou vysku a roluje se cely velky obsahovy panel `Prace`, stejny
  zpusob jako u velkeho panelu `Plan`.
- Cilenych 50 UI testu proslo.
- Cela Cockpit quality gate prosla: Python, JavaScript a shell syntaxe a 826 testu.
- Checkpoint `e1bc193` byl potvrzenym fast-forwardem prevzaty do `main`, pushnuty
  na GitHub a Cockpit byl rizene restartovany.
- Nova instance bezi pod novym PID; petibodovy smoke test prosel a nasazene HTML
  obsahuje tlacitko `?`, oba vyvojove postupy, stavy vetvi i nouzove pravidlo.
- Ergonomicka oprava i regresni test jsou pripravene do jednoho WIP checkpointu
  na vetvi `wip/human-adam-work-help-layout-20260719`.
- Ergonomicky checkpoint `20c64a7` byl po cerstvem auditu potvrzenym
  fast-forwardem prevzaty do `main` a pushnuty na GitHub bez merge commitu nebo
  prepisu historie.
- Cockpit byl rizene restartovany z PID `27623` na PID `33066`; nova instance ma
  code stamp `15c51d12ca51ff0e` a vsech pet smoke kontrol proslo.
- Zive HTML potvrzuje velky `.work-panel-body`, napovedu bez puvodniho
  `max-height` a pritomnost celeho textu navodu.

Co neni hotove:

- Zbyva Mílův rucni vizualni retest velkeho zobrazeni na Macu nebo iPhonu.
- V teto Codex relaci nebyl dostupny lokalni prohlizec pro obrazovou kontrolu;
  zive nasazeni bylo overeno HTML kontraktem a smoke testem.

Dalsi krok:

- Rucne otevrit `Prace -> ?` a overit, ze se napoveda zobrazuje jako velky panel
  bez maleho vnitrniho rolovaciho okna.

Navrhovane dalsi kroky:

- Po nasazeni rucne overit, ze se napoveda roluje jako cely velky panel a nema
  maly vnitrni scrollbar; test nema menit semafor.
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
