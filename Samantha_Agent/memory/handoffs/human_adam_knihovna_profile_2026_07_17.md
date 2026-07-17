Nazev: Human–Adam – druhý pracovní profil Knihovna
Priorita: 1
Stav: rozpracované, implementace hotová, čeká na checkpoint a živý retest
Pripomenout pri startu: ano
Datum: 2026-07-17

Co se resilo:

- Bezpečné použití r-Adama pro jiný projekt bez ruční záměny vlákna, workspace,
  TVBCP a checkpointu.
- První pilot dvou pracovních profilů: původní `Human–Adam` a nový `Knihovna`.
- Zachování dosavadního Human–Adam vlákna a privátního workspace bez migrace.

Co je hotove:

- Nový profilový router drží každý profil jako jeden celek: identita, vlákno,
  izolovaný workspace, TVBCP a deployment receipt/diagnostic.
- Knihovna má vlastní developer instrukce a TVBCP `knihovna_cockpit.txt`.
- UI má výběr pracovního profilu a samostatné potvrzované tlačítko `Přepnout`.
- Rozepsaný pokyn se při přepnutí nemaže; UI přepnutí odmítne.
- Server odmítá přepnutí během tahu, aktivní operace nebo deploymentu, při
  nejistém doručení, dirty workspace, čekajícím WIP checkpointu, Git remote nebo
  divergenci.
- Čistý starší cílový workspace lze bezpečně fast-forwardovat z `main`.
- Deployment je po celou operaci připoutaný ke konkrétnímu profilu, takže účtenka
  po restartu nemůže přeskočit k jinému vláknu.
- Původní importní cesta `HUMAN_ADAM` zůstává kompatibilní.
- Read-only kontrola potvrdila aktivní profil Human–Adam, zachované existující
  vlákno a zarovnaný workspace.
- Kanonická quality gate byla rozšířena o nový modul/testy a prošla 734 testy;
  prošly i Python, oba JavaScripty, shell a `git diff --check`.

Co neni hotove:

- Změny nejsou commitnuté ani pushnuté.
- Běžící Cockpit používá dosavadní nasazenou verzi; nový přepínač zatím není živý.
- Reálné vlákno a workspace Knihovny ještě nebyly vytvořené.
- Nebyl proveden živý obousměrný smoke test na Macu ani iPhonu.

Dalsi krok:

- Po Mílově rozhodnutí cíleně zkontrolovat diff, commitnout a pushnout tento
  tematický celek, restartovat Cockpit a ověřit aktivní Human–Adam.
- Potom bez změny soukromých dat přepnout Human–Adam → Knihovna, otevřít TVBCP,
  poslat krátký neškodný pokyn a při čistém workspace přepnout zpět.

Navrhovane dalsi kroky:

- Po úspěšném smoke testu zapsat do obou TVBCP pouze redigovaný důkaz.
- Další profily přidávat až po ověření tohoto dvouprofilového pilotu.
- Obecné tlačítko `Nový profil` zatím neimplementovat.

Zmenene nebo relevantni soubory:

- `human_adam_profiles.py`
- `human_adam_service.py`
- `human_adam_workspace.py`
- `human_adam_deploy.py`
- `human_adam_ui.py`
- `cockpit.py`
- `cockpit_quality_gate.py`
- `test_human_adam_profiles.py`
- `test_human_adam_ui.py`
- `test_cockpit_quality_gate.py`
- `knihovna_cockpit.txt`
- `architektura_komunikace_samantha.txt`

Bezpecnost / neukladat:

- Neukládat texty soukromých článků, přílohy, osobní metadata, obsah koše,
  thread ID, celé chaty, tokeny ani privátní cesty.
- Nepřepínat profil při nejistém doručení nebo rozpracovaném workspace.
- Nevytvářet checkpoint, commit, push ani nasazení automaticky za r-Adama.
- Soubory v `data/private/` a `data/session_autosave/` nikdy necommitovat.
