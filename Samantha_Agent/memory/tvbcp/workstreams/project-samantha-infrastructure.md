<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

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
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: Samantha Infrastructure

Pracovni proud: `project-samantha-infrastructure`
Typ: `Project`
Rezim: `active`
Priorita: `1`

## Cil a hranice

Cilem proudu je udrzovat jednoduchou, odolnou a obnovitelnou infrastrukturu,
ve ktere Samantha bezpecne funguje na Macu i z iPhonu a terminal zustava
plnohodnotnou vyvojovou a nouzovou cestou.

Tento git-safe TVBCP zachycuje pouze kanonicka rozhodnuti, podstatne milniky,
rizika a dalsi smer infrastruktury. Detailni historie komunikacni vrstvy zustava
v `memory/tvbcp/architektura_komunikace_samantha.txt`; zde se neduplikuje.
Dokument nesmi obsahovat hesla, tokeny, API klice, private obsah ani
identifikatory vlaken.

## Soucasna architektura

### Rozhrani a runtime

- Cockpit na Macu je hlavni rozhrani pro beznou praci, stav, potvrzeni a
  rizene operace. iPhone pouziva stejny soukromy Cockpit pres Tailscale.
- Codex app-server bezi pouze lokalne a komunikuje pres privátní Unix socket.
  Tailscale zpristupnuje Cockpit, nikoli samotny app-server.
- Terminalovy start `samantha` zustava nezavislym vyvojovym, diagnostickym a
  recovery rozhranim pro pripad poruchy Cockpitu nebo app-serveru.

### Pracovni proudy a komunikace

- Organizacni jednotkou je `Project`, `Tool`, `Layer` nebo `Misc`. Kazdy proud
  ma vlastni dlouhodobou kontinuitu vlakna, handoff, TVBCP a izolovany workspace.
- Human-Adam a Knihovna jsou docasne kompatibilni adaptery; ostatni proudy
  pouzivaji jednotny lazy backend.
- V jednom vlakne probiha nejvyse jeden aktivni tah. Doručení se koreluje pres
  `client_message_id`; stav `delivery_unknown` je fail-closed a nesmi vest k
  automatickemu opakovani pokynu.

### Opravneni a private data

- Kazdy modelovy tah dostava explicitni `DEVELOPMENT_CONTROL`. Bez zapisoveho
  opravneni se workspace ani Git nemeni.
- Capability registry urcuje dostupnou operaci, jeji riziko, datovy rozsah a
  potrebne potvrzeni. Pracovni proud urcuje vecny kontext, ne obchazeni
  bezpecnostnich pravidel.
- Private data zustavaji mimo Git. Do handoffu, TVBCP, logu a odpovedi se
  propousti jen nezbytny redigovany dukaz.

### Vyvoj, Git a nasazeni

- Adam smi v zapisovacim tahu provest pouze vymezenou zmenu a relevantni testy.
- V Human–Adam jsou checkpoint/commit, GitHub balík a nasazení řízeny
  potvrzenými mechanismy Cockpitu. Terminálový Adam na main má samostatný
  dávkový Git režim podle AGENTS.md; jeho oprávnění se na model v Cockpitu nevztahují.
- Lokalni `main` muze byt ciste napred pred `origin/main`; jde o cekajici
  GitHub balik, nikoli automaticky o chybu nebo povoleni k pushi.
- Nasazeni vyzaduje samostatnou branu, rizeny restart, overeni serveroveho
  stavu a smoke test. Git commit sam o sobe neni dukaz nasazeni.

### Pamet, zivy stav a recovery

- TVBCP drzi rozhodnuti a dlouhodoby smer. Handoff drzi obnovitelny soucasny
  stav. Autosave je pouze nouzova technicka obnova.
- Promenlive tvrzeni jako `bezi`, `aktivni` nebo `nasazeno` se opira o
  redigovany live audit; historicka pamet musi priznat sve stari a nejistotu.
