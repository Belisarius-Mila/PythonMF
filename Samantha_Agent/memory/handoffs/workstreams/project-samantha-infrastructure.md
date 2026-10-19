<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- 2026-10-19 21:49 CEST: Doplněna skutečná šifrovaná záloha živého Camina
  `20261019_212828-78238a8a`: 1 587 souborů / 5 078 684 995 B, čtyři DB,
  304 originálů, filmové projekty, konfigurace a přesný nasazený release.
  Celá kopie obnovena do nové soukromé složky; všechny SHA-256, čtyři DB
  a mediální účtenky PASS. Vlastní služba se vrátila zdravá HTTP/HTTPS;
  archiv, konfigurace a Serve/Funnel přesně shodné, Cockpit HTTP 200.
  Nový recovery program automaticky pořizuje doplněk a zapisuje jeho ID
  do projektového manifestu; samostatné pevné CLI má dry-run/execute.
  První neúspěšný pokus nevytvořil snapshot; opravené čekání na asynchronní
  stop/start ověřeno 34 cílenými testy a plnou bránou 2 133/2 133.
  TXT verze 1.1 směřuje na obě datové zálohy a doplněk kódu na SSD.
  Projektový snapshot jádra zůstává `20261018_210658`; dnešní doplněk jej
  nepřepisuje. Změna zdrojů je lokální, bez push/nasazení Cockpitu.
  [PRIPOMENOUT] Úplná instalace a přejímka skutečného nového Macu neprovedena.
  Dříve existující neshoda vlastnické účtenky Serve zachovaná: skutečné
  HTTPS funguje, síť se neměnila; oprava není součástí zálohování.

- 2026-10-16 21:59 CEST: po přesném potvrzení proveden omezený úklid SSD:
  čtyři starší stažené aktualizační balíčky Wordu a npm cache. Nejnovější
  instalátor zachovaný; měřené volné místo 23.47 → 28.51 GiB
  (skutečný zisk 5.04 GiB). Camino i filmový editor před/po shodné,
  autosave nadále jeden čerstvý proces bez chyby. Další mazání neproběhlo.

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


### 2026-10-16 21:59 CEST — Cílený úklid SSD s ověřeným skutečným ziskem

Hotovo:
- Odstraněny čtyři schválené starší instalátory Wordu 16.113 (buildy
  26091433, 26091740, 26092012, 26092714) a pouze domácí npm `_cacache`.
- Nejnovější stažený instalátor 26100421 a ostatní npm složky zůstaly zachované.
- Skutečné volné místo SSD vzrostlo z 23.47 na 28.51 GiB;
  přírůstek podle `df` je 5.04 GiB. Autosave i Camino ověřené bez změny.

Rozhodnutí:
- Míla přesnou globální brzdou potvrdil právě tento omezený rozsah.
  Nainstalované aplikace, dokumenty, média, autosave, Claude VM a podpora
  iPhonu zůstaly mimo úklid. Žádný restart ani síťová změna.

Další krok:
- Po plánovaném restartu Macu doma znovu změřit SSD a ověřit dostupnost
  Cockpitu a průběžné autosave.

Navrhované další kroky:
- Případné další mazání posoudit samostatně podle nového měření.

Technický důkaz:
- Před zásahem ověřena totožnost čtyř souborů a neexistence symlinků či
  otevřených cílů; úklid přes přesná jména a adresářové deskriptory.
- Logická/alokovaná velikost kandidátů 6,36 GiB není slib zisku na APFS;
  doložený zisk je až výše uvedený rozdíl `df`. Volno zůstává pod 30 GiB.
- Camino PID 47332/release `f60a33c98fd5`, konfigurace, Serve, cursor 893,
  flags false a celý editor shodné před/po; owner HTTP/HTTPS i anonymní
  401 PASS, Funnel off. Autosave PID 15725, jeden watcher, čerstvé uložení,
  poslední chyba prázdná, trvalá služba nastavená a automatické mazání vypnuté.
- Redigované účtenky `logs/ssd_cleanup_receipt_20261016.log` a
  `logs/ssd_cleanup_camino_before_20261016.log` / `ssd_cleanup_camino_after_20261016.log`.
- Jde o provozní úklid; aplikační kód se neměnil a publikování není součástí kroku.


### 2026-10-19 07:36 CEST — Podrobný TXT návod obnovy nového Macu a rozsah zálohy

Hotovo:
- Jeden srozumitelný TXT obsahuje přípravu prázdného Macu, instalace aplikací,
  Python 3.12, hlavní i doplňkové knihovny, Codex, data, služby, Tailscale,
  Xcode/iLoader/SideStore a závěrečný kontrolní seznam. Stará recovery karta
  a kopie návodu pro budoucí snapshoty odkazují na tento soubor.
- Doložený projektový snapshot 20261018_210658 měl 90 833 souborů,
  0 přeskočených, manifest, SHA-256 vzorků 4/4 a obnovu jednoho souboru.
  Dnes jde o uloženou účtenku; externí svazek není připojený.

Rozhodnutí:
- Míla požádal o podrobný TXT pro případ ztráty Macu nebo poruchy SSD.
  Rozsah je dokumentace; nejde o změnu zálohovacího programu, systému,
  služeb, síťového nastavení ani o povolení publikace.
- Oddělit obnovu jádra od úplného archivu Camina. Čtecí audit potvrdil živé
  DB, originály a filmové projekty v Library/Application Support/PythonMF/Camino,
  mimo zdroj standardní zálohy. Obecný recovery profil tuto mezeru neřeší.

Další krok:
- S Mílou vymezit samostatné rozšíření registrovaného zálohování o konzistentní
  celek Camina a jeho ověřenou obnovu; nedeklarovat dnešní snapshot za úplnou
  ochranu všech dat Macu.

Navrhované další kroky:
- Uložit schválený návod také mimo notebook; nynější lokální commit není
  důkaz dostupnosti na GitHubu ani součást včerejšího snapshotu.
- Při příležitosti provést skutečný obnovovací test na čistém Macu.

Technický důkaz:
- 27 lokálních cest existuje; 48 příkazových bloků prošlo zsh -n bez spuštění;
  19 číslovaných zdrojových referencí je uzavřených. Instalační kroky byly
  ověřeny v primární dokumentaci a porovnány s místními verzemi a skripty.
- Rychlá statická Cockpit brána PASS: logs/recovery_guide_static_gate_20261019.log.
  Žádný instalační/obnovovací příkaz z TXT se na současném Macu nespouštěl.
- Rizika: plná obnova nebyla provedena; Keychain, systémová oprávnění,
  aktuálnost nezamčených závislostí a změny uživatele/architektury vyžadují
  vlastní kontrolu. Backup pokrytí Camina je otevřená funkční mezera.
