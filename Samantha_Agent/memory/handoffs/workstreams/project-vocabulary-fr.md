<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Ověřeno při auditu projektové paměti: 2026-08-07 14:07 CEST

### Hotovo
- Obě iPhone verze francouzského slovníku umožňují procvičovat posledních 20 nebo 50 slovíček.
- Volby jsou vzájemně výlučné, opětovné klepnutí aktivní volbu vypne a horní HT se aplikuje až nad zvoleným rozsahem.
- Míla funkci po nasazení do používaných aplikací ručně potvrdil.
- Lokální VocabularyFR spouštěná z Cockpitu používá opravený Tk runtime a Míla potvrdil, že funguje.

### Otevřeno
- Projekt je pozastavený bez bezprostředního implementačního kroku.

### Rizika
- Při budoucí změně francouzské aplikace je nutné udržet společný kontrakt Míla/Jana a u Janiny CSV vždy ověřit `Sentence` i `SentenceT`.

### Další krok
- Až vznikne nový požadavek, provést změnu párově v určených FR variantách a zopakovat povinný audit slovníkových dat.

### Rozhodnutí
- Ověřený stav se považuje za uzavřený; starý pokyn k nahrání do Pythonisty už není aktuální další krok.

### Navrhované další kroky
- Bez nového věcného požadavku nic dalšího neměnit.

### Technický stav checkpointu
- Filtry jsou v commitu `354a13b`; oprava lokálního Tk spuštění v commitu `20cd809`.
- Funkční výsledek po změnách potvrdil Míla v reálném používání.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Vocabulary FR

Nazev: Vocabulary FR
Pracovni proud: project-vocabulary-fr
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

### Automatický checkpoint 2026-08-04 16:45 CEST

- Pracovní proud: `project-vocabulary-fr`
- Hotovo: Obě iPhone verze francouzského slovníku nyní umožňují procvičovat posledních 20 nebo 50 slovíček.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 7.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (3): `MBSoft/AppFR.py`, `MBSoft/JanaIphoneFR/AppFR.py`, `Samantha_Agent/tests/test_canonical_vocabulary_mapping.py`
- Commit: `Add Last 20 and 50 filters to iPhone FR trainers`
- Další krok: Nahrát příslušné AppFR.py do Pythonisty a ručně ověřit rozložení i výběr posledních slovíček.

### Auditní dorovnání 2026-08-07 14:07 CEST

- Hotovo: Míla potvrdil funkční Last 20/50 v používaných FR aplikacích i funkční lokální VocabularyFR z Cockpitu.
- Rozhodnutí: Původní pokyn k nahrání a ručnímu testu je splněný; proud je nyní pozastavený.
- Další krok: Až vznikne nový požadavek, měnit párově určené FR varianty a zopakovat audit dat včetně `Sentence` a `SentenceT` u Jany.
- Navrhované další kroky: Bez nového věcného požadavku nic dalšího neměnit.
- Technický důkaz: Commity `354a13b` a `20cd809`; následné potvrzení Míly v reálném používání.
