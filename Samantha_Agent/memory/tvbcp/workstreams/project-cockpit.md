<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Stav znovu ověřen: 2026-08-07 13:59 CEST

### Hotovo
- Přímé Tailscale doručení důležitých připomenutí i Quick Notes funguje a iCloud
  zůstává fallbackem.
- VocabularyFR, VocabularyIT a MultiLO mají funkční lokální vstupy z Cockpitu.
- Servisní souhrn dokumentového trezoru ukazuje aktuální stav před historií.

### Otevřeno
- Lokální `main` obsahuje jeden novější knihovní commit než běžící Cockpit;
  nejde o blokátor Cockpit architektury.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Bez okamžité architektonické změny; pokračovat podle konkrétní uživatelské
  zkušenosti nebo provozní chyby.

### Rozhodnutí
- Přímé Tailscale doručení je primární cesta a iCloud soubory zůstávají
  bezpečným fallbackem; servisní historie nemá přebíjet aktuální pracovní stav.

### Navrhované další kroky
- Při dalším UI auditu oddělit aktuální úkol od historických technických detailů.

### Technický stav checkpointu
- Běžící Cockpit je serverově ověřený na `91dc700`; smoke prošel 5/5.
- Oba profilové workspaces byly při posledním nasazení čisté a zarovnané.
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
