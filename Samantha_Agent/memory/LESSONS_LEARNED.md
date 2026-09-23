# Lessons Learned (LL)

Tento soubor je stručný registr ověřených řešení problémů, které se mohou vrátit
nebo jejichž princip lze znovu použít v jiné části projektu.

## Jak LL používat

- Při známém, podobném nebo opakovaném problému nejdřív prohledej tento soubor.
- Nový záznam přidej až po prakticky ověřeném řešení, ne při pouhém návrhu.
- Stejný problém neduplikuj; nové upřesnění doplň k existujícímu záznamu.
- Záznam drž krátký. Provozní historii nech v handoffu nebo TVBCP.
- Neukládej sem hesla, tokeny, soukromý obsah ani jiné citlivé údaje.

## Šablona

### LL-NNN — Stručný název

- Problém:
- Typ: opakující se | jednorázový
- Řešení nalezeno: DDMMRRRR
- Řešení:

## Záznamy

### LL-001 — Lokální kontrola sovy znečišťovala pracovní strom

- Problém: Opakované lokální generování sovího MP3 zapisovalo dvě MP3 a měnilo
  dva produkční `app.js`. `main` pak nebyl čistý, profilové workspaces se
  zablokovaly a bylo nutné soubory ručně uklízet a znovu dorovnávat.
- Typ: opakující se
- Řešení nalezeno: 29072026
- Řešení: Pro místní kontrolu používat `daily_3am.py --local-preview`. MP3 vznikne
  jen v ignorované složce `data/daily_3am/previews/`; produkční soubory ani denní
  stav se nezmění. Produkční MP3 vytváří až GitHub Pages workflow ve svém
  dočasném runneru.

### LL-002 — Slovníkové aplikace: konzistence kódu, mappingu a obrázků

- Problém: Obrázky se nemusí zobrazovat, přestože mapping vypadá správně.
  Příčinou může být záměna variant aplikace nebo mappingu, neúplný `Pict`, jiná
  cesta na cílovém zařízení, starý obsah v paměti nebo rozdíl ve formátu či
  názvu souboru. Lokální obrázky navíc nemají znečišťovat Git.
- Typ: opakující se
- Řešení nalezeno: 29072026
- Řešení: Každou variantu aplikace udržovat odděleně. Kontrolovat celý řetězec
  `CSV -> mapping.json -> skutečný soubor v Pict -> dekódování aplikací`,
  ideálně diagnostikou přímo na cílovém zařízení včetně cest, počtů a
  kontrolních součtů. Mapping před změnou zálohovat, na zařízení nahrát do všech
  skutečně používaných míst a aplikaci restartovat. Chybějící obrázky doplňovat
  podle výsledku úplného auditu. Před webovým syncem navíc vypsat nepoužívané
  assety; bez samostatně potvrzeného mazání je zachovat. Lokální či iCloudové
  servisní obrázky držet mimo Git pomocí přesného lokálního exclude.

### LL-003 — Proměnlivý provozní stav neověřovat jen z projektové paměti

- Problém: Potvrzená aktivace rodinného kalendáře se po runtime kroku
  nepropsala do kanonické git-safe paměti. Pozdější bezpečný audit nečetl
  soukromou konfiguraci a aktivní souhrny proto vedly režim jako neověřený.
- Typ: opakující se
- Řešení nalezeno: 01082026
- Řešení: U dotazů typu `je aktivní`, `běží` nebo `je připraveno` nejprve
  použít dostupný redigovaný read-only live audit. Paměť používat jako
  historický kontext a bezpečnostní pravidla, ne jako důkaz současného runtime
  stavu. Po významné provozní změně zapsat git-safe redigovanou účtenku bez
  tajemství a soukromého obsahu.

### LL-004 — Sdílený provozní stav nesmí být relativní k profilovému workspace

- Problém: Izolovaný profil hledal záznam poslední zálohy ve své kopii projektu,
  takže hlásil chybějící zálohu, i když ji kanonický projekt správně evidoval.
- Typ: opakující se
- Řešení nalezeno: 02082026
- Řešení: Provozní stav společný pro všechny profily rozpoznávat přes kanonický
  kořen projektu. Profilové workspaces stav pouze čtou nebo aktualizují ve
  společném umístění; nevytvářejí vlastní kopie, které by se mohly rozejít.

### LL-005 — Procvičování slovíček může zablokovat direct-main vývoj

- Problém: Slovníkové aplikace při běžném procvičování zapsaly příznaky `HT`
  přímo do verzovaných CSV. Zdrojový `main` tím zůstal pracovní, takže Knihovna
  správně povolila chat, ale bezpečnostní brána odmítla další zapisovací tah.
- Typ: opakující se
- Řešení nalezeno: 04082026
- Řešení: Nejdřív ukončit slovníkové aplikace, ověřit, že diff obsahuje jen
  očekávané změny `HT`, provést povinný společný audit všech tří slovníků,
  mappingů, vět a obrázků a potom změny uložit jako samostatný cílený commit.
  Tréninkový stav bez výslovného pokynu nezahazovat.

### LL-006 — Lokální katalog může omylem otevřít jen ukázková data

- Problém: Family Video Organizer v Cockpitu servíroval verzovanou veřejnou
  šablonu se třemi ukázkovými záznamy, přestože úplný soukromý balíček existoval.
  Generátor navíc nepočítal již zachované video, pokud chybělo v původním zdroji.
- Typ: opakující se
- Řešení nalezeno: 04082026
- Řešení: Lokální katalog má přednostně vybrat ověřený soukromý balíček a při
  jeho neúplnosti bezpečně spadnout na veřejnou šablonu. Po obnově balíčku
  ověřit počty dat, náhledů a skutečně existujících videí; generátor má jako
  dostupný započítat i již přítomný cílový soubor.

### LL-007 — Unit test nesmí číst živý iCloudový zdroj

- Problém: Plná checkpointová brána zůstala viset v testu hlavního stavu
  Cockpitu, protože test neizoloval načítání urgentních připomínek a sáhl do
  živého iCloudového zdroje.
- Typ: opakující se
- Řešení nalezeno: 05082026
- Řešení: Ve stavových unit testech stubovat všechny loadery napojené na externí
  nebo soukromé zdroje, včetně urgentních připomínek. Po opravě nejprve spustit
  přímo dříve visící test a potom celou plnou bránu.

### LL-008 — Modelová účtenka není důkaz serverového dokončení

- Problém: Human–Adam vystavil dokončovací účtenku a server vytvořil checkpoint,
  ale výsledek se doplnil jen do lokální odpovědi. Další modelový tah proto
  nemusel vědět, zda brána a Git operace skutečně uspěly.
- Typ: opakující se
- Řešení nalezeno: 05082026
- Řešení: Výsledek zapisovacího tahu ukládat jako samostatný redigovaný private
  serverový stav. Před dalším tahem jej ověřit proti historii `main` a čistotě
  workspace, zobrazit v Cockpitu a vložit do modelového kontextu. Neuzavřený,
  nejistý nebo neověřitelný stav nesmí nový zapisovací tah tiše přepsat.

### LL-009 — Dokončení nesmí být životně závislé na chatovém HTTP tahu

- Problém: I se správnou modelovou účtenkou a serverovou diagnostikou mohl pád
  nebo restart Cockpitu přerušit testovací bránu, checkpoint či převzetí do
  `main`; po návratu z chatu už neexistoval vykonavatel, který by přesně stejnou
  práci bezpečně dokončil.
- Typ: opakující se
- Řešení nalezeno: 05082026
- Řešení: Po přijetí platné účtenky uložit samostatnou private dokončovací úlohu
  s přesným otiskem WIP, Git základem a idempotentním klíčem. Worker běží mimo
  chatový tah, čekající úlohu obnoví po restartu a přechodnou chybu procesu
  brány zopakuje nejvýše jednou; chybu testů neopakuje. Idempotentní klíč uložený
  v commit traileru umožní dokončit zachovaný commit bez vytvoření druhého.

### LL-010 — iCloud placeholder není automaticky nové čekající doručení

- Problém: Cockpit počítal každý odložený iCloud soubor s chybou `EDEADLK` jako
  nové čekající stažení, i když už měl tentýž soubor úplně uložený v private
  indexu a připomenutí mohlo být dávno splněné. Karta proto trvale hlásila
  zaseknutý iCloud a opakovala pomalé hydratační pokusy.
