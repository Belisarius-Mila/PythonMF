Nazev: Architektura komunikace Samantha – kanonická smlouva a první checkpoint
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-07-13

Co se resilo:

- Sjednocení plného terminálového Adama a Cockpitu nad jedním trvalým Codex
  app-serverem a jedním konverzačním vláknem.
- Rozdělení rolí Cockpit Mac/iPhone, vývojový terminál a nezávislý nouzový
  terminálový režim.
- Založení dlouhodobého projektového TVBCP jako human–machine smlouvy.
- Pravidlo budoucího odstranění starých komunikačních větví po prokázání nové
  cesty.

Co je hotove:

- Kanonická smlouva je v
  `memory/tvbcp/architektura_komunikace_samantha.txt`.
- Projektová pravidla TVBCP jsou v `memory/technical/project_tvbcp_rules.md` a
  doplněná do `AGENTS.md`.
- TVBCP je propojený s `MEMORY_INDEX.md` a `ACTIVE_PROJECTS.md`.
- Je přijato pravidlo: nový TVBCP vzniká jen po výslovné dohodě pro větší projekt
  nebo úlohu, nikoli pro každou malou opravu.
- Je přijato pravidlo: po ověření nové komunikace odstranit nepoužívaný watcher,
  TTY bridge, duplicitní LAB/Remote větve a související runtime/UI/start/test kód.
  Cenný nepoužívaný kód lze zachovat pouze mimo aktivní Cockpit a runtime; Git
  historie je výchozí archiv.

Co neni hotove:

- Trvalý app-server daemon a dva klienti zatím nejsou implementované ani
  otestované jako jeden kanonický systém.
- Současná terminálová relace nebyla migrována.
- Staré komunikační vrstvy nebyly odstraněny; do přijetí nové cesty zůstávají
  zmrazené, nikoli rozvíjené.
- Projektové TVBCP zatím nemají vlastní registr a výběr v novém Cockpit UI.

Dalsi krok:

- Připravit nejmenší izolovaný důkaz jednoho lokálního app-serveru, jednoho
  testovacího vlákna a dvou klientů bez zásahu do současné relace a recovery
  cesty.

Navrhovane dalsi kroky:

1. Ověřit společnou historii, reconnect, restart/resume a replay událostí.
2. Ověřit zámek jednoho aktivního tahu a idempotentní odesílání.
3. Ověřit plnohodnotný samostatný terminálový failover bez Cockpitu/app-serveru.
4. Po automatických a ručních Mac/iPhone testech rozhodnout o migraci kanonické
   relace.
5. Až po přijetí nové cesty vytvořit inventuru legacy komunikace a provést
   samostatně kontrolované odstranění.

Zmenene nebo relevantni soubory:

- `memory/tvbcp/architektura_komunikace_samantha.txt`
- `memory/technical/project_tvbcp_rules.md`
- `memory/MEMORY_INDEX.md`
- `memory/ACTIVE_PROJECTS.md`
- `AGENTS.md`
- `app/codex_appserver.py`
- `app/cockpit.py`
- `scripts/samantha_codex.sh`

Bezpecnost / neukladat:

- Neukládat API klíče, tokeny, soukromé texty ani obsah private/autosave dat.
- Neodstraňovat staré komunikační vrstvy před splněním přejímacích testů a novým
  výslovným rozhodnutím Míly.
- Nezahrnout do checkpointu cizí untracked soubor `AuditCockpit56_M.txt`.
