<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- 2026-10-17: Po úspěšném pilotu je routine_reviewer opět neaktivní. Běžící Cockpit má starý parser vyžadující jedinou roli release_executor; původní config/agent_roles.json zůstává zachovaný. Pilotní schválení a výsledky jsou uložené v runtime logu. Aktivace nové role až po samostatném nasazení podpory více rolí, bez obcházení současného p+n.

- 2026-10-17 19:06 CEST: omezený lokální pilot report_documentation_review přes samostatnou roli Sol/medium. Skutečný audit veřejného katalogu a dokumentace dokončen za 4,95 s bez doložených rozporů; 0,6515 Standard za kontrolora + 0,64077 za jedno převzetí hlavním Adamem = 1,29227 odhadovaného kreditu. Nulové přírůstky hlavního modelu během čekání, chráněné služby a role p+n přesně shodné. 63 cílených testů PASS, plná brána 2046/2046 PASS (261,278 s unit testů); logs/routine_full_gate_20261017.log. Zatím bez push/nasazení, bez obecného autonomního vývoje. Předchozí C je dokončené podle runtime účtenky a logs/pn_async_comparison_20261017.log.

- 2026-10-17 18:31 CEST: pilot C odhalil chybu čtecí ochrany Tailscale pod launchd. Lokální oprava explicitního CLI režimu a samostatné fáze protection prošla 43 cílenými testy, skutečným minimálním prostředím a plnou branou 2034/2034. Dokumentace a oprava tvoří dva autorizované commity; následné p+n a srovnání doloží runtime účtenka a logs/pn_async_comparison_20261017.log.

- 2026-10-17 18:18 CEST: A/B dokončené a živě ověřené; náklad dohledu převážil úsporu Luny. Míla autorizoval nový pilot C přes skutečný Cockpit bez průběžných modelových návratů. Jeden nový dokumentační commit; stávající modely a ochrany zůstávají zachované. Výsledek C dokládají runtime účtenka a logs/pn_async_comparison_20261017.log.

- 2026-10-17 17:30 CEST: měření je nasazené; přímé p+n A prošlo 2032 testy a smoke 5/5, GitHub aligned, Camino/autosave zachované. UI identity balíčku nasazené. UI výsledků kontrol lokálně hotové (68 UI testů a Node VM PASS); Míla schválil následné měřené p+n B přes Lunu. Aktuální výsledek B a číselné srovnání dokládají runtime účtenka a logs/pn_cost_comparison_20261017.log.

- 2026-10-17 16:53 CEST: role `release_executor` je lokálně oddělená od konkrétního modelu.
  Jediné nastavení `config/agent_roles.json` platí pro všechny vývojové proudy
  i nativního pomocníka. Schválený model/úsilí a otisk politiky jsou v účtence;
  katalogové doporučení nepovoluje migraci. Kandidát vyžaduje cenové posouzení
  a samostatnou syntetickou zkoušku. 169 integračních testů PASS, skutečný
  suchý běh role i izolovaná zkouška kandidáta PASS; plná brána role 2024/2024 PASS (265,823 s testů).
  Míla výslovně autorizoval následné p+n celého připraveného balíčku.
  Provozní výsledek této publikace ověřit podle aktuální účtenky vykonavatele,
  serverového deployment souhrnu a shody main/GitHub; tento záznam je vývojový
  checkpoint před publikací. Fyzická přejímka zůstává samostatně.

- 2026-10-17 16:37 CEST: předání celého p+n balíčku Luně je lokálně rozšířené na všech
  33 kanonických vývojových proudů portálu i přímou relaci. Potvrzení váže
  projekt, registrovaný cíl a oba heads; výsledek míří původnímu Adamovi.
  Běžné proudy nasazují runtime Samanthy, MMTX/ToBeToHave/ColorsAndNumbers
  používají Pages s vlastní HTTP kontrolou. Již odeslaný main projde plnou
  bránou bez dalšího push. 286 integračních testů PASS; plná brána obecného rozšíření 2011/2011 PASS (263,223 s testů).
  Skutečná Luna a živé ochrany prošly v oddělených syntetických suchých bězích
  pro obecný proud i Pages. Žádný push, restart ani změna Camino/autosave.
  První zavedení stále čeká na samostatné p+n; vydání samostatných klientů
  a zařízení zůstává oddělenou operací s vlastními pravidly.

- 2026-10-17 15:43 CEST: orchestrace p+n přes Lunu je implementovaná lokálně. Převzetí
  celého balíčku s přesnými heads, trvalá soukromá účtenka a vykonavatel mimo
  restartovaný Cockpit; původní plná brána/push/deploy/smoke zachované.
  Návrat míří do původního vlákna Cockpitu nebo k původnímu terminálovému
  Adamovi. UI má přesné p+n, zkoušku, potvrzení balíčku a obnovu stavu.
  147 cílených a 27 závěrečných regresních testů PASS; plná brána 1993/1993 PASS (267,315 s testů).
  Skutečná Luna přijala syntetických 7 commitů; celý suchý běh prošel i
  read-only ochranami Camino/autosave. Bez push, nasazení a změny služeb.
  První zavedení nových rout a ostré p+n zbývají jako samostatný krok.

- 2026-10-17 14:58 CEST: podle Mílova rozhodnutí je lokálně odstraněný panel Vývojový
  runner ze Servisu včetně jeho DOM vazeb, obsluhy tlačítek a formátování
  výstupu. Vývoj nabízí Projekty, Git a terminál. Serverový allowlist/API
  a standardní vývojové brány zůstávají zachované. 33 cílených testů
  a rychlá statická brána PASS. Bez restartu či změny Camino/autosave;
  push a nasazení této úpravy čekají na samostatné p+n.

- 2026-10-17 14:41 CEST: body 1–3 jsou pushnuté a funkčně nasazené. Kód `ae30beddcdfd`,
  otisk `50ffdf992ae6552a`, nový proces potvrzený, receipt deployed a smoke 5/5.
  Plná publikační brána 1963 testů OK (11 přeskočených). Shoda místního
  a Tailscale HTTPS HTML; pět částí Servisu, bezpečný kalendářový stav
  a zdroje/neověřený provoz v auditu ověřené přes běžící API.
  Camino před/po shodné: PID 47332, konfigurace, Serve, stav i editor filmu;
  owner HTTP/HTTPS a anonymní 401 PASS, Funnel off. Autosave jeden čerstvý
  worker, bez poslední chyby, automatické mazání vypnuté.
  Fyzická Safari/iPhone/VoiceOver přejímka čeká. Finální dokumentační head
  a PID dokládá živá účtenka; následuje zveřejnění tohoto uzavíracího zápisu.

- 2026-10-17 14:30 CEST: bod 3 lokálně hotový. Audit schopností odděluje zjištěné
  mezery registru od ručně udržovaných podnětů; odstraněné staré úkoly
  kalendáře a pevný červnový termín. Projektový audit uvádí čas sestavení,
  poslední commit podkladu i zdroj u projektu a označuje neověřený provoz.
  Při novější kanonické paměti nenavrhuje konkrétní práci ze starého agregátu.
  20 cílených testů a statická brána PASS; skutečné read-only CLI výstupy
  ověřené. Body 1–3 čekají na samostatný push/nasazení; služby beze změny.

- 2026-10-17 13:51 CEST: bod 2 U07 je lokálně hotový. Servis má pět samostatně
  rozbalovacích částí Provoz / Relace / Obnova / Vývoj / Diagnostika;
  relace a autosave mají přímý vstup bez vzdálené duplicitní zkratky.
  Původní akce, ochrany procesů a potvrzení zachované, Webové aplikace
  zůstávají v horní liště. 341 cílených testů PASS, závěrečný frontend 20/20
  PASS, navigace a statická brána PASS; 3 browser scénáře 320/390/1440 px
  s testovacími daty. Bod 1 i 2 čekají na samostatný push/nasazení.
  Fyzická Safari/iPhone/VoiceOver přejímka čeká. Další návrh: bod 3 auditu.

- 2026-10-17 13:39 CEST: bod 1 U07/U08 je implementovaný lokálně. Kontrola UI nyní
  přesně hlásí přítomnost prvků; diagnostika netvrdí ověření funkčnosti tlačítek.
  Kalendář má samostatný read-only stav z registrovaného auditu, čas ověření,
  rozlišení zapnuto/vypnuto/náhled/překážka a bezpečný neověřený stav při chybě.
  42 cílených testů PASS; plná brána 1961/1961 PASS. Běžící Cockpit zatím
  nebyl aktualizovaný; push a nasazení zůstávají samostatným krokem.

- 2026-10-16 21:21 CEST: trvalý autosave po přesném potvrzení aktivovaný a živě
  ověřený včetně automatické obnovy po ukončení workeru. Právě jeden proces,
  čerstvý technický i čitelný záznam, historie a předchozí dvojice zachované;
  automatické mazání vypnuté. Panel Stav autosave pushnutý a řízeně nasazený,
  kód `0c2908c9`, otisk `1de95c8007aa2f39`, nový proces a smoke 5/5.
  45 cílených servisních testů a závěrečná plná brána 1957/1957 PASS.
  Camino před/po přesně shodné (proces, release, konfigurace, Serve, stav
  a filmový editor), owner HTTP/HTTPS i anonymní 401 PASS, Funnel off.
  Zbývá žluté upozornění SSD 23,6 GiB; nejde o chybu ukládání. Finální
  dokumentační head/PID dokládá živá účtenka, tento zápis jí předchází.

- 2026-10-16 19:59 CEST: oprava kvantitativního přehledu je pushnutá a řízeně nasazená
  v Cockpitu. Kód `475fc852`, otisk `236dd9f53426942e`, nový proces potvrzený,
  receipt `deployed` a smoke 5/5. Živé API při ověření 2 143 souborů /
  347 051 řádků místo 16 164 / 877 153; další projektové zápisy součet mírně
  mění. Úplná místní publikační brána 1941/1941 PASS, cíleně 12/12 PASS.
  Camino zůstalo ve stejném procesu PID 47332/release `f60a33c98fd5`;
  konfigurace, Serve, 893 operací, 304 ověřených médií, flags false a úplná
  odpověď filmového editoru shodné před/po. Owner HTTP/HTTPS i anonymní
  odmítnutí PASS, Funnel off. Další krok: obnovit přehled v Cockpitu.
  U07 zůstává odložený; finální Git head a proces ověřuje živá účtenka.

- 2026-09-14 21:44 CEST: meziúkol ToBeToHave vrací Webové aplikace do horní lišty. Jejich přesun do Servisu v U06 způsobil ztrátu dohledatelnosti. Dlaždice ToBeToHave nyní míří na web; U07 zůstává odložený. 22 cílených testů OK; finální nasazení ověřovat živě.

- Aktualizováno 2026-09-14 20:25 CEST: U01–U06 funkčně nasazené, head `980aed7a`, nový proces potvrzen, smoke 5/5 a shoda podávaného HTML; otisk `55373c8c1c4da728`.
- Míla schválil přesun nesouvisejících podkladů mimo Git; provedeno, 35 souborů shodných podle SHA-256. Publikační překážka odstraněna.
- Uzavírací zápis je součást schváleného GitHub balíčku. Aktuální odeslání a finální nasazený head poskytují živé audity; tento zápis předchází závěrečnému push.
- Historie 14. 9.: U07 tehdy odložený; aktuálně body 1 a 2 lokálně hotové.

- Závěrečné ověření 2026-09-14 20:19 CEST: plná brána **1680/1680 OK**, testy 318,932 s a statické kontroly OK. Opraven jeden zastaralý test odstraněné funkce; původní kontrola zachovaná. Souhrnný report `reports/cockpit_ui_release_2026_09_14.md`.
- Souhrn U01–U06: společná odezva, hlavička/návraty, kompaktní Dokumenty, stránkování, prioritní Přehled a jednotná navigace/dialogy. TXT v2.8 obsahuje aktuální bod návratu a odkazy na důkazy.
- U06: společná správa 16 dialogů; vstup/vracení fokusu, uzavřený Tab/Shift+Tab, Escape podle vrstvy, inertní pozadí a zachovaný scroll.
- Šest hlavních oblastí má bezpečné přímé odkazy/hash a označení aktivního místa. Komunikace sdružuje poštu/připomenutí, projekty a katalog jsou v Servisu; rodinné zkratky zachované.
- Zavření/obnova Knihovny drží vybranou položku, editor, nové texty a fotografie; rodinný formulář se nečistí. Záměrné přepnutí/reset dál chrání původní potvrzení. Návrat k Janičce je u hledání, kde ho nepřekrývá odezva.
- Důkaz: 28 cílených testů včetně stavů dialogů a vazeb DOM; 3 browser scénáře na 320/390/1440 px, v každém 16 dialogů a 6 přímých odkazů/reloadů. Rychlá statická brána prošla. `reports/cockpit_ui_u06_2026_09_14.json`. Regrese návratů rodiny, Recovery, vnořeného náhledu, rozepsané editace i varování před opuštěním stránky.
- U07: struktura Servisu a přesné health štítky jsou 17. 10. lokálně dokončené; nasazení a fyzická přejímka čekají.
- Rizika: fyzický Safari/iPhone/VoiceOver čeká; drafty žijí jen v aktuální kartě, potvrzený reload/ukončení je může ztratit. beforeunload není záruka proti ukončení OS. Odkaz obnoví hlavní oblast, ne přesný vnořený kontext.
- Záloha odložená kvůli disku; Santiago pouze zvažované. Cizí nesledovaný adresář zachovaný mimo commit.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: Cockpit / hlavní architektura

Pracovni proud: `project-cockpit`
Typ: `Project`
Rezim: `active`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

Nove chronologicke zaznamy uprednostni lidsky stav v poradi Hotovo,
Rozhodnuti, Dalsi krok a Navrhovane dalsi kroky. Technicky dukaz je az
posledni kratka sekce. Starsi zaznamy se zpetne neprepisuji.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-08-02 14:10 CEST – Důležitá připomenutí lze doručit přímo přes Tailscale do soukromého Cockpitu; opakované doručení je idempotentní a iCloud zůstává záložní cestou.

Hotovo:
- Důležitá připomenutí lze doručit přímo přes Tailscale do soukromého Cockpitu; opakované doručení je idempotentní a iCloud zůstává záložní cestou.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Přímé Tailscale doručení je primární cesta a iCloud soubory zůstávají bezpečným fallbackem.

Další krok:
- Samostatně auditovat a potvrdit nasazení do Cockpitu; potom v iPhonové zkratce doplnit soukromou Tailscale adresu a provést jeden živý doručovací test.

Navrhované další kroky:
- Opravit recovery dokončovací účtenky také pro lazy pracovní proudy, aby se stejný WIP blok neopakoval.

Technický důkaz:
- plná Cockpit brána: 1269 testů, 281.3 s, výsledek OK.
- Pracovní proud: `project-cockpit`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`disconnected`.

### 2026-08-05 22:41 CEST – Už indexované iCloud placeholdery nevytvářejí falešné čekání

Hotovo:
- Synchronizace důležitých připomenutí před hydratačním pokusem ověří, zda je
  zdroj už úplně a beze změny zachycený v private indexu.
- Přesně shodná cesta, velikost a čas změny s uloženým tělem se znovu nestahují
  a nezvyšují počet čekajících položek.
- Nový, změněný nebo neúplně indexovaný placeholder zůstává fail-closed
  čekajícím stažením.

Rozhodnutí:
- Stav iCloud hydratace se nesmí zaměňovat se stavem doručení připomenutí.
  Odložený soubor může být již bezpečně indexovaný.
- Přímé Tailscale doručení zůstává samostatným navazujícím krokem; tato změna
  neupravuje ani neinstaluje iPhonovou zkratku.

Další krok:
- Vytvořit lokální commit. Nasazení do běžícího Cockpitu zůstává samostatné.

Navrhované další kroky:
- Po nasazení ověřit, že karta ponechá otevřená připomenutí, ale odstraní pouze
  falešný počet iCloud čekání.
- Potom nakonfigurovat přímou Tailscale zkratku a provést jedno živé doručení.

Technický důkaz:
- Cílená sada 14 testů prošla.
- Suchý běh nad kopií živého indexu vrátil otevřená připomenutí bez falešného
  čekajícího nebo zaseknutého iCloudu.
- Plná Cockpit Quality Gate prošla 1311 testy za 338,409 s.

### 2026-08-07 13:59 CEST – Současný Cockpit a servisní orientace narovnány

Hotovo:
- Přímé zkratky připomenutí a Quick Notes jsou funkční.
- Lokální vstupy VocabularyFR, VocabularyIT a MultiLO jsou zapojené.
- Dokumentový trezor v Servisu ukazuje nejdřív aktuální stav a historii až po
  rozbalení.

Rozhodnutí:
- Historické servisní statistiky zůstávají dostupné, ale nejsou výchozím
  pracovním úkolem.

Další krok:
- Bez okamžité změny; sledovat konkrétní uživatelskou zkušenost.

Navrhované další kroky:
- Při dalším systémovém auditu ověřit stáří agregované projektové paměti.

Technický důkaz:
- Běžící Cockpit je serverově ověřený na `91dc700`; smoke 5/5.

