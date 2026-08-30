<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-19 22:05 CEST

### Hotovo
- Dokumentová práce v Cockpitu je sjednocená do jediné fronty; každý dokument se zobrazuje jen jednou a nabízí přímo potřebné akce pro čtení i metadata.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Dotykový a vizuální test sjednocené fronty na skutečném iPhonu zatím neproběhl.

### Další krok
- Samostatně potvrdit nasazení do Cockpitu a potom na iPhonu ověřit jednu položku se čtením a jednu s doplněním metadat.

### Rozhodnutí
- Revize a klasifikace dokumentu jsou jeden uživatelský úkol; klasifikace už není samostatný duplicitní pracovní oddíl.

### Navrhované další kroky
- Podle živého iPhonového testu upravit jen konkrétní nejasnost, nevracet další paralelní seznam.

### Technický stav checkpointu
- Změna je otestovaná (1446 testů).
- Git před checkpointem: lokální `main` na `c74cc57b4872`; GitHub je o 4 commity pozadu a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `c74cc57b4872` · smoke 5/5 · 2026-08-18T15:07:32+00:00.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Cockpit / hlavní architektura

Nazev: Cockpit / hlavní architektura
Pracovni proud: project-cockpit
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne

Co se resilo:
Kanonicky handoff byl zalozen prvnim potvrzenym checkpointem tohoto proudu.

Co je hotove:
- Viz chronologicke checkpointy nize.

Co neni hotove:
- Viz posledni checkpoint a jeho dalsi krok.

Dalsi krok:
Viz posledni chronologicky checkpoint.

Navrhovane dalsi kroky:
- Prubezne aktualizovat pouze potvrzenymi checkpointy tohoto proudu.

Zmenene nebo relevantni soubory:
- Viz jednotlive checkpointy.

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice ani soukromy obsah.

### Automatický checkpoint 2026-08-02 14:10 CEST

- Pracovní proud: `project-cockpit`
- Hotovo: Důležitá připomenutí lze doručit přímo přes Tailscale do soukromého Cockpitu; opakované doručení je idempotentní a iCloud zůstává záložní cestou.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1269 testů, 281.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/urgent_reminders.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_urgent_reminders.py`, `Samantha_Agent/generated_shortcuts/Samantha_Dulezite_pripomenuti.xml`
- Commit: `Deliver urgent reminders directly to Cockpit`
- Další krok: Samostatně auditovat a potvrdit nasazení do Cockpitu; potom v iPhonové zkratce doplnit soukromou Tailscale adresu a provést jeden živý doručovací test.

### 2026-08-05 22:41 CEST – Falešné iCloud čekání odstraněno v kódu

Hotovo:
- Nezměněný iCloud placeholder, který je už úplně uložený v private indexu, se
  nepovažuje za nové čekající stažení.
- Nový, změněný nebo neúplný zdroj zůstává varováním.

Rozhodnutí:
- iCloud hydratace a doručení připomenutí jsou dva různé stavy.
- Přímá iPhonová Tailscale zkratka není součástí tohoto kroku.

Další krok:
- Lokálně commitnout a samostatně nasadit; potom zkontrolovat kartu v živém
  Cockpitu.

Navrhované další kroky:
- Dokončit konfiguraci přímé Tailscale zkratky a živý doručovací test.

Technický důkaz:
- Cíleně 14 testů; plná Cockpit Quality Gate 1311 testů, vše OK.

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

### Automatický checkpoint 2026-08-18 08:18 CEST

- Pracovní proud: `project-cockpit`
- Hotovo: Cockpit nyní vybírá nejvýše tři aktuální kroky, vysvětluje jejich prioritu a ukazuje zdroj i stáří důkazu
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1432 testů, 304.9 s, výsledek OK
- Změněné cesty před paměťovým zápisem (11): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/app/frontend/cockpit/styles.css`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_capability_audit.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/decision_cockpit.py`, `Samantha_Agent/tests/test_decision_cockpit.py`
- Commit: `Add read-only Decision Cockpit D4`
- Další krok: Převzít checkpoint, nasadit Cockpit a vizuálně ověřit přehled na Macu a iPhonu

### Automatický checkpoint 2026-08-18 10:16 CEST

- Pracovní proud: `project-cockpit`
- Hotovo: Health, diagnostika, Recovery a autosave jsou oddělené od hlavního frontendového souboru bez změny jejich chování.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/cockpit_frontend.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`, `Samantha_Agent/app/frontend/cockpit/health_recovery_autosave.js`
- Commit: `Extract health recovery and autosave frontend module`
- Další krok: Vytvořit checkpoint, nasadit Cockpit a živě ověřit diagnostiku, Recovery a autosave.

