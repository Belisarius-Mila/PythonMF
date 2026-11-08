<!-- SAMANTHA_CURRENT_STATUS_START -->
## 2026-11-08 15:11 CET — REC: sjednocená forma v každé týdenní revizi

### Hotovo
- Týdenní generátor nyní vyžaduje jediný průběžně aktualizovaný návod.
  Změny patří přímo do kapitol, nikoli do připojovaných doplnění.
- Datum Nejnovější update dokumentu z ddmmyyyy vkládá program; model je
  neurčuje. Původní bloky se zachovají přesně, doloženě přepíší nebo se
  doloženě odstraní pouze zastaralá historická poznámka. Audit je mimo návod.
- Neúplné pokrytí, ztracená ochrana nebo potřebný příkaz, stará snapshot ID,
  zálohovací statistiky a vrstvy dodatků návrh zastaví. Neplatný výsledek
  zůstane attention bez automatického opakování.

### Rozhodnutí
- Mílův pokyn je výchozí kontrakt integrovaného týdenního generátoru,
  nikoli pouze doporučení v dokumentaci. Úplné čtení bez obsahové změny
  může ponechat bloky a aktualizovat datum revize; nejde o nový živý audit.
- Zmrazené jednorázové piloty mají explicitní legacy formát. Žádná automatická
  detekce či fallback na starý formát v týdenní větvi, žádné otevření starého jobu.
- Obsahová přejímka zůstává nutná. Tento krok neaktivuje službu ani roli,
  nepublikuje TXT do PythonMF/iCloud a nevolá model.

### Další krok
- Will převezme lokální změnu formátu do navazující integrace týdenního běhu;
  propojení s produkčním adapterem a writerem musí zachovat tento kontrakt.

### Navrhované další kroky
- Převzít již dodaný sjednocený čtenářský návrh z Downloads.
- Při integraci předat poslední přijatý návod, důkazy a trusted datum, nikoli
  znovu původní historickou verzi; writer přijme přesné ověřené bajty.
- Dvě provozní kopie a upload ověřit samostatně.
- Týdenní aktivace, role a rozpočet zůstávají samostatnou přejímkou.

### Technický důkaz
- 30 nových kontraktních testů; cílená kompatibilní sada 153 PASS.
- Plná projektová brána 2 824 testů OK, 5 skipped; závěrečná statická brána a git diff --check OK.
- Skutečný návod 75 415 B: dvě offline revize 15./22.11., 17 kapitol a všech 340
  bloků zachovaných, jediné nové datum, nezávislá JSON Schema validace PASS.
  Jde o simulaci formátu, nikoli dva skutečné týdny/modelové čtení dokumentace.
- Původních 24 finančních artefaktů SHA shodných, placený job nadále attention.
  Podrobnosti recovery_guide_weekly_consolidation_20261108.md a .json.
<!-- SAMANTHA_CURRENT_STATUS_END -->

### Předchozí stav infrastruktury

- 2026-10-24 15:45 CEST: Závěrečné měření po dokončení cache a profilového checkpointu: skutečně +30,20 GiB, volno 49,28 GiB. Cíl +30 GiB splněný; hlavní aplikace a chráněné služby shodné. Další mazání se neprovádí.

- 2026-10-24 15:43 CEST: Schválený úklid SSD dokončen: skutečně +30,10 GiB, volno 19,07 → 49,18 GiB. Publikační kopie, instalační zbytky, vybrané sestavovací cache a syntetické testovací payloady uklizené; potřebná data a účtenky zachované. Systémová cache 4,28 GiB zůstala nedotčená po odmítnutí macOS i se správcem; žádná změna ochran/oprávnění. Ukončeni pouze čekající aktualizační pomocníci, hlavní aplikace běží se shodnými binárními otisky. Camino/Cockpit/autosave před/po shodné. Další krok: návrat k praktické přejímce střižny, bez dalšího mazání.

- 2026-10-24 15:30 CEST: Po výslovné globální brzdě proveden schválený úklid SSD. Čtecí měření 19,08 → 41,38 GiB volných, skutečný zisk 22,30 GiB; cíl dalších 30 GiB dosud nesplněn. Publikační kopie odstraněné po ověřené záchraně ignorovaných souborů; dokončené buildy, staré autosave a DeviceSupport uklizené. Starý simulátor odstraněný až po zachování dat. Camino/Cockpit/autosave před/po shodné. Zbývá systémová cache (správce macOS) a novější čekající aktualizace aplikací; aktivní instalátory se nemazaly. Private účtenka a zachované soubory: data/private/ssd_cleanup_20261024/.

- 2026-10-19 22:13 CEST: Aktuální TXT 1.2 uložen do kořene externího disku Falta
  a do kořene iCloud Drive jako `OBNOVA_SAMANTHY_NOVY_MAC.txt`. Projekt,
  Plocha, externí SSD i iCloud mají shodný SHA-256. macOS Foundation
  potvrzuje uploaded true, uploading false a žádnou chybu uploadu.
  Připomenutí přenosu TXT po připojení disku je vyřízené.
  Důkaz: `logs/recovery_txt_external_icloud_20261019.log`.

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


### 2026-10-24 15:30 CEST — Schválený úklid SSD, první dávky a zbývající překážky

Hotovo:
- SSD má při kontrole 41,38 GiB volných proti výchozím 19,08 GiB; skutečný
  přírůstek je 22,30 GiB. Cíl uvolnit dalších 30 GiB zůstává otevřený.
- Odstraněné čisté publikační kopie ze září/října po ověření dosažitelnosti
  historie a zachování 3 798 ignorovaných souborů se shodnými SHA-256.
- Uklizený nevyužívaný aktualizační balíček Claude, přesné dokončené buildy
  a testovací výstupy, zbytky instalace Microsoftu, DerivedData a 134 starých
  autosave souborů. Posledních 12 dvojic a všechny aktuální obnovy zachované.
- Obě složky symbolů iPhonu v DeviceSupport odstraněné. Starý vypnutý
  simulátor Camino UI odstraněný přes simctl až po ověřené záchraně dat
  aplikací, médií, předvoleb a testovacího keychainu (583 souborů / 161 MB).

Rozhodnutí:
- Míla výslovně potvrdil globální brzdu pro postupné body 1–4 návrhu.
- Produkční data Camina, rodinná média, iCloud/CloudKit, Claude VM a historie
  Codexu zůstávají mimo úklid. Přesun rodinného archivu není autorizovaný.
- Stažené balíčky VS Code, Notion a ChatGPT jsou novější než instalované
  aplikace; jejich čekající aktualizátory nebyly ukončeny ani smazány.

Další krok:
- Dokončit administrátorem schválený omezený úklid systémové cache simulátoru
  a dořešit čekající aktualizace bez ztráty otevřených relací; znovu změřit df.

Navrhované další kroky:
- Po dosažení cíle vrátit se k praktické přejímce střižny Camino.
- Nová recovery záloha po připojení externího disku; poslední jádro je 18. 10.

Technický důkaz:
- Private receipt.json, preservation manifesty a jednorázové helpery jsou
  pouze data/private/ssd_cleanup_20261024/; necommitovat jejich obsah.
- Registrovaný protected_snapshot před/po shodný: Camino PID 1761, původní
  konfigurace a Serve, autosave jeden proces 1855; automatický úklid vypnutý.
  Cockpit health HTTP 200, PID 59746 a otisk aee39190d9dd21aa zachované.
- Git reference a pracovní main po úklidu shodné. Systémová dyld cache 4,28 GiB
  má root vlastníka; sudo -n není dostupné. Připravený helper dosud nespuštěný.
- Logické/alokované velikosti nejsou zisk df: například instalační zbytky
  Microsoftu sdílely bloky a odstranění simulátoru doběhlo asynchronně.
- Rychlá statická brána PASS; aplikační kód se neměnil, plná vývojová sada
  se neopakovala. Push, nasazení ani restart neproběhly.
- Prázdný osiřelý index.lock starý 36 minut archivovaný do private evidence
  po ověření nulových otevřených držitelů a nepřítomnosti Git procesu.


### 2026-10-24 15:43 CEST — Úklid SSD dokončen, měřený zisk přes 30 GiB

Hotovo:
- Cíl splněn: volno 19,07 → 49,18 GiB, skutečný přírůstek 30,10 GiB.
- Dokončen úklid čekajících instalačních balíčků a regenerovatelných Swift
  a Xcode sestavovacích cache. Hlavní aplikace ChatGPT, VS Code a Notion
  běží se stejnými PID a shodnými otisky executable/Info.plist.
- Dvanáct starých syntetických přenosových vzorků obsahovalo totožná
  generovaná data. Před odstraněním 168 binárních souborů byly ověřené
  všechny SHA-256; malá gzip kopie (390 851 B) prošla úplnou obnovou hashů.
  Původní JSON účtenky, manifesty a výsledky testů zůstaly zachované.

Rozhodnutí:
- Pokračování pokrývala již udělená globální brzda a Mílův pokyn pokračovat.
- Čekající aktualizační pomocníci ukončeni šetrně, hlavní aplikace zachované;
  odstraněné novější instalační balíčky se při další aktualizaci stáhnou znovu.
- Systémový dialog správce potvrzen, ale macOS odmítl přímé odstranění
  souborů dyld cache. Jejích 4,28 GiB zůstává zachovaných; žádná změna SIP,
  systémových oprávnění, Full Disk Access ani instalovaného runtime.