- Typ: opakující se
- Řešení nalezeno: 05082026
- Řešení: Před hydratací porovnat přesnou cestu, velikost, čas změny a přítomnost
  uloženého těla. Pouze úplná shoda znamená bezpečně indexovaný nezměněný zdroj;
  nový, změněný nebo neúplný placeholder zůstává čekajícím stažením.

### LL-011 — Projektový audit nesmí tiše vydávat starý agregát za aktuální stav

- Problém: Automatické checkpointy správně aktualizovaly kanonické handoffy a
  TVBCP, ale ne souhrnný `ACTIVE_PROJECTS.md`. Systémový audit četl hlavně tento
  starší agregát, takže nové milníky opakoval jako zastaralý aktuální stav.
- Typ: opakující se
- Řešení nalezeno: 07082026
- Řešení: Před projektovým reportem porovnat Git stáří agregátu s kanonickými
  handoffy/TVBCP. Pokud je kanonická paměť novější, report musí drift viditelně
  přiznat a doporučit synchronizaci; nesmí starý souhrn prezentovat bez
  varování. Potvrzený Human–Adam checkpoint od 2026-08-07 aktualizuje handoff,
  TVBCP i primární řádek `ACTIVE_PROJECTS.md` v jediném commitu a při chybě
  trojici obnoví. Terminálové commity mimo tento workflow se dál dorovnávají
  ručně.
- Doplnění 05092026: Práce na zkratce v projektu Cockpit sama neobnovuje
  samostatný pozastavený proud Mobile Input. Jeho řádek se při práci na
  připomínkách 30082026 změnil na `active`, katalog zůstal `paused`, P2.
  Návrat pouze tohoto pole na `paused` odstranil rozpor i živou P1 kartu.
  Režim a prioritu souvisejícího proudu nepřebírat z právě vyvíjeného projektu;
  při skutečné změně režimu musí souhlasit katalog i souhrnný registr.

### LL-012 — IMAP složka s mezerou musí být při SELECT správně zakódovaná

- Problém: Trvalé mazání iCloud e-mailů z koše opakovaně selhávalo, protože
  skutečná složka `Deleted Messages` byla předána příkazu IMAP SELECT bez
  uvozovek a server ji odmítl jako chybný příkaz.
- Typ: opakující se
- Řešení nalezeno: 12082026
- Řešení: Před IMAP SELECT zakódovat název složky stejnou bezpečnou funkcí jako
  před MOVE/COPY. Při diagnostice nejdřív read-only ověřit skutečnou složku
  označenou `\\Trash` a jednoznačné nalezení kandidátů podle Message-ID; teprve
  potom opakovat samostatně potvrzené nevratné mazání.

### LL-013 — Checkpoint nemá blokovat veřejná média jen podle přípony

- Problém: Human–Adam odmítl veřejný obrázek webového prototypu, protože
  checkpoint považoval každé PNG, MP3 nebo jiné médium za citlivé bez ohledu na
  jeho skutečnou cestu.
- Typ: opakující se
- Řešení nalezeno: 12082026
- Řešení: Běžné obrázky, audio a video povolit v libovolné verzované části repa
  do 25 MiB na soubor. Nadále blokovat soukromé a env cesty i neprůhledné
  dokumenty a balíky; stejný kontrakt používat při checkpointu, převzetí i
  synchronizaci workspace z `main`.

### LL-014 — Vlákno s generovaným obrázkem může překročit rámec app-serveru

- Problém: Human–Adam se po vytvoření obrázku nedokázal znovu připojit, přestože
  Cockpit, app-server i privátní socket běžely. Obnova vlákna vrátila jeden
  WebSocket rámec o velikosti přibližně 18 MiB a klient jej odmítl původním
  limitem 8 MiB jako `MESSAGE_TOO_BIG`.
- Typ: opakující se
- Řešení nalezeno: 13082026; rozšířeno 02092026
- Řešení: U privátního Unix-socket transportu zachovat konečný limit. Původních
  32 MiB stačilo pro rámec kolem 18 MiB, ale dlouhá MMTX relace se čtyřmi dalšími
  obrazovými sadami dosáhla 46 323 050 B; ověřený limit je proto 64 MiB. Při
  podobné chybě nejdřív ověřit vnitřní příčinu WebSocket uzavření; samotná
  existence socketu a úspěšný `initialize` ještě nedokládají, že se vejde
  odpověď `thread/resume` s nahromaděnými médii.

### LL-015 — Obrazový výstup modelového tahu není automaticky kandidát chatu

- Problém: Human–Adam správně vytvořil několik `imageGeneration` výstupů, ale
  session hub persistoval pouze textovou odpověď. UI četlo jiné private
  kandidátní úložiště, takže obrázky existovaly uvnitř app-server vlákna, ale v
  chatu se nezobrazily.
- Typ: opakující se
- Řešení nalezeno: 13082026
- Řešení: Při potvrzeném dokončení tahu zachytit nejvýše osm dokončených
  obrazových položek, před veřejnou odpovědí je idempotentně a create-only
  importovat do private kandidátů a pro jednu zprávu zobrazit galerii. Base64
  data ani lokální cesty nepersistovat do session JSON a nevystavovat přes API.

### LL-016 — Retence podle dnů neomezuje autosave dlouhé relace

- Problém: Autosave každých deset minut ukládal celou rostoucí Codex relaci a
  třídenní retence proto chránila stovky téměř shodných velkých kopií. Ruční
  úklid fungoval, ale při dlouhé relaci uvolnil jen malou část prostoru.
- Typ: opakující se
- Řešení nalezeno: 14082026
- Řešení: Aktuální `latest` obnovu dál přepisovat každých deset minut, historický
  JSONL/TXT pár vytvářet nejvýše jednou za hodinu a po každém autosave
  automaticky ponechat pouze 12 nejnovějších časů. Stav autosave současně hlásí
  varování pod 30 GiB a kritický stav pod 15 GiB volného místa.

### LL-017 — Logická velikost souborů není zaručený zisk volného místa na APFS

- Problém: Cleanup správně smazal potvrzenou sadu starých autosave souborů, ale
  odhad uvolnění vznikl součtem jejich logických velikostí. Volné místo na SSD
  proto nevzrostlo o hlášený součet; copy-on-write bloky mohly být sdílené a
  souběžně místo používaly cache, VM/swap a otevřené smazané soubory.
- Typ: opakující se
- Řešení nalezeno: 15082026
- Řešení: Před cleanupem i po něm odděleně měřit logickou velikost, fyzicky
  alokované bloky a `df`. Uživatelům nikdy neslibovat logický součet jako
  skutečně uvolnitelné GiB. Proměnlivé cache a VM ověřit znovu po restartu;
  CloudKit ani jiné systémové cache nemazat automaticky.

### LL-018 — Dokončený app-server tah může ztratit transportní účtenku

- Problém: Codex lokálně dokončil tah a uložil finální odpověď i `task_complete`,
  ale Human–Adam neobdržel povinné `turn/completed` a správně ponechal doručení
  jako nejisté. Opakované odeslání by mohlo zdvojit už provedenou práci.
- Typ: opakující se
- Řešení nalezeno: 16082026
- Řešení: Zprávu nikdy automaticky neposílat znovu. Po transportní chybě přijmout
  dokončení jen z právě jednoho lokálního záznamu se shodným vláknem a client
  ID, shodnou finální odpovědí a následným `task_complete`; při jakékoli
  nejednoznačnosti zachovat `delivery_unknown` a vyžádat ruční recovery audit.

### LL-019 — Finální app-server událost nemusí opakovat vstupní položku

- Problém: Codex 0.147 poslal správnou `userMessage` přes `item/completed`, ale
  finální `turn/completed` obsahoval pouze výstupní položky. Klient dříve
  ověřený vstup zahodil, dokončený tah označil za nejistý a uzavřel spojení.
- Typ: opakující se
- Řešení nalezeno: 16082026
- Řešení: Zachovat dříve přijatou `userMessage` pouze při přesné shodě
  `clientId` a jen pokud finální tah neobsahuje žádnou uživatelskou položku.
  Pokud finále uživatelskou položku obsahuje, použít ji autoritativně a při
  neshodě dál selhat uzavřeně.

### LL-020 — Lokální pomocná aplikace se z iPhonu otevírá pod původem Cockpitu

