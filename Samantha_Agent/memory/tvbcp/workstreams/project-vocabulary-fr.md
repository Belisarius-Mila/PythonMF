<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-09 22:51 CEST

### Hotovo
- Před vývojem vznikla ověřená privátní záloha aktuální Janiny aplikace, původního distribučního ZIPu a pracovních CSV.
- VocabularyFR ukládá hlavní CSV přes samostatnou atomickou vrstvu s kontrolou hashe, zálohou před prvním zápisem relace a zachováním neznámých sloupců.
- Uložení prázdného seznamu nyní vytvoří platné CSV pouze s hlavičkou.

### Otevřeno
- Nová datová vrstva zatím není zabalená ani nasazená do Janiny používané aplikace.
- Zůstává odstranit obousměrné kopírování mezi přenosným umístěním a Application Support a doplnit bezpečné znovunačtení po konfliktu.

### Rizika
- Reálný balíček ještě neprošel ručním testem na Janině Macu; současná funkční aplikace proto zůstala beze změny.

### Další krok
- V další oddělené iteraci určit jediný kanonický datový soubor a odstranit tiché obousměrné synchronizační kopie bez migrace živých dat.

### Rozhodnutí
- První bezpečnostní iterace mění jen ukládání hlavního VocabularyFR.csv; živá Janina aplikace se nenasazuje bez samostatného potvrzení a testu balíčku.

### Navrhované další kroky
- Doplnit uživatelsky bezpečné znovunačtení při souběžné změně CSV.
- Potom opravit český palec, jednopoložkový interval a detekci víceslovných sloves.
- Až následně připravit reprodukovatelný Janin build a ruční test zápisu i zvuku.

### Technický stav checkpointu
- Cílená sada prošla 19/19, plná Cockpit brána 1330/1330 a společný slovníkový audit 6/6.
- Janin živý CSV byl pouze read-only ověřen: 391 řádků a 0 plánovaných oprav Sentence/SentenceT.
- Předvývojová záloha je v privátní necommitované oblasti a má kontrolní součty i manifest obnovy.
- Nasazení nové verze nebylo součástí tohoto kroku.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: Vocabulary FR

Pracovni proud: `project-vocabulary-fr`
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

### 2026-08-07 21:55 CEST – Připraven dvoukrokový instalátor oddělené VocabularyFR pro Janin účet včetně návodu a testů

Hotovo:
- Připraven dvoukrokový instalátor oddělené VocabularyFR pro Janin účet včetně návodu a testů
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Program a obrázky budou společné pouze ke čtení, zatímco Janina pracovní CSV zůstanou v jejím uživatelském účtu

Další krok:
- Spustit redigovaný náhled instalace s Janiným aktuálním iCloudovým CSV

Navrhované další kroky:
- Po ověření fingerprintu provést instalaci přes sudo
- V Janině vzdálené relaci ověřit spuštění, zápis L nebo HT a přenos zvuku

Technický důkaz:
- rychlá Cockpit brána syntaxe a whitespace: 9.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu.
- Pracovní proud: `project-vocabulary-fr`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`connected`.

### 2026-08-09 22:51 CEST – První bezpečnostní vrstva ukládání VocabularyFR.csv

Hotovo:
- Před vývojem vznikla ověřená privátní záloha používané aplikace, původního distribučního ZIPu a pracovních dat.
- Hlavní CSV se nově zapisuje přes dočasný soubor, ověření znovunačtení, zálohu původní verze a atomickou výměnu.
- Hash načtené verze brání přepsání souboru, který se mezitím změnil jinde.
- Prázdný seznam se uloží jako platné hlavičkové CSV a neznámé sloupce zůstanou zachované.

Rozhodnutí:
- První iterace se omezuje na hlavní VocabularyFR.csv.
- Současná Janina aplikace se nemění ani nenasazuje bez samostatného buildu a reálného testu.

Další krok:
- Určit jediný kanonický datový soubor a odstranit tiché obousměrné kopírování s bezpečnou migrací.

Navrhované další kroky:
- Doplnit bezpečné znovunačtení při konfliktu.
- Potom opravit český palec, jednopoložkový interval a víceslovná slovesa.
- Následně oddělit správce zvuku a zakotvit reprodukovatelný build.

Technický důkaz:
- Cílené testy 19/19, plná Cockpit brána 1330/1330 a společný obrazový audit 6/6.
- Janin živý CSV byl kontrolován pouze read-only: 391 řádků, 0 plánovaných oprav Sentence/SentenceT.
- Privátní záloha je mimo Git a obsahuje manifest i kontrolní součty.