- Recovery nejdrive overi doruceni, Git, workspaces, app-server a autosave.
  Nejasny pokyn se neposila znovu a neodpovidajici socket nebo proces se nemeni
  bez dukazu vlastnictvi.

## Kanonicka rozhodnuti

- Zachovat jeden Macem hostovany soukromy Cockpit a nevytvaret druhy vzdaleny
  app-server ani paralelni kopii aplikace pro iPhone.
- App-server ponechat na lokalnim Unix socketu a nevystavovat jej primo pres
  Tailscale ani verejnou sit.
- Zachovat jeden aktivni tah, presnou korelaci doruceni a fail-closed
  `delivery_unknown`.
- Zachovat explicitni zapisove opravneni pro jeden tah a capability-based
  bezpecnostni rozsah.
- Zachovat checkpoint, GitHub push a nasazeni jako samostatne potvrzovane
  operace s vlastnim dukazem.
- WebMCP muze byt pozdeji pouze tenkou vrstvou nad existujici logikou a
  opravnenimi Cockpitu; nesmi vytvorit druhou bezpecnostni autoritu.

## Otevrene kroky a rizika

- Stav pred zalozenim dokumentu: lokalni `main` byl ciste napred pred GitHubem,
  bezici Cockpit pouzival starsi overeny commit a jeho code stamp nebyl
  potvrzeny. Tento dokumentacni krok nic nepushuje ani nenasazuje.
- Servisní upgrade CLI i App Serveru na 0.154.0 byl ověřen 2026-09-12
  včetně stdio/Unix transportu a obnovení kontextu. Budoucí upgrade má znovu
  ověřit kompatibilitu; tento snapshot není trvalým důkazem živého stavu.
- Sladěné serverové prompty jsou nasazené a spojení obnovené; otevřené je
  posouzení praktičnosti při běžné práci. Důkaz publikování je v aktuálním souhrnu.
- WebMCP je dostupnostne omezeny a website-provided tools jsou neduveryhodny
  vstup. Pripadny pilot musi byt necitlivy, read-only a musi znovu pouzit
  existujici autorizaci Cockpitu.
- Event-triggered ulohy ChatGPT nejsou soucasti kanonicke infrastruktury.
  Nepripojovat osobni e-mail nebo externi sluzbu bez konkretniho prinosu a
  samostatneho rozhodnuti o opravnenich.

## Chronologicke zaznamy

Prvni casovany zaznam prida potvrzeny checkpoint tohoto dokumentacniho kroku.

### 2026-08-26 09:35 CEST – Samantha Infrastructure má stručný kanonický handoff a TVBCP se současnou architekturou, bezpečnostními hranicemi a otevřenými kroky

Hotovo:
- Samantha Infrastructure má stručný kanonický handoff a TVBCP se současnou architekturou, bezpečnostními hranicemi a otevřenými kroky

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- Samantha Infrastructure bude mít vlastní stručný handoff a TVBCP; podrobná historie komunikace zůstává v existujícím TVBCP architektury komunikace

Další krok:
- Potvrdit checkpoint, který dvojici transakčně doplní o první časovaný stav

