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

Aktualizace 2026-07-14:

- Přímý Unix WebSocket transport je implementovaný s `/rpc` a vypnutou
  kompresí, jak vyžaduje lokální `codex-cli 0.144.1`.
- Živý izolovaný probe prokázal dva klienty nad jedním persistovaným threadem,
  zachování kontextu, potvrzené doručení a následnou archivaci testovacího
  threadu.
- `app/communication/session_hub.py` drží kanonické thread ID, reconnect, jeden
  aktivní tah, idempotenci a fail-closed `delivery_unknown`.
- 34 cílených testů app-server/LAB/Remote/Session Hub prošlo.
- Není ještě hotový daemon controller ani nové textové Human–Adam UI.

Dalsi krok:

- Doplnit řízený daemon controller a první minimální textové Human–Adam UI nad
  hotovým Session Hubem bez přesunu doménové logiky do `cockpit.py`.

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
- `app/communication/session_hub.py`
- `scripts/codex_appserver_shared_thread_probe.py`
- `tests/test_communication_session_hub.py`
- `tests/test_codex_appserver_shared_thread_probe.py`
- `app/cockpit.py`
- `scripts/samantha_codex.sh`

Bezpecnost / neukladat:

- Neukládat API klíče, tokeny, soukromé texty ani obsah private/autosave dat.
- Neodstraňovat staré komunikační vrstvy před splněním přejímacích testů a novým
  výslovným rozhodnutím Míly.
- Nezahrnout do checkpointu cizí untracked soubor `AuditCockpit56_M.txt`.
