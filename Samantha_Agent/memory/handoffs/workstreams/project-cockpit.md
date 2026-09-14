<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-14 15:11 CEST. U01–U04 hotové lokálně; AuditCockpit56_2.txt v2.4.
- U04: Předchozí/Další a rozsah výsledků; HTTP limit/offset napojené na existující backend. Výchozí stránka 8, maximum 20; neplatné či opakované parametry vrací 400 před poskytovatelem.
- Nový dotaz resetuje stránku; stará opožděná odpověď se ignoruje. Při chybě další stránky zůstávají dosavadní výsledky a lze opakovat. Návrat čtečky zachová původní stránku; blokovaný popup nabídne odkaz bez ztráty hledání.
- Důkaz: 27 cílených testů; HTTP nad 23 dokumenty + duplicitním řádkem bez vynechání/duplicit, čtyři browser šířky 320–1440 px s 23/9/0 výsledky. Plná brána: 1677 testů / 299.260 s, OK. `reports/cockpit_ui_u04_2026_09_14.json`.
- Zachováno: reference, oprávnění, hlavičky, potvrzení a backendová logika hledání. Žádné soukromé vyhledávání ani ostré akce v přejímce.
- Dodání: lokální vývoj, bez nového push/nasazení. Dřívější nasazení 10ec0877 je historický ověřený podklad, nikoli aktuální živý audit.
- Další krok U05: zúžit opakované přehledy do jedné prioritní fronty a rozlišit provozní stav od čekající práce.
- Rizika/přejímka: fyzický Safari Mac/iPhone čeká; živý index se mezi stránkami může změnit. Reload původního Cockpitu hledání resetuje, dotazy nejsou persistované.
- Záloha odložená kvůli disku; Santiago pouze zvažované. Cizí nesledovaný adresář zachovaný mimo commit.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Cockpit / hlavní architektura

Nazev: Cockpit / hlavní architektura
Pracovni proud: project-cockpit
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne

Co se resilo:
U04: stránkování dokumentového hledání přes HTTP a UI.

Co je hotove:
- U01–U04 lokálně implementované a ověřené; roadmapa v2.4. U04 prošel i plnou branou.

Co neni hotove:
- Push/nasazení a fyzická přejímka. Kroky U05–U11.

Dalsi krok:
U05: jedna prioritní fronta a oddělený provozní stav.

Navrhovane dalsi kroky:
- Navigace, Servis a grafika podle TXT.

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

### 2026-08-30 21:35 CEST – Připomínky ověřené, QN fallback připravený

Hotovo:
- U připomenutí je doložený bdící záznam 46 s Issue `#6` i spánkový záznam 47
  s Issue `#7`; spánková Issue vznikla při zavřeném Macu, po probuzení byla
  právě jednou doručena do Cockpitu a uzavřena.
- Quick Notes mají lokálně připravenou kopii stejného dvoucestného kontraktu:
  oddělený GitHub write-ahead, přímý Tailscale POST a přesné `delivery_id`.
- Aktivní QN cesta už neimportuje iCloud. GitHub záznam je označený
  `github_fallback`, konflikt ID selže zavřeně a Issue se uzavírá až po lokální
  účtence.
- Secret-free zdroj QN zkratky je validovaný pro iOS 27 a podepsaná zástupná
  varianta je bezpečně uložená mimo git.

Rozhodnutí:
- QN budou mít jen dvě cesty a vlastní soukromý repozitář, token a proměnné
  prostředí. Token připomenutí se nerozšiřuje.
- Do soukromé GitHub Issue mohou dočasně vstoupit pouze technické QN texty;
  Míla tuto bezpečnostní hranici výslovně přijal.

Co není hotové:
- QN inbox a token ještě neexistují; skutečné tajemství není v kódu ani
  podepsané zástupné zkratce.
- QN změna není nasazená a neproběhl její živý bdící ani spánkový test.

Další krok:
- Vytvořit soukromý QN inbox a fine-grained token pouze pro něj s oprávněním
  `Issues: Read and write`; potom jej bez výpisu vložit do ignorovaného `.env`
  a soukromé zkratky.

Navrhované další kroky:
- Samostatně potvrdit nasazení Cockpitu, provést jeden bdící QN test a až po
  přesné shodě ID jeden test se spícím Macem.

Technický důkaz:
- Cílená sada 301/301 a plná Cockpit Quality Gate 1506/1506 prošly.
- iOS 27 validace i podpis zástupné zkratky prošly; výstup má 25 724 bajtů a
  režim `0600`.
- Poslední živé nasazení zůstává `04e776351a047f95563f2d97ae43fa69544e5c7a`;
  tento checkpoint zatím nasazený není.


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
