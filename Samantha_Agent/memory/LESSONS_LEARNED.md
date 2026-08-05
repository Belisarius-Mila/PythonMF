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
  podle výsledku úplného auditu. Lokální či iCloudové servisní obrázky držet mimo
  Git pomocí přesného lokálního exclude.

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
