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

# TVBCP: Vocabulary IT

Pracovni proud: `project-vocabulary-it`
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

### 2026-08-04 19:15 CEST – AppIT nabízí vzájemně výlučné volby posledních 20 nebo 50 slovíček a návrat k celému výběru

Hotovo:
- AppIT nabízí vzájemně výlučné volby posledních 20 nebo 50 slovíček a návrat k celému výběru

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.

Rozhodnutí:
- V tomto kroku nebylo přijato nové kanonické rozhodnutí.

Další krok:
- V Pythonistě krátce ověřit tlačítka 20, 50 a jejich vypnutí

Navrhované další kroky:
- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku.

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 8.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-vocabulary-it`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_other_main`, runtime=`connected`.

### 2026-08-07 14:07 CEST – Funkční stav IT aplikace je potvrzený a proud je pozastavený

Hotovo:
- Míla potvrdil funkční Last 20/50 v AppIT.
- Lokální VocabularyIT se po opravě Tk runtime spouští z Cockpitu správně.

Rozhodnutí:
- Původní pokyn k ručnímu testu je splněný; proud je nyní pozastavený.

Další krok:
- Až vznikne nový požadavek, zachovat stejný kontrakt Last 20/50/HT jako ve FR aplikacích a zopakovat společný audit dat.

Navrhované další kroky:
- Bez nového věcného požadavku nic dalšího neměnit.

Technický důkaz:
- Filtry: commit `b2355b7`.
- Oprava lokálního spuštění: commit `ae67bea`.
- Následné potvrzení Míly v reálném používání.
