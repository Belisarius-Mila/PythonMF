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

- Nové textové UI zatím neprošlo ručním Mac/iPhone testem ani restartem Cockpitu.
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
- První Human–Adam řez je hotový: privátní Unix proces controller, samostatné
  responzivní UI a kanonická relace v izolovaném workspace bez Git remote a sítě.
- Živý test s modelem `gpt-5.6-sol`, reasoning `high` potvrdil přesnou odpověď
  `KANON-14`, potvrzené doručení a resume stejného threadu po restartu app-serveru.
- Opraven je bezpečný lifecycle prázdného threadu, který Codex před prvním tahem
  ještě nepersistuje. Thread s historií se při resume chybě nikdy nenahrazuje.
- Plná Cockpit quality gate prošla: 672 testů včetně obou JavaScript syntaxí.
- Míla následně potvrdil první ruční Mac test textového Human–Adam UI jako
  úspěšný; kanonická relace zůstala připojená a izolovaný workspace čistý.
- Nasazen je ručně otevíraný read-only panel kanonického projektového TVBCP z
  izolovaného workspace; neumožňuje libovolnou cestu ani automatický refresh a
  jeho živý HTTP endpoint byl ověřen.
- Horní badge ukazuje počet pracovních změn. Brána po doplnění panelu má 673
  úspěšných testů.
- Reálný Human–Adam tah z TVBCP proběhl bez změn a s potvrzeným doručením;
  správně poznal čistý workspace a základní commit. Absence private backup
  metadat v izolovaném clone je nově výslovně označená jako záměrná, ne jako
  důkaz chybějící zálohy.
- Nasazen je panel `Práce`, který ukazuje pouze změněné cesty a Git stavy, a
  potvrzovaný lokální WIP checkpoint bez pushnutí. Workspace rozlišuje lokální
  commit před main od novějšího main a od skutečného rozvětvení.
- Souběžný veřejný Colors & Numbers audio commit byl bezpečně převzat. Source
  sync má úzký allowlist do 8 MiB jen pro dvě veřejné webové asset cesty; ostatní
  média a private/env zůstávají blokované. Plná brána má 677 testů.

Dalsi krok:

- Z iPhonu nebo Macu provést první omezený zápis pouze do TVBCP, ověřit jeden
  změněný soubor a vytvořit lokální WIP checkpoint. Další implementační krok je
  řízené převzetí zkontrolovaného checkpointu do `main`.

Navrhovane dalsi kroky:

1. Ručně ověřit společnou historii a restart/resume přes nové UI.
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
- `app/communication/local_runtime.py`
- `app/communication/human_adam_service.py`
- `app/communication/human_adam_ui.py`
- `scripts/codex_appserver_shared_thread_probe.py`
- `tests/test_communication_session_hub.py`
- `tests/test_human_adam_service.py`
- `tests/test_human_adam_ui.py`
- `tests/test_local_appserver_runtime.py`
- `tests/test_codex_appserver_shared_thread_probe.py`
- `app/cockpit.py`
- `scripts/samantha_codex.sh`

Bezpecnost / neukladat:

- Neukládat API klíče, tokeny, soukromé texty ani obsah private/autosave dat.
- Neodstraňovat staré komunikační vrstvy před splněním přejímacích testů a novým
  výslovným rozhodnutím Míly.
- Nezahrnout do checkpointu cizí untracked soubor `AuditCockpit56_M.txt`.