- Produkční Camino, rodinná média, Claude VM, iCloud/CloudKit a historie
  Codexu nebyly mazány. Rezervní přesun rodinného archivu nebyl použit.

Další krok:
- Vrátit se k praktické přejímce střižny podle project-camino; další mazání
  se pro dosažený cíl neprovádí.

Navrhované další kroky:
- Po připojení externího disku nová recovery záloha; předchozí jádro je 18. 10.

Technický důkaz:
- Registrovaný protected_snapshot a health před/po shodné: Camino PID 1761,
  konfigurace/Serve zachované, Cockpit PID 59746 / aee39190d9dd21aa,
  autosave jediný PID 1855, čerstvé uložení bez chyby; approval karta vyčištěná.
- Private final-verification.json, receipt.json, synthetic-payload-plan.json
  a komprimovaná obnova jsou v data/private/ssd_cleanup_20261024/.
  Gzip se rozbalí na přesně 100 663 553 B a původní SHA-256; každý chunk
  lze obnovit podle offsetu/délky v manifestu. Nejde o osobní audio/video.
- První systémové pokusy nevykonaly žádné smazání; macOS omezil čtení
  helperu z Plochy, další pokus odmítl samotné soubory cache.
- Soukromé důkazy a helpery nejsou v Gitu. Aplikační kód nezměněn;
  dokumentační checkpoint zůstává místní bez push/nasazení.
- Závěrečná rychlá statická brána PASS; data obnovy a chráněné runtime
  metadata ověřené. Symboly/kompilační cache se mohou při práci znovu vytvořit.
- Finální kontrola 15:45 CEST po poslední regenerovatelné Swift cache:
  skutečně +30,20 GiB, volno 49,28 GiB; hlavní aplikace i chráněné služby
  nadále shodné. Kompilační cache izolovaného workspace byla ignorovaná,
  bez běžící kompilace či otevřených souborů; zdroje workspace beze změny.

### 2026-10-25 14:53 CET — nová ověřená recovery záloha včetně živého Camina

Hotovo:

- Šifrovaná recovery záloha projektů a samostatného živého archivu Camina dokončená. Služba se vrátila zdravá; zkouška souborové obnovy prošla. Zastaralé upozornění na chybějící novou zálohu je vyřešené.

Rozhodnutí:

- Míla výslovně požádal nyní provést zálohu. Použit stávající registrovaný recovery postup včetně náhledu, šifrovaného cíle a řízené pauzy/návratu Camina; žádná změna zálohovacího kódu, sítě ani retenční mazání. Provozní evidence navazuje na existující vazbu zálohy v ACTIVE_PROJECTS a infrastrukturním handoffu/TVBCP; nový TVBCP nevznikl.

Další krok:

- Pro obnovu vybírat dokončený snapshot 20261025_142837 a jeho manifest s Camino doplňkem 20261025_143650-abf7e7e5; další pravidelná záloha podle živého stavu.

Navrhované další kroky:

- Samostatně navázat opravou potvrzení urgentních zpráv z iPhonu a převzetí po probuzení.
- Kompletní instalace/přejímka skutečného náhradního Macu zůstává samostatná.

Technický důkaz:

- Exit 0; 63 143 projektových souborů, 17 050 copied, 46 092 linked, 1 symlink, 0 skipped, 4 309 588 279 nových B; správná evidence 25. 10. 2026.
- Camino 1 647 souborů / 5 167 041 733 B, 4 DB; 316 mediálních originálů SHA/účtenky PASS. Čtyři vybrané projektové SHA a jejich skutečná zkušební obnova PASS, čtyři DB quick_check PASS.
- Šifrovaný mount před/po ověřený; auth.json/autosave vyloučené, HTTP/HTTPS i config/Serve/Cockpit shodné. Přesný souhrn backup_recovery_20261025.md je v projektu i v šifrovaném recovery_updates; soukromá evidence mimo Git. Zápis výsledku následný lokální checkpoint, bez push/deploy.

## 2026-11-07 12:02 CET — plán vývoje týdenního správce obnovovacího TXT

### Hotovo
Připravený plán šesti etap od úplného čtení podkladů po dvě ověřené kopie
návodu a týdenní provoz. Detail v projects/samantha_external_backup.md.

### Rozhodnutí
Míla požaduje model 6.1-Sol, jednou týdně celý návod a dokumentaci, aktualizace
se zaměřením na aplikace/nastavení Macu a iPhonu. TXT vždy PythonMF a iCloud
Dokumenty. Dnes schválené plánování, nikoli spuštění modelu nebo plánovače.

### Další krok
Po přijetí plánu REC-01: explicitní úplný manifest a identita obou cílů.

### Navrhované další kroky
Čtecí Sol pilot s nákladem, validátor, writer se shodnými hash/uploadem,
týdenní plánovač a fyzická přejímka na iPhonu. Harmonogram/rozpočet dohodnout.

### Technický důkaz
Read-only ověřené současné kopie i chybějící cíle; dílčí dokumentace 409
souborů / 5 002 170 B. Stávající rutinní pilot není obecný writer/scheduler.
Žádné modelové volání, změna souboru obnovy, role, LaunchAgentu, push/deploy.

## 2026-11-07 12:23 CET — vývojový základ týdenního správce obnovy

### Hotovo
- Po Mílově pokynu zahájen vývoj podle REC-01 až REC-06. Připraven neaktivní
  izolovaný pilot: úplné soubory/manifest, dávky a syntéza, citace/kapitoly,
  trvalý stav bez automatického opakování, rozpočty, dva jednotlivé atomické
  zápisy s historií a kontrolou iCloud uploadu, návrh plánovače.
- Registrované neplacené preview/status; run/tick zůstává activation_required.
  Nový parser zná budoucí roli, centrální JSON ani modelové role se neměnily.
- Nález: také sledovaný Samantha_Agent TXT je shodný s Plochou a kořenem
  iCloudu. Oba nové cílové TXT stále chybějí. Foundation po rozřešení známého
  aliasu Documents potvrzuje synchronizaci skutečné složky; nikoli nový TXT.

### Rozhodnutí
- Míla schválil zahájení vývoje. Placený pilot, provozní kopírování, aktivace
  role/plánovače a p+n zůstávají samostatné kroky původního plánu.
- Nejde o dokončený bezobslužný agent. Podrobný kontrakt a chybějící části
  jsou v technical/recovery_guide_maintainer.md. Výstup syntézy vždy review.

### Další krok
- Will převezme lokální vývojový balíček do aktuálního main, sjednotí známé
  role se svými novějšími rolemi a nad čistým main vytvoří neplacený manifest.
  Potom dokončit rozsah zdrojů a přesný tokenizační preflight pro cenový pilot.

### Navrhované další kroky
- Doplnit registrované bezpečné důkazy nastavení Mac/iPhone a přijmout korpus.
- Teprve nad konkrétním rozpočtem schválit jeden živý čtecí pilot Solem.
- Přijmout celý návrh TXT, provést samostatně schválenou migraci, upload/iPhone.
- Propojit přijatou účtenku s pevnými cíli a aktivovat týdenní běh až po přejímce.

### Technický důkaz
- Výchozí neplacená inventura před zápisem této etapy: 508 zdrojů,
  5 899 527 B, 114 vynechaných textů; jde o návrh rozsahu, ne přijatý korpus.
- Cílené ověření a plná brána: 65 cílených testů OK (37 nových); plná brána 2 413 testů OK, 5 skipped; po posledním zpřesnění metadat znovu cílené testy a statická brána OK..
- Testy pouze syntetické/dočasné. Foundation audit čtecí; původní iCloud TXT
  i skutečný cíl Documents: ubiquitous/uploaded true, uploading/error false.
- Bez placeného tahu, zápisu provozních TXT, instalace, push či nasazení.

## 2026-11-07 12:39 CET — REC-02: neplacený preflight, živý pilot dosud neproveden

### Hotovo
- Změřen celý zmrazený korpus 509 dokumentů a původní TXT; plán 10 dávek +
  syntéza, úplné pokrytí bez zkrácení souborů. Referenčně 2 222 784 vstupních
  a 112 000 rezervovaných výstupních tokenů, 139,1392 Standard kreditů bez
  cache. Není to potvrzená cena Solu ani tvrdý fakturační strop.
- Tiktoken 0.14.0 nainstalovaný jen do vlastního izolovaného prostředí.
  Nový neplacený preflight/runtime workflow a oddělená rezerva inspekce
  a syntézy; zachování známé ceny i po nadlimitním výstupu.
- Redigovaný manifest/plán/audit je v reports/recovery_guide_rec02_20261107.json,
  praktické vysvětlení v příslušném .md. Žádný placený tah ani nový thread.

### Rozhodnutí
- Míla schválil pokračování fází 2. Nezadaná cena/rozsah živého pilotu se
  nepovažují za schválené utrácení; žádná aktivace rolí, služeb či writeru.
- Fáze REC-02 není celá hotová: upstream tiktoken nezná mapování Solu,
  reference o200k_base není náhradou modelu. Připojený server hlásí 0.163.0,
  lokální CLI 0.166.0; preference runtime nevyhovuje Standard kontrole,
  kontext a účinnost izolace zatím nejsou doložené. Nic se nepřepínalo.

