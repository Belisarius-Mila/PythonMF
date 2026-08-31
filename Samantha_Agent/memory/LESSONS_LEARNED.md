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
- Řešení nalezeno: 13082026
- Řešení: U privátního Unix-socket transportu zachovat konečný limit, ale zvýšit
  jej na 32 MiB. Při podobné chybě ověřit nejdřív vnitřní příčinu WebSocket
  uzavření; samotná existence socketu a úspěšný `initialize` ještě nedokládají,
  že se vejde odpověď `thread/resume` s nahromaděnými médii.

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
