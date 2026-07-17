Nazev: Human–Adam – druhý pracovní profil Knihovna
Priorita: 1
Stav: hotovo, nasazeno a živě ověřeno
Pripomenout pri startu: ne
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
- Profilový celek byl commitnut a pushnut jako `6a2e205`; Cockpit byl bezpečně
  restartován a nová UI/API verze je živá.
- Živý test Human–Adam → Knihovna → Human–Adam prošel. Knihovna dostala vlastní
  čistý workspace bez remote, vlastní vlákno, správný TVBCP a jeden potvrzený
  read-only tah. Návrat zachoval původní Human–Adam vlákno i 54 zpráv.
- Zdrojový `main` a oba workspaces skončily na `6a2e205`, čisté, bez Git remote,
  WIP checkpointu nebo nejistého doručení. Aktivní je opět Human–Adam.

Co neni hotove:

- Nebyl proveden samostatný vizuální klikací test přepínače na iPhonu; backend,
  lokální UI přítomnost a obousměrná izolace jsou však živě potvrzené.
- Obecný editor nebo zakládání dalších profilů z UI záměrně neexistuje.

Dalsi krok:

- Pro další knihovní úkol v Human–Adam vybrat `Knihovna`, stisknout `Přepnout`
  a pokračovat v jejím vlastním vlákně. Po dokončení se vrátit jen při čistém
  workspace a bez čekajícího WIP checkpointu.

Navrhovane dalsi kroky:

- Při prvním použití na iPhonu pouze posoudit čitelnost přepínače.
- Další profily přidávat až podle skutečné potřeby.
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