### Další krok
- Will převezme vývoj do současného main a registrovaným read-only auditem
  doloží skutečný kontrakt runtime a možnost izolovaného Standard tahu.
  Případný release/restart potřebuje samostatné oprávnění; Data jej nespouští.

### Navrhované další kroky
- Uzavřít tokenizační důkaz nebo výslovně přijmout poctivý odhad + kalibraci.
- Nad čistým cílovým HEAD přijmout úplný korpus a konkrétní cenový rozsah
  jednoho pevného syntetického Sol/medium kandidátního tahu; bez retry.
- Potom přijmout cenu čtení celého korpusu a konkrétní návrh TXT.
- Migrace dvou kopií, iPhone přejímka a týdenní aktivace zůstávají samostatně.

### Technický důkaz
- Podrobná evidence, oba snapshot/plan otisky a oficiální zdroje v REC-02 reportu.
- Plná projektová brána: 2 423 testů OK, 5 skipped; po doplnění Fast a měsíčního regresního případu znovu 76 cílených testů OK (11 nových v REC-02), závěrečná statická brána OK.
- Bez změny config/agent_roles.json, společné .venv, globálního CLI,
  provozních TXT, služeb, Gitu mimo vlastní větev, push či nasazení.

## 2026-11-07 13:03 CET — REC-03: kontrola kvality a důkazů

### Hotovo
- Povinná kontrola syntézy nyní zachová kapitoly i jejich obsah/úvod, váže
  nové cesty/role/příkazy na přesné citace a blokuje známý zrušený hlas,
  skrytá tajemství, falešné aktuální ověření a změnu pouhého data.
- Samostatná přejímka vyžaduje schválený úplný seznam aplikací, Mac/iPhone
  checklist, zdrojové otisky, autoritu a stáří důkazů. Nový OS/rozpor blokuje.
  Ani úspěšný strojový výsledek sám nepovoluje publikaci.
- Připraven balíček bez soukromé historie a otestované čtení novým izolovaným
  procesem pouze přes stdin. Nejde o lidskou/modelovou přejímku skutečného TXT.
- Stávající TXT pouze čtecí kontrolou prošel a vrací se přesně 62 778 B;
  žádné umělé přidání newline ani změna verze při běhu beze změn.

### Rozhodnutí
- Míla schválil třetí etapu REC-03. Rozsah nadále nezahrnuje placený pilot,
  publikaci provozních TXT, aktivaci role/služby, push ani nasazení.
- Checklist a důkazy smějí schválit pouze důvěryhodný řadič/operátor,
  nikoli model. Úplný skutečný seznam aplikací zatím schválený není.

### Další krok
- REC-04: svázat konkrétně přijatou kvalitativní účtenku, checklist, kandidát
  a oba pevné cíle s writerem; testovat přerušení a souběžné úpravy na kopiích.

### Navrhované další kroky
- Will převezme vývoj do aktuálního main s uchováním své práce/rolí.
- Dořešit dosud otevřený REC-02 tokenizer/Standard/runtime kontrakt a cenový pilot.
- Přijmout skutečný úplný korpus/aplikace a doložená nastavení včetně iPhonu.
- Po skutečném návrhu provést lidskou přejímku čtenářem bez soukromé historie.

### Technický důkaz
- 38 nových REC-03 testů; závěrečná cílená sada 114/114 OK. Plná projektová brána: 2 459 testů OK, 5 skipped. Po závěrečných zpřesněních znovu cílená sada a statická brána OK; nezměněné testy se zbytečně neopakovaly..
- Podrobný kontrakt/scénáře v reports/recovery_guide_rec03_20261107.md;
  bezpečný syntetický balíček v recovery_guide_rec03_example_20261107.json.
- Chybná syntéza -> attention + quality_issue, bez kandidáta/retry.
  Bez změny produkčního klienta/runtime/Cockpitu/e-mailu, rolí a služeb.

## 2026-11-07 13:45 CET — REC-04: přijatý kandidát a dvojí zápis na kopiích

### Hotovo
- Připraven PublicationStore: přesný kandidát, REC-03 účtenka/checklist,
  úplné vstupy, verze validátoru a oba připnuté cíle mají jeden neměnný binding.
  Výslovné sandboxové přijetí vzniká poslední; pouhý hash textu nestačí.
- Převod uchová zdrojový TXT i staré verze obou cílů, včetně CRLF. Po pádu
  pokračuje stejnými bajty bez modelu. Čekající upload neopakuje hotové výměny.
- Zámek/aktivní marker chrání souběh a novější verze. Ruční změny včetně
  návratu k původním bajtům se nepřepíšou. Selhání rollbacku je pozorovatelné.
- Nový vstup povoluje pouze izolované testovací cíle v podadresáři vlastní
  .venv nebo systémového temp. Produkční režim je výslovně vypnutý.

### Rozhodnutí
- Míla schválil REC-04 vývoj a ověření na kopiích. Testovací přijetí není
  skutečná přejímka nového produkčního TXT ani souhlas se zápisem do iCloudu.
- Živý REC-02 pilot, úplný produkční korpus/aplikace a fyzická přejímka na
  iPhonu zůstávají otevřené; nic se nenasazovalo ani neaktivovalo.

### Další krok
- REC-05: připojit trvalý plánovač k registrovanému preview/run/status,
  před novou analýzou řešit čekající přenos, připravit samostatnou aktivaci.

### Navrhované další kroky
- Will převezme lokální změny do aktuálního main bez přepsání svých rolí/práce.
- Dořešit REC-02 runtime/Standard/tokenizer a konkrétní placený pilot.
- Přijmout skutečný návrh a autoritativní seznam aplikací/nastavení.
- REC-06 teprve povolí přesné provozní cíle, skutečný upload/iPhone a týdenní běh.

### Technický důkaz
- 38 nových REC-04 testů; cílená sada 152/152 OK. Závěrečná plná projektová brána nad poslední verzí writeru: 2 501 testů OK, 5 skipped. Dřívější mezibrána 2 498 OK; po zpřesnění written/manifest se plná brána opakovala..
- Report recovery_guide_rec04_20261107.md a redigovaný syntetický JSON příklad.
- Testované uploady jsou simulované; žádný skutečný iCloud zápis/audit v této
  etapě, modelový tah, služba, push ani nasazení. Provozní TXT beze změny.

## 2026-11-07 14:21 CET — REC-05: trvalý plánovač a dohled bez aktivace

### Hotovo
- Připraven trvalý sandboxový plánovač: společný ISO týden pro ruční/timer
  vstup, zámek, jeden poslední doháněný týden, DST/rok a restart. Nejasná
  analýza zastaví i další týdny; známá místní účtenka se připojuje bez retry.
- Přenos REC-04 má přednost před novou analýzou. Čekající cloud dokončí
  stejné bajty bez dalšího modelu. Běh beze změn vyžaduje nové konečné
  ověření kopií/snapshotu, nikoli jen starý předběžný údaj.
- Registrované schedule-preview/status a launchd/environment preview;
  neaktivní plist má absolutní cesty, minimální PATH a umask 077.
  Čtecí CLI bootstrap pod minimálním prostředím prošel.

### Rozhodnutí
- Míla schválil REC-05 vývoj, ne instalaci/aktivaci či placený modelový tah.
  Neděle 09:00 Europe/Prague zůstává návrh, rozpočty nejsou schválené.
- Běžná budoucí automatika má fungovat v jednorázově schváleném úzkém
  rozsahu; současné syntetické callbacky tuto produkční autoritu nenahrazují.
- Produkční CLI run/tick zůstávají activation_required. Centrální role,
  globální Codex, společné služby i provozní TXT se neměnily.

### Další krok
- REC-06 nejprve uzavře předpoklady živého REC-02 pilotu a konkrétní přejímku
  skutečného TXT; potom teprve autorizovaný produkční adapter/role/cíle,
  reálný iCloud/iPhone důkaz a samostatně povolenou aktivaci jednoho slotu.

### Navrhované další kroky
- Will převezme balíček do aktuálního main s uchováním svých rolí/práce.
- Fresh audit runtime/Standard/tokenizer, konkrétní cenový syntetický pilot.
- Přijetí skutečného korpusu/aplikací, návrhu a omezené automatické politiky.
- Po schválení dne/času a limitů ověřit launchd session/auth a bezpečný catch-up.

### Technický důkaz
- 42 nových REC-05 scénářů; cílená sada 194/194 OK. Finální plná projektová brána nad posledním kódem: 2 543 testů OK, 5 skipped. Čtecí CLI bootstrap pod minimálním PATH OK; skutečná launchd/auth session a produkční model zůstávají neověřené..
- Report recovery_guide_rec05_20261107.md a redigovaný syntetický JSON příklad.
- Minimální CLI PATH ověřený; skutečný launchd/auth kontext neověřený,
  služba neinstalovaná, žádný placený model, iCloud zápis, push či nasazení.

## 2026-11-07 14:56 CET — REC-06: konkrétní jednorázová kalibrace před placeným pilotem

### Hotovo
- Čtecí audit připojeného App Serveru, účtu a přesného Sol/medium. Standard
  pro jeden tah doložen oficiální dokumentací a schématem přesného peeru .163.0.
- Nový oddělený kandidátní vstup s pevným syntetickým podkladem, přesnou
  kartou souhlasu, kontrolou oprávnění/socketu, trvalým slotem a bez retry.
