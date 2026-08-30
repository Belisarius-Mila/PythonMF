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