- Problém: Cockpit mohl na Macu otevřít ScanDocu přes `127.0.0.1:8766`, ale na
  iPhonu stejná adresa ukazuje na telefon. Omezená náhradní revize přímo v kartě
  Cockpitu zároveň neukázala celý dokument a všechny nástroje ScanDocu.
- Typ: opakující se
- Řešení nalezeno: 22082026
- Řešení: Plné rozhraní lokální pomocné aplikace vést přes úzce allowlistovaný
  same-origin průchod pod Cockpitem. Konkrétní položku předávat jen neprůhledným
  bezpečným odkazem a na backendu jej znovu vyhodnotit proti kanonickému indexu;
  do klienta neposílat interní cestu ani skutečný identifikátor dokumentu.

### LL-021 — Historický handoff není aktuální ToDo

- Problém: Přehled „Co teď?“ doplňoval volná místa do pevného počtu tří kroků
  také z historických handoffů. Dokončené nebo neověřené návrhy tak vypadaly
  stejně závazně jako položky ze živé provozní fronty.
- Typ: opakující se
- Řešení nalezeno: 28082026
- Řešení: Aktuální ToDo sestavovat pouze z živé fronty a živě prokázaných
  rozporů. Handoffové kroky zobrazit odděleně jako návrhy z projektové paměti,
  vždy se zdrojem a stářím důkazu; počet aktuálních úkolů nikdy nedoplňovat na
  předem dané číslo.

### LL-022 — Push webových souborů není důkaz GitHub Pages publikace

- Problém: Nový VocabularyEN commit byl čistě na `main` i `origin/main`, ale
  poslední Pages workflow běželo nad starším commitem. Veřejná aplikace proto
  nový audio manifest a MP3 ještě neobsahovala.
- Typ: opakující se
- Řešení nalezeno: 29082026
- Řešení: Před tvrzením o produkci porovnat commit posledního úspěšného Pages
  workflow s cílovým commitem. Při neshodě spustit ruční Pages workflow a po
  jeho úspěchu nezávisle ověřit veřejný HTTP stav i shodu hashů manifestu,
  aplikačního JavaScriptu a reprezentativních assetů.

### LL-023 — Pages workflow může uspět dříve než úplná produkční účtenka

- Problém: GitHub workflow správně publikoval cílový commit, ale deployment se
  v API objevil o několik sekund později a lokální Python `urllib` navíc neměl
  použitelný certifikační řetězec. Produkce běžela, zatímco serverová účtenka
  dvakrát správně zůstala fail-closed.
- Typ: opakující se
- Řešení nalezeno: 29082026
- Řešení: Po dokončení přesného workflow omezeně čekat na success deployment
  stejného commitu a závěrečný HTTPS smoke provést přes systémový curl. Nejasný
  výsledek nikdy automaticky neopakovat; nejprve korelovat workflow ID,
  deployment ID, commit a veřejný HTTP stav.

### LL-024 — Server-owned operaci nesmí autorizovat ani blokovat modelová obálka

- Problém: Přesný uživatelský `p+n` byl správně autorizovaný, ale vadná
  modelová provozní obálka jej zablokovala ještě před serverovým backendem.
- Typ: opakující se
- Řešení nalezeno: 29082026
- Řešení: Pro přesný příkaz a deklarovaný produkční cíl vytvořit kanonický
  serverový požadavek bez ohledu na chybějící, platnou nebo vadnou modelovou
  obálku. Model smí dodat pouze viditelný text; autorizaci, volbu operace a
  produkční účtenku vlastní server.

### LL-025 — Python HTTPS klient na tomto Macu potřebuje projektový CA bundle

- Problém: Nový GitHub API klient přes `urllib` selhal na
  `CERTIFICATE_VERIFY_FAILED`, i když systémový `curl` stejné HTTPS API ověřil.
- Typ: opakující se
- Řešení nalezeno: 30082026
- Řešení: U dlouhodobého Python klienta vytvořit explicitní TLS context přes
  `ssl.create_default_context(cafile=certifi.where())`; chybu dál hlásit
  redigovaně a fail-closed. Systémový `curl` ponechat pro omezené diagnostické
  ověření, ne jako skrytý runtime fallback zapisovacího workflow.

### LL-026 — Unit test lokálního indexu nesmí dědit živý GitHub inbox

- Problém: Dva testy lokálního přehledu připomenutí zavolaly produkční GitHub
  synchronizaci z `.env`; otevřená skutečná Issue změnila jejich dočasné počty.
- Typ: opakující se
- Řešení nalezeno: 30082026
- Řešení: V každém unit testu lokálního indexu výslovně nahradit externí GitHub
  synchronizaci deterministickým neaktivním výsledkem. Živý inbox patří jen do
  samostatného integračního testu s přesnou korelací a bezpečnostními hranami.

### LL-027 — Migrace transkripce není jen výměna názvu modelu

- Problém: Nový `gpt-transcribe` používá místo jednoho `language` strukturovaná
  pole `languages` a `keywords`; lokální SDK je ještě nemusí mít v běžném
  podpisu a záložní multipartová `curl` cesta potřebuje správné názvy polí.
- Typ: opakující se
- Řešení nalezeno: 31082026
- Řešení: Zachovat endpoint i výstupní kontrakt, nová pole v SDK poslat přes
  `extra_body` a v multipart formuláři jako opakovaná `languages[]` a
  `keywords[]`. Ověřit obě cesty unit testy a jediným syntetickým API smoke bez
  soukromého audia; u klíčových slov následně hlídat i možné vložení
  nevysloveného termínu.

### LL-028 — Citlivý dokument nesmí automaticky zdědit plný OCR index

- Problém: Standardní import dokumentu ukládá extrahovaný text do soukromého
  fulltextového indexu. U bankovní smlouvy by tím zbytečně duplikoval rodné
  číslo, adresu a aktivační údaj, přestože pro hledání stačí bezpečný souhrn.
- Typ: opakující se
- Řešení nalezeno: 31082026
- Řešení: Pro citlivé bankovní dokumenty použít restricted import. Originál
  zachovat v private vaultu, úplné účetní identifikátory uložit jen do
  samostatných restricted metadat a do běžného indexu zapsat pouze maskovaný
  text. Surový OCR text, rodné číslo, adresu a aktivační údaje neindexovat ani
  neduplikovat do metadat.

### LL-029 — Přímý curl klient nesmí opakovat každou chybu 429 nebo 503

- Problém: Přímá multipartová cesta hlasového přepisu přes systémový `curl`
  neznala HTTP stav ani `Retry-After`; obecné opakování všech chyb by navíc
  zbytečně opakovalo kvótové a platební chyby.
- Typ: opakující se
- Řešení nalezeno: 03092026
- Řešení: Z odpovědi odděleně načíst pouze HTTP stav a `Retry-After`, opakovat
  nejvýše třikrát jen přesné dvojice `429/slow_down` a
  `503/server_is_overloaded`, bez hlavičky použít krátký exponenciální backoff
  s jitterem a celý běh držet v jednom časovém rozpočtu. Do logu propustit jen
  stav, kód, číslo pokusu a čekání; nikdy klíč, audio ani celé tělo chyby.

### LL-030 — Projektové audio a skutečné asociace Apple Music

- Problém: Opravený generátor s `afplay` nezabránil dalším importům pracovního
  audia při obecném otevření nebo dvojkliku; Music byla výchozí aplikací.
- Typ: opakující se
- Řešení nalezeno: 05092026
- Řešení: Projektové audio přehrávat explicitně přes `afplay`, browser nebo
  QuickTime. Po schválené změně asociací ověřit skutečnou aplikaci pro konkrétní
  soubor přes NSWorkspace, nestačí návratový kód nastavení. M4A na tomto Macu
  používá `com.apple.m4a-audio`, ne pouze `public.mpeg-4-audio`. Před úklidem
  Music sestavit seznam podle persistent ID, zachovat audio a ověřit ostatní
  záznamy i playlisty před/po; chybějící místní soubor neznamená chybějící
  záznam knihovny. Podrobnosti jsou v handoffu z 2026-09-05.

### LL-031 — Chybná výslovnost jedné hotové slovníkové MP3

- Problém: Aria četla samostatné `cat` jako jméno Kate; správný text v CSV
  ani opakované generování s interpunkcí chybu neodstranily.
