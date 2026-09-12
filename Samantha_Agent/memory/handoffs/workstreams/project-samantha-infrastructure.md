<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-12 20:50 CEST

### Hotovo
- Zjednodušené Markdown instrukce i sladěné serverové prompty jsou pushnuté
  a nasazené do Cockpitu. Funkční commit: `2570a14715fe`.
- Human–Adam, Knihovna i lazy proudy používají společná pravidla pro potřebný
  kontext, dokončení autorizované práce, cílené ověření a kanonický zápis.
- Řízený restart a smoke 5/5 prošly; pracovní vlákno infrastruktury bylo
  úspěšně připojeno. Živý audit potvrdil `current` a čisté kopie 2/2.

### Rozhodnutí
- Mílův pokyn „Prosím dokonči p+n.“ autorizoval push a nasazení tohoto balíčku.
- DEVELOPMENT_CONTROL, private hranice a potvrzované Git/deploy operace
  zůstávají zachované. Při writable=false se projektové dokumenty nemění.

### Další krok
- Pokračovat v běžné práci v Cockpitu a posoudit praktičnost nových instrukcí.

### Navrhované další kroky
- Případný hlasový pilot a Agents API posoudit samostatně podle konkrétního přínosu.

### Rizika / otevřeno
- Testy a obnovené spojení dokládají nasazení a technickou kontinuitu;
  samy neměří kvalitu rozhodování modelu ani časovou úsporu.
- Provozní údaje jsou snapshot; při dalším dotazu na aktuální stav použít živý audit.

### Technický důkaz
- Registrovaný GitHub balíček odeslal oba commity. Plná brána: OK,
  1 555 testů (1 přeskočený), 556,7 s. Předchozí chyba velikosti písmene se neopakovala.
- Nasazení `2570a14715fe` ověřeno 2026-09-12 20:48 CEST; nový proces,
  otisk `d12a6e19e855247f`, rychlá brána 9,4 s, smoke 5/5.
- Živý audit 20:49 CEST: `verified_current`, main=origin, kopie 2/2 čisté,
  runtime připojený a nečinný, bez nejistého doručení a bez blokátorů.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovniho proudu: Samantha Infrastructure

Nazev: Samantha Infrastructure
Pracovni proud: project-samantha-infrastructure
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-09-12

Co se resilo:
- Sladění serverových instrukcí Cockpitu s dokončeným Markdown balíčkem.
- Odstranění rozporu mezi starým TVBCP zákazem a povinným projektovým zápisem.

Co je hotove:
- Hlavnim uzivatelskym rozhranim je Cockpit bezici na Macu; z iPhonu je
  dostupny pres soukromou Tailscale cestu.
- Codex app-server bezi lokalne pres privátní Unix socket. Neni primo vystaven
  do Tailscale ani do verejne site.
- Kazdy pracovni proud ma vlastni kontinuitu vlakna, pracovního kontextu,
  handoffu, TVBCP a izolovaneho workspace. Human-Adam a Knihovna zustavaji
  docasne kompatibilnimi adaptery; ostatni proudy pouzivaji lazy backend.
- Jeden aktivni tah, `client_message_id`, persistovany stav a
  `delivery_unknown` chrani proti soubehu a automatickemu opakovani nejasne
  doruceneho pokynu.
- `DEVELOPMENT_CONTROL` uděluje zapis pouze pro jeden vymezeny tah. Capability
  registry urcuje dostupne operace a jejich bezpecnostni rozsah.
- Human–Adam používá potvrzené mechanismy Cockpitu pro checkpoint a další
  operace. Terminálový Adam na main používá samostatný dávkový režim podle
  AGENTS.md; oprávnění jednoho prostředí se nepřenášejí do druhého.
- Projektova pamet rozlisuje TVBCP, handoff, autosave a redigovany live status.
  Promenlivy provozni stav se overuje zive; historicky snapshot jej nenahrazuje.
- Pri selhani Cockpitu nebo app-serveru zustava plnohodnotna terminalova
  recovery cesta pres `samantha`, Git, autosave a projektovou pamet.

