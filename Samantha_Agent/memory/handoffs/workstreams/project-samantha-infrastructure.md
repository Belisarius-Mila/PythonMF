<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-12 20:12 CEST

### Hotovo
- První balíček instrukcí: stručné oba AGENTS.md, návody načítané podle situace,
  jednotný ruční handoff a výslovně oddělená oprávnění terminálu a Cockpitu.
- Zachována ochrana soukromých dat, neautorizovaného mazání, povinný projektový
  zápis, bezpečnostní/testovací brány a samostatné oprávnění k publikování.
- Dřívější servisní krok 2026-09-12 ověřil CLI i App Server 0.154.0,
  obnovení původního vlákna, 40 cílených testů a Cockpit smoke 5/5.

### Rozhodnutí
- Podrobnosti handoffu žijí v session_recovery_rules.md; pravidla TVBCP
  v project_tvbcp_rules.md. Ve stejném úkolu se nezměněné podklady nečtou znovu.
- Historický plán „Agents SDK bude základ budoucího agenta“ není příkaz
  k migraci současné komunikace Human–Adam z App Serveru.

### Další krok
- Po načtení nových instrukcí při další práci posoudit jejich praktičnost.

### Navrhované další kroky
- Samostatně sladit odpovídající instrukce vložené v kódu Human–Adam.
- Případný hlasový pilot a Agents API zůstávají samostatná rozhodnutí.

### Rizika / otevřeno
- Instrukce v kódu Cockpitu ani dodávané skills tento balíček nemění.
  Existující vlákno může dál obsahovat dříve načtená pravidla; samotná změna
  Markdownu nedokládá změnu serverového promptu nebo chování modelu.
- Push a nasazení nejsou součástí tohoto balíčku; provozní stav se ověřuje živě.

### Technický důkaz
- 41 cílených testů prošlo; rychlá statická brána a kontrola odkazů prošly.
- Oba AGENTS.md mají celkem 125 řádků místo 262. Bezpečnostní návody,
  původní chronologické záznamy a aplikační kód zůstaly beze změn.
- Ověření dokládá konzistenci dokumentů; přínos pro chování modelu se posoudí
  při další práci, není odvozen jen ze zkrácení textu.
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
- Zjednodušení vstupních instrukcí a sjednocení handoff/TVBCP návodů.
- Oprava popisu autosave intervalů a historické formulace o Agents SDK.

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
- Sladění instrukcí vložených v kódu Human–Adam je samostatný navazující krok.
- WebMCP ani hlasový pilot nejsou tímto dokumentačním balíčkem implementovány.
- Balíček není pushnutý ani nasazený; dřívější provozní snapshoty níže jsou historické.

Dalsi krok:
- Posoudit praktičnost nových instrukcí při další práci po jejich načtení.

Navrhovane dalsi kroky:
- Samostatně sladit serverové instrukce Human–Adam při zachování jeho oprávnění.
- Případný hlasový pilot posoudit samostatně; žádná automatická migrace architektury.

Zmenene nebo relevantni soubory:
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
