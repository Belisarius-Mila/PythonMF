<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-08 09:59 CEST

### Hotovo
- Převzato 100 dodaných sloves s českými významy a 1 800 nezměněných FR/CZ vět.
- VerbeTraining.csv určuje tréninkovou stovku; VerbeFR.csv má celkem 107 sloves,
  protože sedm původních mimo nový seznam zůstalo zachovaných. Původní časování
  všech časů i výběrové značky jsou zachované; nové významy odpovídají zadání.
- VerbeSentences.csv má explicitní vazby na sloveso, présent, číslo a osobu.
  Všech 18 vět falloir je přiřazeno jen k S/3 (il faut).
- Dosavadní hlavní CSV dál chrání atomický zápis a konfliktní hash. Aplikace
  používá jeden datový adresář, bez tichého obousměrného kopírování.

### Rozhodnutí
- Nový screen začne pouze přítomným časem. Smyčka prochází osoby v rámci S/P.
- České věty budou na vyžádání pod obrázkem, bez automatického čtení.
- Pauza a zopakování jsou součástí návrhu; Zkus si vzpomenout je přepínatelný režim.
- Detailní chování a datový kontrakt: VocabularyFR/VERB_TRAINING.md.

### Otevřeno
- Nový screen, zvuková sekvence, obrázky a sestavení aplikace ještě nejsou hotové.
- Nadále zbývá bezpečné znovunačtení při konfliktu CSV a izolovaný test balíčku.

### Rizika
- Dosavadní desktopový zvuk používá macOS say; Linux vyžaduje jiné přehrávání.
- Nová slovesa mají jen dodané přítomné tvary. Jazyková redakce vět neproběhla.
- Obrázkový audit našel existující neabecední mapping.json už v HEAD před importem.
- Živá Janina aplikace a soukromé CSV se v tomto kroku neměnily.

### Další krok
- Implementovat dohodnutý tréninkový screen nad převzatými daty; nejdřív ověřit
  jednu kompletní sekvenci aller a neosobní falloir.

### Navrhované další kroky
- Audit dostupných kontextových obrázků a společné přehrávání pro Mac/Linux.
- Potom izolovaný build a ruční test; rozšíření časů až v další iteraci.

### Technický důkaz
- 21/21 cílených testů dat, ukládání a instalátoru prošlo.
- Přímé porovnání: 100/100 položek a 1 800/1 800 dvojic shodných se zdroji.
- Všech 50 původních sloves zachovalo časování a M; změněno jen pořadí a dodané významy.
- Širší obrázková sada: 5/6 prošlo; chyba řazení mapping.json reprodukována v původním HEAD.
- Nový screen zatím není implementovaný; žádný push ani nasazení v tomto kroku.
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

### 2026-08-09 23:30 CEST – Jeden kanonický datový adresář bez tiché synchronizace

Hotovo:
- Zdrojová aplikace používá CSV v projektovém adresáři, explicitní `--data-dir` používá přesně zadané umístění a budoucí zabalená `.app` používá Application Support.
- Tiché kopírování tří CSV při startu i ukončení bylo odstraněné.
- První start balíčku smí pouze create-only založit úplnou trojici CSV z interních seedů. Pokud najde starší přenosná data, zastaví se bez migrace a bez přepsání.
- Oddělený instalátor nyní zahrnuje i podpůrný modul bezpečného CSV zápisu.

Rozhodnutí:
- Pro zabalenou aplikaci je jedinou zapisovatelnou autoritou Application Support; pro Janin oddělený účet je autoritou explicitní `--data-dir`.
- Žádná z těchto cest se automaticky nesynchronizuje s kopií vedle programu.
- Živá Janina aplikace ani CSV nejsou součástí této zdrojové iterace.

Další krok:
- Připravit izolovaný testovací build a na pracovní kopii tří CSV ověřit start, zápis a restart.

Navrhované další kroky:
- Doplnit bezpečné znovunačtení po konfliktu.
- Potom opravit český palec, jednopoložkový interval a víceslovná slovesa.
- O samostatném nasazení k Janě rozhodnout až po úspěšném reálném testu balíčku.

Technický důkaz:
- Cílené testy 18/18, plná Cockpit brána 1330/1330 a společný slovníkový audit 6/6.
- Janin CSV prošel pouze read-only auditem: 391 řádků a 0 plánovaných oprav Sentence/SentenceT.
- Nebyl vytvořen build ani spuštěn instalační apply.


### 2026-09-08 09:59 CEST – Data a dohodnuté chování tréninku sloves

Hotovo:
- Import 100 sloves a 1 800 přesných FR/CZ dvojic do samostatných datových souborů.
- Společné VerbeFR má 107 sloves se zachováním všech původních tvarů a značek.
- Věty mají přiřazený présent, S/P, osobu, konkrétní zájmeno a tvar; falloir pouze S/3.

Rozhodnutí:
- Přítomný čas, smyčka pouze v rámci zvoleného čísla, překlady na vyžádání pod obrázkem.
- Pauza, zopakování a volitelný režim Zkus si vzpomenout. Specifikace v VERB_TRAINING.md.
- U běžné osoby tři věty dovolují zatím jen náhodné pořadí; falloir má výběr tří z 18.

Další krok:
- Implementovat screen a ověřit kompletní průchod aller i falloir.

Navrhované další kroky:
- Audit obrázků, přehrávání na Mac/Linux a izolovaný build; další časy později.

Technický důkaz:
- 21/21 cílených testů prošlo; přesná shoda se 100 položkami a 1 800 větami zdroje.
- Všechna původní časování a výběrové značky zachované.
- Širší obrázkový audit 5/6: existující chyba řazení mapping.json potvrzena i v původním HEAD.
- UI ani živá data se neměnila; bez push a nasazení.