Co neni hotove:
- Vyhodnocení praktičnosti instrukcí při následné běžné práci.
- WebMCP ani hlasový pilot nejsou tímto dokumentačním balíčkem implementovány.
- Dřívější provozní snapshoty níže jsou historické; aktuální dokončení je uvedeno nahoře.

Dalsi krok:
- Pokračovat v běžné práci; push, nasazení a obnovení spojení jsou ověřené.

Navrhovane dalsi kroky:
- Po aktivaci posoudit praktičnost instrukcí při běžné práci.
- Případný hlasový pilot posoudit samostatně; žádná automatická migrace architektury.

Zmenene nebo relevantni soubory:
- `app/communication/human_adam_workspace.py`
- `app/communication/human_adam_service.py`
- `app/communication/human_adam_profiles.py`
- `app/communication/legacy_tvbcp_migration.py` (jen instrukce pro čtení kontextu)
- `tests/test_communication_session_hub.py`
- `tests/test_human_adam_service.py`
- `../AGENTS.md` a `AGENTS.md`
- `memory/technical/session_recovery_rules.md`
- `memory/technical/project_tvbcp_rules.md`
- `memory/tvbcp/workstreams/project-samantha-infrastructure.md`
- `memory/tvbcp/architektura_komunikace_samantha.txt`
- `memory/infrastructure/operating_model.md`
- `memory/WORKSTREAMS.md`
- `memory/ACTIVE_PROJECTS.md`
- `app/communication/local_runtime.py`
- `app/codex_appserver.py`
- `app/communication/session_hub.py`
- `app/communication/human_adam_workstream_catalog.py`
- `app/communication/human_adam_workstream_memory.py`

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice, soukromy obsah ani identifikatory vlaken.
- App-server nevystavovat primo do site; vzdalene zpristupnovat pouze rizeny
  Cockpit.
- Nezaměnovat checkpoint, push a nasazeni a zadny z techto kroku nespoustet bez
  odpovidajiciho potvrzeni.
- Pri `delivery_unknown` pokyn automaticky neopakovat.

### Automatický checkpoint 2026-08-26 09:35 CEST