- Testy výpadků/souběhu, neznámé spotřeby a obsahu; konkrétní cenová karta
  a reprodukční omezení jsou v recovery_guide_rec06_20261107.md.

### Rozhodnutí
- Pokyn k REC-06 autorizuje přípravu přejímky. Samostatný souhlas s konkrétní
  placenou zkouškou podle schváleného plánu zatím chybí; živé modelové tahy 0.
- Návrh první kalibrace: jeden Sol/medium Standard tah, pět syntetických
  záznamů bez skutečného návodu; rezerva 1,6 Standard kreditu a přijímací
  mez 2 kredity. Nejde o tvrdý fakturační/výstupní strop. Karta není souhlas.
- Přesný tokenizer Solu zůstává nedoložený; referenčních 500 tokenů není
  fallback pro celý korpus. Produkční run/tick, role a služba neaktivované.

### Další krok
- Míla přijme přesnou kartu jediné syntetické kalibrace; poté ji Data může
  jednou provést nad stejným digestem. Nejasný výsledek se neopakuje.

### Navrhované další kroky
- Vyhodnotit skutečnou spotřebu a odděleně přijmout úplný korpus/cenový pilot TXT.
- Will převezme nový modul/testy/zápis do aktuálního main, uchová své role/práci.
- Přijmout celý návrh, povolený produkční adaptér a dvě kopie; upload/iPhone zvlášť.
- Samostatně schválit p+n, centrální roli, den/čas/rozpočet a launchd/auth přejímku.

### Technický důkaz
- 28 nových testů; cílená sada 193/193 OK. Plná brána persistenčního vstupu: 2 570 testů OK, 5 skipped.
  Po malé čtecí normalizaci peer verze dalších 28/28 cílených testů OK;
  závěrečná statická brána OK.
- Globální CLI .166.0, připojený peer .163.0; stará ownership sidecar není
  důkaz současného listeneru. Žádná změna služby, globálního CLI, závislostí
  projektu, modelových rolí či provozních TXT; žádný push/nasazení/integrace.

## 2026-11-07 16:19 CET — REC-06: skutečná syntetická kalibrace Solem prošla

### Hotovo
- Jedna schválená živá zkouška Sol/medium se Standardem pro jediný tah prošla.
  Všech pět klasifikací i přesných citací sedí: dokumentace, historie, návrh,
  zrušený placený hlas jako irrelevant a neověřené nastavení iPhonu.
- Potvrzeno jedno doručení, žádný zaznamenaný nástrojový typ, žádné opakování.
  Skutečná spotřeba 5 436 tokenů; odhad 0,3094 Standard kreditu proti rezervě 1,6.

### Rozhodnutí
- Míla výslovně schválil přesnou naceněnou zkoušku a oznámil nasazení balíčku.
  Použita původní karta/digest, žádné přegenerování ani druhý request.
- Souhlas nepokrývá další placené čtení celého korpusu, publikaci TXT nebo
  aktivaci týdenní služby. Tyto kroky touto zkouškou neproběhly.
- REC-06 zůstává otevřená do skutečného návrhu, obou kopií, uploadu/iPhonu
  a zvlášť povoleného spuštění automatizace. Celý REC-02 pilot není uzavřený.

### Další krok
- Připravit aktuální manifest nad převzatým main, bezpečné Mac/iPhone
  doklady a konkrétní rozpočet úplného čtecího pilotu; dosavadní odhad
  o200k_base nepovažovat za přesný Sol prompt ani univerzální násobek ceny.

### Navrhované další kroky
- Will převezme tento výsledkový zápis, zachová své role a souběžnou práci.
- Po obsahové a cenové přejímce provést skutečný čtecí pilot a přijmout celý TXT.
- Autorizovaný produkční adapter, dvě kopie, skutečný upload a iPhone přejímka.
- Samostatně povolená centrální role, termín/limity, launchd/auth a plánovaný slot.

### Technický důkaz
- Původní approval digest d613768b…0a4329a; jedna trvalá účtenka trial_passed.
  Input 5 248, cache 0, output 188 (reasoning 0); čas 6 646 ms; 51 skills vypnuto.
- Git-safe numerický a syntetický výsledek v recovery_guide_rec06_result_20261107.json.
  Projekce porovnána s původní účtenkou; závěrečná statická brána OK.
  Soukromá původní karta/účtenka zůstávají ve vlastní .venv, mimo Git.
- Produkční klient, role, závislosti ani provozní TXT se neměnily. V tomto
  kroku žádný deploy/restart/push; nasazení bylo oznámeno Mílou, neprovedeno Datou.

## 2026-11-07 19:09 CET — REC-06: připraven celý čtecí pilot s konkrétní cenovou kartou

### Hotovo
- Připraven celý neměnný manifest z committed main bez přepnutí či změny
  Willovy pracovní kopie: 529 dokumentů, 6 281 401 bajtů včetně původního TXT.
  Historické doklady jsou oddělené od dokumentovaných nastavení.
- Samostatný spustitelný kandidátní pilot: 14 čtecích dávek a syntéza,
  per-turn Standard, ověřené pořadí/payload, trvalý job a účtenky bez retry.
  Opakování po výpadku ani v jiném týdnu nevytvoří další modelovou akci.
- Konkrétní plán s marží 193,61315 Standard kreditu, navržená přijímací mez
  200; žádný tvrdý fakturační strop. Žádný další placený tah nebyl spuštěn.

### Rozhodnutí
- Mílův pokyn k pokračování REC-06 pokrývá přípravu úplné přejímky. Konkrétní
  rozsah a cena úplného pilotu se ještě přijímají; starý souhlas s jednou
  syntetickou zkouškou není souhlas se všemi 15 tahy a publikací.
- Plný návrh zahrnuje připojenou dokumentaci PythonMF/MatysekANJ/iOS.
  Mílovi je nabízena volba tohoto rozsahu nebo jen Samanthy/Camina.
  Bez jiné volby zůstává připravený plný návrh, nikoli povolený modelový běh.
- Přesný tokenizer Solu, číselný runtime kontext a úplná Mac/iPhone aplikační
  přejímka zůstávají nedoložené. Marže 1,25 textového počtu + 8 000 tokenů
  na tah není prokázaný horní odhad. Výsledkem smí být jen privátní kandidát.

### Další krok
- Míla přijme přesnou kartu rozsahu a ceny; potom Data může jednou spustit
  konkrétní full pilot. I neúspěšný či částečný placený výsledek se neopakuje.

### Navrhované další kroky
- Will má předání; tuto kartu provést před dalším main, nebo po převzetí
  připravit nový manifest. Pro izolovaný pilot není potřeba nasazení.
- Po skutečném čtení posoudit celý návrh a skutečnou spotřebu; doplnit Mac/iPhone důkazy.
- Autorizovaný produkční adapter, oba pevné TXT cíle, upload a fyzická iPhone přejímka.
- Zvlášť schválit centrální roli, týdenní termín/rozpočet, launchd/auth a plánovaný slot.

### Technický důkaz
- Main 2909ea5ace2e; snapshot 7b08aba8…adec0072b; karta 9a532089…38ba0133.
  Referenční základ 144,8141, s explicitní marží 193,61315 Standard kreditu.
- 28 nových neplacených testů OK; plná brána: 2 599 testů OK, 5 skipped; závěrečná statická brána OK.
  Skutečný socket peer .163.0, účet chatgpt a přesný Sol/medium znovu čtecími RPC.
- Zdraví stávajícího Cockpitu ok a 12 katalogových položek nejsou úplná
  aplikační inventura ani důkaz nasazení každého Git blobu či nastavení iPhonu.
- Karta/report: recovery_guide_rec06_full_card_20261107.json a
  recovery_guide_rec06_full_pilot_20261107.md. Privátní snapshot/účtenky jen ve vlastní .venv.
  Žádná změna produkčního klienta/runtime, role JSON, závislostí, služeb,
  provozních TXT, žádný další model, push/nasazení či integrace do main.

## 2026-11-07 19:58 CET — REC-06: schválený běh zastaven před modelem, nový manifest v2

### Hotovo
- Výslovný souhlas s úplnou revizí byl zpracován. Zdrojová kontrola ale
  zastavila původní kartu ještě před rezervací, připojením a placeným tahem:
  Will mezitím přidal kalendářový main 4a33af2a místo původního 2909ea5a.
- Připraven nový plný manifest: 530 dokumentů, 6 290 890 bajtů včetně TXT;
  přidán jeden dokument a změněno pět dříve vybraných dokumentů, nic vynecháno.
- Nová neměnná karta v2 zachovává 15 tahů a schválenou mez 200 kreditů;
  plán s marží 193,79845 Standard kreditu. Počet placených tahů tohoto běhu 0.

### Rozhodnutí
- Míla schválil model, jednorázové celé čtení a přijímací mez 200 bez tvrdého
  fakturačního stropu. Tento cenový souhlas se zachovává; čeká pouze přijetí
  nového konkrétního zdrojového manifestu včetně kalendáře.
- Starý packet se nepřepisuje. Neplacený refresh smí vzniknout jen bez
  attempt/controller/turns; všechny verze mají jeden job a nesmějí navýšit limit.
  Po rezervaci, nejistém či částečném pokusu žádný refresh ani modelový retry.