- Typ: opakující se
- Řešení nalezeno: 05092026
- Řešení: pro anglické `cat` použít cílenou výjimku hlasu Jenny v generátoru
  a manifestu. Strojový přepis se změnil z `Kate.` na `Cat.`; poslech na
  cílovém zařízení zůstává závěrečnou kontrolou. Výjimku udržet při rebuild,
  zachovat učební text a změnit adresu MP3 kvůli cache. Testy ověřily úzký
  rozsah a opakované sestavení bez dalších generování. Publikaci Pages
  prokazovat zvlášť podle LL-022.

### LL-032 — Směr překladu nesmí resetovat historii losovaných karet

- Problém: VocabularyEN zahrnoval směr překladu do identity vybrané sady.
  Přepnutí směru proto při dalším losování vymazalo historii a mohlo vrátit
  již zobrazenou kartu před vyčerpáním sady. Počítadlo navíc nikdy neukázalo
  nulu a přechod do dalšího kola nebyl viditelný.
- Typ: opakující se
- Řešení nalezeno: 05092026
- Řešení: identitu sady odvozovat z filtru, okruhů a ID karet; směr mění jen
  zobrazení. Počítat dosud nezobrazená ID, oznámit konec kola a zamezit
  bezprostřednímu opakování při přechodu mezi koly. Reprodukční testy ověřily
  opravu i tři celá kola se změnami směru. Shodný text u různých významů
  není opakování stejné karty.

### LL-033 — Audit MMTX musí zahrnout i dialogy bez slovníčku

- Problém: Import kontrolující jen čtyři historické slovníčky hlásil úplnost,
  přestože v mluvených textech dalších scén, školních pokynech a narozeninách
  chybělo ve VocabularyEN 120 základních hesel.
- Typ: opakující se
- Řešení nalezeno: 05092026
- Řešení: porovnat i anglické klíče audio manifestů a deklarované texty
  úvodu/narozenin; ověřit shodu zdrojů s veřejným MMTX. Tvary slov mapovat
  explicitně, jména a domluvené výjimky zachovat. Nové heslo musí mít
  kurátorský CZ, Sentence, SentenceT, Benji a audio; neznámé budoucí slovo
  blokuje falešné hlášení úplnosti. Po doplnění prošel audit bez mezer,
  30 cílených testů a dekódování všech 239 nových MP3.

### LL-034 — Prázdný autosave TXT neznamená chybějící historii

- Problém: latest_session.txt obsahoval pouze hlavičku, přestože JSONL
  obsahoval přerušené zadání a důkazy uložených obrázků.
- Typ: opakující se
- Řešení nalezeno: 06092026
- Řešení: při povolené obnově číst zprávy response_item/message z JSONL,
  nikoli spoléhat jen na TXT export. Nevypisovat obrazové base64 ani celé
  interní obálky. Stav následně ověřit podle manifestu, receipts a souborů;
  poslední lidská zpráva hlásila 45 obrázků, na disku již bylo 47. Díky
  této kontrole se dogenerovaly pouze dvě zbývající položky z 49.


## 2026-09-06 — Oddělení offline lekcí bez ztráty postupu

- Typ: opakujici se.
- Problém: postup ukládaný podle číselné pozice by po přeuspořádání lekcí
  přiřadil rozepsaný kód jinému tématu.
- Řešení: trvalá ID v balíčku i postupu; migraci odvozovat z pevné původní
  mapy sedmi lekcí, nikoli z nového pořadí. Původní data zachovat, nový formát
  ukládat samostatně s byte-for-byte zálohou a detekcí konfliktu.
- Ověření: PythonSeSamanthou, 27 testů a skutečné Tk GUI; znovuotevření
  s obráceným pořadím zachovalo výběr, sedm pokusů i dokončení. Testy pouze
  nad dočasnými daty, žádný zásah do Mílova skutečného postupu.
- Další ověření 2026-09-06: třetí balíček byl přidán pouze do kurzy původního
  vydaného ZIPu 1.5. GUI dokončilo všech sedm lekcí a obnovilo postup; kontrolní
  porovnání zachovalo všech 79 původních distribuovaných souborů. Kompatibilitu
  nového obsahu dokazovat i proti skutečně vydané aplikaci, nejen aktuálním zdrojům.


## 2026-09-06 — Samostatný projekt versus pracovní proud Cockpitu

- Typ: opakujici se.
- Problém: nový aktivní tabulkový řádek v ACTIVE_PROJECTS automaticky podléhá
  invariantě úplnosti katalogu pracovních proudů. U samostatné učebny bez
  Cockpit integrace tak test katalogu odhalil chybějící vazbu.
- Řešení: samostatný terminálový projekt vést explicitně v textové části
  registru a přes index, projektovou paměť a handoff. Do tabulky pracovních
  proudů ho zařadit až spolu se skutečně dohodnutou integrací; nezakládat
  implicitně TVBCP jen kvůli registraci aplikace.
- Ověření: po přesunutí záznamu Python se Samanthou prošlo všech 28 testů
  test_human_adam_workstream_catalog a test_project_audit_report. Při příštím
  přidávání projektu spustit tyto testy až po finální úpravě registru.

## 2026-09-06 — Přenosný Python HTTPS klient bez pip závislostí na macOS

- Typ: opakujici se.
- Problém: Python.org instalace neměla CA bundle; urllib skončil na
  CERTIFICATE_VERIFY_FAILED. Souvisí s LL-025, zde však aplikace nesmí
  vyžadovat instalaci certifi na uživatelském Linuxu.
- Řešení: zachovat ssl.create_default_context() a na macOS přidat existující
  systémový /etc/ssl/cert.pem přes load_verify_locations. Na Linuxu ponechat
  standardní CA; nevypínat ověřování certifikátů a neměnit systémovou instalaci.
- Ověření: PythonSeSamanthou 1.4, skutečný HTTPS požadavek do OpenAI i navazující
  otázka prošly po této změně. Klíč ani osobní data se při ověření nevypisovaly.

## 2026-09-06 — Codex tutor přes ChatGPT nesmí tiše použít API přihlášení

- Typ: opakujici se.
- Problém: automatický Codex může dědit jiný způsob autentizace a API proměnné.
  Samotné forced_login_method může podle dokumentace odhlásit neslučitelný login.
- Řešení: před dotazem nejprve codex login status bez vynucení; API/unknown login
  odmítnout bez spuštění a bez logoutu. Až pro ověřené ChatGPT použít explicitní
  forced_login_method, čisté prostředí bez API proměnných a --ignore-user-config.
- Ověření: PythonSeSamanthou 1.5, testy odmítnutí API bez mutace přihlášení,
  skutečné ChatGPT Codex vysvětlení/doptání i odpověď v Tk okně na Macu.


## 2026-09-08 — Přerušitelná zvuková sekvence v Tk

- Typ: opakujici se.
- Problém: trénink musí čekat na dočtení věty a při změně výběru zabránit
  starým timerům pokračovat v nové sekvenci.
- Řešení: jeden vlastněný audio proces, jeden Tk timer a generační identita
  callbacku; při pauze nebo přepnutí zrušit timer i vlastní proces. Pokračování
  znovu přehraje přerušenou výpověď. Žádné globální ukončování přehrávačů.
- Ověření: testy čekání na audio, pauzy, pozdního callbacku, chyby hlasu a
  skutečný Tk průchod v Tréninku sloves; macOS Thomas dokončil ukázku.


## 2026-09-08 — Ověření samostatné VocabularyFR.app pro sdílený iCloud

- Typ: opakujici se.
- Problém: úspěšný zdrojový Tk běh nedokazuje správně zabalená data; PyInstaller
  onedir používá odkazy Frameworks → Resources. Finder může pod Desktopem
  přidávat metadata odmítaná strict codesign i po očištění.
- Řešení: nový izolovaný build ideálně v /private/tmp, kontrolovat skutečnou
  .app na dočasné kopii seedů, respektovat resource odkazy a ověřit podpis.
  Janina edice výslovně předává --data-dir vedle .app; nepřepíná na jiný CSV.
- Ověření: aktuální bundle prošel strict podpisem; z místní sdílené kopie
  fungovalo 406 řádků, 107 ilustrací a psaný recall. Data a stará .app nejprve
  zálohované, přenos porovnaný včetně odkazů a SHA-256.


