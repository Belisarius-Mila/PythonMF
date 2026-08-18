<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-18 13:06 CEST

### Hotovo
- Všechny zapisovací a odesílací POST akce mají nyní přímo dohledatelný testovací kontrakt.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Vytvořit checkpoint, nasadit Cockpit a ověřit běžný smoke test.

### Rozhodnutí
- Akce typu private_write a external_send musí mít v POST registru doloženou úroveň direct.

### Navrhované další kroky
- Osm zbývajících nízkorizikových non-direct položek řešit pouze při jejich konkrétní změně nebo samostatném auditu.

### Technický stav checkpointu
- Změna je otestovaná (1444 testů).
- Git před checkpointem: lokální `main` na `b7caf4dd1c28`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `b7caf4dd1c28` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-18T10:40:39+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
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