### Další krok
- Míla potvrdí nový manifest v2; potom jednou spustit stejnou schválenou
  revizi nad jeho digestem. Do spuštění/běhu zachovat zdrojový main a TXT.

### Navrhované další kroky
- Pro tento pilot není třeba nasazení; další main znamená znovu kontrolu zdrojů.
- Po skutečném čtení posoudit stejný kandidát a spotřebu bez opakování modelu.
- Mac/iPhone důkazy, celý přijatý návrh a obě povolené kopie s upload/iPhone přejímkou.
- Zvlášť autorizovaná centrální role, plánovač, launchd/auth a první týdenní slot.

### Technický důkaz
- Starý digest 9a532089…38ba0133, nový 09a6ed5b…999f4e0b; snapshot
  90e85eb7…f27ab8ad; source main 4a33af2a1e57. Attempt/controller/turns nevznikly.
- Šest nových regresí, cílená sada 34 OK; plná brána 2 605 testů OK, 5 skipped; závěrečná statická brána OK.
- Původní TXT, syntetická kalibrace a stará karta zachované; produkční kód,
  kalendář, role JSON, závislosti, služby a provozní TXT se neměnily.
- Report recovery_guide_rec06_source_refresh_20261107.md; nová veřejná karta
  recovery_guide_rec06_full_card_20261107_v2.json. Žádný paid turn, push či deploy.

## 2026-11-07 21:26 CET — REC-06: první úplná dávka dorazila, známá účtenka bez opakování

### Hotovo
- Míla přijal manifest v2 včetně kalendáře a skutečný SDK běh se spustil.
  První tah je jednoznačně completed/delivered: 36 přesných citací dokumentů
  a jedna přesná citace original_guide navíc. Nejde o nejisté doručení.
- Známá spotřeba 194 389 tokenů / 10,44505 Standard kreditu, čas 78 142 ms.
  Controller zastavil další dávky kvůli délce covered 37 místo 36; žádný retry.
- Opravena úzká interpretace pokrytí: přesný nadbytečný původní návod se
  vyjme jen při úplné shodě všech očekávaných citací. Raw odpověď/notes se nemění.

### Rozhodnutí
- Pokračování dokončí jen zbývajících 14 původně schválených SDK kroků
  nad stejným manifestem v2 a v celkové přijímací mezi 200. Nepřidává nový
  placený pokus ani zdroje. První výsledek se převezme lokálně, nikoli SDK.
- Povolena pouze prokázaná completed první účtenka a tento přesný případ.
  Unknown delivery, neznámá spotřeba, další SDK tah, neúplné citace nebo
  změněné vstupy jsou odmítnuté. Starý run/refresh zůstávají uzavřené.
- Konečný TXT, Mac/iPhone důkazy, publikace a aktivace zůstávají oddělené.

### Další krok
- Pokračování s checkpointem 82e75dfd…ab613642 již bylo spuštěno. Číst
  receipt-recovery-attempt.json a receipt-recovery-controller účtenku, čekat
  na stejný běh. První SDK tah se nikdy neposílá znovu; žádný nový run/refresh.

### Navrhované další kroky
- Vyhodnotit jediný navazující výsledek a celkovou spotřebu s první cenou jen jednou.
- Celý kandidát převzít obsahově, doplnit Mac/iPhone doklady a aplikační dossier.
- Obě povolené kopie, upload a fyzická iPhone přejímka.
- Zvlášť schválit centrální roli, týdenní službu a první plánovaný slot.

### Technický důkaz
- Raw první receipt SHA 1727d71f…c28b2e26, turn 01a1b7a6-1282-7f20-83d1-520c89973061.
  Input 190 761, cached 0, output 3 628 (reasoning subset 49); 36 dokumentů přesně.
- 13 nových regresí; cílená sada 47 OK; plná brána 2 618 testů OK, 5 skipped.
- Nový explicitní continuation marker pod stejným job lockem, SDK reviewer
  začíná indexem 2. Celkový limit 200, zbývající allowance 189,55495.
- Report recovery_guide_rec06_run_20261107.md; checkpoint
  recovery_guide_rec06_known_receipt_20261107.json. Žádná změna produkčního
  klienta/runtime, role JSON, služeb, provozních TXT, žádný push/deploy.

## 2026-11-07 21:44 CET — REC-06: živý pilot zastaven citačním kontraktem po dvou tazích

### Hotovo
- Schválená v2 revize proběhla kontrolovaně do druhé SDK dávky. Obě odpovědi
  jsou completed/delivered; dva jedinečné turny, žádný SDK retry. První odpověď
  byla v pokračování převzata lokálně, původní raw soubor zůstává beze změny.
- Celkem 387 928 tokenů, odhad 21,013 Standard kreditu včetně první ceny jednou.
  V doručených odpovědích je 101 dokumentů; 99 raw citací je doslovných.
- Druhá dávka se zastavila na dvou změnách prvního písmena citace proti zdroji
  (Restart/restart, Oddělit/oddělit). Celý návrh TXT ani syntéza nevznikly.

### Rozhodnutí
- Dalších 13 plánovaných SDK tahů se neodesílá. Doslovný citační kontrakt
  zůstává přísný; dvě nepřesné modelové citace se automaticky nenahradily
  zdrojovým textem. Nejde o nejisté doručení, ale o doloženou chybu přesnosti.
- REC-06 ani celý REC-02 nejsou přijaté; týdenní automatiku zatím neaktivovat.
  Další placená zkouška vyžaduje nový konkrétní podklad, nikoli retry z této rezervy.
- Produkční TXT/kopie, role JSON, služby a nasazení se v tomto kroku neměnily.

### Další krok
- Neplaceně připravit pilot source/anchor ID: model odkazuje na povolené
  úseky, přesnou citaci vrací program ze zmrazených znaků zdroje. Ověřit
  inspect i synthesis a stávající doslovný validátor zachovat.

### Navrhované další kroky
- Will převezme známý výsledek a izolovanou opravu s uchováním své kalendářové práce.
- Po offline anchor testech znovu nacenit a výslovně přijmout případnou novou zkoušku.
- Až po celém kandidátovi doplnit Mac/iPhone dossier a obsahovou přejímku.
- Teprve potom povolené dvě kopie/upload/iPhone a samostatná týdenní aktivace.

### Technický důkaz
- Celkem input 379 845, cached 0, output 8 083 (reasoning subset 109).
  Ceny dvou SDK účtenek 10,44505 + 10,56795 = 21,013; historické ledgery nesčítat.
- První 36-dokumentová dávka převzata; druhá 65-dokumentová dávka atomicky
  odmítnuta kvůli 2 ze 65 citací. Žádný raw soubor třetího SDK tahu.
- 47 cílených testů, plná brána 2 618 OK / 5 skipped; finální statická brána OK.
- Účtenky zůstávají v soukromé .venv. Git-safe důkaz
  recovery_guide_rec06_full_result_20261107.json a report recovery_guide_rec06_run_20261107.md.
  Starý run/refresh i známé pokračování jsou uzavřené; znovu je nespouštět.

## 2026-11-07 22:53 CET — REC-06: offline source/anchor protokol hotov

### Hotovo
- Nový neměnný katalog a inspect/synthesis protokol: model vybírá ID,
  přesné citace dodává program ze zmrazeného textu. Původní quality gate zůstává.
- 24 nových testů OK. Čtecí audit historického v2 zachoval celý original
  a 530 dokumentů; 14 úplných requestů, 81 612 neprázdných anchorů.
- Offline fixture pro 101 dokumentů včetně dvou známých kapitalizačních
  případů prošly; neúplná syntéza byla odmítnuta. Fixture nejsou nový modelový výsledek.

### Rozhodnutí
- Žádný nový SDK/modelový tah; staré raw účtenky i uzavřený job beze změny.
  Původní odhad 21,013 Standard kreditu zůstává historickou cenou dvou tahů.
- REC-06 zůstává otevřená, nový protokol nemá živou modelovou přejímku.
  Exact reference nedokazuje správnost tvrzení ani nastavení Macu/iPhonu.
- Žádná změna produkčního klienta/runtime, role JSON, provozních TXT/kopií,
  iCloudu, služeb, aktivace, push nebo nasazení.

### Další krok
- Připravit nový izolovaný anchor trial adapter a neplacenou kartu s novou
  identitou, přepočtem tokenů/ceny včetně anchor/schema/synthesis režie.
  Malou živou zkoušku předložit zvlášť; uzavřený v2 job se nesmí znovu spustit.

### Navrhované další kroky
- Will přezkoumá lokální pilotní diff a zachová svoji kalendářovou práci.
- Neplacený live adapter/cenová karta, potom samostatně přijatý malý živý test.
- Teprve po úspěchu případně nový úplný pilot a obsahový Mac/iPhone dossier.
- Přijetí kopií/upload/iPhone a týdenní aktivace zůstávají samostatné kroky.

### Technický důkaz
- recovery_guide_anchors_20261107.md a recovery_guide_anchors_offline_20261107.json.
- Katalog ceb6dbe4…ac238dc, snapshot 90e85eb7…27ab8ad; 6 290 890 zdrojových B.
- 14 inspect payloadů 8 742 382 B + schémata 47 756 B; není to cena ani
  tokenový odhad. max 996 zdrojů/schema, prázdné zdroje nepodporovány.
- 24 cílených testů OK; plná brána 2 642 testů OK / 5 skipped (620,921 s).
  Finální statická brána a git diff --check OK.