### 2026-09-10 – Přehled terminálových relací Codexu
- Typ: opakující se.
- Problém: hledání podřetězce `codex` označovalo screen/shell a podpůrné procesy za konverzace; OS cwd skutečného Codexu navíc nemusí odpovídat projektu.
- Ověřené řešení: rozlišit nativní spustitelný soubor a argumenty služby, ověřit TTY a vlastnictví, projekt odvodit i z `-C` / `--cd`. Před potvrzeným signálem obnovit identitu včetně času startu; předky správce chránit. Prohlížečový test ukončení používal jen vlastní syntetické procesy.


### Screen na macOS obsahuje systémový login obal

- Problém: Kontrola vlastníka všech potomků odmítala běžný vlastní screen, protože macOS mezi něj a uživatelský program vkládá root proces login.
- Typ: opakující se
- Řešení nalezeno: 2026-09-12 08:31 CEST
- Řešení: Ověřit vlastního správce screenu a úzce rozpoznat přímého potomka login s přesnými argumenty pro stejného uživatele a ověřeným spustitelným souborem. Ostatní cizí procesy, Codex a služby zůstanou chráněné; před uzavřením znovu ověřit identitu i členství. Prohlížečový test se skutečným testovacím screenem prošel.


### 2026-09-12 – Ovládání MMTX musí sledovat skutečnou velikost obrazu

- Typ: opakující se.
- Problém: scéna s pevným poměrem stran může být kvůli výšce okna výrazně užší než viewport; samotný mobilní media query pak nechá příliš velký dialog a tlačítka zakryjí postavy.
- Řešení: rozložení odvodit od šířky kontejneru scény, zkrátit dialogovou kartu a v závěrečném obrazu umístit ovládání do volné části. Kontrolovat skutečné obdélníky prvků i screenshot, nejen průchod JavaScriptu.
- Ověření: scéna 5 prošla celým příběhem a pěti rozměry 1440×1000 až 390×844; dialog se nekříží s tlačítky a všech šest postav závěru je viditelných.


### 2026-09-12 – Počet objektů musí souhlasit i v přechodovém obrázku

- Typ: opakující se.
- Problém: tři správně animované klády překryl obraz hotového mostu jen se dvěma kládami; třetí se vizuálně objevila až v dalším obrazu. Samotný počet DOM prvků chybu neodhalil.
- Řešení: opravovat konkrétní překrývající ilustraci a při vizuálním retestu kontrolovat okamžik po animaci před následujícím krokem. Při výměně pod stejným názvem změnit verzi URL v preloadu i src.
- Ověření: browserový screenshot po třetím klepnutí před Benjiho přechodem ukazuje tři klády; veřejný WebP po publikaci přesně odpovídá opravenému souboru.


### LL-035 — Zkrácení instrukcí při zachování projektového kontraktu

- Problém: vstupní instrukce duplikovaly handoff návody; recovery navíc
  používalo slovní priority, zatímco AGENTS.md vyžadovalo 1–3.
- Typ: opakující se
- Řešení nalezeno: 12092026
- Řešení: jediný postup handoffu v session_recovery_rules.md, kontrakt TVBCP
  v project_tvbcp_rules.md a krátké situační odkazy z AGENTS.md. Při přesunu
  ověřit zachování povinností, platnost odkazů a původních historických zápisů.
  Rozlišovat terminálový commit od oprávnění modelu v Cockpitu. Změna Markdownu
  sama nedokazuje změnu serverových promptů ani zrychlení modelu.
- Ověření: 41 cílených testů, rychlá brána a kontrola odkazů prošly;
  bezpečnostní návody i historické záznamy zůstaly beze změn.
- Doplnění 2026-09-12: serverové prompty je nutné ověřit na skutečné cestě
  přes profilovou/lazy factory a start/resume vlákna. Starý zákaz TVBCP zápisu
  při milníku odporoval povinnému projektovému zápisu; nahrazen zápisem pouze
  při writable=true do správné kanonické dvojice, bez oprávnění ke commitu.
  Cílená sada 198 testů prošla. Aktivaci dokládá až samostatné nasazení a
  načtení nových instrukcí, nikoli samotný commit nebo zarovnání workspace.


### LL-036 — Fotografie na pozadí potřebují pevný cíl a bezpečné opakování

- Problém: limit původního snímku blokoval upload ještě před zmenšením; čekání
  na foto brzdilo novou kartu. Souběžné připojení a editace mohou přepsat metadata.
- Typ: opakující se
- Řešení nalezeno: 12092026
- Řešení: připravovat ihned po výběru mimo UI vlákno, kartu uložit samostatně
  a fotografii navázat na její neměnné ID. Opakovaný request musí mít stejné ID
  a kontrolu obsahu; archivní zápisy serializovat, registry zapisovat atomicky.
  Přenos po zavření stránky neslibovat. Při skrytí formulářových polí ověřit
  vypočtený display: pozdější display:grid může přebít obecné .hidden.
- Ověření: velké PNG/HEIC, ztracená odpověď po uložení bez duplicit, dvě karty,
  souběžná editace, neblokující obálka nové knihy a computed display desktop/mobil
  prošly na syntetických datech; 0 chyb JavaScriptu.

- Doplnění 2026-09-12 k LL-036: limit uploadu neomezuje celkové úložiště,
  pokud backend ještě ukládá originál, čitelnou kopii a náhled. Pro ilustrace
  použít jeden JPEG do 285 KiB a náhled do 20 KiB, při měření deduplikovat
  skutečné cesty. Zachovat zvláštní vyšší kvalitu dočasného OCR a podporovat
  také camera JPEG/MPO. Převod starých dat musí kontrolovat otisky i shodu
  metadat s registrem a mít ověřenou obnovu; úspora aktivního archivu není
  úsporou disku, pokud zůstává jednorázová záloha. Ověřeno testy a browserem.


### 2026-09-13 12:45 CEST — Připojení screenu zachovává běžící Codex

- Typ: opakující se.
- Problém: Po zavření terminálu může screen s Codexem pokračovat, ale uživatel k němu nemá otevřené okno. Úspěšné předání URI editoru samo neprokazuje připojení.
- Ověřené řešení: Rozlišit obnovu od ukončení a od `codex resume`; ověřený screen spustit přímo jako terminál VS Code přes `screen -d -r <socket>`. Připojený stav vyžaduje potvrzení převzetí. PID/start a ochrany ověřit znovu při jednorázovém převzetí.
- Ověření: Vývojové okno skutečného VS Code připojilo vlastní testovací screen a zachovalo PID screenu i vnitřních procesů. UI test používá náhradní DOM; skutečný první klik z Cockpitu zůstává samostatným ověřením.

### 2026-09-13 – Viditelná šipka může být zakrytá úvodním audio panelem

- Problém: návrat ve scénách MMTX 4 a 5 byl vidět, ale úvodní audio překryv zachytával kliknutí. Samotná kontrola href ani viditelnosti chybu neodhalila.
- Řešení: ovládací vrstvu umístit nad audio překryv a zachovat průhlednost ke kliknutí mimo tlačítka. Ověřit skutečný klik ještě před spuštěním příběhu.
- Ověření: návraty 4 → 3 a 5 → 4 prošly bez spuštění audia v desktopovém i mobilním viewportu. Celá navigační sada prošla 18/18.

### 2026-09-13 — Pomalou bránu zrychlovat podle měření skupin

- Problém: celkový čas plné brány neukazuje, zda zdržuje frontend, Git integrace nebo společná příprava; vede k neúčelnému opakování či škrtání testů.
- Typ: opakující se.
- Řešení: volitelné `--unit-test-timings PATH` nad kanonickou bránou zachová stejný manifest, pořadí a výsledky; report obsahuje jen názvy, počty a časy. Testový setUp/tearDown je v čase testu, importy a společná režie zvlášť. Běžné změny ověřovat cíleně; povinné rizikové/release brány zachovat.
- Ověření: 1649/1649 v jediném plném běhu; 88 Git/workspace testů zabralo 73,5 % času. Gate/smoke uvnitř pomalých testů jsou nahrazené. Podíl tvorby repozitáře a samotných Git operací vyžaduje další dílčí měření, nelze jej vydávat za doloženou příčinu nebo hotovou úsporu.
- Navazující ověření téhož dne: dva deploy testy mají přibližně třetinu času ve společné přípravě a 98 % v Git procesech celkem. Dokončit syntetický zdroj před klonováním ušetří druhý úvodní push/sync (87 → 53 procesů přípravy), bez cache či změn vlastních scénářů. Osm měřených běhů před/po a test nezávislosti dvou sad prošly; report `reports/cockpit_deploy_fixture_pilot_2026_09_13.md`. Plná brána 1650/1650 prošla. Nízký počet vzorků ani úspora jedné fixture nejsou záruka stejného zrychlení celé brány.