### 2026-08-14 17:24 CEST – Autosave má omezený růst a hlídá volné místo

Hotovo:
- Aktuální obnovovací kopie zůstává ukládaná každých deset minut.
- Historický JSONL/TXT pár vzniká nejvýše jednou za hodinu a automatická
  retence ponechává jen 12 nejnovějších časů.
- Autosave stav a servisní panel Cockpitu hlásí varování pod 30 GiB a kritický
  stav pod 15 GiB volného místa.
- Cockpit byl po implementaci řízeně restartován a ověřen novým procesem.

Rozhodnutí:
- Nouzový autosave není dlouhodobý archiv; přednost má čerstvá desetiminutová
  obnova a omezená hodinová historie.
- Skutečné jednorázové odstranění starých nouzových kopií zůstává oddělenou
  destruktivní akcí pod globální bezpečnostní brzdou.

Další krok:
- Po přesné potvrzovací větě jednorázově ponechat 12 nejnovějších časů,
  restartovat watcher na nový kontrakt a ověřit uvolněné místo.

Navrhované další kroky:
- Po aktivaci pouze sledovat, zda se velikost autosave stabilizuje přibližně na
  12 hodinových kopiích aktuální relace.

Technický důkaz:
- Implementační commit: `e5335ad`.
- Plná Cockpit Quality Gate: 1414/1414 testů, výsledek OK.
- První řízené nasazení: nový proces a smoke 5/5.

### 2026-08-16 08:04 CEST – Autosave cleanup odděluje tři různé metriky místa

Hotovo:
- Dry-run ukazuje zvlášť logickou velikost kandidátů a fyzicky alokované bloky.
- Potvrzený úklid měří volné místo filesystemu před a po smazání a zachová
  výsledný report místo jeho okamžitého přepsání novým dry-runem.
- Reálný read-only dry-run nad autosave stavem hlásil nula kandidátů a nic
  nesmazal.

Rozhodnutí:
- Ani logická velikost, ani alokované bloky nejsou na APFS příslibem skutečně
  uvolněného místa. Skutečný výsledek je pouze naměřený rozdíl volného místa.
- Dry-run proto skutečný zisk neslibuje; ten se zobrazí až po potvrzeném úklidu.

Další krok:
- Samostatně potvrdit nasazení do Cockpitu a po restartu živě ověřit nový text
  dry-runu bez provedení mazání.

Navrhované další kroky:
- Na Macu a iPhonu zkontrolovat čitelnost tří oddělených metrik.

Technický důkaz:
- Cílených šest testů prošlo.
- Plná Cockpit Quality Gate prošla 1414/1414 testy.

### 2026-08-16 08:17 CEST – Druhý audit 5.6 Sol určil další vývoj

Hotovo:
- Vznikl samostatný `AuditCockpit56_2.txt` nad aktuálním kódem, projektovou
  pamětí, handoffy, TVBCP, registry a živými read-only kontrolami.
- Audit oddělil historicky dokončené priority od současných slabin.

Rozhodnutí:
- Bezpečnostní a capability základ zůstává zachovaný; plošný přepis ani změna
  frameworku nejsou doporučené.
- První nový milník je read-only Decision Cockpit D4 s nejvýše třemi aktuálními
  kroky, zdrojem priority a stářím důkazu.
- Frontend a HTTP routing se mají dělit pouze po malých doménových řezech.

Další krok:
- V rámci stejného úkolu řízeně nasadit již ověřenou opravu autosave matematiky
  a ověřit nový proces, code stamp a smoke 5/5.

Navrhované další kroky:
- Ručně projít pět reálných scénářů na Macu a iPhonu.
- Potom připravit malý návrh Decision Cockpit D4 bez provádění akcí.

Technický důkaz:
- Živý přednasazovací smoke prošel 5/5.
- Capability audit evidoval 83/83 mapovaných agent tools a 88 POST akcí.
- Audit výslovně zachoval otevřenou vizuální přejímku, protože interaktivní
  prohlížeč nebyl v relaci dostupný.

### 2026-08-18 08:18 CEST – Cockpit nyní vybírá nejvýše tři aktuální kroky, vysvětluje jejich prioritu a ukazuje zdroj i stáří důkazu

Hotovo:
- Cockpit nyní vybírá nejvýše tři aktuální kroky, vysvětluje jejich prioritu a ukazuje zdroj i stáří důkazu

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- Decision Cockpit D4 zůstává read-only a povoluje pouze navigaci do existujících přehledů

Další krok:
- Převzít checkpoint, nasadit Cockpit a vizuálně ověřit přehled na Macu a iPhonu

Navrhované další kroky:
- Vyjmout health, recovery a autosave frontend do prvního samostatného modulu
- Doplnit přímé kontraktní testy nejrizikovějších POST akcí

Technický důkaz:
- plná Cockpit brána: 1432 testů, 304.9 s, výsledek OK.
- Pracovní proud: `project-cockpit`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_other_main`, runtime=`connected`.

### 2026-08-18 10:16 CEST – Health, diagnostika, Recovery a autosave jsou oddělené od hlavního frontendového souboru bez změny jejich chování.

Hotovo:
- Health, diagnostika, Recovery a autosave jsou oddělené od hlavního frontendového souboru bez změny jejich chování.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Health, Recovery a autosave tvoří první samostatný frontendový modul Cockpitu.

Další krok:
- Vytvořit checkpoint, nasadit Cockpit a živě ověřit diagnostiku, Recovery a autosave.

Navrhované další kroky:
- Po živém ověření pokračovat bodem 5 auditu.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 4.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-cockpit`.
- Read-only živý stav při checkpointu: main=`aligned`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-18 11:03 CEST – Health, Recovery a hlavní statusové GET cesty mají samostatný backendový dispatch bez změny veřejných kontraktů.

Hotovo:
- Health, Recovery a hlavní statusové GET cesty mají samostatný backendový dispatch bez změny veřejných kontraktů.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Health, Recovery a status tvoří první samostatnou read-only routing doménu Cockpitu.

Další krok:
- Vytvořit checkpoint, nasadit Cockpit a ověřit pět vyčleněných endpointů.

Navrhované další kroky:
- Po živém ověření pokračovat bodem 6 auditu a doplnit přímé testy nejrizikovějších non-direct POST akcí.

Technický důkaz:
- plná Cockpit brána: 1440 testů, 312.7 s, výsledek OK.
- Pracovní proud: `project-cockpit`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-18 13:06 CEST – Všechny zapisovací a odesílací POST akce mají nyní přímo dohledatelný testovací kontrakt.

Hotovo:
- Všechny zapisovací a odesílací POST akce mají nyní přímo dohledatelný testovací kontrakt.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Akce typu private_write a external_send musí mít v POST registru doloženou úroveň direct.

Další krok:
- Vytvořit checkpoint, nasadit Cockpit a ověřit běžný smoke test.

Navrhované další kroky:
- Osm zbývajících nízkorizikových non-direct položek řešit pouze při jejich konkrétní změně nebo samostatném auditu.

Technický důkaz:
- plná Cockpit brána: 1444 testů, 302.1 s, výsledek OK.
- Pracovní proud: `project-cockpit`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-18 17:05 CEST – Revize dokumentů se nyní otevírá přímo v Cockpitu a funguje i přes Tailscale na iPhonu

Hotovo:
- Revize dokumentů se nyní otevírá přímo v Cockpitu a funguje i přes Tailscale na iPhonu
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- Po automatickém převzetí ověřit na iPhonu tlačítko Revidovat

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- plná Cockpit brána: 1445 testů, 305.6 s, výsledek OK.
- Pracovní proud: `project-cockpit`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-19 22:05 CEST – Dokumenty mají jednu funkční frontu místo tří překrývajících se oddílů

Hotovo:
- Dokumentová práce v Cockpitu je sjednocená do jediné fronty.
- Každý dokument se zobrazuje jen jednou a přímo u něj jsou jen relevantní akce:
  otevření, stav čtení, přijetí bezpečného návrhu metadat nebo doplnění chybějícího údaje.
- Na iPhonu se ručně zadávají pouze skutečně chybějící pole, ne celý pětikrokový formulář.

Rozhodnutí:
- Revize a klasifikace dokumentu jsou jeden uživatelský úkol; klasifikace už není samostatný duplicitní pracovní oddíl.

Další krok:
- Samostatně potvrdit nasazení do Cockpitu a potom na iPhonu ověřit jednu položku se čtením a jednu s doplněním metadat.

Navrhované další kroky:
- Podle živého iPhonového testu upravit jen konkrétní nejasnost, nevracet další paralelní seznam.

Technický důkaz:
- Cílená sada 279 testů prošla.
- Plná Cockpit Quality Gate prošla 1446 testy.
- JavaScript, Python syntaxe, `git diff --check` a Git safety check jsou zelené.

### 2026-08-30 11:19 CEST – Důležitá připomenutí mají GitHub-only fallback

Hotovo:
- Samostatný soukromý GitHub Issues inbox je vytvořený a synteticky ověřený.
- Cockpit umí přes přesné `delivery_id` převzít otevřenou Issue do private
  indexu, bezpečně deduplikovat opakování a uzavřít Issue až po lokálním zápisu.
- iCloud sync důležitých připomenutí byl z aktivní Cockpit cesty odstraněn.
- Nová zkratka je validovaná a podepsaná; její verzovaný zdroj obsahuje pouze
  bezpečné placeholdery.

Rozhodnutí:
- Kanonické pořadí je GitHub write-ahead -> přímý Tailscale pokus -> přesná
  účtenka `delivery_id`; nejednoznačný stav nesmí zavřít GitHub fallback.
- GitHub inbox je oddělený soukromý repozitář a neznečišťuje `PythonMF` historií
  připomenutí, submodulem ani pracovními soubory.

Další krok:
- Míla vytvoří fine-grained token omezený na inbox; potom se token doplní pouze
  lokálně, zkratka se importuje a nasazení Cockpitu se potvrdí samostatně.

Navrhované další kroky:
- Provozně ověřit právě dva scénáře: bdící Mac a spící Mac s následným
  probuzením. Teprve potom označit mobilní fallback za hotový.

Technický důkaz:
- Syntetický pilot: právě jeden lokální záznam a uzavřená GitHub Issue.
- Shortcuts validace prošla a podepsaný výstup má 25 822 bajtů.
- Plná Cockpit Quality Gate: 1485/1485 testů, 317,8 s, OK.
- Změna zatím není nasazená ani pushnutá.

### 2026-08-30 14:13 CEST – GitHub fallback je živý v Cockpitu

Hotovo:
- Produkční token je pouze v ignorovaném `.env` a má ověřený přístup právě k
  jednomu soukromému inboxu s Issues read/write.
- Soukromá podepsaná zkratka má nakonfigurovaný GitHub inbox i Tailscale
  endpoint bez ručního vkládání tokenu při importu.
- Cockpit hotfix `20742e9` načítá lokální `.env` při startu bez přepsání hodnot
  z launchd a je serverově nasazený.

Rozhodnutí:
- Token se nyní ponechá; při budoucím citlivějším obsahu se vymění.
- Architektura zůstává dvoucestná: GitHub write-ahead a přímý Tailscale pokus.

Další krok:
- Míla provede jeden neškodný iPhone test s bdícím Macem; potom samostatně test
  se spícím Macem a převzetím po probuzení.

Navrhované další kroky:
- Po obou testech uzavřít provozní milník jen tehdy, pokud nevznikne duplicita a
  GitHub Issue zůstane otevřená pouze po dobu nedostupnosti Macu.

Technický důkaz:
- Cílené testy hotfixu 21/21 a plná Cockpit Quality Gate 1487/1487 prošly.
- Deployment účtenka potvrdila nový proces, workstream `project-cockpit` a smoke
  5/5; živá GitHub synchronizace hlásí `configured=true`, nula chyb a nula
  čekajících Issues.

### 2026-08-30 14:28 CEST – Oprava URL vstupů po prvním iPhone testu

Hotovo:
- První iPhone test bezpečně skončil před zápisem, protože akce Načíst obsah URL
  viděla prázdný vstup.
- Obě URL proměnné jsou opravené na iOS-kompatibilní tokenizovaný textový vstup.
- Opravená soukromá varianta je validovaná a podepsaná pod nekolidujícím názvem
  `Samantha – důležité připomenutí 2`.

Rozhodnutí:
- Chybný pokus se neopakuje automaticky. Stav zůstal jednoznačný: žádná nová
  lokální položka ani čekající GitHub Issue.

Další krok:
- Importovat opravenou variantu a provést nový neškodný test s bdícím Macem.

Navrhované další kroky:
- Po přesně korelovaném úspěchu samostatně ověřit fallback se spícím Macem.

Technický důkaz:
- Živý stav po chybě: 4 otevřená lokální připomenutí, GitHub pending 0,
  synchronizační chyby 0.
- Builder testy 4/4, validátor zdroje i soukromé kopie OK a plná Cockpit Quality
  Gate 1488/1488; podepsaný výstup 26 706 bajtů, režim `0600`.

### 2026-08-30 16:04 CEST – Fail-closed ochrana proti opakovanému delivery_id

Hotovo:
- Bdící test přes Issue `#2` prošel přesně jednou přímou cestou.
- Spánkový test odhalil, že varianta `2` při novém textu znovu použila staré
  `delivery_id`; nový text proto nebyl lokálně uložen a zůstal jen v uzavřené
  testovací Issue `#3`.
- Varianta `3` používá časové ID s milisekundami a je validovaná a podepsaná.
- Backend při kolizi stejného ID s jiným textem nově ponechá stav nejednoznačný
  a Issue otevřenou místo tichého uzavření jako duplicity.

Rozhodnutí:
- Issue `#3` se nepočítá jako úspěšný fallback test.
- Automatické opakování nebo obnovení jejího textu se neprovádí.

Další krok:
- Po zelené plné bráně vytvořit checkpoint; nasazení backendu a import varianty
  `3` zůstávají samostatnými kroky před retestem.

Navrhované další kroky:
- Ověřit nejprve dvě různá ID při dvou bdících bězích a potom skutečný fallback
  při nedostupném Macu.

Technický důkaz:
- Issues `#2` a `#3`: stejné ID, rozdílný text; přesná lokální shoda pouze jedna.
- Cílené testy 26/26 a iOS 27 validace zdroje i soukromé varianty `3` prošly.
- Plná Cockpit Quality Gate prošla 1491/1491 testy.

### 2026-08-30 16:52 CEST – Kanonické datumové výstupy pro variantu 4

Hotovo:
- Fail-closed backend je nasazený na `04e7763` a živý serverový smoke prošel
  5/5 lokálně i přes tailnet.
- Bdící běh varianty `3` vytvořil nový přímý záznam 45, ale odeslal jen
  `delivery_id` `samantha-`; nelze jej použít jako důkaz jedinečného ID.
- Zkratka nyní odkazuje na kanonické Apple výstupy `Date` a `Formatted Date`.
  Nakonfigurovaná varianta `4` je validovaná a podepsaná mimo git.

Rozhodnutí:
- Spánkový test zůstává pozastavený, dokud varianta `4` při bdícím Macu
  neprokáže celé nové časové ID. Záznam 45 se automaticky neopakuje ani nemaže.

Další krok:
- Importovat variantu `4`, provést jeden bdící test a přesně ověřit nový
  lokální záznam a jeho celé `delivery_id`.

Navrhované další kroky:
- Až potom udělat jeden test se spícím Macem a ověřit převzetí GitHub Issue
  právě jednou po probuzení.

Technický důkaz:
- Cílené testy 26/26, iOS 27 validace zdroje i private varianty `4` a plná
  Cockpit Quality Gate 1491/1491 prošly; podepsaný soubor má režim `0600`.

### 2026-08-30 18:00 CEST – Přímá CurrentDate magic variable ve variantě 5

Hotovo:
- Varianta `4` při bdícím běhu znovu vytvořila jen ID `samantha-`; Issue `#5`
  zůstala díky fail-closed backendu otevřená a lokální index se nezměnil.
- Varianta `5` odstranila akce Date a Format Date a vkládá formátovanou
  `CurrentDate` přímo do textu ID.
- Jednotkové testy stavu připomenutí jsou izolované od živé GitHub konfigurace.

Rozhodnutí:
- Issue `#5` se bez samostatného rozhodnutí nemění ani neopakuje. Varianty `3`
  a `4` se dále netestují.

Další krok:
- Importovat variantu `5` a při bdícím Macu ověřit právě jedno celé nové ID.

Navrhované další kroky:
- Spánkový test povolit až po přesné korelaci bdícího běhu varianty `5`.

Technický důkaz:
- Cílené testy 28/28, iOS 27 validace a podepsání varianty `5` prošly.
- Po opravě testovací izolace prošla plná Cockpit Quality Gate 1491/1491.

### 2026-08-30 21:35 CEST – Ověřený fallback připomínek zkopírovaný pro Quick Notes

Hotovo:
- Dvoucestné připomínky jsou provozně ověřené při bdícím i spícím Macu.
- Quick Notes mají lokálně připravený samostatný GitHub write-ahead, přímý
  Tailscale POST a fail-closed korelaci podle `delivery_id`.
