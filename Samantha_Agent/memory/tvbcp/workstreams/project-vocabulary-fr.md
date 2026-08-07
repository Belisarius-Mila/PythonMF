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

# TVBCP: Vocabulary FR

Pracovni proud: `project-vocabulary-fr`
Typ: `Project`
Rezim: `paused`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

Nove chronologicke zaznamy uprednostni lidsky stav v poradi Hotovo,
Rozhodnuti, Dalsi krok a Navrhovane dalsi kroky. Technicky dukaz je az
posledni kratka sekce. Starsi zaznamy se zpetne neprepisuji.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-08-04 16:45 CEST – Obě iPhone verze francouzského slovníku nyní umožňují procvičovat posledních 20 nebo 50 slovíček.

Hotovo:
- Obě iPhone verze francouzského slovníku nyní umožňují procvičovat posledních 20 nebo 50 slovíček.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Volby Last 20 a 50 jsou vzájemně výlučné a opětovné klepnutí na aktivní volbu obnoví celý běžný výběr.

Další krok:
- Nahrát příslušné AppFR.py do Pythonisty a ručně ověřit rozložení i výběr posledních slovíček.

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 7.5 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-vocabulary-fr`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-07 14:07 CEST – Funkční stav FR aplikací je potvrzený a proud je pozastavený

Hotovo:
- Míla potvrdil funkční Last 20/50 v používaných FR aplikacích.
- Lokální VocabularyFR se po opravě Tk runtime spouští z Cockpitu správně.

Rozhodnutí:
- Původní pokyn k nahrání a ručnímu testu je splněný; proud je nyní pozastavený.

Další krok:
- Až vznikne nový požadavek, měnit párově určené FR varianty a zopakovat audit dat včetně `Sentence` a `SentenceT` u Jany.

Navrhované další kroky:
- Bez nového věcného požadavku nic dalšího neměnit.

Technický důkaz:
- Filtry: commit `354a13b`.
- Oprava lokálního spuštění: commit `20cd809`.
- Následné potvrzení Míly v reálném používání.