Navrhované další kroky:
- Po vyřešení rozdílu mezi main a deploymentem zvážit necitlivý read-only WebMCP pilot
- Upgrade Codex CLI provést samostatně s regresním testem app-server transportů

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 5.9 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-samantha-infrastructure`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.

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


### 2026-10-19 21:49 CEST — Šifrovaný doplněk Camina a návod na SSD

Hotovo:
- Živý archiv má samostatnou dokončenou externí kopii `20261019_212828-78238a8a`
  včetně čtyř DB, všech médií, střihů, konfigurace a pevného releasu.
- Celá kopie byla obnovena do nové soukromé složky a ověřena; produkční
  služba je zpět zdravá. Návod v TXT obsahuje konkrétní obnovu a je na SSD,
  spolu s doplňkem novějšího kódu pro projektový snapshot z 18. 10.

Rozhodnutí:
- Výslovný pokyn Míly pokrývá ostrý doplněk a uložení návodu na SSD.
  Nový recovery běh přidává doplněk automaticky a odkazuje na něj manifestem.
  Starší snapshoty se nepřepisují; žádný push/deploy ani nová iPhone instalace.

Další krok:
- Pravidelná recovery záloha aktualizovaným programem; úplná obnova nového
  Macu zůstává samostatnou přejímkou podle TXT.

Navrhované další kroky:
- Samostatný restore test skutečného nového Macu; otevřená telefonní přejímka
  střižny zůstává podle P2CD reportu, bez změny rozsahu.

Technický důkaz:
- 1 587 souborů / 5 078 684 995 B; čtyři DB, 304 originálů /
  2 339 685 533 B, archiv 893 operací / 124 Momentů / 3 cesty.
- Úplné SHA-256, quick_check, mediální účtenky a nezávislá souborová obnova PASS.
  Produkce owner HTTP/HTTPS a anonymní odmítnutí PASS, archiv/config/síť shodné.
- 34 cílených a plná brána 2 133/2 133 PASS; logy `camino_backup_*_20261019*`.
  První pokus bez snapshotu vedl k ověřené opravě čekání na asynchronní stop/start.
- Předchozí neshoda vlastnické účtenky Serve zachovaná; skutečné HTTPS funguje.
  Systémová Klíčenka, další externí data a celková nová instalace nejsou tímto testem pokryté.


### 2026-10-19 22:10 CEST — Jednoznačné potvrzení hotové zálohy Camina v TXT

Hotovo:
- Místní TXT 1.2 na Ploše i v projektu hned v úvodu říká, že Camino je
  zazálohované a celá souborová obnova prošla. Staré matoucí formulace
  byly odstraněny; data zůstávají ve stejném dokončeném snapshotu.

Rozhodnutí:
- Upřesnit dokumentaci podle Mílovy připomínky; nové zálohování ani změny
  služeb kvůli opravě textu neprovádět.

Další krok:
- Po připojení disku Falta přenést aktualizovaný TXT 1.2; tam zatím zůstává 1.1.

Navrhované další kroky:
- Celková přejímka nového Macu zůstává otevřená podle dosavadního návodu.

Technický důkaz:
- Projektová a desktopová kopie mají shodný SHA-256; příkazové bloky se
  nemění. Snapshot `20261019_212828-78238a8a` byl doložen dokončeným během
  a úspěšnou nezávislou souborovou obnovou v původních lokálních logách.
  Externí svazek při nynější opravě není připojený, nové čtení snapshotu neproběhlo.


### 2026-10-19 22:13 CEST — Aktuální TXT na externím SSD a v iCloudu

Hotovo:
- Návod 1.2 je dostupný v kořeni disku Falta i iCloud Drive pod názvem
  `OBNOVA_SAMANTHY_NOVY_MAC.txt`; všechny čtyři kopie včetně projektu
  a Plochy mají shodný SHA-256. macOS potvrdil dokončené nahrání do cloudu.

Rozhodnutí:
- Míla výslovně zadal uložit aktuální TXT na připojený externí disk i do iCloudu.
  Rozsah této distribuce je textový návod bez tajemství.

Další krok:
- Při obnově otevřít návod z disku Falta nebo z iCloud Drive.

Navrhované další kroky:
- Celková přejímka nového Macu zůstává dosavadní samostatnou úlohou.

Technický důkaz:
- SHA-256 čtyř souborů shodné; iCloud NSURL resource values:
  ubiquitous=true, uploaded=true, uploading=false, upload_error_present=false.
- Lokální receipt `logs/recovery_txt_external_icloud_20261019.log`.
  Starší externí TXT zachovaný před přepsáním aktuální verzí.


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