- Aktivní QN cesta nepoužívá iCloud a secret-free zkratka je validovaná i
  podepsaná jako zástupná varianta mimo git.

Rozhodnutí:
- QN používají pouze GitHub a Tailscale, bez třetí cesty.
- QN dostanou vlastní soukromý repozitář a vlastní fine-grained token pouze s
  `Issues: Read and write`; token připomenutí zůstává beze změny.
- GitHub Issue se zavře až po potvrzeném lokálním zápisu. Konflikt stejného ID
  s jiným textem zůstane otevřený a nesmí se automaticky opakovat.

Další krok:
- Založit soukromý QN inbox, vytvořit omezený token a bez výpisu jej vložit do
  ignorovaného `.env` a soukromé podepsané zkratky.

Navrhované další kroky:
- Po samostatném potvrzení nasadit QN backend a udělat nejprve jeden bdící,
  potom jeden spánkový syntetický test s přesnou korelací.

Technický důkaz:
- Připomínky: záznam 46 / Issue `#6` bdící; záznam 47 / Issue `#7` vytvořená
  při spánku a po probuzení právě jednou převzatá a uzavřená.
- QN testy: cíleně 301/301, plná Cockpit Quality Gate 1506/1506.
- iOS 27 validace a podpis zástupné zkratky prošly; soubor má 25 724 bajtů a
  režim `0600`.


### 2026-09-10 08:47 CEST – Přehled a ukončení terminálových relací

Hotovo:
- Servis obsahuje přehled skutečných terminálových procesů Codexu: TTY, PID, začátek a délka běhu, ochrana a ověřený projekt.
- Běžné ukončení vyžaduje potvrzení konkrétní identity. Vynucené ukončení je dostupné až po předchozím pokusu a dalším potvrzení.
- Startovací report už nezaměňuje screen, shell ani podpůrný code-mode proces za samostatnou konverzaci.

Rozhodnutí:
- Před signálem se znovu ověřuje proces, čas startu, vlastník, spustitelný soubor, projekt a ochrana. Služby a předci správce jsou chránění; plné argumenty procesu se do UI neposílají.
- Projekt z příkazu `-C` / `--cd` se zohledňuje, protože OS cwd může zůstat domovským adresářem.
- Ukončuje se pouze zvolený Codex; stáří neznamená zaseknutí. Guard rozpracovaných souborů se neobchází.

Další krok:
- Commit a uživatelem požadovaný push, řízený restart Cockpitu a živá kontrola Human–Adam.

Navrhované další kroky:
- Při příštím skutečném zaseknutí použít Servis → Běžící relace a potvrdit konkrétní TTY/PID.

Technický důkaz:
- Plná Cockpit Quality Gate 1540/1540, cílená sada 45/45, rychlá statická brána a diff kontrola prošly.
- Edge test přes skutečné HTTP cesty: zrušení potvrzení zachovalo proces, SIGTERM ukončil běžnou testovací relaci a až další potvrzení SIGKILL ukončilo nereagující testovací relaci; 0 JS chyb.
- Testovací důkazy jsou mimo git v `data/private/codex_sessions_smoke_20260910/`. Reálná aktuální relace a služby zůstaly běžet.


### 2026-09-10 08:51 CEST – Živé nasazení a čistý stav pro Human–Adam

Hotovo:
- Funkční commit `6907de35e4ce` i předchozí připravený commit byly odeslané na GitHub. Přehled relací a tlačítka jsou dostupné v živém Cockpitu.
- Human–Adam i Knihovna jsou čisté a zarovnané; runtime odpovídá, žádný tah neběží a semafor je volný. Startovací guard povoluje další téma.
- Původní `attention_required` zmizelo po uložení změn; šlo o průběžný nečistý zdroj, nikoliv zaseknutou relaci. Vybraný Linux rozhovor je zachovaný.

Rozhodnutí:
- Uklízelo se uložením práce a bezpečným zarovnáním čistých profilů. Žádná reálná terminálová relace ani soukromá data se nemazala; zůstává pouze naše aktuální CLI relace.
- Tento závěrečný zápis je pouze dokumentace; aplikační kód se od úspěšné plné brány nemění.

Další krok:
- Po závěrečném uložení tohoto zápisu lze pokračovat vývojem Human–Adam; při problému použít Servis → Běžící relace.

Navrhované další kroky:
- Dřívější otevřenou konfiguraci Quick Notes řešit samostatně; nebyla součástí této opravy.

Technický důkaz:
- Plná brána 1540/1540; při nasazení samostatná rychlá brána a serverové smoke 5/5.
- První ověřený restart: PID 24557 → 63335, otisk `e0541dcc9782856d`; serverová účtenka `state=deployed`, `workstream_id=project-cockpit`.
- Živé GET potvrdilo panel, jeho HTTP ovládání a jediný CLI proces; žádný cizí proces nebyl ukončován. Soukromý redigovaný důkaz je v `data/private/codex_sessions_smoke_20260910/live_receipt.json`.
- Obecný health check nemá kritické varování; dříve připomenutá starší záloha se tímto krokem nemění.


### 2026-09-12 08:28 CEST – Přehled screenů a potvrzované uzavření

Hotovo:
- Servis → Běžící relace nově zobrazuje také screeny, jejich stav připojení, stáří a počet procesů uvnitř.
- Běžné uzavření používá přesnou identitu screenu; při neúspěchu lze po dalším potvrzení vynutit ukončení samotného procesu screenu.

Rozhodnutí:
- Screen s běžícím Codexem, chráněným procesem nebo správcem je chráněný. Nejprve se ukončí příslušný Codex.
- Ověřuje se vlastník, spustitelný soubor, projektový adresář i aktuální složení procesů uvnitř. Změna od náhledu požadavek odmítne.
- Riziko: uzavření může přerušit práci v terminálových oknech; po vynucení mohou vnitřní procesy zůstat běžet. UI oba dopady výslovně uvádí.

Další krok:
- Dokončit plnou testovací bránu nad finální verzí, potom provést požadovaný push, řízené nasazení a živé ověření.

Navrhované další kroky:
- Při příštím zaseknutí použít přehled a konkrétní potvrzení; samotné stáří není důkaz zaseknutí.

Technický důkaz:
- Cílené testy screenů a Codex relací 28/28. Skutečný prohlížečový test ověřil zrušení potvrzení, uzavření vlastního testovacího screenu, ochranu aktuálního screenu, mobilní šířku bez přetékání a 0 JS chyb. Plná brána první verze prošla 1553/1553; finální kontrola je součástí odeslání balíčku. Systémový macOS login obal je povolený jen pro ověřeného vlastníka screenu; jiné root procesy zůstávají chráněné.


### 2026-09-12 08:45 CEST – Screeny nasazené a živě ověřené

Hotovo:
- Přehled a potvrzované uzavření screenů jsou dostupné v živém Cockpitu. Aktuální screen s Codexem je chráněný a UI vysvětluje další krok.
- Historický auditní report je uložený; startovací guard již nehlásí nesledovaný soubor.

Rozhodnutí:
- Ověřený rozsah zůstává u konkrétního screenu. Soubory se nemažou a vnitřní procesy se hromadně neukončují.
- Riziko přerušení práce a případného přežití vnitřních procesů zůstává uvedené v aktuálním souhrnu; běžné uzavření ani vynucení se automaticky neopakují.

Další krok:
- Používat Servis → Běžící relace → Screeny. Při obsazeném screenu nejprve ukončit jeho Codex.

Navrhované další kroky:
- Další změny až podle konkrétní zkušenosti při běžném použití.

Technický důkaz:
- Cíleně 28/28, finální plná brána 1554/1554. Prohlížeč: zrušení potvrzení zachovalo vlastní testovací screen, potvrzení ho uzavřelo; současný screen chráněný; mobil bez přetékání; 0 JS chyb.
- Funkční commit 4aa85ca1 odeslaný na GitHub. První živé nasazení: nový PID 9574, otisk 6bc95209fbd6828c, stav deployed a smoke 5/5. Živé GET potvrdilo nový panel i chráněný screen.
- Soukromé technické účtenky jsou v data/private/screen_sessions_smoke_20260912/; závěrečná dokumentace nemění aplikační kód.


### 2026-09-13 12:45 CEST — Obnovení screenu ve VS Code

Hotovo:
- Lokální tlačítko obnoví konkrétní screen do terminálu VS Code na Macu; podporuje běžícího Codexe i potvrzené převzetí připojení.
- Místní doplněk je sestavený bez npm závislostí a nainstalovaný; obsah je verzovaný v `tools/vscode-screen-recovery/`.

Rozhodnutí:
- Míla schválil začít obnovou screenu. Zachovat běžící práci a nepřidávat obnovu samostatných Codex rozhovorů.
- Obnovení je oddělené od uzavření; služby a cizí procesy zůstávají chráněné. Krátkodobé předání se při nejistotě automaticky neopakuje.

Další krok:
- Samostatně potvrdit nasazení Cockpitu a projít první obnovu v běžném okně VS Code.

Navrhované další kroky:
- Případnou obnovu terminálu bez screenu řešit až jako samostatný další rozsah.

Technický důkaz:
- 11 cílených Python testů, 5 JS testů včetně zrušení potvrzení a správného cílení UI. Skutečné připojení v terminálu VS Code zachovalo screen i původní procesy.
- Nativní test přesných argumentů `screen -d -r` potvrdil převzetí připojení: původní testovací terminál oznámil `remote detached`, nový zůstal aktivní.
- Plná Cockpit brána prošla 1 640/1 640 testy. Vizuální kontrola skutečné stránky a první systémové potvrzení zůstávají otevřené; Browser native bridge nebyl dostupný.
- Žádný push ani nasazení Cockpitu. Běžící uživatelské relace nebyly při testech ukončeny; vlastní testovací screeny skončily časovým limitem.

### 2026-09-13 13:18 CEST — Nasazená obnova screenu ve VS Code

Hotovo:
- Běžící Cockpit nabízí obnovu existujícího screenu do VS Code na Macu. Kód obnovy i předchozí lokální prototyp ToBeToHave jsou odeslané na GitHub.

Rozhodnutí:
- Míla výslovně schválil push a nasazení Cockpitu. Nasazení je svázané s kanonickým proudem `project-cockpit`.

Další krok:
- V Servisu projít první obnovu v běžném okně VS Code a případné systémové potvrzení.

Navrhované další kroky:
- Obnova terminálů bez screenu zůstává samostatným případným rozšířením.

Technický důkaz:
- Publikační plná brána: 1 640/1 640 testů. GitHub převzal oba připravené commity včetně `ea13d3d6`.
- Řízené nasazení `ea13d3d6`: `state=deployed`, code stamp `e2ac789cc2a51926`, nový PID 45183; provozní smoke 5/5. Živá stránka obsahuje tlačítko i endpoint obnovy a API screenů vrací oprávnění k připojení.
- První uživatelské potvrzení a skutečná vizuální kontrola zůstávají otevřené; úspěšné předání požadavku samo neprokazuje připojení. Předchozí skutečný test terminálu VS Code zachoval screen i jeho procesy.

### 2026-09-13 20:48 CEST — Navázání na architektonický audit a dokumentový frontend

Hotovo:
- Aktualizovaná TXT roadmapa ukazuje, co z modernizace už vzniklo a kde pokračovat. Původní audit zůstal dohledatelný jako historie.
- Přehled „Dokumenty k vyřešení“ má samostatný frontendový modul s předanými závislostmi; hlavní soubor zkrácen o 121 řádků.

Rozhodnutí:
- Míla schválil aktualizaci auditu a pokračování malým řezem. Zachovat chování, URL, potvrzování a soukromé hranice; nerozšiřovat změnu na celý dokumentový systém.

Další krok:
- Samostatně schválit push/nasazení lokálně ověřeného řezu a provést živou přejímku.

Navrhované další kroky:
- Při další etapě zmapovat read-only hledání/čtečku a její vazby.
- Změřit nejdražší testovací skupiny; plnou release bránu zachovat.
- Dokončit společnou Mac/iPhone přejímku pěti původních auditních scénářů.

Technický důkaz:
- Těla čtyř původních funkcí jsou byte-identická; HTML/CSS nezměněné. Hash celé sestavené stránky změněn po kontrole samotného přesunu a nových předaných závislostí.
- 29 cílených Python testů, včetně 5 Node kontraktů. Browser před/po: stejný DOM a POST payload pro přesně vybraný syntetický dokument, desktop/mobilní viewport, žádné JS chyby.
- Plná brána: 1641/1641 prošlo; unit část 462.2 s. Žádný push ani nasazení tohoto řezu.

### 2026-09-13 21:18 CEST — Dokumentový modul nasazen a systémový audit uložen

Hotovo:
- Cockpit používá oddělený modul „Dokumenty k vyřešení“ se zachovaným ovládáním. Řízený restart a všech pět provozních kontrol prošly.
- Dokončený systémový audit z Cockpitu je uložen jako historický snapshot; cesta k externí záloze je redigovaná.

Rozhodnutí:
- Míla výslovně schválil push, nasazení a zahrnutí dokončeného auditního reportu. Zápis neslibuje novou implementaci dalších architektonických řezů.

Další krok:
- Při běžném použití zkontrolovat dokumentový panel na Macu/iPhonu; skutečné soukromé dokumenty nebyly součástí automatického UI testu.

Navrhované další kroky:
- Zmapovat read-only hledání/čtečku a vazby na metadata, lifecycle a tisk.
- Změřit nejdražší testovací skupiny a dokončit původní společnou přejímku pěti scénářů.

Technický důkaz:
- Funkční commit `b565d5d6` a auditní `63c2a6d3` pushnuté; řízené nasazení `63c2a6d37955` má `state=deployed`, nový proces potvrzen, stamp `dca8e8f41f3480c0`, smoke 5/5.
- HTTP stránka je shodná s aktuálně sestaveným HTML a obsahuje nový dokumentový modul. Plná brána funkčního řezu 1641/1641; následná statická a nasazovací rychlá brána prošly.
- První pokus zastavil souběžně vytvořený report v nečistém Gitu; po jeho schváleném uložení blokátor odstraněn. Závěrečný dokumentační commit podléhá stejnému řízenému nasazení; autoritou přesného headu je živý deployment receipt.
- Omezení: uživatelská přejímka skutečného dokumentového toku na Macu/iPhonu zůstává otevřená. Report upozorňuje na zálohu z 5. 9.; záloha nebyla tímto krokem spouštěna.

### 2026-09-13 22:00 CEST — Hledání dokumentů odděleno od hlavního frontendu

Hotovo:
- Hledání a výsledkové karty mají samostatný modul. Zachované ovládání i rozdíl mezi dokumentem a nákupním PDF.
- Průzkum oddělil načítání/vykreslování od akcí a zmapoval čtečku sdílenou s případy, připomínkami a e-mailovým zpracováním.

Rozhodnutí:
- Míla schválil přesný návrh a lokální vývoj. Do modulu přesunout pouze dvě funkce, předat závislosti a vystavit pouze hledání. Zapisující obsluhy, serverovou čtečku, HTML/CSS a backend zachovat.

Další krok:
- Samostatně schválit push/nasazení tohoto řezu; pak běžná uživatelská přejímka.

Navrhované další kroky:
- Oddělení stránek čtečky připravit jako další samostatný strukturální krok.
- Navazující audit a úpravu UI řešit po strukturální etapě; v UI prověřit chybějící stránkování a Janiččino otevření zavřeného panelu.
- Záloha odložena Mílou na 14. 9. pro nedostupný disk; Santiago zatím bez založení projektu.

Technický důkaz:
- 49 cílených Python testů (32 frontend/gate/search + 17 stávajících testů čtečky, vyhledávání a navazujících akcí), včetně spuštění 8 nových Node kontraktů, vše OK.
- Před/po browser 1440/390 px: shodné výsledkové DOM a přesné obsluhované reference/payloady, správné zrušení tisku i obnovení hledání po lifecycle/stavu; nulové JS chyby. Všechna API v testu nahrazená, včetně stávajícího startup intake monitoru; žádný reálný tisk ani práce se soukromými dokumenty.
- Dvě původní funkce přenesené doslova (142 řádků); ostatní `app.js` po odečtení wiring bloku shodný, HTML/CSS shodné. App 7196 → 7063 řádků, nový modul 159. Hash celé složené stránky aktualizován až po této kontrole.
- Push ani nasazení nového řezu neprovedeny. Neřeší stránkování, paralelní dotazy ani pozdější grafické změny; plná brána předchozího řezu se nevydává za současnou.

### 2026-09-13 22:15 CEST — Generování obou čteček odděleno ze serveru

Hotovo:
- Dokumentová i nákupní čtečka mají samostatný modul pro generování stránky. Jejich vzhled, otevření, návraty a tisk zůstávají zachované.
- `cockpit.py` je kratší o 176 řádků; souborové resolvery, HTTP odpovědi a tiskové endpointy zůstávají na původním místě.

Rozhodnutí:
- Míla schválil další lokální commit a odložení společného push/nasazení. Přenést obě funkce doslova a zachovat jejich původní importovatelné názvy přes `cockpit.py`.

Další krok:
- Na samostatný pokyn společně pushnout a nasadit hledání i čtečky; do té doby čistý main napřed neblokuje další téma.