### Automatický checkpoint 2026-08-18 11:03 CEST

- Pracovní proud: `project-cockpit`
- Hotovo: Health, Recovery a hlavní statusové GET cesty mají samostatný backendový dispatch bez změny veřejných kontraktů.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1440 testů, 312.7 s, výsledek OK
- Změněné cesty před paměťovým zápisem (8): `.github/workflows/cockpit-quality-gate.yml`, `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/scripts/cockpit_quality_gate.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_http_security.py`, `Samantha_Agent/tests/test_cockpit_quality_gate.py`, `Samantha_Agent/app/cockpit_readonly_routes.py`, `Samantha_Agent/tests/test_cockpit_readonly_routes.py`
- Commit: `Extract read-only health recovery status routes`
- Další krok: Vytvořit checkpoint, nasadit Cockpit a ověřit pět vyčleněných endpointů.

### Automatický checkpoint 2026-08-18 13:06 CEST

- Pracovní proud: `project-cockpit`
- Hotovo: Všechny zapisovací a odesílací POST akce mají nyní přímo dohledatelný testovací kontrakt.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1444 testů, 302.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_cockpit.py`
- Commit: `Add direct contracts for high-risk POST actions`
- Další krok: Vytvořit checkpoint, nasadit Cockpit a ověřit běžný smoke test.

### Automatický checkpoint 2026-08-18 17:05 CEST

- Pracovní proud: `project-cockpit`
- Hotovo: Revize dokumentů se nyní otevírá přímo v Cockpitu a funguje i přes Tailscale na iPhonu; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1445 testů, 305.6 s, výsledek OK
- Změněné cesty před paměťovým zápisem (6): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/decision_cockpit.py`, `Samantha_Agent/app/frontend/cockpit/app.js`, `Samantha_Agent/app/frontend/cockpit/page.html`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_cockpit_frontend.py`
- Commit: `Fix iPhone document review navigation`
- Další krok: Po automatickém převzetí ověřit na iPhonu tlačítko Revidovat

### 2026-08-19 22:05 CEST – Dokumenty mají jednu funkční frontu

Hotovo:
- Dokumentová práce v Cockpitu je sjednocená do jediné fronty.
- Každý dokument se zobrazuje jen jednou a přímo u něj jsou relevantní akce pro čtení i metadata.
- Na iPhonu se ručně zadávají pouze skutečně chybějící pole.

Rozhodnutí:
- Revize a klasifikace dokumentu jsou jeden uživatelský úkol; klasifikace už není samostatný duplicitní pracovní oddíl.

Další krok:
- Samostatně potvrdit nasazení do Cockpitu a potom na iPhonu ověřit jednu položku se čtením a jednu s doplněním metadat.

Navrhované další kroky:
- Podle živého iPhonového testu upravit jen konkrétní nejasnost, nevracet další paralelní seznam.

Technický důkaz:
- Cílená sada 279 testů a plná Cockpit Quality Gate 1446/1446 prošly.
- JavaScript, Python syntaxe, `git diff --check` a Git safety check jsou zelené.

### 2026-08-30 11:19 CEST – GitHub je jediný fallback důležitých připomenutí

Hotovo:
- Vznikl samostatný soukromý GitHub Issues inbox bez klonu, submodulu nebo
  pracovních souborů v `PythonMF`.
- Nový klient přebírá pouze Issues s přesným protokolem a `delivery_id`, uloží je
  atomicky do private indexu a Issue zavře až po lokálním převzetí.
- Opakování po selhání uzavření je idempotentní: lokální připomenutí se
  nezdvojí a otevřená Issue se může bezpečně zpracovat znovu.
- Cockpit už pro důležitá připomenutí nečte iCloud; aktivní architektura má jen
  přímý Tailscale a GitHub fallback.
- Podepsaná zkratka `Samantha – důležité připomenutí.shortcut` je připravená
  mimo git a při importu vyžádá token, GitHub Issues URL a Tailscale URL.
- Syntetický GitHub pilot bez soukromého obsahu vytvořil jeden lokální záznam a
  uzavřel tutéž Issue.

Rozhodnutí:
- GitHub zápis je write-ahead: zkratka nejprve založí Issue a až potom zkusí
  Cockpit. Mac Issue uzavře po převzetí; zkratka ji sama nezavírá.
- Do gitu ani do unsigned zdroje zkratky nepatří skutečný token ani název
  soukromého repozitáře.

Co není hotové:
- Fine-grained produkční token zatím není vytvořený ani uložený v lokálním
  `.env` a zkratka ještě nebyla importovaná a ručně otestovaná na iPhonu.
- Kód není nasazený do běžícího Cockpitu a commit není pushnutý.

Další krok:
- Vytvořit token omezený jen na soukromý inbox s oprávněním Issues read/write,
  doplnit lokální konfiguraci a importní otázky zkratky; nasazení potvrdit
  samostatně.

Navrhované další kroky:
- Po nasazení provést jeden skutečný test s bdícím Macem a jeden se spícím Macem
  a ověřit, že Issue zůstane otevřená pouze ve druhém případě a po probuzení se
  přesune právě jednou do Cockpitu.

Technický důkaz:
- Shortcuts validátor po jedné opravě prošel pro iOS; podepsaný soubor má
  25 822 bajtů.
- Cílená sada 286 testů prošla.
- Plná Cockpit Quality Gate prošla 1485/1485 testy za 317,8 s.
- Syntetický pilot: `created_count=1`, `closed_count=1`, lokální záznam 1,
  výsledný stav Issue `closed`.

### 2026-08-30 14:13 CEST – GitHub fallback je nasazený a načítá lokální konfiguraci

Hotovo:
- Fine-grained token je uložený pouze v ignorovaném lokálním `.env`; živý
  Cockpit hlásí GitHub fallback jako nakonfigurovaný a synchronizace je bez
  chyby.
- Podepsaná soukromá kopie zkratky má předvyplněný GitHub inbox i Tailscale
  endpoint a neobsahuje další importní otázky.
- První nasazení odhalilo, že launchd proces `.env` nenačítal. Start serveru byl
  opraven tak, aby lokální `.env` načetl bez přepisování hodnot dodaných
  procesním prostředím; hotfix `20742e9` je nasazený.

Rozhodnutí:
- Token zůstává omezený na jediný soukromý inbox s oprávněním Issues read/write.
  Pokud se přes fallback začne posílat citlivější obsah, token se vymění.
- Provozní uzavření ještě vyžaduje dva skutečné iPhone testy; syntetický test
  nesmí být vydáván za uživatelské ověření.

Co není hotové:
- Chybí skutečný test zkratky s bdícím Macem a následně test se spícím Macem a
  převzetím po probuzení.

Další krok:
- Spustit z iPhonu jedno neškodné připomenutí s bdícím Macem a ověřit právě
  jednu lokální položku a uzavřenou GitHub Issue.

Navrhované další kroky:
- Potom zopakovat test se spícím Macem: Issue musí během spánku zůstat otevřená
  a po probuzení se převzít právě jednou.

Technický důkaz:
- Cílené testy hotfixu: 21/21 OK; plná Cockpit Quality Gate: 1487/1487 OK.
- Serverová deployment účtenka pro `project-cockpit`: nový proces, smoke 5/5 a
  přesný hotfix commit `20742e9`.
- Živý stav po restartu: `configured=true`, GitHub synchronizace OK, nula chyb
  a nula čekajících inboxových Issues; Tailscale health i nemutující kontrola
  doručovacího endpointu prošly.

### 2026-08-30 14:28 CEST – První iPhone test bezpečně odhalil prázdný vstup URL

Hotovo:
- První skutečné spuštění zkratky skončilo ještě před síťovým zápisem hláškou,
  že akce Načíst obsah URL nedostala platnou URL.
- Živá read-only kontrola potvrdila beze změny 4 otevřená lokální připomenutí,
  nula čekajících GitHub Issues a nula synchronizačních chyb; nevznikla
  duplicita ani nejednoznačné doručení.
- Obě síťové akce nyní dostávají URL jako viditelnou magic variable ve formátu,
  který iOS zachová. Nová soukromá varianta s názvem zakončeným `2` je
  validovaná a podepsaná mimo git, aby import nekolidoval se starou kopií.

Rozhodnutí:
- Původní zkratku nepoužívat pro další test; nová varianta má odlišný název jen
  kvůli spolehlivému importu vedle již nainstalované kopie.

Co není hotové:
- Opravená zkratka ještě nemá skutečný iPhone retest. Nelze proto potvrdit
  provozní doručení s bdícím ani spícím Macem.

Další krok:
- Importovat variantu `Samantha – důležité připomenutí 2` a provést jeden nový
  neškodný test s bdícím Macem; nic neopakovat, pokud výsledek nebude přesně
  korelovatelný.

Navrhované další kroky:
- Teprve po úspěšném bdícím testu provést test se spícím Macem a převzetím po
  probuzení právě jednou.

Technický důkaz:
- Cílené testy builderu: 4/4 OK; Shortcuts Playground validátor prošel pro
  verzovaný zdroj i soukromou nakonfigurovanou kopii.
- Plná Cockpit Quality Gate prošla 1488/1488 testy.
- Podepsaný soubor opravené varianty má 26 706 bajtů a oprávnění `0600`.

### 2026-08-30 16:04 CEST – Opakované delivery_id odhalené při testu spánku

Hotovo:
- Test s bdícím Macem přes Issue `#2` byl přesně korelovaný: jedna lokální
  položka, zdroj `direct_tailscale`, Issue uzavřená bez duplicity.
