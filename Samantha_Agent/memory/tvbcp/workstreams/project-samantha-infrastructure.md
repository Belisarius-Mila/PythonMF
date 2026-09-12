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