Navrhované další kroky:
- Podle roadmapy změřit nákladné testovací skupiny a dokončit společnou Mac/iPhone přejímku.
- Navazující audit a UI řešit odděleně; k dřívějším dvěma UI nálezům přibývá stávající návrat nákupní čtečky bez fallbacku při chybějícím openeru. Zachované chování, zde bez opravy.

Technický důkaz:
- 40 cílených Python testů (28 frontend/gate + 12 čtečka/soubory/tisk/URL), včetně 11 nových Node testů nad JS skutečně vygenerované dokumentové a nákupní stránky, vše OK. Testy používají syntetické reference a nahrazené transporty.
- Byte shoda šesti variant HTML před/po (PDF, obrázek, prázdné vstupy, escapovaný název/URL, nákup a prázdný nákup). Těla obou funkcí a ostatní cockpit.py po odečtení importu shodné; žádné změny frontendových fingerprintů.
- `cockpit.py` 11068 → 10892 řádků, nový `cockpit_document_readers.py` 191. Čistý renderer s importy pouze ze standardní knihovny; serverový code stamp automaticky zahrnuje všechny app/*.py moduly.
- Jde o běžný přesun bez změny tiskové/persistenční logiky: cílené testy a statická brána, bez nového běhu plné brány a bez reálného tisku. Starší plná brána se nevydává za aktuální. Nový push/nasazení neprovedeny.

### 2026-09-13 22:42 CEST — Změřené náklady celé testovací brány

Hotovo:
- Volitelné měření ukazuje časy jednotlivých testů a součty podle modulů. Výchozí brána i všechny její kontroly zachované.
- Jedna plná brána 1649/1649 prošla. Čtyři Git/workspace skupiny: 88 testů, 313,32 s (73,5 % času); běh celé unittest sady 426,38 s.

Rozhodnutí:
- Míla schválil třetí lokální commit s měřením, jedním plným během a návrhem zrychlení. Žádné vyřazení testů, paralelizace ani obcházení release brány.

Další krok:
- Pro případný optimalizační pilot rozdělit dva nejpomalejší deploy testy na cenu přípravy a Git operací; až podle toho upravit izolované testovací prostředí.

Navrhované další kroky:
- Společný push/nasazení tří lokálních kroků až na samostatný pokyn; čistý main napřed neblokuje další téma.
- Podle roadmapy dokončit společnou Mac/iPhone přejímku a potom navazující audit/UI.

Technický důkaz:
- Přepínač `--unit-test-timings PATH`, bezpečný JSON a report `cockpit_test_timings_2026_09_13.md`. 18 cílených testů, poté jedna plná brána 1649/1649, unit 426,384 s, podproces 429,7 s, importy 2,773 s. Žádné selhání ani skip.
- Měřený test zahrnuje vlastní setUp/tearDown; ostatní společná příprava a režie explicitně zvlášť (0,071 s). Stejný manifest/pořadí, výsledky i návratové kódy.
- Staticky potvrzené skutečné lokální Git repozitáře v pomalých testech a nahrazená gate/smoke. Podíl přípravy versus jednotlivých Git operací zatím není změřený; zrychlení se ještě neslibuje.
- Kód/plná brána ověřené nad lokálním základem f1b41dc5 plus tento krok; následně pouze projektový zápis a statická kontrola. Push/nasazení zůstávají odložené.


### 2026-09-13 23:05 CEST — Jednodušší příprava testů nasazení

Hotovo:
- Příprava integračních testů nasazení potřebuje o 34 Git procesů méně; v pilotu klesla přibližně ze 3,7–4,7 na 2,3–2,5 sekundy.
- Testy si nadále vytvářejí vlastní skutečné repozitáře. Nový regresní test ověřuje jejich čistý výchozí stav a vzájemnou nezávislost.

Rozhodnutí:
- Míla schválil další lokální krok. Podle měření přesunuta konfigurace syntetické brány před vytvoření kopií; produkční kontroly a vlastní testové scénáře zachované.

Další krok:
- Vybrat další strukturální řez podle konkrétní HTTP/doménové vazby v roadmapě.

Navrhované další kroky:
- Společný push/nasazení čtyř lokálních kroků na samostatný pokyn.
- Dokončit společnou Mac/iPhone přejímku a navázat auditem/UI.

Technický důkaz:
- Osm úspěšných měřených běhů dvou původních testů; příprava 87 → 53 Git procesů, počty ve vlastních scénářích stejné. Report `cockpit_deploy_fixture_pilot_2026_09_13.md` a bezpečný JSON.
- Samostatný regresní test izolace prošel. Plná brána po změně 1650/1650 prošla; unit 455,34 s, deploy skupina 18 testů / 84,49 s.
- Dva vzorky každé varianty nejsou garantovaný benchmark; skutečná úspora celé brány závisí i na ostatních testech a zátěži. Produkční kód, manifest, timeouty a release brány beze změny; push/nasazení odložené.


### 2026-09-13 23:50 CEST — Rychlejší spouštění Gitu bez škrtání testů

Hotovo:
- Správa pracovních kopií na Macu používá přímo systémem vybraný Apple Git; při každém dotazu odpadá opakované spouštění přes systémový launcher.
- Stejných 1655/1655 testů prošlo před i po; unittest 453,73 → 340,30 s, úspora 113,43 s (25,0 %).

Rozhodnutí:
- Míla požádal o další zrychlení a posouzení potřebnosti celé sady. Zachovat kontroly a skutečné Git operace; pro běžný vývoj používat existující cílené sady. Žádné vyřazení testů bez doložení nadbytečnosti.

Další krok:
- Pokračovat strukturálním řezem podle HTTP/doménové vazby s odpovídající cílenou sadou.

Navrhované další kroky:
- Společný push/nasazení pěti lokálních kroků na samostatný pokyn.
- Dokončit společnou Mac/iPhone přejímku a navázat auditem/UI.
- Případné sémantické duplicity testů auditovat po jednotlivých doménách.

Technický důkaz:
- Sedm cílených testů prošlo; fallback při chybě/nedostupné cestě/timeoutu a mimo Mac. AST potvrzuje zachování původní workspace logiky kromě dvou executable pozic.
- Stejných 1655/1655 testů prošlo před i po; unittest 453,73 → 340,30 s, úspora 113,43 s (25,0 %).
- Stejný manifest, testový kód i verze Gitu. Baseline v diagnostickém procesu použil původní launcher, nový běh kanonickou plnou bránu. Report `cockpit_git_launcher_2026_09_13.md` + bezpečný JSON.
- Jeden pár měření není záruka jiného stroje; na Linuxu zůstává původní cesta. Po změně zvoleného Xcode je třeba restart. Nový kód není nasazený a živé zrychlení Cockpitu se netvrdí.


### 2026-09-14 00:00 CEST — Večerní dodání a ranní navázání

Hotovo:
- Funkční balík všech pěti lokálních kroků `21b73cbf` je ověřeně nasazený: hledání, čtečky, měření a obě optimalizace brány.
- Po restartu prošel smoke 5/5 a bylo obnovené připojení Knihovny. Obě pracovní kopie čisté a zarovnané, žádný probíhající tah ani nejisté doručení.
- Závěrečný souhrn a ranní připomenutí jsou součástí tohoto dokumentačního commitu.

Rozhodnutí:
- Míla výslovně schválil push, nasazení a úplné uzavření večera. Ráno pokračovat zrychlením brány, bez dnešního dalšího vývoje.

Další krok:
- Ráno 14. 9. změřit zbývající volání systémového Git launcheru mimo společný workspace helper a vybrat další zrychlení při zachování celé sady.

Navrhované další kroky:
- Zhodnotit cílené vývojové sady a sémantické duplicity po jednotlivých doménách; plnou rizikovou/release kontrolu zachovat.
- Po optimalizaci navázat společnou Mac/iPhone přejímkou a auditem/UI podle roadmapy.

Technický důkaz:
- Funkční nasazení `21b73cbfd4f2`, code stamp `16520ea0d29e3ad1`, nový proces a smoke 5/5; účtenka `2026-09-13T21:56:48+00:00`.
- Redigovaný live audit `2026-09-13T21:58:23+00:00`: deployment `verified_current`, workspaces `aligned_clean` 2/2, runtime `connected`, `turn_busy=false`, bez nejistého doručení. V tomto okamžiku ještě lokální dávka čekala na finální push.
- Srovnávací plné sady 1655/1655, 453,73 → 340,30 s. Dávkový push nad finálním headem provede vlastní povinnou plnou bránu; následné zarovnání nasazení a finální čistotu dokládá živý audit. Tento zápis se nevydává za budoucí GitHub účtenku.

### 2026-09-14 09:10 CEST — Další úspora díky společnému spouštění Gitu

Hotovo:
- Další lokální zrychlení celé testovací sady. Stejných 1656/1656 testů prošlo před i po; 307,14 → 261,43 s, úspora 45,71 s (14,88 % proti dnešnímu výchozímu stavu).
- Testy používají skutečné oddělené repozitáře a zachované operace; přibyla ochrana společného Git modulu plnou bránou.

Rozhodnutí:
- Na Mílův pokyn pokračovat v hledání úspor; sdílet již ověřený výběr Apple Git mezi navazujícími operacemi a společnou testovou přípravou. Zachovat kontroly a původní testy.

Další krok:
- Na samostatný pokyn zahrnout lokální krok do dávkového push/nasazení; další optimalizaci vybírat podle nového měření Git skupin.

Navrhované další kroky:
- Případné další zrychlení nejdřív změřit v nejdražších Git scénářích; nesčítat procenta oddělených měření.
- Pokračovat společnou přejímkou a strukturálními řezy/auditem/UI podle roadmapy.

Technický důkaz:
- Plná kanonická brána prošla, 1656/1656 před i po. Stejné počty po modulech, manifest i Git verze. Report `cockpit_shared_git_2026_09_14.md` + JSON.
- AST: původní resolver a workspace logika zachované; v pěti dalších produkčních modulech jen executable/import a nový gate prefix. Fallback scénáře prošly v obou plných bězích.
- Jeden pár měření na tomto Macu. Nový krok je pouze lokální; poslední nasazený základ `e7723c9a` potvrzen read-only auditem, účtenka a smoke 5/5. Nový push/nasazení se netvrdí.

### 2026-09-14 09:27 CEST — Dodání další optimalizace Gitu

Hotovo:
- Další optimalizace funkčně nasazená, nový proces a smoke 5/5. Dokumentace doplněná pro uzavření společného balíčku.

Rozhodnutí:
- Míla výslovně schválil c+p+n; odeslat připravenou změnu včetně tohoto redigovaného zápisu a ověřit finální nasazení.

Další krok:
- Společná Mac/iPhone přejímka a navazující strukturální řez podle roadmapy.

Navrhované další kroky:
- Další případné zrychlení měřit podle nových Git skupin; pokračovat auditem/UI.

Technický důkaz:
- Funkční `9b306b3d`, code stamp `06880920474429e4`, nový proces, smoke 5/5, účtenka `2026-09-14T07:25:27+00:00`.
- Předchozí plná lokální brána 1656/1656; srovnání 307,14 → 261,43 s. Povinná publikační brána nad konečným commitem běží při dávkovém pushi; její výsledek a finální GitHub/runtime head nejsou předjímány tímto zápisem.

### 2026-09-14 10:10 CEST — Samostatná obsluha čtení dokumentů

Hotovo:
- Dokumentové čtecí HTTP rozhraní má vlastní modul; hlavní server je menší a doména samostatně ověřitelná. Sedm cest a čtyři obsluhy přesunuté při zachování odpovědí.

Rozhodnutí:
- Míla schválil navržený malý strukturální řez. Přístupové kontroly, stávající resolvery a společné ošetření chyb zachovat; dokončit lokálním commitem.

Další krok:
- Samostatně vydat řez a dokončit společnou Mac/iPhone přejímku čteček.

Navrhované další kroky:
- Pokračovat navazujícím auditem/UI a dalším řezem podle konkrétní doménové vazby.

Technický důkaz:
- 61/61 HTTP kontraktů shodných před/po (bez Date/Server); syntetická data, včetně symlinků a vnějších cest. 35 cílených testů; plná brána 1665/1665, unit 252.042 s.
- AST: přesunutá logika a zbytek `cockpit.py` shodné po explicitním předání závislostí. Nový modul v kompilaci, CI filtrech a povinné plné bráně. Report `cockpit_document_routes_2026_09_14.md` + JSON.
- Lokální krok bez nového push/nasazení. `OwlSpeech.csv` a souběžný `8db5cd81` zůstávají mimo tento řez. Ruční přejímka a známé UI nálezy zůstávají otevřené.

### 2026-09-14 10:39 CEST — Samostatná čtecí část e-mailového archivu

Hotovo:
- Stránka archivu, seznam/detail a obsluha souborů i příloh mají vlastní HTTP modul. Šest cest a tři obsluhy přesunuté při zachování odpovědí a pravidel příloh.

Rozhodnutí:
- Míla schválil navržené pokračování stejným postupem jako dokumentový řez; dokončit dalším lokálním commitem pro pozdější společné vydání.

Další krok:
- Samostatně vydat oba HTTP řezy a dokončit společnou Mac/iPhone přejímku dokumentů, archivu a příloh.

Navrhované další kroky:
- Navázat auditem/UI a další strukturální řez volit podle konkrétní doménové vazby.

Technický důkaz:
- 53/53 HTTP kontraktů shodných (bez Date/Server), 49 cílených testů a plná brána 1675/1675, unit 231.324 s. Syntetické soubory/EML, ověřená ochrana před traversal/symlinkem a přesné bajty vybrané přílohy.
- AST: šest větví, tři obsluhy a zbytek hlavního souboru zachované. MIME/disposition politika beze změny. CI, kompilace, rizikové gate cesty i inventura frontendových adres aktualizované.
- Report `cockpit_email_archive_routes_2026_09_14.md` + JSON. Nový krok i dokumentový `8ce24999` pouze lokální, bez push/nasazení či ruční přejímky.

### 2026-09-14 10:47 CEST — Vydání dokumentového a archivačního HTTP rozhraní

Hotovo:
- Funkční kód obou řezů nasazen, nový proces a smoke 5/5 ověřeny. Připraven přesný Mac/iPhone test v `reports/cockpit_http_routes_release_2026_09_14.md`.

Rozhodnutí:
- Míla schválil p+n včetně dokončení zápisů. Audit UI proběhne později samostatně.

Další krok:
- Dokončit společný GitHub balíček s tímto zápisem, ověřit CI a finální nasazení; Míla následně provede ruční přejímku.

Navrhované další kroky:
- Po přejímce samostatný audit UI podle AuditCockpit56_2.txt.

Technický důkaz:
- Nasazený funkční head `da9d0bea`, nový proces potvrzen, smoke 5/5, otisk `0461867a886fdf42`, receipt `2026-09-14T08:45:07+00:00`. Vývojová plná brána 1675/1675; HTTP kontrakty 61/61 a 53/53.
- Ruční přejímka otevřená. Push/CI a finální head se ověřují živými registrovanými audity po uzavření balíčku; nejsou předjímány tímto zápisem.

### 2026-09-14 11:09 CEST — Oprava posouvání archivu na Macu

Hotovo:
- Chyba z Mílovy přejímky reprodukovaná a opravená dvěma CSS deklaracemi. Desktopový seznam i dlouhá zpráva se ve skutečném renderovacím enginu posouvají; mobilní rozložení zachované.

Rozhodnutí:
- Dokončit tuto opravu v návaznosti na schválené p+n. Širší audit UI zůstává samostatný.

Další krok:
- Opravný balíček a řízené nasazení; potom Mílův krátký retest Macu a iPhonu.

Navrhované další kroky:
- Po přejímce samostatný audit UI.

Technický důkaz:
- 160 syntetických zpráv, desktop 1440×900/1024×768 před opravou posun 0, po opravě dosažitelná poslední zpráva a dlouhý detail. Mobil 390×844 před/po shodný. 24 cílených testů, žádné POST či živá soukromá data. Report `cockpit_email_archive_scroll_2026_09_14.md` + JSON.
- Předchozí release 088f725c ověřený včetně CI; tento zápis předchází opravnému push/nasazení. Přímá přejímka opravy na Mílově Macu otevřená.

### 2026-09-14 11:41 CEST — Hluboký UI audit a plán kompaktního řídicího pultu

Hotovo:
- Audit zapsaný na začátek AuditCockpit56_2.txt v2.0: 22 doložených nálezů, rozhodnutí co přesunout/sloučit/zachovat, 11 kroků s přejímkou a aktualizovaný audit struktury. Historie zachovaná.

Rozhodnutí:
- Míla chce přehledné řízení stavů a práce, méně velkých prázdných karet a nepodstatného scrollování. Tento krok je pouze audit a zápis, nikoli implementace. Opravu scrollu 10ec0877 výslovně potvrdil jako funkční.

Další krok:
- Vybrat implementaci U01 (viditelná odezva), U02 (hlavička/návraty), U03 (kompaktní dokumenty); podrobný postup a kritéria jsou v TXT.

Navrhované další kroky:
- U04 stránkování, potom oddělení provozního stavu od běžné práce, jednotná navigace a vizuální přejímka. Funkční rodinné/screen/recovery cesty zachovat.

Technický důkaz:
- Šest browser scénářů s nahrazeným API, žádná živá soukromá data nebo ostré akce. Dva kontrakty adres/registru prošly. Klidný desktop po otevření Dokumentů 1764 px, mobil 3529 px; při naplnění natažené prázdné sousední karty až na 1501 px. Emulace není Safari přejímka.
- Evidence a source otisky: reports/cockpit_ui_audit_2026_09_14.json. Kód aplikace beze změny. Audit neoznačuje DOM existence check za důkaz funkčnosti; návrhy UI dosud neimplementované.

### 2026-09-14 11:53 CEST — U01: viditelný výsledek akcí

Hotovo:
- Společné zprávy jsou dostupné i bez otevření Servisu a nad dialogy. Text zůstane do zavření nebo nové zprávy; chybová či neověřená odpověď společné akce už nemá výchozí „Hotovo“.

Rozhodnutí:
- Míla schválil první vývojový krok. U01 realizován jako malý společný panel; bez změny backendu, potvrzení či payloadů. Push/nasazení nejsou tímto krokem provedené.

Další krok:
- U02: opravit rozměry hlavičky a návraty podle TXT.

Navrhované další kroky:
- U03 kompaktní Dokumenty, U04 stránkování, později sjednocení navigace a vzhledu.

Technický důkaz:
- 15 frontendových testů, statická brána OK. Čtyři izolované browser scénáře: 16 dialogových kontejnerů, pět variant odpovědi, jeden POST na kliknutí, žádné JS chyby. Všechny požadavky syntetické; report `reports/cockpit_ui_u01_2026_09_14.json`.
- Fyzická přejímka Safari/čteček zůstává otevřená. Panel má jednu poslední zprávu, může do zavření překrývat spodní obsah; bez automatického opakování akcí.

### 2026-09-14 14:18 CEST — U02: dostupná hlavička a návraty

Hotovo:
- Tlačítka hlavní lišty se ve zkoušených šířkách neořezávají. Nákupní čtečka se vrací i ze samostatné karty a vysvětlí odmítnuté zavření.
- Blokovaný popup nabízí skutečný odkaz; otevření nové karty zachová práci v Cockpitu. Odkaz je pouze HTTP(S), bez openeru, nová zpráva jej odstraní.

Rozhodnutí:
- Míla schválil další krok U02. Jde o dostupnost navigace, grafický redesign a kompaktní Dokumenty následují samostatně. Bez změny tiskového workflow či backendu.

Další krok:
- U03: hledání nahoře a kompaktní dokumentové karty.

Navrhované další kroky:
- U04 stránkování, později jednotná navigace a grafika podle TXT.

Technický důkaz:
- 15 frontendových testů včetně návratů a tisku; pět izolovaných browser scénářů od 320 do 1440 px. Report `reports/cockpit_ui_u02_2026_09_14.json`.
- Fyzická přejímka Safari po samostatně schváleném nasazení. Cizí nesledovaný adresář zachovaný, změna pouze v konkrétních souborech Cockpitu.
- Doplněné ověření: statická brána prošla, U01 regrese ve čtyřech šířkách (16 dialogů a pět odpovědí v každé) také prošla.

### 2026-09-14 14:44 CEST — U03: kompaktní dokumentová plocha

Hotovo:
- Hledání je nahoře, ověřené nuly mají 43px rozbalovací řádek; skutečná práce a chyby se otevřou. Zdrojové souhrny jsou v detailu. Obecný přehled se při otevření Dokumentů sbalí, hlavní stav a naléhavé prvky zůstávají mimo něj.
- Klidný desktop se ve fixture vejde do jedné obrazovky: 1764→900 px proti auditu. Naplněný desktop 3320→1643 px; mobil 5285→2577 px. Jde o výšku, nikoli čas běhu.

Rozhodnutí:
- Míla schválil U03. Zachované funkční reference, potvrzení, deduplikace i backend; menší zobrazení vzniklo sbalením a rozložením. Publikace/nasazení tímto krokem neprovedené.

Další krok:
- U04: napojit stránkování hledání přes HTTP a UI.

Navrhované další kroky:
- Později sjednocení stavů, navigace a grafiky podle TXT.

Technický důkaz:
- 15 frontendových testů, doplněné dva případy chyby revize; statická brána prošla. Šest syntetických měření a tři behaviorální scénáře: poslední položka klávesnicí, chybové karty, zdroje, revizní reference, zrušená připomínka bez zápisu, case detail, zkrácení, hledání a návrat přehledu.
- `reports/cockpit_ui_u03_2026_09_14.json`. Fyzický Safari Mac/iPhone dosud neověřen; limity backendových seznamů nezměněné. Cizí nesledovaný adresář zachovaný.

### 2026-09-14 15:11 CEST — U04: stránkování dokumentového hledání

Hotovo:
- Dostupné jsou i výsledky za prvními osmi položkami. Předchozí/Další ukazuje rozsah a celkový počet; chybná další stránka neshodí dosavadní výsledek.
- Nový dotaz začíná od první stránky a stará odpověď ho nepřepíše. Návrat ze čtečky zachovává hledání v původním okně, blokovaná čtečka nabídne náhradní odkaz.

Rozhodnutí:
- Míla schválil U04. Napojený existující backend bez změny relevance či deduplikace; nepřidána persistence soukromých dotazů. Push/nasazení neprovedeny.

Další krok:
- U05: jedna prioritní fronta a oddělený provozní stav.

Navrhované další kroky:
- Později jednotná navigace, Servis a grafika podle TXT.

Technický důkaz:
- 27 cílených testů; skutečný HTTP test 23 dokumentů + duplicitní řádek, stránky 8/8/7 a neplatné parametry před poskytovatelem. Čtyři syntetické browser scénáře: více stránek, nulový výsledek, návraty, zablokovaná čtečka, chyba/opakování a opožděná odpověď.
- Plná brána: 1677 testů / 299.260 s, OK. Report `reports/cockpit_ui_u04_2026_09_14.json`.
- Safari přejímka čeká; živý index není zmrazený a reload původního okna hledání resetuje. Cizí nesledovaný adresář zachovaný.

### 2026-09-14 15:25 CEST — U05: jedna fronta a samostatný provozní stav

Hotovo:
- Odstraněné opakované bloky Dnes/Stav/Rychlé akce, zachovaný existující výběr nejvýše tří priorit. Podrobnosti a statistiky patří do Servisu.
- Běžná práce nevyvolává provozní alarm, skutečné problémy i nedostupné zdroje jsou zřetelné. U signálů je čas načtení; úkoly mají zdroj a čas důkazu.

Rozhodnutí:
- Míla schválil U05. Bez nového backendu, persistence či provozních akcí; pouze lokální vývoj, push a nasazení neprovedeny.

Další krok:
- U06: navigace, fokus, návraty; začít jedním reprezentativním dialogem.

Navrhované další kroky:
- Servis a sjednocení grafiky podle TXT; fyzická Safari přejímka po samostatně schváleném nasazení.

Technický důkaz:
- 24 cílených testů (včetně 10 stavových JS scénářů), 10 syntetických browser scénářů a rychlá statická brána OK. Report `reports/cockpit_ui_u05_2026_09_14.json`. Klidný desktop 1440×900 bez scrollu, první mobilní priorita v prvním viewportu; přímý vstup do úkolu/diagnostiky/Human–Adam, výpadek a obnova fronty.
- Plná brána v tomto omezeném frontendovém kroku neopakována; U04 1677 testů je historický důkaz. Zbytková rizika: fyzický Safari netestovaný, čas načtení není záruka čerstvosti zdroje, mobilní stránka dále scrolluje. Cizí nesledovaný adresář zachovaný.

### 2026-09-14 18:36 CEST — U06: navigace a zachování kontextu dialogů

Hotovo:
- Společná správa 16 dialogů; fokus/Tab/Escape podle skutečné vrstvy, pozadí inertní, návrat do původního místa. Pilot Komunikace nejprve ověřen na dvou šířkách.
- Hlavní oblasti mají hash odkazy a označení; pošta/připomenutí patří do Komunikace, projekty/katalog do Servisu. Rodinné zkratky a přístup k Human–Adam zachované.
- Zavření formuláře neznamená zahození: Knihovna a rodinný kalendář zachovávají rozepsanou práci v aktuální kartě. Kolize odezvy s rodinným návratem odstraněna přesunem návratu k hledání.

Rozhodnutí:
- Míla schválil U06. Bez persistence soukromých draftů, změny backendových oprávnění, odchozích akcí, push či nasazení. Původní potvrzení při resetu/editaci jiné položky zachovaná.

Další krok:
- U07: Servis podle účelu, detaily na vyžádání a pravdivé štítky health.

Navrhované další kroky:
- Grafika podle TXT a fyzická Safari/iPhone přejímka po samostatně schváleném nasazení.

Technický důkaz:
- 28 cílených testů včetně stavů dialogů a vazeb DOM; 3 browser scénáře na 320/390/1440 px, v každém 16 dialogů a 6 přímých odkazů/reloadů. Rychlá statická brána prošla. Report `reports/cockpit_ui_u06_2026_09_14.json`. Automatizovaná přejímka zahrnuje vnořený náhled, Recovery, rodinné projekty/hledání a rozepsanou existující editaci.
- Omezení: fyzický Safari/iPhone/VoiceOver neověřený; draft nepřežije potvrzený reload/ukončení; hlavní hash není přesný vnořený stav. Plná brána se u omezené UI změny neopakuje. Cizí nesledovaný adresář zachovaný.

### 2026-09-14 20:03 CEST — Předání U01–U06, U07 až příště

Hotovo:
- Souhrn šesti dokončených UI kroků a jejich důkazů zapsán do AuditCockpit56_2.txt, handoffu a TVBCP.

Rozhodnutí:
- Míla schválil push a nasazení celého čekajícího UI balíčku. U07 výslovně odložený na příští pokračování.

Další krok:
- Po rozhodnutí o nesouvisejícím adresáři dokončit schválené p+n; při příštím vývoji začít U07 (Servis podle účelu).

Navrhované další kroky:
- Po nasazení fyzická Safari/iPhone/VoiceOver přejímka, dále roadmapa TXT. Záloha zůstává odložená.

Technický důkaz:
- Funkční commity končí 2bbdcfc7; poslední lokální U06 přejímka: 28 testů, 16 dialogů na třech šířkách, návraty rodiny a přímé odkazy. Publikace zatím nepotvrzená; nesouvisející nesledované audio podklady zachované mimo commit.

- Závěrečné ověření: 1680/1680 OK (318,932 s), statická brána OK; opraveno zastaralé vymezení funkce v testu. Report `reports/cockpit_ui_release_2026_09_14.md`. Publikace a nasazení nadále čekají na vyřešení nesledovaných podkladů, které zůstaly beze změny.


### 2026-09-14 20:25 CEST — Nasazení U01–U06 a odstranění publikační překážky

Hotovo:
- Funkční head `980aed7a66426665b2e809b097522fba2910dc8c` nasazen a ověřen: nový proces, smoke 5/5 a shoda skutečně podávaného HTML. TXT v2.8 a souhrnný report aktualizované.
- Po Mílově souhlasu přesunuto 35 souborů s audio podklady mimo Git; obsah i oprávnění shodné, SHA-256 ověřeno. Obě publikační brány prošly.

Rozhodnutí:
- Dokončit schválený společný GitHub balíček včetně tohoto zápisu a ověřit finální nasazený head. U07 až příště; dnes jej nezahajovat.

Další krok:
- Při příštím vývoji U07: Servis podle účelu. Fyzická Safari/iPhone/VoiceOver přejímka zatím čeká.

Navrhované další kroky:
- Pokračovat roadmapou TXT; záloha zůstává odložená kvůli nedostupnému disku.

Technický důkaz:
- Receipt `2026-09-14T18:23:41+00:00`, otisk `55373c8c1c4da728`, smoke 5/5. Vývojová plná brána 1680/1680; nasazovací rychlá brána OK. Podrobnosti `reports/cockpit_ui_release_2026_09_14.md`.
- Zápis předchází závěrečnému push; aktuální odeslání a finální head ověřovat živým auditem. Ruční přejímka neproběhla, drafty žijí pouze v aktuální kartě.


### 2026-09-14 21:44 CEST — Web ToBeToHave a přímý vstup z Cockpitu

Hotovo:
- Schválený lokální prototyp má kompletní publikační kopii v `docs/to-be-to-have/`.
- Dlaždice ToBeToHave otevírá web v samostatném okně; Webové aplikace jsou opět
  přímo v horní liště, bez nutnosti hledat je v Servisu.

Rozhodnutí:
- Míla potvrdil, že lokální prototyp je dobrý, a zadal jeho zpřístupnění na webu
  z Cockpitu. Používá se stávající GitHub Pages, cílová adresa https://belisarius-mila.github.io/PythonMF/to-be-to-have/
- Původní aplikace, CSV a zdrojový web se nemění; nejde o vývoj C00 Camina ani U07 Cockpitu.

Další krok:
- Po zveřejnění otevřít Webové aplikace → ToBeToHave a používat oba režimy.

Navrhované další kroky:
- Na fyzickém iPhonu ověřit první tap se zvukem a návrat z pozadí; automatická
  přejímka není důkaz systémové audio politiky Safari.

Technický důkaz:
- 14/14 JS testů trenažéru, 22/22 cílených testů Cockpitu.
- 184/184 MP3, 47/47 WebP a 236/236 místních HTTP odpovědí shodných se zdrojem.
- Regresní test hlídá vstup do aplikací přímo v hlavičce a webový cíl dlaždice.
- Zdrojový checkpoint předchází publikaci; finální head, Pages a nasazení
  ověřují živé GitHub a Cockpit účtenky. Podrobnosti v `reports/to_be_web_release_2026_09_14.md`.


### 2026-10-16 19:45 CEST — Kvantitativní přehled vynechává pracovní kopie a sestavené soubory

Hotovo:
- Místní statistika znovu měří vlastní projekt: přibližně 347 tisíc řádků
  a 2 143 souborů místo 877 153 řádků / 16 164 souborů.
- Skutečné nesledované zdroje zůstávají zahrnuté; jde o text včetně testů,
  paměti a dokumentace, nikoli pouze programový kód.

Rozhodnutí:
- Cílená oprava počítání; žádný úklid ani mazání. Film, Camino aplikace,
  přenosová služba, archiv a síť nejsou součástí změny. U07 se nezahajuje.

Další krok:
- Samostatně autorizovat nasazení Cockpitu a porovnat živý součet. Do té
  doby běžící proces používá starý výpočet; push neproběhl.

Navrhované další kroky:
- U07 Servis podle účelu zůstává odložený. Filmové ovládání Míla vyzkouší
  v neděli 18. 10. doma; tato oprava film nemění.

Technický důkaz:
- Původní oprava `f5014992` zůstala v kódu; pokrývala Python prostředí a tmp,
  ne `data/daily_3am` (8 519 souborů / 525 023 řádků) a Swift `.build`
  (5 502 souborů / 5 251 řádků). Oprava navíc vynechává vnořené Git kořeny
  podle `.git` adresáře i souboru, běžné build/závislostní adresáře a symlinky.
- Registrovaný read-only CLI a živé API měly před opravou shodné součty.
  Po opravě místní CLI 2 143 souborů / 347 049 řádků včetně zápisu dokumentace.
  12 cílených testů PASS (agregace, klony/buildy/worktrees/symlinky, Cockpit
  přehled a systémový audit). Rychlá statická brána PASS; důkaz
  `logs/cockpit_quantitative_scope_20261016.log` (agregáty, mimo Git).


### 2026-10-16 19:59 CEST — Opravený počet souborů a řádků je v živém Cockpitu

Hotovo:
- Živá statistika při přejímce ukázala 2 143 souborů / 347 051 řádků;
  publikační klon a sestavené výstupy se už nezapočítávají.
- Oprava je na GitHubu a řízeně nasazená v Cockpitu, smoke 5/5 PASS.

Rozhodnutí:
- Míla zadal „prosím p+n“ pro tuto opravu. Nasazuje se pouze Cockpit.
  U07 ani další vývoj střižny se tím nezahajují.

Další krok:
- Obnovit přehled v Cockpitu a zkontrolovat nový součet.

Navrhované další kroky:
- U07 Servis podle účelu zůstává odložený; fyzický test filmového ovládání
  podle dohody v neděli 18. 10. doma.

Technický důkaz:
- Kód `475fc852`, otisk `236dd9f53426942e`, při prvním ověřeném nasazení
  PID 2889, nový proces potvrzený a receipt `deployed`. Úplná místní brána
  1941/1941 PASS (477,2 s), předchozích 12 cílených testů PASS a rychlá
  nasazovací brána PASS. GitHub workflow tuto změnu podle filtrů samo
  nespouští; publikační důkaz je místní úplná brána, nikoli výsledek CI.
- Camino: PID 47332, release `f60a33c98fd5`, konfigurace/Serve a stav
  893 operací / 304 ověřených médií přesně shodné před/po, flags false.
  Owner HTTP/HTTPS i anonymní 401 PASS, Funnel off; celý JSON filmového
  editoru má shodný hash. Žádný nový render ani změna střihu.
- Redigované důkazy `logs/cockpit_quantitative_publish_gate_20261016.log`,
  `logs/cockpit_quantitative_live_20261016.log` a před/po Camino logy.
  Zápis předchází dokumentačnímu uzavření; jeho finální head/PID potvrzuje
  řízené nasazení a následná živá účtenka.


### 2026-10-16 20:38 CEST — Autosave znovu ukládá i mimo původní terminálovou relaci

Hotovo:
- Obnoveno průběžné ukládání aktuální relace a čitelný text. Původních
  12 historických dvojic je zachováno; automatické mazání zůstává vypnuté.
- Lokálně je připravený přehled Stav autosave: červené zastavení, zastarání
  i chyba ukládání, datum poslední kopie a vysvětlení režimu retence.
- Samostatný start přežije zavření terminálu. Připravený vlastní LaunchAgent
  zajistí start po přihlášení a automatické obnovení po pádu po jeho aktivaci.

Rozhodnutí:
- Míla označil trvalý běh autosave za absolutní prioritu a zadal zapnutí
  i navržené úpravy. Systémová instalace vyžaduje přesnou globální brzdu;
  bez ní je připravená pouze v projektu. Camino, přenosy a film se nemění.

Další krok:
- Potvrdit přesnou globální brzdu pro připravený LaunchAgent a samostatně
  schválit push/nasazení panelu; průběžné ukládání mezitím běží.

Navrhované další kroky:
- Aktivovat připravené spouštění po přihlášení a znovu ověřit čerstvou kopii.
- Fyzický filmový test zůstává na neděli 18. 10.; tato oprava ho nezahajuje.

Technický důkaz:
- 72 cílených testů PASS: moderní zprávy, cizí projekt, neúplný koncový
  řádek, chybějící zdroj, zachování předchozí dvojice při diskové chybě
  a následná obnova, ochrana historie, vlastnictví procesu, restartový
  LaunchAgent a zákaz zaměnit běžné ano za globální potvrzení.
- Živý redigovaný důkaz `logs/autosave_continuity_live_20261016.log`: jeden
  proces, čerstvý záznam právě této relace, čitelný TXT přes 90 KiB,
  předchozí dvojice a všech 24 původních historických souborů zachované.
- Úplná brána 1954/1954 PASS (334,664 s testů),
  `logs/autosave_continuity_full_gate_20261016.log`. Žádný obsah konverzace
  ani soukromé autosave soubory nejsou součástí Gitu.


### 2026-10-16 21:19 CEST — Trvalý autosave a automatická obnova jsou živě ověřené

Hotovo:
- Autosave je po přesném potvrzení nainstalovaný jako vlastní uživatelská
  služba; nezávisí na otevřeném terminálu a je nastavený ke startu po přihlášení.
- Po řízeném ukončení ukládacího procesu služba sama vytvořila nový proces
  a čerstvou technickou i čitelnou kopii. Starší historie zůstala zachovaná.

Rozhodnutí:
- Potvrzení zahrnuje připravenou systémovou aktivaci i push/nasazení panelu.
  Automatické mazání zůstává vypnuté. Camino ani síť se neupravují.
- Start služby používá projektový Python jako rodiče workeru; přímý shellový
  start na tomto Macu nedokázal otevřít skript na Ploše. Instalace vyžaduje
  čerstvé úspěšné uložení; samotná registrace není důkazem funkčnosti.

Další krok:
- Odeslat schválené změny a řízeně nasadit panel Stav autosave v Cockpitu.

Navrhované další kroky:
- Fyzický filmový test zůstává na neděli 18. 10.; U07 zůstává odložený.

Technický důkaz:
- 45 cílených servisních testů PASS, závěrečná plná brána 1957/1957 PASS
  (338,377 s testů); log `logs/autosave_continuity_service_full_gate_20261016.log`.
- Živá obnova: supervisor 15687 → 15724, worker 15689 → 15725, jediný
  watcher, čerstvý JSONL/TXT (čitelný text přes 90 KiB), předchozí dvojice
  zachovaná, bez poslední chyby. `logs/autosave_continuity_launchd_20261016.log`.
- Skutečný restart Macu ani nové přihlášení nebyly fyzicky zkoušeny.


### 2026-10-16 21:21 CEST — Stav autosave je nasazený a Camino zachované

Hotovo:
- Cockpit ukazuje běh, stáří poslední kopie, případnou chybu a skutečný
  režim mazání; červené zastavení není skryté prázdným seznamem úklidu.
- Trvalá služba ukládá nezávisle na relaci a přežila restart Cockpitu.
  Automatické obnovení workeru a čerstvé kopie byly před nasazením živě ověřené.
- Schválený kód je na GitHubu a v běžícím Cockpitu, smoke 5/5.

Rozhodnutí:
- Historie zůstává zachovaná a automatické mazání vypnuté. Žádná změna
  služby Camino, původních médií, filmového střihu ani síťové konfigurace.

Další krok:
- Obnovit stránku Cockpitu a používat přehled Stav autosave.

Navrhované další kroky:
- Filmový editor vyzkoušet podle dohody v neděli 18. 10.; U07 je odložený.

Technický důkaz:
- Kód `0c2908c9`, otisk `1de95c8007aa2f39`, první nový PID 25774,
  receipt `deployed`, smoke 5/5. Místní úplná brána 1957/1957 PASS;
  GitHub kontrola byla při publikaci spuštěná, tento zápis její výsledek netvrdí.
- Camino PID 47332/release `f60a33c98fd5`, konfigurace/Serve,
  cursor 893, flags false a úplný JSON editoru shodné před/po.
  Owner HTTP/HTTPS i anonymní 401 PASS, Funnel off.
- Redigované důkazy `logs/autosave_continuity_deploy_code_20261016.log`,
  `logs/autosave_continuity_launchd_20261016.log` a Camino before/after logy.
  Finální dokumentační head/PID potvrdí závěrečná živá účtenka.
- Skutečný restart Macu/přihlášení ani fyzický Safari/iPhone test neproběhly.
  SSD hlásí 23,6 GiB volného místa; ukládání samo chybu nehlásí.


### 2026-10-17 13:39 CEST — Bod 1: pravdivé provozní informace připravené lokálně

Hotovo:
- Kontrola stránky a diagnostika označují přítomnost UI prvků; netvrdí ověření
  napojených událostí nebo funkčnosti všech tlačítek.
- Rodinný kalendář čte aktuální bezpečný stav automatiky s časem kontroly.
  Rozlišuje zapnuté/vypnuté odesílání, náhledový režim a překážku; výpadek
  nebo neplatná odpověď přizná neověřený stav.
- Novější odpověď má přednost před opožděnou a zavřený dialog zneplatní
  probíhající kontrolu. Návrat do otevřeného kalendáře stav znovu ověří.

Rozhodnutí:
- Míla zadal bod 1. Jde o zobrazení a read-only GET, nikoli změnu konfigurace
  nebo aktivace odesílání. Bod 2 (struktura Servisu) zůstává další samostatný krok.
- Implementace a ověření jsou lokální; push ani nasazení tím nejsou provedené.

Další krok:
- Samostatně potvrdit publikování a nasazení tohoto dokončeného kroku.

Navrhované další kroky:
- Bod 2 U07: rozdělit Servis podle účelu.
- Bod 3: narovnat zastaralé návrhy v systémových auditech.
- Filmový editor vyzkoušet doma podle dohody 18. 10.

Technický důkaz:
- 42 cílených testů PASS, plná brána 1961/1961 PASS (267.752 s testů).
  Ověřeny režimy, bezpečný výpadek, redakce soukromé chyby, skutečný read-only
  GET a regresní pořadí/zavření asynchronních odpovědí v prohlížeči.
- GET `/api/family-calendar/delivery-status` vrací pouze stav, bezpečnou zprávu,
  čas a read-only příznak. Přímý registrovaný audit potvrdil aktivní režim;
  kontrolní součty soukromé konfigurace i doručovacího stavu se nezměnily.
- Camino PID 47332, konfigurace a Serve shodné; owner HTTP/HTTPS a anonymní
  401 ověřené, Funnel off. Autosave nadále jeden čerstvý proces bez chyby.
- Důkazy v `logs/cockpit_truthful_status_targeted_20261017.log`,
  `logs/cockpit_truthful_status_full_gate_20261017.log` a redigované validation log.
  Běžící Cockpit zůstává v předchozím nasazení; fyzická přejímka nového UI čeká.


### 2026-10-17 13:51 CEST — Bod 2: Servis přehledně podle účelu

Hotovo:
- Servis má pět samostatně rozbalovacích částí: Provoz, Relace, Obnova,
  Vývoj a Diagnostika. Každá má stručnou nápovědu k obsahu.
- Přehled relací a stav autosave se otevírají přímo; odstraněné dvě vzdálené
  duplicitní zkratky. Akce jsou u souvisejícího stavu, podrobnosti dokumentů
  a zálohy se rozbalují na vyžádání. Dlouhé výpisy se zalamují, tabulka PDF
  má na úzkém displeji vlastní posouvání.

Rozhodnutí:
- Míla zadal bod 2. Použité běžné rozbalovací prvky prohlížeče, bez další
  vrstvy navigace či ukládání. Původní ovládání, potvrzení a ochrana procesů
  zůstávají; samotné otevření části nespouští restart ani úklid.
- Změna je lokální. Push, nasazení a fyzická přejímka se posuzují samostatně.
  Camino, filmová data, síť ani služba autosave se neupravují.

Další krok:
- Samostatně potvrdit publikování a nasazení dokončených bodů 1 a 2.

Navrhované další kroky:
- Bod 3: narovnat zastaralé návrhy v systémových auditech.
- Filmový editor vyzkoušet doma podle dohody 18. 10.

Technický důkaz:
- 341 cílených testů PASS; po finálním mobilním zalamování frontend 20/20
  PASS. Společná navigace a rychlá statická brána PASS; úplná brána se pro
  tento omezený frontendový krok neopakuje, předchozí bod 1 měl 1961/1961 PASS.
- Headless Edge: 320/390/1440 px, Enter/mezerník, návrat fokusu z pěti dialogů,
  dostupnost obnovy screenu a zrušení ukončení relace, obnovy, úklidu i restartu.
  Všechny požadavky nahrazené testovacími odpověďmi; žádná živá akce neproběhla.
  Rozbalené podrobnosti na 320 px: výpis čitelný, tabulka posouvatelná, bez
  vodorovného posouvání celé stránky. Screenshoty vizuálně zkontrolované.
- Read-only provozní kontrola 13:49 CEST: Camino vlastněné/běžící; autosave
  jediný worker, kopie 4 min, bez poslední chyby, automatické mazání vypnuté.
- Report `reports/cockpit_ui_u07_2026_10_17.json`, redigované logy
  `logs/cockpit_service_groups_*_20261017.log`. Běžící Cockpit nebyl nasazený;
  fyzický Safari/iPhone/VoiceOver test tohoto kroku zůstává otevřený.


### 2026-10-17 14:30 CEST — Bod 3: Doporučení auditů mají zdroj a přiznávají nejistotu

Hotovo:
- Audit schopností už neoznačuje ručně napsané podněty jako zjištěné mezery
  nebo aktuální priority. Starý návrh implementovat kalendář a červnový
  termín sítě odstraněné; u zkratek, tisku a fotografií odkaz na dnešní ověření.
- Projektový audit uvádí čas sestavení, poslední commit ACTIVE_PROJECTS.md
  a odkaz na handoff u projektu. Čas celého souboru nepovažuje za důkaz
  stáří či pravdivosti každého údaje. Neověřený provoz přiznává i u vrstev.
- Při zjištěném driftu se ze starého agregátu nenabízí konkrétní projektová
  práce. Skutečné registry gaps zůstávají viditelné.

Rozhodnutí:
- Míla schválil bod 3. Reporty zůstávají read-only nad git-safe podklady;
  živou aktivaci kalendáře, doručení ani fyzická zařízení samy neověřují.
  Pro tyto údaje odkazují na registrované živé audity, bez čtení tajemství.
- Žádná změna služeb Camino/Cockpit/autosave, sítě, médií či odesílání.
  Starý nesledovaný report z 16. 10. zachovaný, nikoli automaticky přepsaný.
  Push a nasazení nebyly zadané ani provedené.

Další krok:
- Samostatně potvrdit publikování a nasazení dokončených bodů 1–3.

Navrhované další kroky:
- Po nasazení fyzicky vyzkoušet nové členění Servisu na iPhonu.
- Filmový editor vyzkoušet doma podle dohody 18. 10.

Technický důkaz:
- 20 cílených testů PASS včetně skutečně chybějícího toolu, starých podnětů,
  času podkladu vs. sestavení, neznámého stáří, potlačení práce při driftu,
  save=False bez nového reportu a původního Cockpit rozhraní/reportů.
- Rychlá Cockpit statická brána PASS. Nezměněná persistence ani odchozí
  workflow, proto se pro tento reportovací krok neopakuje plná brána.
- Registrované CLI capability a quick projektového auditu ověřené read-only;
  tool registry 85/85, původní autoritativní drift kontrola zachovaná.
- Důkazy `logs/cockpit_audit_recommendations_targeted_20261017.log`,
  `logs/cockpit_audit_recommendations_static_20261017.log` a oba after logy.
  Vše lokální; běžící Cockpit používá dosavadní nasazení.
- Read-only kontrola 14:30 CEST: Camino vlastněné/běžící, autosave jediný
  worker, kopie 5 min, bez poslední chyby, automatické mazání vypnuté;
  `logs/cockpit_audit_recommendations_live_20261017.log`.


### 2026-10-17 14:41 CEST — Body 1–3 zveřejněné a funkčně nasazené

Hotovo:
- V běžícím Cockpitu je přesná kontrola přítomnosti prvků, živý bezpečný stav
  kalendáře, pět účelových částí Servisu a opravené zdroje doporučení auditů.
- Čtyřcommitový balíček včetně dřívějšího zápisu o omezeném SSD úklidu je
  na GitHubu. Řízené nasazení doložilo nový proces a smoke 5/5.
- Místní i Tailscale HTTPS HTML přesně odpovídá implementaci; nové API
  kalendáře vrací aktivní režim, čas a read-only příznak. Projektový audit
  má zdroje a neověřený provoz, GET nevytvořil uložený report.

Rozhodnutí:
- Míla výslovně zadal „Vše nyní p+n“. Publikování a nasazení jsou tím
  schválené včetně tohoto povinného uzavíracího zápisu.
- Push po úspěšné plné bráně narazil na Keychain helper v Cockpitu;
  platné terminálové CLI přihlášení dokončilo stejný přesný fast-forward
  po novém auditu hlav a push guardu podle LL-060.
- Starší nesledovaný TXT audit z 16. 10. zůstal na stejném místě a se
  shodným SHA-256; přesné místní exclude pravidlo vyjímá jen tento podklad.
  Žádné mazání, změna Camino, sítě, médií, střihu ani služby autosave.

Další krok:
- Obnovit Cockpit a fyzicky vyzkoušet nové členění Servisu na iPhonu.

Navrhované další kroky:
- Filmový editor vyzkoušet doma podle dohody 18. 10.
- Další UI vývoj vybírat podle fyzické přejímky a zbývajících bodů roadmapy.

Technický důkaz:
- Kód `ae30beddcdfd`, otisk `50ffdf992ae6552a`, první nový PID 59776,
  receipt deployed, new_process_confirmed=true, smoke 5/5. Plná publikační
  brána: 1963 testů OK, 11 přeskočených (266,195 s samotných testů).
  Nasazení používá navazující rychlou bránu; fyzická přejímka se netvrdí.
- Hash místního/HTTPS HTML shodný. Nový kalendářový GET vrací výhradně
  ok/state/message/checked_at/read_only; změny automatiky ani odeslání neproběhly.
- Camino PID, konfigurace, Serve a HTTP/HTTPS state i celý JSON filmového
  editoru přesně shodné před/po. Owner HTTP/HTTPS a anonymní 401 PASS,
  Funnel off. Autosave jediný worker, kopie 5 min, bez poslední chyby;
  automatické mazání vypnuté a trvalá služba zachovaná.
- Redigované důkazy `logs/cockpit_release_deploy_code_20261017.log`,
  `logs/cockpit_release_ui_code_20261017.log`, protected before/after logy
  a záznam zachování TXT auditu. Finální dokumentační head/PID ověřuje živá
  účtenka po závěrečné publikaci tohoto zápisu.


### 2026-10-17 14:58 CEST — Vývojový runner vyřazený ze Servisu

Hotovo:
- V místní verzi už Servis neobsahuje panel Vývojový runner ani jeho tři
  tlačítka. Část Vývoj ponechává Projekty, Git a terminál; popisek tomu odpovídá.
- Odstraněné jsou také příslušné DOM proměnné, click handler a formátování
  výsledku, aby po odebrání panelu nevznikla chyba při inicializaci stránky.

Rozhodnutí:
- Míla potvrdil odstranění panelu, protože jej pro společnou práci nepotřebuje.
- Rozsah je pouze frontend. Backendový allowlist/API a standardní kontroly
  vývoje zůstávají. Žádná změna služeb, síťové konfigurace ani soukromých dat.

Další krok:
- Po samostatném p+n nasadit tuto místní změnu a zkontrolovat Servis.

Navrhované další kroky:
- Zachovat domluvenou fyzickou přejímku Servisu a filmového editoru.

Technický důkaz:
- 33 cílených unittestů PASS: frontendové kontrakty, navigace, vyřazený hlasový
  frontend a hlavní HTML/route kontrakty. Aktualizovaný očekávaný otisk HTML.
- Rychlá statická brána PASS; logy `logs/cockpit_runner_ui_targeted_20261017.log`
  a `logs/cockpit_runner_ui_static_20261017.log`.
- Bez push a restartu/nasazení. Fyzická přejímka nové úpravy čeká;
  současný provoz se tímto zápisem znovu nepotvrzuje.


### 2026-10-17 15:43 CEST — Předání celého p+n balíčku Luně a návrat původnímu Adamovi

Hotovo:
- Lokální implementace předává Luně celý neprázdný rozsah commitů pro Cockpit.
  Náhled a souhlas určují oba přesné heads; počet commitů není omezený na jeden.
- Záznam a oddělený vykonavatel přežijí zavření karty či restart Cockpitu.
  Dosavadní plná brána, batch push, řízený restart a následné smoke zůstávají.
- Chat Cockpitu umí přesné p+n, přehled stavu a zkoušku bez publikování.
  Běžné otázky a p+n jiných pracovních proudů zachovávají původní cestu.
- Řízení se vrací původnímu Adamovi: Cockpit do stejného uloženého vlákna
  v read-only režimu; přímá relace přes pomocného agenta ke svému volajícímu.
  Výchozí model ani globální konfigurace se nepřepínají.

Rozhodnutí:
- Míla schválil implementaci předání celého balíčku a návratu do jedné
  konverzace. Vývoj není souhlasem k ostrému push/nasazení tohoto kroku.
- První podporovaný cíl je Cockpit. Luna má krátké předání a read-only
  modelový tah; privilegované kroky vlastní registrovaný Python.
- Neopakovat nejistý push ani restart, neopravovat kód či přihlášení. Soukromý
  token je svázaný s fází, změna SHA/projektu blokuje další publikování.
- Známý Keychain problém řeší jen jednorázová volba již platného CLI helperu
  pro přesný HTTPS GitHub push podle LL-060. Žádná změna globálního helperu
  ani token v argv; stav stávajícího CLI přihlášení read-only potvrzený.

Další krok:
- Po samostatném p+n zavést nové routy dosavadní cestou; následující balíček
  projde prvním ostrým předáním Luně.

Navrhované další kroky:
- Fyzicky vyzkoušet Servis a novou kartu předání na iPhonu.
- Filmový editor vyzkoušet doma podle dřívější dohody.

Technický důkaz:
- 147 cílených a 27 závěrečných regresních testů PASS; širší integrační sada 554 testů PASS.
  Plná brána 1993/1993 PASS, bez přeskočení (267,315 s testů).
  Ověřená oprava zastaralého počtu rizikových schopností a souběhu při
  dokončení úlohy; bezpečný důvod chyby se zachovává v účtence pro Adama.
- Skutečný model gpt-6-luna přijal syntetický balíček 7 commitů s přesným SHA
  za 5,81 s. Suchý běh vykonavatele prošel i skutečnými read-only kontrolami
  Camino/autosave. Žádný push, restart, změna sítě, filmu ani autosave.
- Skutečný App Server návrat do stejného vlákna prošel v oddělené syntetické
  konverzaci; doručení potvrzené, testovací model zachovaný, provozní konverzace
  beze změny. Log `logs/luna_release_live_return_20261017.log`.
- Node VM ověřil zrušení potvrzení, nepublikující dry-run, chybu transportu,
  obnovení výsledku po reloadu a zachování běžného p+n jiných proudů.
- Logy `logs/luna_release_final_targeted_20261017.log`,
  `logs/luna_release_live_probe_20261017.log`,
  `logs/luna_release_live_dry_run_20261017.log`,
  `logs/luna_release_full_gate_20261017.log`.
- Pravidla `technical/luna_release_orchestration.md`. Ostré p+n a fyzická
  přejímka nejsou suchým během prokázané. Zavedení ještě neproběhlo.

### 2026-10-17 16:37 CEST — Obecné p+n přes Lunu pro vývoj v portálu

Hotovo:
- Stejné předání celého balíčku a návrat původnímu Adamovi funguje lokálně
  ve všech 33 kanonických vývojových proudech a v přímé relaci.
- Náhled a potvrzení svazují projekt, registrovaný cíl a přesné koncové commity.
  Změna projektu se zastaví ještě před push; nonce platí pouze pro danou fázi.
- Běžné proudy používají dosavadní společný runtime Samanthy/Cockpitu.
  MMTX, ToBeToHave a ColorsAndNumbers používají existující Pages publisher;
  webové aplikace mají vlastní HTTP smoke cestu, bez restartu Cockpitu.
- Již odeslaný main lze po plné bráně nasadit bez dalšího push. Soukromá
  účtenka, nepublikující zkouška, ochrany a návrat do původní konverzace zůstávají.

Rozhodnutí:
- Míla výslovně rozšířil workflow na jakýkoliv vývoj obecně.
- Server volí cíl z katalogu a registrovaných vazeb; klient nemůže zadat URL,
  jinou službu ani cestu. Neznámý cíl se neodhaduje. Hlavní Adam dokončí
  projektové kontroly a zápis před commitem; Luna přebírá hotový rozsah.
- Samostatné vydání iPhone aplikace nebo receiveru Camino, instalace a
  systémové změny mají vlastní postup a oprávnění. Toto p+n je neprovádí.
- Historický MMTX modelový protokol zachovaný; jeho strict receipt nepřebírá
  rozšířená interní pole nové orchestrace.

Další krok:
- Po samostatném p+n zavést společný balíček dosavadní cestou; potom ověřit
  první ostré předání Luně ve vybraném vývojovém proudu.

Navrhované další kroky:
- Fyzická přejímka portálu/Servisu a nové karty na iPhonu.
- Filmový editor vyzkoušet doma podle dřívější dohody.

Technický důkaz:
- 286 integračních testů PASS, včetně katalogu všech 33 proudů, Pages cest,
  obnovení účtenky, neměnného projektu/cíle a původního MMTX kontraktu.
  Log `logs/luna_general_integration_20261017.log`.
- Skutečná Luna a skutečné read-only ochrany: syntetický sedmicommitový
  obecný proud 5,29 s a MMTX 5,19 s, oba dry_run_completed bez publikování.
  Log `logs/luna_general_live_dry_run_20261017.log`.
- plná brána obecného rozšíření 2011/2011 PASS (263,223 s testů).
  Log `logs/luna_general_full_gate_20261017.log`.
- Pravidla `technical/luna_release_orchestration.md`; ostré p+n ani fyzická
  přejímka nejsou suchým během doložené. Camino a autosave prošly živou kontrolou.
- Živý Cockpit je PID 1710 pod stávajícím launchd supervisorem (start 16:22:39);
  poslední ověřená deployment účtenka stále patří staršímu e3c7075ef4ad.
  Toto rozšíření nebylo samostatně nasazeno ani serverově ověřeno.

### 2026-10-17 16:53 CEST — Společná modelová role vykonavatele a schválené p+n

Hotovo:
- Nové i existující vývojové proudy používají jednu modelovou roli; změna
  modelu nevyžaduje úpravy jednotlivých proudů ani pevný model nativního pomocníka.
- Upřednostňuje se centrální preference; případná náhrada musí být výslovně
  schválená, cenově posouzená, doložená suchou zkouškou a kompatibilní s katalogem.
- Syntetická zkouška kandidáta nepublikuje, nezmění roli a nepřebírá skutečný
  balíček. Účtenka běhu zmrazí model, úsilí a otisk nastavení; změna před
  publikováním se zastaví. Hlavní model konverzace zůstává zachovaný.

Rozhodnutí:
- Míla schválil implementaci této vrstvy a poté výslovně všechny připravené p+n.
- Současná volba zachovává již schválenou rozpočtovou Lunu. Žádný nový dražší
  model se automaticky nevybírá. Katalog není zdrojem automaticky ověřené ceny.
- Pro první runtime balíček s čekajícími commity lze použít dosavadní registrované
  GitHub/deploy/verification operace. Publikační cesta zůstává oddělená od
  vydání klienta nebo receiveru Camino; autosave se nevypíná.

Další krok:
- Dokončit schválené p+n a ověřit aktuální soukromou účtenku vykonavatele,
  serverovou deployment účtenku, ochrany Camino/autosave a shodu GitHub/main.
  Provozní výsledek je registrovaný runtime důkaz mimo Git; tento zápis jej
  předem neprohlašuje za úspěšný.

Navrhované další kroky:
- Fyzicky vyzkoušet portál a editor podle dřívější dohody.

Technický důkaz:
- 169 integračních testů PASS: schválená náhrada, ignorované katalogové upgrade,
  chybějící/cenově neposouzený model, nepodporované úsilí, zmrazení politiky,
  klientská změna modelu, syntetický kandidát a původní publikační ochrany.
- Skutečný suchý běh nové role: gpt-6-luna/high, dry_run_completed za 6,8 s,
  skutečné read-only ochrany, bez publikování.
- Skutečný samostatný kandidátský probe téže schválené Luny: probe_only=true,
  published=false. Důkazy `logs/executor_role_live_probe_20261017.log`,
  `logs/executor_candidate_live_probe_20261017.log` a integrační log.
- plná brána role 2024/2024 PASS (265,823 s testů). Log `logs/executor_role_full_gate_20261017.log`.
- Oficiální model/list dokumentace ověřená: https://learn.chatgpt.com/docs/app-server#list-models-modellist
- Provozní důkaz p+n: read-only `GET /api/human-adam/luna-release/status`
  a deployment souhrn `GET /api/human-adam/status`; nečíst celé soukromé vlákno.
  Stav origin/main ověřit registrovaným GitHub batch auditem.

### 2026-10-17 17:12 CEST — Příprava měření nákladů p+n

Hotovo:
- Připravené číselné měření vybrané relace a spotřeby modelového převzetí; do účtenky nepatří prompty ani odpovědi. Chybějící telemetrie je neznámá, nikoli nula.

Rozhodnutí:
- Míla schválil dva malé UI commity: identita balíčku s přímým p+n Adamem a výsledky kontrol s p+n Lunou. Společná příprava měření je mimo srovnání.
- Porovnání zahrne Adamovo předání a závěrečnou kontrolu, nativního pomocníka i jednorázové modelové převzetí. Vývoj a závěrečné sepsání reportu jsou zvlášť.
- Jde o jeden orientační pár, různé commity a existující dlouhý kontext Adama proti krátkému kontextu pomocníka. Kredity jsou odhad Standard dle ceníku 17. 10., nikoli účetní doklad ani procenta limitu.

Další krok:
- Ověřit a nasadit společné měření, potom postupně provést oba schválené UI kroky.

Navrhované další kroky:
- Fyzická přejímka UI a filmu zůstává samostatně.

Technický důkaz:
- 81 cílených testů PASS; plná brána přípravy 2032/2032 PASS a skutečný modelový tah vrátil číselnou spotřebu. Důkazy: logs/release_usage_targeted_20261017.log, logs/release_usage_full_gate_20261017.log, logs/release_usage_live_probe_20261017.log. Výsledné číselné srovnání bude logs/pn_cost_comparison_20261017.log; tento checkpoint žádné budoucí nasazení nepotvrzuje.

### 2026-10-17 17:23 CEST — Identita balíčku, měřený krok A

Hotovo:
- Karta dokončeného p+n zobrazuje commit, počet nových commitů a použitý model. Chybějící identita je výslovně neověřená.
- Společné měření je nasazené a ověřené: 2032 testů PASS, smoke 5/5, Camino/autosave přesně zachované.

Rozhodnutí:
- První UI commit publikuje Adam přímo registrovanými kroky; začátek měření následuje až po commitu a zarovnání profilů. Příprava a vývoj zůstávají mimo interval.

Další krok:
- Provést měřené přímé p+n A, potom doplnit výsledky kontrol a změřit Lunu.

Navrhované další kroky:
- Fyzická přejímka UI/filmu čeká.

Technický důkaz:
- 68 UI testů PASS; skutečná bezpečná účtenka a chybějící údaje ověřené v Node VM. Důkazy logs/pn_benchmark_a_ui_tests_20261017.log a logs/pn_benchmark_a_identity_20261017.log. Aktuální publikaci doloží serverová účtenka a logs/pn_benchmark_a_20261017.log; celkové srovnání logs/pn_cost_comparison_20261017.log.

### 2026-10-17 17:30 CEST — Výsledky kontrol, měřený krok B

Hotovo:
- Karta výsledku nově ukazuje doložený počet testů, dobu plné brány a živou kontrolu 5/5. Chybějící či nepotvrzené důkazy výslovně označí jako neověřené.
- Přímé p+n A je ověřené: commit d9e6e287, 2032 testů PASS, smoke 5/5, GitHub aligned a chráněné služby přesně zachované. Interval A: 2 369 937 tokenů, odhad Standard 7,27533 kreditu.

Rozhodnutí:
- Druhý malý UI commit převezme čerstvý nativní pomocník centrální role. Interval B zahrne předání, pomocníka, jednorázové převzetí i závěrečnou kontrolu Adama; vývoj a sepsání reportu jsou mimo měření.
- Jeden pár je orientační srovnání konkrétního workflow v dlouhé relaci, nikoli obecná úspora modelu. Kredity nejsou vyúčtování ani procenta limitu.

Další krok:
- Provést měřené p+n B přes Lunu a porovnat bezpečné číselné souhrny.

Navrhované další kroky:
- Fyzická přejímka UI/filmu čeká.

Technický důkaz:
- 68 UI testů PASS a Node VM s reálnou účtenkou i nepotvrzenými důkazy PASS. A: logs/pn_benchmark_a_20261017.log a logs/pn_benchmark_a_usage_20261017.log. B doloží trvalá runtime účtenka vykonavatele a logs/pn_benchmark_b_usage_20261017.log. Finální srovnání logs/pn_cost_comparison_20261017.log; tento checkpoint před měřením B nepředjímá jeho výsledek.

### 2026-10-17 18:18 CEST — Opakování měření asynchronní cestou Cockpitu

Hotovo:
- Předchozí UI kroky A/B jsou nasazené: main f0ccfb49, oba úspěšné běhy 2032 testů PASS a smoke 5/5, GitHub aligned a Camino/autosave zachované.
- Skutečné dosavadní náklady Standard: A 7,27533; úspěšný terminálový B včetně dohledu 10,276513; celý B s incidentem 26,941798. Z toho samotná Luna v úspěšném B 0,534383. Nejde o účetní vyúčtování.

Rozhodnutí:
- Míla schválil opakování podle návrhu: skutečná registrovaná asynchronní cesta Cockpitu, deterministické sledování bez průběžných modelových kontrol, jediný read-only návrat do původního projektového vlákna. Jeho model se nemění.
- Tento malý dokumentační commit vytvoří nový skutečný jednocommitový balíček. Nebude se předstírat push již nasazeného commitu.
- Pro tento pilot se použije start_release hlavního Cockpitu a jeho původní projektový callback; výslovný test portálové cesty je výjimkou z terminálového předávání přes start_terminal_release. Nejde o změnu pravidel dalších vydání.

Další krok:
- Provést autorizované p+n C, změřit také callback Cockpit Adama a závěrečnou kontrolu terminálového Adama, výsledek porovnat s A/B.

Navrhované další kroky:
- Fyzická přejímka UI/filmu zůstává samostatně.

Technický důkaz:
- Předchozí finální důkazy: logs/pn_cost_comparison_20261017.log a účtenka 4afbc4a25c40ec4a545deb6745b498b4. C doloží nová trvalá runtime účtenka a logs/pn_async_comparison_20261017.log; tento checkpoint před publikací jeho výsledek nepředjímá.

### 2026-10-17 18:26 CEST — Ochranné ověření v prostředí služby opravené

Hotovo:
- Oba první asynchronní pokusy skončily před push: Luna balíček přijala, ale čtecí síťová kontrola spustila Tailscale GUI a místo JSON dostala chybový text. Návrat účtenky do původního Cockpit vlákna v obou případech fungoval.
- Oprava vynucuje TAILSCALE_BE_CLI=1 pouze pro Tailscale čtecí subprocess. Nastavení služby, sítě ani Camino se nemění. Fáze protection nyní odděluje úspěšné modelové převzetí od selhání ochranného auditu.
- Cílené testy a skutečný ochranný snapshot v minimálním launchd prostředí PASS, přesná shoda s původními chráněnými službami.

Rozhodnutí:
- Dokončení schváleného pilotu vyžaduje tuto úzkou opravu. Původní dokumentační commit a oprava tvoří jeden přesný dvoucommitový balíček. Předchozí neúspěšné účtenky zůstávají zachované.
- Čistý úspěšný pokus se změří samostatně; celkový souhrn přizná i předchozí pokusy a opravu. Obnovené Cockpit vlákno vykázalo aktuální gpt-6.1-sol, bez zásahu do modelových nastavení.

Další krok:
- Dokončit plnou bránu opravy, commit a autorizované asynchronní p+n obou commitů.

Navrhované další kroky:
- Fyzická přejímka UI/filmu zůstává samostatně.

Technický důkaz:
- logs/pn_async_fix_targeted_20261017.log, logs/pn_async_fix_live_20261017.log; plná brána 2034/2034 PASS (262,874 s unit testů), logs/pn_async_fix_full_gate_20261017.log. Neúspěšné joby 5a5129c49ba44e26047c4402d4e4cbf4 a 424f7252a5273566b8f63c1c7fa253e9. Finální pilot dokládá runtime účtenka a logs/pn_async_comparison_20261017.log.


## 2026-10-17 19:06 CEST — Pilot rutinního kontrolora dokumentace

Hotovo:
- Sol v jediném čtecím tahu porovnal devět veřejných reportů s jejich dokumentací; konkrétní rozpor nedoložen. Program vybírá přesný schválený typ bez modelového rozhodování, neznámé typy vrací Adamovi.
- Oddělená role, krátké zadání, per-thread vypnuté nástroje/konektory/MCP/hooky/paměti a projektové instrukce/dovednosti; historie hlavní relace se nepřenáší. Běžné nastavení hlavního Adama a vykonavatele p+n se nemění.
- Skutečné ceny včetně jednoho převzetí změřené. C dřívějšího p+n je dokončené: 1,7030575 Standard úspěšný běh, 37,6101705 celá série s opravou; tento pilot je oddělené měření.

Rozhodnutí:
- Míla souhlasil s pokusem jedné omezené rutiny. Jde výhradně o tento čtecí pilot; obecné automatické směrování vývoje ani automatické publikování nevzniklo.
- Neznámý rozsah, chyba, drift rolí/podkladů nebo nadlimitní spotřeba vrací stav k posouzení bez automatického opakování. Limit 12 000 bajtů vstupu a jeden tah; 16 000 tokenů / 1 Standard kontrolora jsou hranice přijetí po dokončení, nikoli pevný fakturační strop.
- Původní syntetický test (neukládání vs mazání) byl nejednoznačný a Sol správně nevymyslel rozpor; opraven na výslovné ukládání. Novější readOnly.access instalovaný server odmítl před modelem; zachován podporovaný read-only režim a vypnutí nástrojů.

Další krok:
- Vyhodnotit přínos této úzké rutiny před rozšiřováním na zápis do kódu; push a nasazení zůstávají samostatně. Jediný běh bez srovnatelného přímého kontrolního pokusu neprokazuje úsporu.

Navrhované další kroky:
- Fyzická přejímka UI/filmu zůstává samostatně.

Technický důkaz:
- 63 cílených testů PASS; plná brána 2046/2046 PASS (261,278 s unit testů), logs/routine_full_gate_20261017.log. Syntetický test i skutečný audit prošly, chráněný snapshot Camino/autosave a otisk release_executor před/po shodné.
- Úspěšný audit 12 594 tokenů, 0,6515 Standard; hlavní převzetí 177 625 tokenů (175 488 cached input), 0,64077 Standard. Celkem 190 219 tokenů / 1,29227 Standard. Během čekání nula nových tokenů hlavního modelu.
- logs/routine_candidate_probe_20261017.log, logs/routine_pilot_completed_20261017.log, logs/routine_pilot_usage_20261017.log; souhrn v logs/routine_pilot_report_20261017.log. Náklady zavedení jsou oddělené, nevyvozují se z ceny samotného kontrolora.

Doplnění k aktivaci pilotu: Novou roli nyní neaktivovat v centrálním JSON. Běžící starší Cockpit by odmítl celý seznam rolí, takže je po experimentu obnovena přesná původní konfigurace. Kód a měření jsou lokálně připravené; registrované spuštění bez schválené role bezpečně vrátí attention. Nejprve samostatně nasadit podporu více rolí, teprve potom aktivovat routine_reviewer v config/agent_roles.json.


## 2026-10-17 19:37 CEST — Jednoduchý vývoj přes samostatnou roli

Hotovo:
- Jedna vhodná čistá Python funkce s původními testy se může předat Solovi bez dalšího modelového rozhodování. Program provede izolovanou opravu a testy, hlavní Adam jednou přebere přesný diff. Kritické, nejasné, triviální a rozpracované úkoly zůstávají Adamovi.
- Skutečný Sol opravil syntetickou funkci; tři nezměněné testy přešly FAIL → PASS a návrh byl přijat. Souborový kanál skutečně prošel uvnitř síťově uzavřeného App Server sandboxu. Portál používá serverovou autoritu aktuálního writable tahu, projektu a vlákna, nejvýše jeden úkol a automatické zrušení grantu po skončení/chybě.

Rozhodnutí:
- Míla schválil dokončení vývojového předávání po upřesnění, že původní krok byl pouze čtecí pilot. Podporovaná třída je jedna čistá Python funkce, ne libovolný autonomní vývoj. Rozhodnutí o rozsahu je programové; checkpoint a p+n zachovávají vlastní oprávnění.
- Žádná modelová kontrola během čekání, žádné automatické opakování nejistého kroku. Limit 30 000 tokenů / 4 Standard se kontroluje po dokončení; nejde o fakturační strop. Samotná cena pomocníka nedokazuje úsporu celého workflow.
- Centrální role zatím původní: starý runtime by nové role odmítl. Registrovaná aktivace nejprve ověří již nasazený kompatibilní Cockpit a skutečnou přijatou zkoušku; teprve potom dovolí konfiguraci simple_developer. release_executor zůstává beze změny, routine_reviewer se tím nezapíná.

Další krok:
- Po samostatném p+n provést dvoufázové zavedení podle technického návodu: nasadit kód, registrovaně aktivovat ověřenou roli, commitnout přesnou konfiguraci a dokončit p+n. Další vývoj pro tuto aktivaci není potřeba.

Navrhované další kroky:
- Fyzická přejímka portálu/UI/filmu zůstává samostatně po nasazení.
- Přínos delegace hodnotit včetně jednorázového převzetí hlavním Adamem; zatím není přímý kontrolní vývojový běh.

Technický důkaz:
- Skutečný probe 9396d97054df4e549a777d930622df1f: 11 093 tokenů a 0,58125 odhad Standard pomocníka; první zastavený test 0,55645. První nevyhovující odpověď nic nepřepsala; upřesnění zadání doložené novou zkouškou.
- logs/simple_development_candidate_corrected_20261017.log, logs/simple_development_acceptance_20261017.log a logs/simple_development_portal_ipc_20261017.log; souhrn logs/simple_development_report_20261017.log. Plná brána 2096/2096 PASS (299,646 s unit testů), logs/simple_development_full_gate_20261017.log. Závěrečný živý chráněný snapshot a role p+n před/po přesně shodné; logs/simple_development_final_verification_20261017.log. Žádný push, restart, změna sítě ani Camino/autosave.


## 2026-10-17 19:55 CEST — Nasazení předávání a aktivace vývojové role

Hotovo:
- Luna převzala celý dvoucommitový balíček a nasadila nový Cockpit; plná publikační brána 2096 testů PASS, živé ověření 5/5. Přesný head af5db5a3, stamp 7fa6d9e50f794ddf a chráněné služby doložené účtenkou 34406940c02bfea7e175725a9c93cbb6.
- Stabilní lokální zámek atomického zápisu centrální konfigurace je přesně ignorovaný v Gitu; zůstává na disku a samotný agent_roles.json se dál verzovává.
- Registrovaný activation_plan ověřil skutečně nasazený nový parser a přijatý vývojový dry-run. activate zapnul simple_developer v jediné centrální konfiguraci; živý capabilities hlásí enabled=true a katalog potvrdil gpt-6.1-sol/medium. Původní role Luna/release_executor i Camino/autosave mají přesně stejný otisk a procesy. Čtecí routine_reviewer zůstává neaktivní.

Rozhodnutí:
- Míla výslovně povolil p+n přes Lunu včetně bezpečné konfigurační aktivace. Aktivace je druhá fáze prvního zavedení; neproběhla před podporou nových rolí. Bez změny hlavního modelu, síťového sandboxu, Camina nebo autosave.
- Toto je checkpoint centrální konfigurace a povinného projektového zápisu před závěrečnou publikací. Konečný head a výsledek tohoto p+n vždy ověřit podle finální serverové účtenky 4935e2096cff56f7aa768ec9d3ab936e; tento zápis je nepředjímá.

Další krok:
- Dokončit plnou bránu a lokální konfigurační commit, zarovnat čisté profily a předat přesný závěrečný balíček Luně v rámci již schváleného p+n.

Navrhované další kroky:
- Fyzická přejímka vhodného drobného vývojového úkolu přes portál/UI zůstává samostatně; systémový dry-run a izolované IPC jsou ověřené.
- Fyzická přejímka filmu čeká podle původní dohody.

Technický důkaz:
- logs/simple_development_release_phase1_20261017.log, logs/simple_development_activation_live_20261017.log a logs/simple_development_activation_model_20261017.log. Konfigurační plná brána 2096/2096 PASS (295,435 s unit testů), logs/simple_development_activation_full_gate_20261017.log; závěrečné p+n doloží logs/simple_development_release_phase2_20261017.log a bezpečná serverová účtenka 4935e2096cff56f7aa768ec9d3ab936e. Žádná zpráva do jiného Cockpit vlákna, mazání ani změna chráněných služeb.


## 2026-10-17 21:18 CEST — Dokončené p+n a předání na příští relaci

Hotovo:
- Předávání je nasazené, Luna dokončila i konfigurační fázi a vývojová role Sol je zapnutá. Plná publikační brána 2096 PASS a smoke 5/5, chráněné služby zachované. Dnešní čtecí kontrola znovu potvrdila dokončenou účtenku a capabilities enabled=true.
- Obnovitelné předání je na začátku kanonického handoffu, priorita 1, stav ceka na retest, připomenout při startu. Náklady posledního p+n jsou rozlišené od dřívějších benchmarků.

Rozhodnutí:
- Míla požádal uložit stav před vyčerpáním kreditu. Nyní pouze dokumentace a lokální checkpoint, bez dalšího vývoje a publikování.
- Poslední dvoufázové p+n včetně aktivace vyšlo na 15,3234425 odhadovaného kreditu Standard (hlavní Adam 14,62797, všechny složky Luny 0,6954725); úspora celku neprokázaná. Starší asi 77% pokles patří jinému asynchronnímu pilotu. Nejde o fakturaci či procento limitu.

Další krok:
- Při navázání přečíst aktuální handoff a fyzicky ověřit předání na vhodném drobném vývojovém úkolu; neopakovat dokončené p+n/aktivaci.

Navrhované další kroky:
- Příští běžné autorizované p+n změřit celé včetně předání a převzetí, s počátečními číselnými snapshoty a programovým čekáním.
- Fyzická přejímka UI/filmu podle původní dohody.

Technický důkaz:
- Nasazený a1437ec2 / stamp 7fa6d9e50f794ddf, job 4935e2096cff56f7aa768ec9d3ab936e completed, testy 2096, smoke 5. logs/simple_development_pn_final_20261017.log a logs/simple_development_release_phase2_20261017.log; podrobnosti výpočtu v technickém návodu. Nynější dokumentační commit zůstává lokální.


## 2026-10-17 21:32 CEST — Jednodušší společné p+n s jedinou Lunou

Hotovo:
- Lokálně jeden vstup provede audit, zmrazení a spuštění jedné Luny. Terminál již nepotřebuje nativního pomocného agenta; portál používá stejnou funkci se zachováním potvrzovací karty a návratu do původního vlákna.
- Programové čekání sleduje konkrétní účtenku, opakování identity nevolá další model ani publikaci. Původní ochrany a celý přesný rozsah commitů zůstávají zachované pro všech 33 proudů.

Rozhodnutí:
- Míla schválil tuto obecnou úpravu. Schválený lokální SHA a zamýšlený projekt jsou povinné; origin/cíl/model určuje program. Všechny publikační brány platí dál, žádné automatické retry či odhad neznámého cíle.
- Toto zadání nezahrnuje nové p+n. Poslední provozní head zůstává a1437ec2; předchozí dokumentační 66e27e70 a tento vývojový checkpoint budou čekat lokálně.

Další krok:
- Po lokálním dokončení samostatné p+n přes nový jediný vstup a provozní ověření; nepoužívat další modelovou mezivrstvu.

Navrhované další kroky:
- Při běžném autorizovaném p+n měřit celý interval včetně startu a převzetí, oddělit jednorázový vývoj. Celková úspora této změny zatím nedoložená.
- Fyzická přejímka portálu/UI/filmu podle dřívější dohody.

Technický důkaz:
- 59 cílených testů PASS; skutečná Luna v syntetickém dry-run: jeden modelový tah, jeden worker, žádný odchozí zápis. Opakované volání vrátilo stejnou účtenku; ochranný snapshot shodný. logs/release_single_entry_dry_20261017.log. Plná brána 2109/2109 PASS (301,702 s unit testů); logs/release_single_entry_full_gate_20261017.log.


## 2026-10-17 22:33 CEST — Společné p+n nasazené, předání do nového chatu

Hotovo:
- Nový jednotný postup úspěšně publikoval a nasadil celý dvoucommitový balíček přes jedinou Lunu. Konečné ověření potvrdilo funkční runtime, chráněné Camino/autosave a aktivní roli pro jednoduchý vývoj.

Rozhodnutí:
- Míla výslovně zadal p+n přes Lunu. Proběhlo přímým submit_release(wait=True), bez nativního modelového prostředníka či modelového pollingu. Další chat navazuje z dokumentace, již dokončenou aktivaci ani publikaci neopakuje.

Další krok:
- Navázat ve stejném projektu podle dalšího Mílova zadání; závěrečný dokumentační checkpoint zůstane lokální do příštího autorizovaného balíčku.

Navrhované další kroky:
- Fyzická přejímka portálu/UI/filmu a případné srovnatelné měření celkové režie dalšího běžného p+n; bez automatického rozšiřování vývoje.

Technický důkaz:
- b47b0bb609bb4eff5c6d0f5971350d007d73fbbe / stamp d769959026d9b405; účtenka cb55493cb02cdfe7055873e1d7485869 completed, 2109 testů PASS, smoke 5/5. Živý audit: GitHub aligned, oba profily aligned, simple_developer enabled=true, chráněné služby shodné. logs/release_single_entry_pn_final_20261017.log.
- Programové čekání hlavního modelu: 0 nových tokenů; jde pouze o čekací interval, ne celý náklad p+n. logs/release_single_entry_pn_20261017.log.

## 2026-10-17 23:36 CEST — Luna pro delší vhodný vývoj, nabídka po analýze

Hotovo:
- Společná pravidla nyní určují, kdy Adam nabídne Lunu: jen delší, jasně vymezený a ověřitelný vývoj s nízkým rizikem a očekávaným přínosem po započtení předání, kontroly a integrace.
- U vícekrokového plánu se vhodné kroky a jejich vykonavatel navrhnou předem. U vhodného ad hoc úkolu přijde po analýze jedna nabídka ano/ne. Drobné a nové kritické změny takovou nabídku nevyvolají.

Rozhodnutí:
- Míla výslovně zvolil Lunu i pro vývoj. Delší trvání je vždy nutná podmínka, také u opakované práce. Pevný časový práh zatím není; pravidlo se bude s Mílou dolaďovat podle zkušeností a nákladů celého postupu.
- Schválený plán pokrývá navržené rozdělení práce bez opakovaného potvrzování každého nezměněného kroku. Každé samostatně autorizované p+n dál provádí Luna.
- Tento krok ukládá pravidlo. Centrální vývojová role nadále používá Sola; Luna se nesmí vydávat za aktivní ani tiše nahrazovat Solem. Dosavadní rozsah jedné čisté Python funkce s testy se nemění.

Další krok:
- Před prvním skutečným vývojovým předáním Luně doložit cenové posouzení, přijmout skutečnou vývojovou zkoušku a bezpečně změnit centrální roli. Volbu Luny již Míla schválil; důkaz převzetí p+n nenahrazuje vývojovou zkoušku.

Navrhované další kroky:
- Při vhodném delším úkolu vyhodnotit celkovou režii a podle zkušenosti upřesnit pravidlo; širší úkoly vyžadují rozšíření stávajícího mechanismu.
- Fyzická přejímka portálu/UI/filmu zůstává podle původní dohody.

Technický důkaz:
- Změněné jsou pouze společné instrukce a projektová dokumentace; config/agent_roles.json ani vykonávací kód se nemění. Registrovaný mechanismus nadále přijímá jednu čistou Python funkci s existujícími testy.
- Předchozí p+n 8cda502f je uzavřené: účtenka 0944dbd793fb4450d6475882c7cb4cef completed, 2109 PASS, smoke 5/5 a chráněné služby zachované; logs/release_cockpit_handoff_pn_final_20261017.log. Nynější dokumentační pravidlo se automaticky nepublikuje.