### 2026-09-13 — U nákladných Git testů změřit i systémový spouštěč

- Problém: Git integrační testy zabírají většinu brány; odstranění několika přípravných operací samo nezaručuje významné zrychlení celku.
- Typ: opakující se.
- Řešení: porovnat stejný dotaz přes `/usr/bin/git` a Git vybraný pomocí `xcrun --find git`. Na Macu lze jednou při startu zjistit platnou absolutní cestu a používat ji se stejnými parametry. Při nedostupnosti, chybě, timeoutu a mimo Mac zachovat původní cestu. Nejde o cache stavu ani o důvod škrtat testy; po změně vybraného toolchainu restart procesu.
- Ověření: stejný Apple Git, medián 33 vs 12 ms ve 30 vzorcích na kombinaci; sedm cílených testů prošlo. Stejných 1655/1655 testů prošlo před i po; unittest 453,73 → 340,30 s, úspora 113,43 s (25,0 %). Report `reports/cockpit_git_launcher_2026_09_13.md`; jeden pár úplných běhů není záruka stejné úspory na jiném stroji.
- Navazující ověření 14. 9.: sdílet jednou zjištěnou binárku také v checkpoint/deploy/batch/sync/takeover a společném Git test helperu; samostatné launchery jinak dál platí tutéž režii. Stejných 1656/1656 testů prošlo před i po; 307,14 → 261,43 s, úspora 45,71 s (14,88 % proti dnešnímu výchozímu stavu). Report `reports/cockpit_shared_git_2026_09_14.md`. Nový společný modul zařazen do povinné plné brány.

### 2026-09-14 — Při přesunu HTTP obsluh zachovat i kontrolní hranice

- Problém: přesun obsluhy z hlavního serveru může nechtěně změnit chybové odpovědi, hlavičky či pořadí autorizace; nový soubor také vypadne z původního CI/gate filtru.
- Typ: opakující se.
- Řešení: před přesunem zachytit HTTP kontrakty na izolovaném serveru se syntetickými daty, po přesunu porovnat stav/hlavičky/otisk těla. Ověřit odmítnutí před voláním backendu a skutečné vnější cesty/symlinky. Zahrnout nový modul do CI, kompilace a stejné povinné brány jako původní soubor. Před plným během rozšířit také existující inventuru adres frontendu o skutečný dispatch nového modulu.
- Ověření: dokumentový řez, 61/61 shodných HTTP kontraktů; 35 cílených testů a plná brána 1665/1665. Report `reports/cockpit_document_routes_2026_09_14.md`.
- Navazující ověření: archivační HTTP řez zachoval 53/53 kontraktů včetně MIME/disposition vložených příloh a čtení syntetického EML přes neprůhlednou referenci. Inventura adres aktualizovaná již před plnou bránou; 49 cílených testů a 1675/1675 celé sady. Report `reports/cockpit_email_archive_routes_2026_09_14.md`.

### 2026-09-14 — Grid panel může zabránit skutečnému posouvání potomka
- Projev: desktopový archiv má overflow-y:auto, ale seznam se roztáhne na celý obsah a scrollTop zůstává 0; body overflow:hidden skryje dolní zprávy.
- Příčina a řešení: automatické minimum nadřazených grid panelů; nastavit min-height:0 na panel seznamu i čtečky. Mobil již tuto hodnotu měl.
- Ověření: browser s dlouhým syntetickým seznamem, skutečný wheel posun až na poslední položku, otevření/detail/návrat a mobilní regrese. Samotná přítomnost overflow v CSS nestačí. Důkaz: reports/cockpit_email_archive_scroll_2026_09_14.md.

### 2026-09-14 11:53 CEST — Společná odezva nesmí záviset na otevřeném detailu
- Projev: akce zapíše zprávu, ale člověk ji nevidí, protože předek je zavřený details nebo překrytý dialogem.
- Řešení: společný panel nezávislý na scrollu a detailech; při modalu přesunout i live region do jeho přístupnostní oblasti. Zobrazení nesmí krást fokus, chyba nesmí sama zmizet.
- Ověření: skutečná viditelnost a překrytí přes elementFromPoint, zavřený detail, aktivní dialog, dlouhý text, blokovaný popup a síťová chyba; samotný textContent ani z-index nestačí. Důkaz: reports/cockpit_ui_u01_2026_09_14.json.

### 2026-09-14 14:18 CEST — Návrat a popup potřebují dostupnou náhradní cestu
- Projev: nákupní čtečka pouze zaměřovala opener; samostatná karta neměla návrat. Zablokovaný popup ukázal jen textovou adresu.
- Řešení: s openerem zaměřit původní okno a zavřít čtečku, bez něj navigovat na Cockpit; při odmítnutém zavření dát instrukci. Náhradní popup odkaz otevřít uživatelským kliknutím v nové kartě bez openeru, přijímat pouze HTTP(S).
- Ověření: samostatná i skutečně otevřená popup karta, uzavřený/nedostupný opener, odmítnuté zavření, zachovaný rozepsaný vstup a odstranění starého odkazu při další zprávě. Důkaz: reports/cockpit_ui_u02_2026_09_14.json.

### 2026-09-14 14:44 CEST — Kompaktní prázdný stav nesmí schovat chybu
- Projev: sbalení podle pouhého count=0 může skrýt selhání poskytovatele; grid se stretch zase natahuje nulové sousedy podle dlouhé fronty.
- Řešení: rozlišit ověřené prázdno, práci a chybu. Nuly sbalit, chyby/práci otevřít při změně stavu; stejný stav respektuje ruční rozbalení. Použít align-items:start a u dlouhých seznamů ověřit skutečné posouvání včetně klávesnice.
- Ověření: nedostupný zdroj a HTTP/provider chyba revize se zobrazí; poslední položka i původní akce zůstávají dosažitelné. Report: reports/cockpit_ui_u03_2026_09_14.json.

### 2026-09-14 15:11 CEST — Stránkování potřebuje HTTP propojení i ochranu před starou odpovědí
- Projev: backend umí offset, ale HTTP ho nepředá; uživatel zůstane na první stránce. Pomalá odpověď navíc může přepsat novější dotaz.
- Řešení: validovat parametry před poskytovatelem, předat limit/offset a použít pořadí požadavků v UI. Při chybě další stránky zachovat předchozí data a retry; nový dotaz resetuje stránku.
- Ověření: skutečné HTTP nad více než jednou stránkou včetně duplicitního indexového řádku, mimo rozsah, chyby a dotaz změněný během načítání. Návrat čtečky i blokovaný popup musí zachovat původní hledání. Důkaz: reports/cockpit_ui_u04_2026_09_14.json.

### 2026-09-14 15:25 CEST — Čekající práce není provozní porucha
- Projev: nové dokumenty, poznámky nebo čistý Git napřed drží hlavní přehled trvale ve varování; skutečná chyba zaniká.
- Řešení: použít existující prioritní frontu, práci hodnotit odděleně od provozu a chybějící zdroj neproměňovat v prázdný zelený inbox. Při selhání obnovy priorit odstranit zastaralé akční karty, ukázat neověřený stav a umožnit nové načtení.
- Ověření: syntetická práce, konflikt, divergence, chybějící záloha, výpadek/obnova API a zdroj/čas důkazu. Report: reports/cockpit_ui_u05_2026_09_14.json.

### 2026-09-14 18:36 CEST — Zavření dialogu není zahození rozepsané práce
- Projev: pevný seznam Escape zavře jinou vrstvu, Tab uteče za dialog a close/reopen vyčistí editor. Plovoucí návrat navíc může překrýt společná odezva.
- Řešení: jeden správce viditelných vrstev, původního fokusu a inertního pozadí; volat existující close obsluhy, uchovat drafty v DOM a reset ponechat explicitní. Návrat navázaný na hledání umístit k hledání.
- Ověření: skutečné Tab/Shift+Tab/Escape, vnořený náhled a Recovery, Janiččiny projekty/hledání se zobrazenou odezvou, draft nové i existující položky a hash/reload. Pouhý textContent neprokazuje dostupnost návratu. Report: reports/cockpit_ui_u06_2026_09_14.json.

