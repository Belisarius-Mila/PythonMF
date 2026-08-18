<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-18 11:03 CEST

### Hotovo
- Health, Recovery a hlavní statusové GET cesty mají samostatný backendový dispatch bez změny veřejných kontraktů.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Vytvořit checkpoint, nasadit Cockpit a ověřit pět vyčleněných endpointů.

### Rozhodnutí
- Health, Recovery a status tvoří první samostatnou read-only routing doménu Cockpitu.

### Navrhované další kroky
- Po živém ověření pokračovat bodem 6 auditu a doplnit přímé testy nejrizikovějších non-direct POST akcí.

### Technický stav checkpointu
- Změna je otestovaná (1440 testů).
- Git před checkpointem: lokální `main` na `1d946b7d5596`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `1d946b7d5596` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-18T08:39:12+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
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