## 2026-11-07 23:11 CET — REC-06: malý anchor adapter a cenová karta připravené

### Hotovo
- Nový izolovaný adapter pro inspect + synthesis nad celým původním návodem
  a dvěma známými citačními dokumenty. Bez změny produkčního klienta/runtime.
- Připraven konkrétní neplacený manifest/karta: 75 100 zdrojových bytů,
  explicitní Sol/medium Standard kandidát, nejvýše dva tahy. Plán 14,72415
  Standard kreditu, navržená přijímací mez 15; není tvrdým fakturačním capem.
- 26 nových testů a cílená sada 50 OK; skutečné zdroje prošly neplacenou
  fixture kontrolou inspect i synthesis včetně původního quality gate.

### Rozhodnutí
- Pokyn pokračovat provedl přípravu, nikoli nový placený pokus. Žádný nový
  model/SDK tah, žádný attempt marker nového pilotu. Karta čeká na přesný souhlas.
- Původní v2 job a raw účtenky zůstávají uzavřené a beze změny; jeho 21,013
  Standard kreditu se nepoužívá jako souhlas ani rozpočet nového testu.
- Malý test neznamená celý korpus ani hotový návod/Mac/iPhone přejímku.
  REC-06, obě provozní kopie a týdenní aktivace zůstávají otevřené.

### Další krok
- Po uzavření testovací brány předložit kartu 566899e7…ddd8cb3 k samostatnému
  přijetí dvou placených tahů s přijímací mezí 15 Standard kreditů; před run
  znovu ověřit main/TXT/kód/socket/peer a nikdy neopakovat nejistý výsledek.

### Navrhované další kroky
- Will přezkoumá nový izolovaný adapter a zachová svoji souběžnou práci.
- Přesný souhlas s kartou, potom jediný malý živý kompatibilitní test.
- Teprve po úspěchu nová cenová karta pro celý korpus a skutečný obsahový návrh.
- Později Mac/iPhone dossier, dvě kopie/upload/iPhone a samostatná týdenní aktivace.

### Technický důkaz
- recovery_guide_anchor_trial_20261107.md, *_card_20261107.json a *_offline_20261107.json.
- Main 0850e6f3, snapshot 7e0e6b6f…90fb738, katalog 6b105182…cabb79a.
- Čtecí runtime: server 0.163.0 / místní CLI 0.166.0; Sol/medium v katalogu.
  Žádné vlákno, tah ani služba při přípravě. Standard se vynucuje per-turn.
- Reference o200k_base/tiktoken 0.14.0 není přesné Sol mapování; syntéza je
  vázaná na skutečný první receipt a před druhým tahem se celý vstup přepočítá.
- Plná projektová brána 2 668 testů OK / 5 skipped; finální statická brána OK.
  Žádný push/deploy, změna rolí,
  společné .venv, globálního CLI, provozního TXT ani iCloudu.

## 2026-11-07 23:28 CET — REC-06: malá živá zkouška dokončena, obsah/cena OK, čas překročen

### Hotovo
- Schválená karta 566899e7…ddd8cb3 provedena jedním run: dva jedinečné
  completed/delivered tahy Sol/medium Standard, žádný retry ani třetí tah.
- Inspect i již doručená syntéza prošly obsahovým kontraktem: oba správné
  source/anchor odkazy, přesné citace, celý original doslovně zachovaný,
  dva unverified dodatky. Syntéza byla ověřena neplaceně z raw účtenky.
- Celkový odhad ze skutečné spotřeby 8,50485 Standard kreditu, pod mezí 15.
  Input/output meze prošly; nebyly pozorované nežádoucí tool události.

### Rozhodnutí
- Celý test zůstává attention / accepted=false: syntéza trvala 400,240 s
  proti schváleným 300 s. Žádná zpětná změna limitu či přijetí jobu.
- Známé dokončené účtenky se zachovávají; samotné časové překročení není
  důvodem k opakování modelových tahů. Starý v2 job/21,013 kreditu beze změny.
- REC-06 a celý korpus/Mac/iPhone nejsou přijaté. Žádný provozní TXT/iCloud,
  role, služba, push, nasazení nebo integrace do main.

### Další krok
- Neplaceně připravit úplný anchor pilot a novou cenovou kartu: aktuální
  manifest, přepočet všech dávek/syntézy a samostatný časový plán fází podle
  naměřených 400,240 s. Nejde o retry ani zvýšení limitu uzavřeného testu.

### Navrhované další kroky
- Will přezkoumá známý výsledek, oba splněné obsahové kontrakty a časový důvod nepřijetí.
- Úplný anchor adapter/preflight bez modelu; nový konkrétní souhlas až s hotovou kartou.
- Volitelně později programově skládat nezměněné části místo jejich modelového opisování.
- Až po celém návrhu Mac/iPhone dossier, dvě kopie/upload a samostatná týdenní aktivace.

### Technický důkaz
- recovery_guide_anchor_trial_run_20261107.md a recovery_guide_anchor_trial_result_20261107.json.
- Inspect 9,008 s / 1,9261; synthesis 400,240 s / 6,57875 Standard kreditu.
  Celkem input 69 602, cached 0, output 20 099 (reasoning subset 132), total 89 701.
- Raw 01 6f8b5922…4b6ae8, raw 02 bea9fa82…bffc4; přesně dva raw turn soubory.
  Návod 62 778 B zachovaný přesně včetně vnějšího whitespace, nové dodatky 366 B.
- Kód se neměnil; předchozí 50 cílených a 2 668 plných testů / 5 skipped platí.
  Finální statická brána a git diff --check OK. Raw data zůstávají v soukromé .venv.

## 2026-11-08 08:21 CET — REC-06: neplacený úplný anchor plán spočten

### Hotovo
- Plán nad main 6d5b576b: 531 dokumentů + celý původní TXT, 6 314 979 B,
  dvacet čtecích dávek a jedna syntéza. Plné texty zachované, každý dokument právě jednou.
- Konzervativní rezerva bez cache 243,50895 Standard kreditu; návrh přijímací
  meze 250. Čtení 300 s/dávku, syntéza 900 s podle skutečného měření malého testu.
- Osmnáct nových testů / 68 cílených OK; úplná zdrojová fixture a request hashe
  prošly. Syntézní rezerva je předem ohraničená, nesmí se krátit historie či zdroje.

### Rozhodnutí
- Jde o neplacený plán dcfb8b2a…c6f805d, nikoli exekuční kartu nebo souhlas
  s placením. Žádný nový modelový tah. Placený run adapter není implementovaný.
- 782 dlouhých řádků je nepodporovaných jako citace v omezené rezervě;
  celé zdrojové texty zůstávají čitelné, žádný dokument se nevynechal.
- Staré placené joby a jejich limity zůstávají uzavřené a beze změny. Nová
  časová mez nezvyšuje zpětně 300 s nepřijatého malého testu.

### Další krok
- Dokončit samostatný běhový adapter nad přesným plánem: zdrojová čerstvost,
  peer/socket/účet/Standard, společný trvalý job bez retry, raw účtenky a skutečné
  přepočty/fázové meze. Až pak vytvořit exekuční kartu k samostatnému přijetí.

### Navrhované další kroky
- Will přezkoumá izolovaný plán a zachová svoji souběžnou práci.
- Implementovat a neplaceně otestovat celý adapter; žádný další malý placený test automaticky.
- Po čerstvé konkrétní kartě zvlášť přijmout jeden celý pilot.
- Později úplný Mac/iPhone dossier, dvě kopie/upload a samostatná týdenní aktivace.

### Technický důkaz
- recovery_guide_anchor_full_plan_20261108.md, stejnojmenný JSON a *_offline_20261108.json.
- Referenční input s marží 4 300 579, output 113 920; synthesis input 236 458.
  Encoding o200k_base / tiktoken 0.14.0 není přesné Sol mapování; meze nejsou billing cap.
- Časový návrh 900 s vychází z 400,240 s / 19 837 output tokenů; při 32 000
  a 25% marži 807,058 s. Součet přijímacích časů 115 minut není předpověď délky.
- Čtecí runtime 0.163.0 / CLI 0.166.0; Sol/medium v katalogu, živý kontext/účetní základ neověřené.
- Plná brána 2 686 testů OK / 5 skipped; statická brána a git diff --check OK. Žádný model/služba/role/push/deploy ani TXT/iCloud.

## 2026-11-08 10:13 CET — REC-06: celý běhový adapter a exekuční karta připravené

### Hotovo
- Samostatný no-retry adapter propojuje přesný celý plán s 20 inspect + 1
  synthesis přes existující sdílený socket; žádná změna produkčního klienta/runtime.
- Čerstvá exekuční karta 4b22ea9e…4cce1d1: 531 dokumentů + original,
  Sol/medium Standard, plán 243,50895 / mez 250 Standard kreditů (ne hard cap),
  časy 300/900 s. Karta čeká na konkrétní souhlas, nikoli na další implementaci.
- 43 nových / 111 cílených testů OK; úplná 20+1 offline fixture nad skutečným
  korpusem prošla, všechna zjištění předaná a původní quality gate zachovaná.

### Rozhodnutí
- Pokyn k adapteru provedl vývoj a neplacenou přípravu. Žádný nový placený
  tah ani attempt marker; žádná aktivace, publikace, zápis TXT/iCloud či role JSON.