- Při následujícím testu Mac skutečně spal a krátce poté proběhl síťový
  DarkWake. Issue `#3` však měla jiný text a stejné `delivery_id` jako předchozí
  běh, takže starý backend ji chybně uzavřel jako duplicitu a nový text lokálně
  neuložil. Text zůstal zachovaný jen v uzavřené testovací Issue.
- Builder nyní vytváří čerstvé časové ID s milisekundami místo nespolehlivě se
  opakující hodnoty. Nakonfigurovaná varianta `3` je validovaná a podepsaná mimo
  git.
- Backend nově při stejném `delivery_id` a jiném textu selže zavřeně: původní
  záznam nepřepíše a GitHub Issue nesmí uzavřít.

Rozhodnutí:
- Test `#3` není úspěšný fallback důkaz a nesmí se tak vykazovat.
- Zpráva s konfliktním ID se nikdy nesmí automaticky znovu poslat ani tiše
  zahodit jako běžná duplicita.

Co není hotové:
- Backendová pojistka ještě není nasazená, varianta `3` není importovaná a oba
  provozní scénáře je nutné znovu ověřit.

Další krok:
- Dokončit plnou bránu a lokální checkpoint, poté samostatně potvrdit nasazení
  Cockpitu a import varianty `3` před novým syntetickým testem.