### LL-037 — Podepisovaný iOS build mimo synchronizovanou Plochu

- Problém: CodeSign nad novým .app na Ploše selhal na resource fork/Finder information; inventura potvrdila FinderInfo.
- Typ: opakující se
- Řešení nalezeno: 15092026
- Řešení: nový DerivedData v /private/tmp, bez plošného mazání xattr ze zdrojů. Podepsaný build a codesign --verify --deep --strict prošly. Tým patří do ignorovaného LocalSigning.xcconfig.

### 2026-09-15 — Přerušení audia musí ukončit také stav přehrávání

- Kontext: Camino C01a, společná obsluha systémové události pro recorder a player.
- Problém: guard pouze pro záznam ignoroval přerušení poslechu; UI čekalo na další timer.
- Řešení: událost zpracovat přímo i ve stavu playing, ukončit player a aktualizovat UI; nové spuštění jen vědomou akcí.
- Ověření: regrese před opravou selhala; po opravě 30 testů, podepsaný iOS build a strict podpis OK. Testovat i bez dalšího ticku a s opakováním události; fyzický test zůstává samostatný.

### 2026-09-15 — UI test návratu nesmí znovu vytvořit ztracený vzorek

- Kontext: Camino, syntetická audio fixture pro XCTest v iOS simulátoru.
- Riziko: automatické vytvoření chybějícího vzorku při každém launchi by skrylo ztrátu dat mezi spuštěními.
- Řešení: náhodné oddělené UUID úložiště, explicitní seed pouze při prvním launchi; při návratu zakázat seed. Pomocný kód kompilovat pouze pro Debug simulátor.
- Ověření: 2 UI testy PASS, vizuální kontrola průběhu; binární program pro iPhone neobsahuje testovací vstupní značky.

### LL-038 — iPhone dostupný přes USB, ale CoreDevice neodpovídá

- Problém: Xcode ukazoval Connected a prázdný seznam aplikací, xcdevice available=true, ale devicectl info apps končilo timeoutem a log uváděl Failed to allocate RSD device.
- Typ: jednorázový
- Řešení nalezeno: 15092026
- Řešení: Přepojení kabelu nepomohlo; běžné ukončení a znovuotevření Xcode uživatelem obnovilo seznam aplikací, instalaci/spuštění i čtení metadat. Ověřit živými příkazy, samotné Connected nestačí. VPN se neměnila; příčinná souvislost s VPN nebyla prokázána.

### 2026-09-16 — Grafické seskupení pokračování není sloučení audio souborů

- Kontext: Camino C01b po telefonním přerušení a vědomém Pokračovat.
- Riziko: Karta „Část 1 / Část 2“ může vypadat jako přilepený jediný záznam a zakrýt, zda se původní médium přepsalo.
- Řešení: bez čtení audia porovnat snímek UI s technickými `started.json`/`completed.json`: rozdílná ID a CAF, první část `interrupted=true`, druhá má continuation na stejné session, předchozí část a evidovanou pauzu.
- Ověření: fyzický iPhone po hovoru měl dvě samostatná média; CoreDevice metadata potvrdila návaznost a UI je správně seskupilo. Samotný vzhled karty ani jediný součet času by nestačil.

### LL-039 — Připojené Bluetooth zařízení ještě není aktivní vstup

- Problém: Po připojení AirPods během přerušené nebo ukončované části může UI ukázat jejich skutečný mikrofon až při další vědomé aktivaci audio session; samotný stav Bluetooth proto neprokazuje změnu vstupu ani samovolné pokračování.
- Typ: opakující se
- Řešení nalezeno: 16092026
- Řešení: Posuzovat `currentRoute` při skutečně aktivní session a návaznost technických účtenek. U T020 potvrdit přerušenou část, explicitní continuation stejné session a nový aktivní vstup až po Pokračovat; nepovažovat pouhé připojení příslušenství za běžící mikrofon.

### 2026-09-16 — Sync musí použít příchozí Git atributy

- Kontext: Human–Adam profil přebírá fast-forward, který ve stejném commitu přidává importovaný Markdown s úmyslnými konci řádků a odpovídající `.gitattributes`.
- Problém: `git diff --check HEAD FETCH_HEAD` použil atributy starého checkoutu a bezpečný update falešně odmítl dříve, než mohl nový `.gitattributes` převzít.
- Řešení: preflight spustit jako `git --attr-source=FETCH_HEAD diff --check HEAD FETCH_HEAD`; ostatní kontroly čistoty, povolených cest, mazání a fast-forward zůstávají beze změny.
- Ověření: nový regresní test přidává atribut i Markdown ve stejném zdrojovém commitu; 192 souvisejících testů a rychlá kontrolní brána prošly.

### 2026-09-17 — AVAudioEngine tap nesmí zdědit MainActor

- Kontext: Camino C01c, Swift 6 strict concurrency a fyzický mikrofon.
- Problém: inline tap closure vytvořená v `@MainActor` metodě zdědila izolaci;
  `AVAudioEngine` ji zavolal na real-time audio frontě a runtime ukončil proces
  přes `_swift_task_checkIsolatedSwift`. Simulátorová syntetická média tuto
  cestu neprovedla.
- Řešení: callback vytvořit v explicitně `nonisolated` helperu a předat mu jen
  vlastní synchronizovaný `Sendable` stav. Nevypínat dynamické kontroly aktorů.
- Ověření: shodný podpis v pěti crash reportech, 52 Swift testů, 2 UI testy,
  arm64 build a strict podpis; fyzický Start/Stop zůstává samostatnou bránou.

### 2026-09-17 — Asynchronní reconciliace nesmí zahodit souběžný impuls

- Kontext: Camino C02b, background `URLSession` fronta po fyzickém výpadku sítě.
- Problém: jediný příznak `reconciling` odmítl callback, který dorazil během
  čekajícího serverového dotazu. Automatický průchod přitom neoznačil UI jako
  zaneprázdněné; ruční tlačítko vypadalo aktivně, ale klepnutí nic neudělalo a
  fronta mohla zůstat stát mezi dvojicemi částí.
- Řešení: žádosti koaleskovat do jednoho příznaku čekajícího dalšího průchodu a
  držet pravdivý busy stav po celou dobu drain loopu. Dostupná Wi-Fi smí spustit
  automatiku; ruční tlačítko je fallback, nikoli paralelní worker.
- Ověření: regresní test zachycuje žádost během aktivního průchodu; Swift 19/19.
  Podepsaný build 0.4.0 (2) po instalaci sám dokončil fyzickou 96MiB dávku 13/13
  bez dalšího klepnutí, se shodnou délkou a serverovým SHA-256.

### 2026-09-19 — Síťová politika dávky patří na každý URLRequest

- Kontext: Camino C02b, příprava mobilního testu T049 a background `URLSession`.
- Problém: kontrola typu sítě jen před plánováním nestačí při přechodu sítě;
  konfigurace background session připouští mobilní data. Velké uploadové
  požadavky měly individuální zákaz správně, malé session/status/finalize
  požadavky jej zatím neměly.
- Řešení: u všech čtyř druhů požadavků nastavit `allowsCellularAccess` a
  `allowsExpensiveNetworkAccess` podle povolení konkrétní dávky; bez grantu
  obojí `false`. Monitor rozlišuje i skutečné mobilní rozhraní. Před grantem
  zobrazit počet, objem a upozornění na možné opakování bajtů.
- Ověření: Swift 20/20, iOS build a UI test potvrzovací brány 1/1 PASS.
  Následný T049 s buildem 3 na iPhonu prošel v syntetickém mobilním rozsahu;
  nešlo o plné T049 se skutečně novým videem.

### 2026-09-19 — Mobilní grant není start nové dávky

- Kontext: Camino C02b, návrat testovací aplikace po povolení mobilních dat.
- Problém: `applicationBecameActive()` i změna sítě volaly reconciliaci, která
  mohla sama vytvořit serverovou relaci dosud nespouštěné dávky.
- Řešení: uložit vědomý první start do journalu a před serverovým voláním
  zadržet novou dávku s mobilním grantem. Po prvním startu nechat retry a
  obnovu pokračovat; starší journal obnovovat podle dosavadního kontraktu.
