<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-11 11:00 CEST

### Hotovo
- KPTL má nový hlasový kvíz o 32 vyvážených otázkách s historií, zpětnou vazbou a závěrečným skóre
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- V Cockpitu otevřít KPTL Introduction, projít krátký vizuální a zvukový test kvízu a ověřit závěrečné skóre

### Rozhodnutí
- Každá ze čtyř postav má 8 otázek, z toho 4 s odpovědí YES a 4 s odpovědí NO

### Navrhované další kroky
- Žádné další návrhy nad rámec bezprostředního kroku.

### Technický stav checkpointu
- Změna prošla rychlou syntax/whitespace bránou; cílené testy doložila dokončovací účtenka vývojového tahu.
- Git před checkpointem: lokální `main` na `292f3a467c8e`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `292f3a467c8e` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-11T08:09:50+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: ToBeToHave

Nazev: ToBeToHave
Pracovni proud: project-to-be-to-have
Typ: Project
Priorita: 2
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

### Automatický checkpoint 2026-08-11 09:33 CEST

- Pracovní proud: `project-to-be-to-have`
- Hotovo: KPTL aplikace nyní správně načítá čtyři postavy, věty, slovník a dostupné portréty; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 11.4 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (1): `kptl_viewer.py`
- Commit: `Fix KPTL application asset paths`
- Další krok: Spustit kptl_viewer.py v běžném desktopovém prostředí a krátce vizuálně ověřit okno a zvuk

### Automatický checkpoint 2026-08-11 10:01 CEST

- Pracovní proud: `project-to-be-to-have`
- Hotovo: KPTL Introduction je dostupné v oddílu Webové aplikace přes bezpečný desktopový launcher; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1336 testů, 319.1 s, výsledek OK
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/tests/test_cockpit.py`
- Commit: `Add KPTL launcher to Cockpit catalog`
- Další krok: Po checkpointu a nasazení otevřít v Cockpitu Webové aplikace → KPTL Introduction a ověřit okno i zvuk

### Automatický checkpoint 2026-08-11 11:00 CEST

- Pracovní proud: `project-to-be-to-have`
- Hotovo: KPTL má nový hlasový kvíz o 32 vyvážených otázkách s historií, zpětnou vazbou a závěrečným skóre; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 4.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (2): `Samantha_Agent/tests/test_cockpit.py`, `kptl_viewer.py`
- Commit: `Add KPTL character quiz`
- Další krok: V Cockpitu otevřít KPTL Introduction, projít krátký vizuální a zvukový test kvízu a ověřit závěrečné skóre