Navrhované další kroky:
- Nejprve dvě spuštění s bdícím Macem pro důkaz dvou odlišných ID; až potom
  opakovat test skutečné nedostupnosti Macu.

Technický důkaz:
- Issues `#2` a `#3` měly stejné ID a rozdílný text; lokální index měl pro ně
  jediný starší záznam a počet položek se při druhém běhu nezvýšil.
- Cílená sada builderu, úložiště a GitHub synchronizace: 26/26 OK; iOS 27
  Shortcuts validátor prošel pro zdroj i soukromou variantu `3`.
- Plná Cockpit Quality Gate prošla 1491/1491 testy.

### 2026-08-30 16:52 CEST – Bdící retest odhalil prázdnou časovou část ID

Hotovo:
- Backendová fail-closed pojistka je nasazená na přesném commitu `04e7763`;
  restart, shodný lokální a tailnet code stamp a serverový smoke 5/5 prošly.
- První bdící běh varianty `3` vytvořil právě jeden nový přímý lokální záznam
  číslo 45, ale jeho `delivery_id` bylo pouze `samantha-`. Běh proto dokládá
  přímé doručení, ne jedinečnost časového ID.
- Builder nyní používá kanonické Apple názvy výstupů `Date` a `Formatted Date`.
  Soukromá varianta `4` je validovaná a podepsaná mimo git s oprávněním `0600`.

