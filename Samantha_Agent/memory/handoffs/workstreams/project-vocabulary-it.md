<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Ověřeno při auditu projektové paměti: 2026-08-07 14:07 CEST

### Hotovo
- AppIT nabízí vzájemně výlučné volby posledních 20 nebo 50 slovíček a návrat k celému výběru.
- Horní HT se aplikuje až nad zvoleným rozsahem a opětovné klepnutí aktivní volbu vypne.
- Míla funkci po změně ručně potvrdil.
- Lokální VocabularyIT spouštěná z Cockpitu používá opravený Tk runtime a Míla potvrdil, že funguje.

### Otevřeno
- Projekt je pozastavený bez bezprostředního implementačního kroku.

### Rizika
- Budoucí změna mapování nebo obrazových aliasů musí znovu projít společným auditem CSV a `Pict/mapping.json`.

### Další krok
- Až vznikne nový požadavek, zachovat stejný kontrakt Last 20/50/HT jako ve FR aplikacích a zopakovat audit dat.

### Rozhodnutí
- Ověřený stav se považuje za uzavřený; starý pokyn k ručnímu testu už není aktuální další krok.

### Navrhované další kroky
- Bez nového věcného požadavku nic dalšího neměnit.

### Technický stav checkpointu
- Filtry jsou v commitu `b2355b7`; oprava lokálního Tk spuštění v commitu `ae67bea`.
- Funkční výsledek po změnách potvrdil Míla v reálném používání.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Vocabulary IT

Nazev: Vocabulary IT
Pracovni proud: project-vocabulary-it
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

### Automatický checkpoint 2026-08-04 19:15 CEST

- Pracovní proud: `project-vocabulary-it`
- Hotovo: AppIT nabízí vzájemně výlučné volby posledních 20 nebo 50 slovíček a návrat k celému výběru
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 8.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (1): `MBSoft/AppIT.py`
- Commit: `Add Last 20 and 50 filters to AppIT`
- Další krok: V Pythonistě krátce ověřit tlačítka 20, 50 a jejich vypnutí

### Auditní dorovnání 2026-08-07 14:07 CEST

- Hotovo: Míla potvrdil funkční Last 20/50 v AppIT i funkční lokální VocabularyIT z Cockpitu.
- Rozhodnutí: Původní pokyn k ručnímu testu je splněný; proud je nyní pozastavený.
- Další krok: Až vznikne nový požadavek, zachovat stejný kontrakt Last 20/50/HT jako ve FR aplikacích a zopakovat společný audit dat.
- Navrhované další kroky: Bez nového věcného požadavku nic dalšího neměnit.
- Technický důkaz: Commity `b2355b7` a `ae67bea`; následné potvrzení Míly v reálném používání.
