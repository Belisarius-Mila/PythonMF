Nazev: Janička Cockpit - Rodinné projekty mezikrok
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-06-26

Co se resilo:
- Navrat k obrazovce `Janička` v Samantha Cockpitu.
- Rychly test stavajiciho Janička/Cockpit stavu a zahajeni dalsiho vyvoje.
- Slabe misto podle pameti bylo tlacitko `Rodinné projekty`, ktere predtim oteviralo rovnou jednu aplikaci bez lidskeho mezikroku.

Co je hotove:
- V `app/cockpit.py` pribyl modal `Rodinné projekty` pro Janičku.
- Tlačítko `Rodinné projekty` v Janičce ted otevre netechnicky mezikrok misto primeho spusteni jedne aplikace.
- Modal ma dve jasne volby:
  - `Rodinný výběr videí a fotek` otevre existujici `family-video-organizer`.
  - `Přehled projektů` otevre stavajici prehled projektu a zachova navratovou cestu zpet k Janičce.
- Doplnene testy v `tests/test_cockpit.py`, aby HTML obsahovalo novy modal a napojene funkce.

Co neni hotove:
- Neni jeste rucne proklikano Janou ani z jejiho realneho scenare.
- Janička zatim nema samostatny vyfiltrovany seznam jen rodinnych projektu; druha volba vede do obecneho prehledu projektu.
- UI stav `Adam cte / odpovida` zustava dalsi mozne zlepseni.

Dalsi krok:
- Rucne v Cockpitu kliknout `Janička` -> `Rodinné projekty`.
- Overit, ze se otevre novy mezikrok, ze `Rodinný výběr videí a fotek` otevira lokalni organizer a ze `Přehled projektů` vede do projektu s navratem k Janičce.

Navrhovane dalsi kroky:
- Okamzity: rucni UI retest noveho mezikroku v lokalnim Cockpitu.
- Volitelne potom: vyfiltrovat v Janičce samostatny seznam rodinnych projektu, aby Jana nevidela obecny technicky projektovy registr.
- Volitelne potom: zlepsit Adam chat stav na lidstejsi `Adam cte dotaz` / `Adam odpovida`.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/handoffs/janicka_cockpit_family_projects_modal_2026_06_26.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Overeni:
- `.venv/bin/python -m unittest tests.test_cockpit tests.test_adam_service` proslo: 187 testu OK.
- `.venv/bin/python -m py_compile app/cockpit.py` proslo; zustava starsi `SyntaxWarning` v dlouhem HTML stringu.
- Lokalni Cockpit byl restartovan a smoke check na `http://127.0.0.1:8770` pro `/`, `/api/status` a `/api/recovery/status` prosel.
- Běžící HTML obsahovalo `janickaFamilyModal`, `Rodinný výběr videí a fotek` a `openJanickaFamilyModal`.

Bezpecnost / neukladat:
- Handoff neobsahuje hesla, tokeny, API klice, cele e-maily, rodna cisla ani soukroma rodinna data.
- Pri commitu nepridavat cizi rozpracovane zmeny a nepouzivat `git add .`.