Rozhodnutí:
- Se spícím Macem se zatím netestuje. Varianta `3` není způsobilá pro další
  korelační test a záznam 45 se automaticky nemaže ani neopakuje.
- Další test musí nejprve prokázat celé nové `delivery_id` při bdícím Macu.

Co není hotové:
- Varianta `4` ještě není importovaná ani skutečně spuštěná na iPhonu.
- Fallback se spícím Macem nad opravenou variantou proto zůstává neověřený.

Další krok:
- Importovat variantu `4`, provést jeden nový neškodný bdící test a ověřit
  právě jeden nový záznam s celým časovým `delivery_id`; teprve potom uspat Mac.

Navrhované další kroky:
- Po úspěšném bdícím důkazu provést jeden spánkový test a po probuzení ověřit
  převzetí otevřené GitHub Issue právě jednou.

Technický důkaz:
- Cílené testy builderu, úložiště a GitHub synchronizace: 26/26 OK.
- iOS 27 Shortcuts validátor prošel pro secret-free zdroj i soukromou variantu
  `4`; podepsaný soubor má 25 868 bajtů.
- Plná Cockpit Quality Gate prošla 1491/1491 testy.

### 2026-08-30 18:00 CEST – Varianta 5 obchází prázdný iOS datumový výstup

Hotovo:
- Bdící běh varianty `4` založil GitHub Issue `#5`, ale její `delivery_id` bylo
  znovu pouze `samantha-`. Backend ji bezpečně odmítl jako konflikt, lokální
  index nezměnil a Issue ponechal otevřenou.
- Varianta `5` odstranila mezikroky Date a Format Date. Časové ID vkládá přímo
  ze systémové magic variable `CurrentDate` s vlastním formátem na milisekundy.
- Dva testy stavu Cockpitu už mají GitHub synchronizaci výslovně izolovanou;
  otevřený produkční inbox proto nemůže měnit jejich dočasné počty.

Rozhodnutí:
- Issue `#5` se automaticky nezavírá, nemění ani znovu nedoručuje; její obsah
  zůstává zachovaný v soukromém inboxu jako nejednoznačný pokus.
- Varianty `3` a `4` se pro další test nepoužijí. Spánkový test dál čeká na
  jednoznačný bdící důkaz varianty `5`.

Co není hotové:
- Varianta `5` ještě není importovaná ani provozně spuštěná na iPhonu.

Další krok:
- Importovat variantu `5`, provést jeden nový bdící test a ověřit celé nové
  `delivery_id`; teprve při přesné shodě povolit spánkový test.

Navrhované další kroky:
- Po úspěšném bdícím běhu provést jeden test se spícím Macem a po probuzení
  ověřit právě jedno převzetí otevřené GitHub Issue.

Technický důkaz:
- Cílená sada prošla 28/28; iOS 27 validace secret-free i soukromé varianty `5`
  prošla a podepsaný soubor má 25 698 bajtů s režimem `0600`.
- První plná brána správně odhalila dva testy závislé na živém inboxu; po jejich
  izolaci finální Cockpit Quality Gate prošla 1491/1491.