- Pracovní proud: `project-samantha-infrastructure`
- Hotovo: Samantha Infrastructure má stručný kanonický handoff a TVBCP se současnou architekturou, bezpečnostními hranicemi a otevřenými kroky
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 5.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/memory/handoffs/workstreams/project-samantha-infrastructure.md`, `Samantha_Agent/memory/tvbcp/workstreams/project-samantha-infrastructure.md`
- Commit: `Založit kanonickou paměť Samantha Infrastructure`
- Další krok: Potvrdit checkpoint, který dvojici transakčně doplní o první časovaný stav

### 2026-09-12 20:14 CEST — První balíček zjednodušení instrukcí

Hotovo:
- Oba AGENTS.md tvoří stručný vstup do práce. Nezměněný kontext se při
  pokračování znovu nečte; cílené ověření se bez důvodu neopakuje.
- Recovery návod obsahuje jediný postup/šablonu ručního handoffu s prioritou
  1–3, předností kanonického souboru a vazbou na povinný zápis do TVBCP.
- Popsány oddělené intervaly latest autosave (600 s) a historie (3600 s).

Rozhodnutí:
- Zachovat ochranu soukromých dat, zákaz neautorizovaného mazání, povinný
  projektový zápis i samostatné oprávnění k publikování a nasazení.
- Automatický terminálový commit neopravňuje model Human–Adam k vlastnímu
  commitu. Vždy platí aktuální DEVELOPMENT_CONTROL a mechanismy Cockpitu.
- Dřívější věta „Agents SDK bude základ budoucího agenta“ je historický plán;
  současná komunikace Human–Adam používá App Server. Existující SDK komponenty
  se tímto dokumentačním krokem nemění ani neruší.

Další krok:
- Po načtení nových instrukcí posoudit jejich praktičnost při další práci.

Navrhované další kroky:
- Samostatně sladit odpovídající serverové prompty Human–Adam; tento balíček
  je neupravuje ani nedokládá jejich změnu v již otevřeném vlákně.

Technický důkaz:
- 41 cílených testů prošlo; rychlá statická brána a kontrola odkazů prošly.
- Oba AGENTS.md mají celkem 125 řádků místo 262. Bezpečnostní návody,
  původní chronologické záznamy a aplikační kód zůstaly beze změn.
- Ověření dokládá konzistenci dokumentů; přínos pro chování modelu se posoudí
  při další práci, není odvozen jen ze zkrácení textu.
- Změněny jen Markdown dokumenty. Push a nasazení nejsou součástí zadání.

### 2026-09-12 20:28 CEST — Sladění serverových instrukcí Cockpitu

Hotovo:
- Společná pravidla se předávají Human–Adam, Knihovně i lazy pracovním proudům.
  Kontext se načítá podle potřeby; autorizovaný úkol zahrnuje ověření a povinný
  projektový zápis. Úspěšné ověření se bez nového důvodu neopakuje.
- Odstraněn starý zákaz samostatného TVBCP zápisu při milníku, který odporoval
  schválenému povinnému zápisu při dokončení vývoje.
- Soukromý historický kontext se znovu načítá jen při potřebě, změně či rozporu;
  jeho absence se nesmí nahrazovat domněnkou.

Rozhodnutí:
- Zápis pouze v povoleném vývojovém tahu do přesné kanonické dvojice aktivního
  proudu. Nejasná vazba blokuje uzavření; nový TVBCP vyžaduje výslovnou dohodu.
- Writable=false nepovoluje zápis projektových dokumentů. Private výjimka jej
  nerozšiřuje. Commit, checkpoint, push a nasazení zůstávají na mechanismu Cockpitu.
- Síťové, private a destruktivní hranice se nemění.

Další krok:
- Samostatně potvrdit nasazení do Cockpitu a ověřit instrukce při obnovení vlákna.

Navrhované další kroky:
- Při následné skutečné práci vyhodnotit praktičnost instrukcí. Neodvozovat
  z automatických testů zlepšení chování modelu nebo časovou úsporu.

Technický důkaz:
- 198 cílených testů prošlo. Plný běh: 1 555 testů, 1 554 prošlo; jediná
  chyba byla citlivost textového testu na velké písmeno. Po opravě pouze testu
  prošla dotčená sada 7/7 a závěrečná statická brána. Celý běh se neopakoval.
- Regresní test použil produkční lazy factory pro MMTX i infrastrukturu a
  skutečné prompty obou profilů; přes fake transport ověřil start i resume
  stejného vlákna se zachováním read-only sandboxu a approval_policy=never.
- Porovnání AST potvrdilo nezměněné DEVELOPMENT_CONTROL/private instrukce,
  síťovou a archivní capability i konstrukci sandbox oprávnění.
- Změna je lokální; běžící Cockpit zatím nedostal nový serverový prompt.

### 2026-09-12 20:50 CEST — Push a nasazení sjednocených instrukcí

Hotovo:
- Oba implementační commity jsou na GitHubu. Cockpit má nasazený funkční
  commit `2570a14715fe`; obnovené pracovní vlákno je připojené.

Rozhodnutí:
- Mílův přímý pokyn p+n pokrývá publikování i řízené nasazení tohoto balíčku.
- Bezpečnostní a zápisové hranice zůstávají zachované.

Další krok:
- Pokračovat v běžné práci a posoudit chování nových instrukcí.

Navrhované další kroky:
- Hlasový pilot nebo Agents API řešit pouze jako samostatné věcné rozhodnutí.

Technický důkaz:
- Plná publikační brána OK: 1 555 testů (1 přeskočený), 556,7 s.
- Registrované nasazení: nový proces, kódový otisk `d12a6e19e855247f`,
  rychlá brána 9,4 s a smoke 5/5; následný live audit `current`.
- Main i origin shodné; obě kopie čisté, runtime připojený a nečinný,
  bez nejistého doručení. Toto je časovaný důkaz, ne trvalá provozní záruka.
- Závěrečný paměťový zápis nemění aplikační kód; jeho commit bude zahrnut
  do téhož autorizovaného publikování a ověření aktuálního main.
