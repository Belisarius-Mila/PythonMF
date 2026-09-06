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