- Ověření: Swift 22/22 včetně nové a starší podoby journalu, simulátorový UI
  test, nepodepsaný iOS build a plná projektová brána 1719/1719 PASS. Fyzická
  část A na iPhonu s buildem 4: po grantu, návratu aplikace a obnově sítě
  telefon 0/13, server 0 relací. Po vědomém startu a pozdějším relaunchi s
  dostupnou sítí se stejná relace automaticky dokončila 13/13; otevření ještě
  bez sítě po force quit nebylo ověřeno.

### LL-040 — Viewer musí rozhodovat podle poslední přijaté revize

- Problém: Výběr každého serverového snapshotu zvlášť by pustil starší
  `diary` Moment, i když server už přijal novější zámek `owner_only`.
- Typ: opakující se
- Řešení nalezeno: 19092026
- Řešení: Před projekcí zvolit pro každé ID nejvyšší serverem přijatou revizi;
  `owner_only`, skrytí, neznámá hodnota nebo konflikt na stejné revizi se
  uzavřou. Výstup neobsahuje počty vyloučených položek.
- Ověření: Syntetický test zkouší obě pořadí staré a nové revize, neznámé
  soukromí i konflikt; C03a 9/9 a plná brána 1728/1728 PASS. Provozní Viewer
  ještě vyžaduje samostatnou integraci a fyzické ověření.

### LL-041 — Vstupní typy API ověř před dotazem do SQLite

- Problém: Pole ID s JSON typem pole by v dotazu SQLite skončilo jako chyba
  úložiště `503`, i když jde o neplatný klientský vstup `422`.
- Typ: opakující se
- Řešení nalezeno: 20092026
- Řešení: Striktně ověř tvar JSON, typ a kanonické UUID před použitím ve
  storage vrstvě. Pro soukromou databázi současně vyžaduj cestu mimo repozitář
  a práva 0600; širší práva odmítni při otevření.
- Ověření: C03b synteticky kontroluje chybné ID jako `422` bez posunu kurzoru
  a odmítnutí databáze s právy 0644. C03b je referenční kontrakt, ne běžící
  produkční server.

### LL-042 — Před mikrofonem ulož vazbu audia k Momentu

- Problém: Po pádu by dokončené audio bez trvalé identity cesty a soukromí
  šlo při obnově chybně připsat jinému Momentu nebo uvolnit do deníku.
- Typ: opakující se
- Řešení nalezeno: 20092026
- Řešení: Po vytvoření create-only audio journalu, ale před startem mikrofonu
  ulož stabilní session ID, Moment ID, Trip ID a soukromí. Po restartu navazuj
  jen ověřenou dokončenou session se shodným ID; neznámé nebo nedokončené
  médium zachovej a ukaž k ruční kontrole.
- Ověření: C04a má syntetický integrační test restartu a idempotence, Swift
  8/8, UI simulátoru 1/1 a nepodepsaný iOS build PASS. Fyzický pád během
  nahrávání nové aplikace na iPhonu zatím NEPROVEDEN.

### LL-043 — Create-only mediální soubor zapisuj bez kombinace Foundation voleb

- Problém: Kombinace `.atomic` a `.withoutOverwriting` u `Data.write` skončila
  při syntetickém C04b foto testu pádem Foundation místo ověřitelné chyby.
- Typ: opakující se
- Řešení nalezeno: 20092026
- Řešení: Po trvalém záměru otevři nový soubor `O_CREAT | O_EXCL` s právy 0600,
  zapiš celé bajty včetně krátkých zápisů a zavolej `fsync`. Při chybě
  záměr/soubor zachovej a nikdy nepotvrzuj uložení před kontrolou formátu,
  SHA-256, stabilní cestou a databázovou vazbou.
- Ověření: C04b syntetický foto/restart průchod a Swift 13/13 PASS; aplikace
  je nainstalovaná na iPhonu, fyzické chování foto/video se teprve zkouší.

### LL-044 — Podepisuj přes správný Xcode projekt a místní tým

- Problém: Xcode ukazoval přihlášený Personal Team v projektu CaminoAudio,
  zatímco příkazový podpis nového Camino hlásil `No Accounts` a žádný profil.
- Typ: opakující se
- Řešení nalezeno: 20092026
- Řešení: Ověř správné bundle ID a cíl projektu, otevři právě tento projekt
  v Xcode a nastav jeho tým v ignorovaném `LocalSigning.xcconfig`. Podepisuj
  nové ID automaticky a ověř profil včetně konkrétního telefonu; nepoužívej
  bundle ID staršího prototypu. Samostatnou příčinu rozporu účtu mezi GUI a
  příkazovým buildem tento průchod neurčil.
- Ověření: C04b potom získalo přesný profil, `codesign --verify` prošel a
  nové Camino 0.1.0 (1) se nainstalovalo a spustilo na iPhonu 14 Plus.

### LL-045 — Den bez sovího řádku nesmí znovu nasadit starý zdrojový zvuk

- Problém: Pages workflow v den bez přesného CSV řádku nevytvořilo nové audio
  a znovu nahrálo zdrojový `app.js`, který ukazoval na historickou MP3.
- Typ: opakující se
- Řešení nalezeno: 21092026
- Řešení: V `OwlSpeech.csv` drž jeden řádek `default`. Přesné datum má
  přednost; bez něj generátor vytvoří z výchozí promluvy novou denní MP3 a
  přepne denní cache adresu. Výchozí cesty CSV/configu odvozuj z aktivního
  checkoutu, aby izolované testy nečetly jiný pracovní strom.
- Ověření: 19 cílených testů, dvě plné brány, workflow nad přesným produkčním
  commitem a veřejný `app.js`/MP3 s HTTP 200 prošly.

### LL-046 — Rizikový low-space scénář nejdřív odděl od skutečného měření

- Problém: Prahy přímo svázané se skutečnou kapacitou dovolovaly ověřit
  T060 jen zaplněním telefonu; audio, text a tepelný stav přitom neměly
  stejnou řízenou a automaticky dokazatelnou politiku.
- Typ: opakující se
- Řešení nalezeno: 21092026
- Řešení: Rozhodovací politiku drž jako čistou funkci nad injektovatelným
  zdrojem. Produkce čte systémovou kapacitu a tepelný stav, pouze Debug
  simulátor smí dodat řízenou hodnotu. Při neznámém stavu blokuj nový velký
  záznam, aktivní bezpečně dokonči, krátký zápis nech rozhodnout skutečným
  zápisem a nikdy automaticky nemaž originály.
- Ověření: C04b Swift 17/17, UI simulátoru 3/3, nepodepsané buildy pro
  simulátor i generic iOS a plná projektová brána 1740/1740 PASS. Integrační
  test zachoval starší originál
  byte-for-byte. Skutečný fyzický low-space a tepelný stres zůstávají
  samostatnou akceptací.

### LL-047 — Více tlačítek v jednom SwiftUI List řádku musí mít vlastní styl

- Problém: Klepnutí na Obnovit ve skrytém Momentu současně spustilo i tlačítko
  detailu ve stejném řádku `List`, takže archiv po správné obnově otevřel
  neočekávaný detail.
- Typ: opakující se
- Řešení nalezeno: 22092026
- Řešení: U samostatných akcí uvnitř jednoho SwiftUI `List` řádku nastavit
  explicitní `.buttonStyle(.borderless)` a každé tlačítko ověřit vlastním UI
  scénářem. C04d cílený test obnovy i následná celá matice 4/4 prošly.

### LL-048 — Retry fronty musí uchovat obálku a mobilní grant zmrazit dávku

- Problém: Nové sestavení JSON při retry může změnit bajty idempotentní
  operace; pouhé globální „mobilní data povolena“ zase může nechtěně zahrnout
  médium pořízené až po souhlasu.
- Typ: opakující se
- Řešení nalezeno: 23092026
- Řešení: Před prvním odesláním trvale uložit přesné bajty operace a její
  sekvenci. Mobilní souhlas navázat na aktuální ID dávky a ve stejné transakci
  otevřít nové ID pro všechny pozdější záznamy. Po výpadku vždy znovu číst
  serverový stav; lokální stav uploadu není důkaz `verified`.
- Ověření: C05b Swift 27/27, cílený UI relaunch/pause 1/1 a provozní workflow
  13/13 PASS; fyzická mobilní a síťová akceptace zůstává samostatná.