- Všechny staré placené joby i přípravný plán zůstávají beze změny. Další
  volání spotřebovaného jobu smí jen vrátit jeho účtenku, nikdy obnovit model.
- Bez nové command allowlist či live/manual dokladů zůstávají nové příkazy
  a živá tvrzení nepodporované podle původního quality gate. Kandidát není přijatý provozní návod.

### Další krok
- Po konečných branách přijmout přesnou novou kartu k jedinému celému pilotu
  (nejvýše 21 tahů). Před run znovu čerstvost snapshot/kód/peer/socket/účet;
  při driftu jen explicitní neplacená revize před pokusem a nový souhlas.

### Navrhované další kroky
- Will přezkoumá izolovaný adapter a kartu, zachová svoji souběžnou práci.
- Konkrétní souhlas s kartou, poté jediný programově řízený celý kandidátní pilot.
- Vyhodnotit známé účtenky/spotřebu a obsah; nikdy neřešit nejistotu dalším turn/start.
- Samostatně Mac/iPhone dossier, obsahová přejímka, dvě kopie/upload a týdenní aktivace.

### Technický důkaz
- recovery_guide_anchor_full_pilot_20261108.md, *_card_20261108.json a *_offline_20261108.json.
- Celý plán dcfb8b2a…c6f805d, main 6d5b576b, peer 0.163.0 / CLI 0.166.0,
  chatgpt účet; aktuální pricing identity a živý kontext nejsou prokázané.
- Trvalý záznam před thread/turn, raw před přejímkou; structured errors,
  failed/interrupted a willRetry/timeout zachované bez resend. Částečná usage není finální účet.
- 43 nových / 111 cílených testů OK. Plná brána 2 729 OK / 5 skipped; statická brána a git diff --check OK.
  Offline fixture není modelový výsledek. Žádný push/deploy či integrace do main.

## 2026-11-08 11:12 CET — REC-06: celý pilot zastaven po jednom doručeném tahu na nevydané kotvě

### Hotovo
- Přijatá karta 4b22ea9e…4cce1d1 spuštěna jedním run; první tah completed/delivered,
  27 dokumentů a 6 findings. Odhad ze skutečné spotřeby 9,58995 Standard kreditu.
- Přesná diagnostika: covered.d0001 = l131111 pro kořenový AGENTS.md s 26 řádky.
  Z 39 referencí je 38 vydaných; ostatní meze a scope prošly.
- Raw účtenka zachovaná, další modelové tahy ani syntéza nebyly odeslané.

### Rozhodnutí
- Job zůstává attention / accepted=false, přijatých dávek 0. Není to nejisté
  doručení, ale chybná modelová hodnota. Žádný retry, reset, oprava ID či přijetí notes.
- Současné schema hlídá formát ID, nikoli množinu vydaných hodnot; přesný
  resolver chybu odmítl. Malý test ani fixtures nejsou zárukou velké odpovědi.
- Zbývajících 20 plánovaných tahů neodesílat automaticky. Staré joby i plán
  beze změny, žádný kandidát, provozní TXT/iCloud, role, služba, push nebo nasazení.

### Další krok
- Neplaceně zpřísnit výstupní kontrakt na vydaná source/anchor ID, ověřit
  upstream/schema limity a novou režii. Nevymýšlet náhradní řádek a nepřepisovat raw.

### Navrhované další kroky
- Will převezme známou příčinu a uzavřenou účtenku, nikoli pokyn k opakování.
- Offline schema/regrese s touto vadnou odpovědí, přesný resolver nadále povinný.
- Po novém přepočtu určit konkrétní další krok a případný samostatný souhlas.
- Mac/iPhone dossier, celý přijatý návrh, dvě kopie/upload a týdenní aktivace později.

### Technický důkaz
- recovery_guide_anchor_full_pilot_run_20261108.md a *_result_20261108.json.
- Raw 6177159d…505b55a; turn 01a1baa0-3849-7e43-8efe-0760d5fc1204.
- Input 184 414, cached 0, output 1 477 (reasoning subset 189), total 185 891.
  SDK délka 34,567 s, celý job 57,990 s. Findings JSON 721/1000 ref tokenů.
- Kód se neměnil; 111 cílených a 2 729 plných testů / 5 skipped z předchozí etapy.
  Aktuální statická brána a git diff --check OK. Žádný další modelový tah.

## 2026-11-08 11:42 CET — REC-06: přesná doména citací offline ověřena a přepočtena

### Hotovo
- Nový source_citation_index_v1 používá pro každý zdroj hustý index 1…N
  s přesnou immutable vazbou na vydané a povolené lN. Schema váže source_id
  a integer range; celý text včetně necitovatelných řádků zůstává zachovaný.
- Regresní protipříklad 131111 pro AGENTS.md odmítnut už schematem (max21).
  Nezávislý JSON Schema validator ověřil 21 schémat / 8683 doménových probes,
  program 99 874 mapování. 19 nových / 130 cílených testů OK.
- Nový plán a59c80c4…516c070: 531 dokumentů + original, 20+1 fází,
  rezerva 237,43795 / návrh meze 240 Standard kreditů; synthesis input 234859.

### Rozhodnutí
- Jde o offline novou reprezentaci, nikoli opravu raw či přijetí původní
  dávky. Starý job zůstává attention / 9,58995, žádný reset či nový model.
- Přesný resolver, původní quality/budget gate a blokace neschválených
  příkazů/live claims se nemění. Platné ID není záruka věcné správnosti.
- Nový formát není živě ověřený ani zapojený do executor/worker. Neexistuje
  nová exekuční karta či žádost o placení. Provozní TXT/iCloud/role/služby bez změny.

### Další krok
- Explicitně integrovat nový dekodér do samostatného adapteru/workeru,
  připnout novou kartu a po čerstvém přepočtu určit další postup. Původní
  uzavřený slot ani chybný raw výstup nepoužít k automatickému pokračování.

### Navrhované další kroky
- Will přezkoumá izolovaný offline diff, limity a novou reprezentaci.
- Integrace dekodéru a čerstvá exekuční karta, zatím bez modelu.
- Před případným dalším placením posoudit kompatibilitu a využití validních částí známé účtenky.
- Mac/iPhone dossier, celý obsahový návrh, dvě kopie/upload a týdenní aktivace později.

### Technický důkaz
- recovery_guide_anchor_exact_20261108.md, *_plan_20261108.json a *_offline_20261108.json.
- Max schema: 195 properties / 536 enum values / 2846 znaků jmen / depth6 / 17290 B.
- Nové integer bounds/anyOf jsou v dokumentovaném subsetu; skutečný model/peer dosud netestován.
- Plán -6,071 proti dřívější rezervě, nejde o reálnou úsporu či hard billing cap.
- Raw 6177159d…505b55a a pět starých jobů/plánů beze změny; counterexample je pouze fixture.
- Plná brána 2 748 OK / 5 skipped; statická brána a git diff --check OK. Žádný push/deploy nebo integrace do main.

## 2026-11-08 12:14 CET — REC-06: přesný číselný protokol integrován, technická část hotová

### Hotovo
- Samostatný executor/worker zapojují source_citation_index_v1 do všech
  inspect a synthesis fází včetně původního resolveru a quality/budget gate.
  Nový pevný job je oddělený od uzavřeného string-ID pilotu.
- Připravená konkrétní karta 741e71da…492f570, plán 586cdf96…f3a3add:
  celý původní návod + 532 dokumentů aktuálního main6c610287, 20+1 fází,
  Sol/medium/Standard, plán 237,88715 / návrh přijímací meze240 kreditů.
- 46 nových kontraktních testů OK. Úplná fixture přes nový executor/worker
  přijala všech 20 dávek a syntézu, 532 dokumentů přesně jednou, celý original
  v každé fázi a všech 20 findings. Jen syntetický wire, nula modelových volání.
- Status zachoval všechny bajty i mtime; opětovné run/status bez připojení.
  Plná kanonická brána OK: 2 794 testů, 5 přeskočeno (539,094 s).
- Závěrečná statická brána a git diff --check OK; lokální commit,
  bez push/deploy či integrace do main.

### Rozhodnutí
- Pokyn „zapoj a dokonči“ dokončuje technickou integraci; není novým
  finančním souhlasem s náhradou uzavřeného neúspěšného modelového běhu.
- Raw a všech 24 JSON v pěti starých stavech/plánech zůstaly beze změny;
  job attention / 9,58995 / nula přijatých dávek se neobnovuje ani neopravuje.
- Nový job not_started, nula modelových pokusů. Provozní TXT/iCloud,
  role, služby, scheduler, push, deploy a main se tímto krokem nemění.

### Další krok
- Přijmout konkrétní novou kartu a jednou spustit hotový registrovaný
  exact_pilot.run; nejde už o další vývoj adapteru. Bez souhlasu placený běh neodesílat.

### Navrhované další kroky
- Jeden placený celý pilot podle nové karty, pak obsahová přejímka kandidáta.
- Will převezme tento handoff a přesný lokální commit, bez integrace či publikace nyní.
- Mac/iPhone dossier a nové příkazy/live facts zůstávají samostatná doložená přejímka.
- Dvě provozní kopie/upload a týdenní aktivace až podle odpovídajícího zvláštního souhlasu.

