<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-13 23:05 CEST.
- Roadmapa `AuditCockpit56_2.txt` je ve verzi 1.5. Čtvrtý čekající lokální krok zjednodušuje přípravu testů nasazení podle naměřených nákladů.
- Předchozí lokální kroky: hledání `674dc194`, čtečky `f1b41dc5`, měření brány `0d1b24f1`. Hledání má vlastní modul, čtečky čistý renderer; obsluhy/API zůstaly zachované. `app.js` 7063 řádků, `cockpit.py` 10892.
- Dva pilotní deploy testy: osm úspěšných měřených běhů před/po; příprava 87 → 53 Git procesů. Konfigurace testovací brány probíhá před vytvořením originu a profilů, takže odpadá druhý úvodní push/sync. Vlastní scénáře a produkční kontroly nezměněné.
- Příprava v pilotu přibližně 3,7–4,7 → 2,3–2,5 s. Jde o malé měření na Macu, nikoli záruku výkonu celé brány. Report a osm vzorků: `memory/reports/cockpit_deploy_fixture_pilot_2026_09_13.*`.
- Nový regresní test potvrdil čistý a zarovnaný výchozí stav i nezávislost dvou sad repozitářů při commitu do jednoho profilu. Plná brána po změně 1650/1650 prošla; unit 455,34 s, deploy skupina 18 testů / 84,49 s.
- Starší výchozí měření `0d1b24f1`: 1649 testů / 426,38 s; čtyři Git/workspace skupiny 73,5 % času. Historický report zachovaný, není přepsán novými čísly.
- Všechny čtyři lokální kroky čekají na společný push/nasazení na samostatný pokyn. Dříve bylo doložené nasazení `97d608f7`; tento krok nový živý audit runtime nedělal.
- Další krok: vybrat následující strukturální řez podle konkrétní HTTP/doménové vazby; optimalizační pilot je dokončený. Produkční status/preflight případně analyzovat odděleně, bez vynechávání kontrol.
- Otevřená uživatelská přejímka Mac/iPhone a pozdější audit/UI: hledání má jen prvních 8 výsledků, Janiččina zkratka sama nerozbaluje panel, nákupní čtečka nemá náhradní návrat bez openeru. Nálezy z kódu, zde bez oprav.
- Záloha na výslovný pokyn odložená na 14. 9. kvůli nedostupnému disku. Navazující audit a změna UI po strukturální etapě; Santiago zatím jen zvažované téma.
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