### Technický důkaz
- recovery_guide_anchor_exact_execution_20261108.md a execution_plan/card/offline JSON.
- Exact executor/worker mají map/schema/wire SHA, kompletní raw historii,
  marker před send, status/replay bez připojení, žádný reset/resume/retry.
- Syntéza input235090/output32000, inspect300s/synthesis900s, run6900s;
  přijímací meze nejsou tvrdé fakturační/output/časové stropy.
- Provider nového formátu není živě ověřený; platná citace není obsahová pravda.
  Nové příkazy bez allowlist a současné Mac/iPhone facts bez důkazů nepodporované.

## 2026-11-08 12:57 CET — REC-06: 21 tahů doručeno; oddělený redakční návrh připraven

### Hotovo
- Jediný nově schválený pilot karty741e71da dokončil 21/21 tahů,
  všech 20 čtecích dávek přijato. 532 dokumentů přesně jednou, celý original
  v každé fázi; 116 findings, inspect764 referencí, syntéza216 platných citací.
- Odhad ze skutečné usage 174,8297 Standard kreditu / mez240.
  Syntéza686,537s / mez900, ale output34115 / mez32000: formální attention.
- Bez dalšího modelu připraven samostatný redakční návrh 93361B / 47 částí,
  SHA72aaa17b…a9b658f. Nezměněný quality gate prošel, 19 původních bloků
  a všech 216 citací beze změny. Rozpis25 redakčních operací je uložený.

### Rozhodnutí
- Původní job zůstává accepted=false; raw, limit, packet ani attempt se
  nepřepisují. Samostatný upravený pracovní návrh není přijetím původního jobu.
- Další placený běh se neopakuje. Necitovaný disclaimer je jen v raw/review,
  dvě nově odvozené absolutní cesty nejsou přijaté, historické části jsou
  označené přísněji. Pravidla validátoru ani citace se neměnily.
- Během posledního tahu vznikl main9c8584ee; schválený snapshot zůstává6c610287.
  Čtecí přezkum rozdílu je oddělený. Návrh není tvrzení o nejnovějším celém main.
- Provozní TXT/iCloud, role, služby, scheduler, push/deploy ani main Data neměnil.

### Další krok
- Míla a Will obsahově převezmou konkrétní redakční návrh a jeho změnový
  záznam včetně zdrojového rozdílu. Tato přejímka nepotřebuje další model.

### Navrhované další kroky
- Obsahová přejímka doplňků, zejména záloh, dat mimo Git a kompatibility Camina.
- Příští offline kontrakt: evidence podle statusu, serverové zachování original,
  posuzovat souběžné změny odděleně od neměnného čteného snapshotu.
- Po přijetí přesných bajtů a příslušném oprávnění dvě kopie do PythonMF a iCloud Dokumentů.
- Týdenní aktivace až po vlastní přejímce role, aplikací/Macu/iPhonu a rozpočtu.

### Technický důkaz
- recovery_guide_anchor_exact_run_20261108.md, *_run_result_20261108.json,
  *_editorial_review_20261108.json; plný návod jen v soukromé .venv, mimo Git.
- Všech 21 provider schémat nezávisle validních. Původní unverified odstavec
  bez citace neprošel resolverem. Některé další texty vyžadovaly redakci
  kvůli přesným literálům, historickému statusu a false-positive regexům.
- 25 operací =21 textových úprav +3 přísnější stavy +1 přesunutý disclaimer.
  Původní non-whitespace obsah zachovaný celý a ve stejném pořadí.
- Usage input3207934/cached0/output57732, reasoning5290 je subset, total3265666.
  Celý job1566,841s; finalraw6fdad250…c7664e, response df93d3a3…a08e6.
- Pět starých stavů/plánů /24JSON beze změny; dalších24 původních finančních
  artefaktů tohoto jobu má soukromý manifest. Kód beze změny, převzato ověření
  bef32ad2:46 nových /2794 plných testů,5 skipped. Závěrečná statická brána a git diff --check OK.

## 2026-11-08 14:38 CET — REC: sjednocený aktuální návod místo vrstev doplnění

### Hotovo
- Podle Mílova směru připraven jeden souvislý text17 kapitol,75415B,
  SHA381963c3…82543c8; nový pracovní soubor je také v Downloads.
- Změny jsou přímo v kapitolách, bez bloků DOPLNĚNÍ. Jediné datum v záhlaví:
  Nejnovější update dokumentu z 08112026. Zastaralé ID/statistiky záloh,
  chronologie testů, staré buildy a vzájemně přebíjející instrukce odstraněné.
- Záloha se vybírá podle dokončených manifestů a správné vazby na Camino,
  nikoli podle pevného starého ID. Epochu popisuje skutečný identical_recovery_v1.

### Rozhodnutí
- Jeden aktuální čtenářský návod: další revize přepisují příslušný obsah,
  nevrství dodatky. Historie změn, důkazy a staré verze patří mimo čtenářský text.
- Datum aktualizace není datum zálohy ani důkaz aktuálního nasazení. Neznámé
  nastavení označit konkrétně OVĚŘIT, ne hádat.
- Původní soubory, raw, účtenky a redakční podklad zachované. Bez modelového
  tahu, služby, role, push/deploy nebo zápisu do provozních cílů PythonMF/iCloud.
- Starý75% retenční gate ani uzavřený pilot se nepřepisuje. Pro nový sjednocený
  text se jeho průchod netvrdí; doloženy jsou obsahové oblasti a níže uvedené kontroly.

### Další krok
- Míla čte soubor OBNOVA_SAMANTHY_NOVY_MAC_AKTUALIZOVANY_08112026.txt
  v Downloads jako jedinou aktuální pracovní verzi k obsahové přejímce.

### Navrhované další kroky
- Převzít obsah sjednocených kapitol, zejména výběr záloh a identickou obnovu Camina.
- Budoucí automatický renderer/kontrakt upravit na tento formát s dohledatelnými zdroji.
- Dvě provozní kopie a upload až po odpovídajícím přijetí a oprávnění.
- Aktivace týdenního běhu zůstává samostatnou integrační přejímkou.

### Technický důkaz
- recovery_guide_consolidated_20261108.md a .json; plný text a mapování47
  podkladových částí jsou soukromé, mimo Git.
- 17 kapitol v pořadí,31 odkazovaných projektových cest existuje, bez starých
  snapshotID a vrstev doplnění. Zachovány klíčové datové a bezpečnostní oblasti.
- Python kontrola zálohy beze změny logiky; opraveno jen prezentační odsazení
  heredocu, AST i zsh -n PASS. Příkazy obnovy nebyly spouštěné.
- Downloads kopie má shodný SHA;24 finančních artefaktů pilotu i předchozí
  93361B redakční podklad beze změny. Závěrečná statická brána a git diff --check OK.

## 2026-11-08 15:11 CET — REC: sjednocená forma v každé týdenní revizi

### Hotovo
- Týdenní generátor nyní vyžaduje jediný průběžně aktualizovaný návod.
  Změny patří přímo do kapitol, nikoli do připojovaných doplnění.
- Datum Nejnovější update dokumentu z ddmmyyyy vkládá program; model je
  neurčuje. Původní bloky se zachovají přesně, doloženě přepíší nebo se
  doloženě odstraní pouze zastaralá historická poznámka. Audit je mimo návod.
- Neúplné pokrytí, ztracená ochrana nebo potřebný příkaz, stará snapshot ID,
  zálohovací statistiky a vrstvy dodatků návrh zastaví. Neplatný výsledek
  zůstane attention bez automatického opakování.

### Rozhodnutí
- Mílův pokyn je výchozí kontrakt integrovaného týdenního generátoru,
  nikoli pouze doporučení v dokumentaci. Úplné čtení bez obsahové změny
  může ponechat bloky a aktualizovat datum revize; nejde o nový živý audit.
- Zmrazené jednorázové piloty mají explicitní legacy formát. Žádná automatická
  detekce či fallback na starý formát v týdenní větvi, žádné otevření starého jobu.
- Obsahová přejímka zůstává nutná. Tento krok neaktivuje službu ani roli,
  nepublikuje TXT do PythonMF/iCloud a nevolá model.

### Další krok
- Will převezme lokální změnu formátu do navazující integrace týdenního běhu;
  propojení s produkčním adapterem a writerem musí zachovat tento kontrakt.

### Navrhované další kroky
- Převzít již dodaný sjednocený čtenářský návrh z Downloads.
- Při integraci předat poslední přijatý návod, důkazy a trusted datum, nikoli
  znovu původní historickou verzi; writer přijme přesné ověřené bajty.
- Dvě provozní kopie a upload ověřit samostatně.
- Týdenní aktivace, role a rozpočet zůstávají samostatnou přejímkou.

### Technický důkaz
- 30 nových kontraktních testů; cílená kompatibilní sada 153 PASS.
- Plná projektová brána 2 824 testů OK, 5 skipped; závěrečná statická brána a git diff --check OK.
- Skutečný návod 75 415 B: dvě offline revize 15./22.11., 17 kapitol a všech 340
  bloků zachovaných, jediné nové datum, nezávislá JSON Schema validace PASS.
  Jde o simulaci formátu, nikoli dva skutečné týdny/modelové čtení dokumentace.
- Původních 24 finančních artefaktů SHA shodných, placený job nadále attention.
  Podrobnosti recovery_guide_weekly_consolidation_20261108.md a .json.
