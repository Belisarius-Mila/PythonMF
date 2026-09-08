<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-08 10:43 CEST

### Hotovo
- Desktopový vocab_trainer_fr.py má samostatný Trénink sloves pro přítomný čas.
- Vybírá všech 107 sloves; 1 926 FR/CZ vět zahrnuje 126 nových vět pro sedm
  původních sloves (tři na každou osobu). Původních 1 800 vět je byteově zachovaných.
- Zasunutí seznamu, S/P, osoby 1/2/3, smyčka a interval; řízený poslech,
  tři věty, velký tvar po písmenech, pauza, zopakování a volitelné vzpomínání.
- České věty pouze na vyžádání pod obrázkem. Falloir nabízí výhradně il faut.
- 107 kontextových obrázků: 95 stávajících, 12 nových projektových ilustrací.
- Místní řeč nové obrazovky: Thomas na Macu, francouzský eSpeak na Linuxu.
  Chybějící hlas je přiznaný a trénink lze používat bez zvuku.

### Rozhodnutí
- Míla rozšířil trénink i o sedm původních sloves a požádal o tři věty na osobu.
- První verze zůstává u présent, S/P smyčky a překladu na vyžádání.
- Tréninková data jsou přibalený obsah pouze ke čtení; živé uživatelské CSV
  a jejich jediný datový adresář se nemění. Specifikace: VERB_TRAINING.md.

### Otevřeno a rizika
- Ruční vizuální a poslechový retest na Macu a Linuxu; v této relaci macOS
  nepovoluje snímání obrazovky. Linuxový přehrávač má ověřený kontrakt,
  nikoli skutečný poslech na Linux PC.
- Distribuční build a výměna aplikace u Jany zatím neproběhly.
- Známé řazení společného mapping.json nadále selhává v jednom širším testu;
  nový screen používá vlastní výslovné vazby a společný mapping nemění.
- Starší samostatný dluh bezpečného znovunačtení po konfliktu CSV zůstává otevřený.

### Další krok
- Míla otevře Trénink sloves a projde aller, falloir a acheter, včetně S/P,
  smyčky, vzpomínání a českých překladů; po retestu připravit distribuci.

### Navrhované další kroky
- Potvrdit vzhled a poslech na Macu i Linuxu.
- Potom izolovaný distribuční balíček bez zásahu do živých Janiných dat.
- Předem nahrané kvalitnější audio zůstává možný samostatný navazující krok.

### Technický důkaz
- 31 cílených testů a plná Cockpit brána 1 518/1 518 prošly.
- Skutečné Tk callbacky: aller, falloir, acheter, vzpomínání, pause/resume
  mezi osobami a zavření; místní Thomas exit 0.
- 107/107 obrázků se dekóduje; 12 nových ilustrací vizuálně ověřeno.
- VerbeFR.csv beze změny; původní prefixy obou tréninkových CSV byteově zachované.
- Společný obrázkový audit 5/6, selhává dříve doložené řazení mapping.json.
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


### 2026-09-08 10:43 CEST – Trénink sloves a věty pro sedm původních sloves

Hotovo:
- Nová obrazovka vede trénink od infinitivu přes tři věty k odhalení tvaru.
- Všech 107 sloves má obrázek; data obsahují 1 926 vět, z toho 126 nových
  pro vendre, laisser, rentrer, travailler, boire, payer a acheter.
- Pauza, opakování, smyčka v rámci S/P, volitelné vzpomínání a české věty
  na vyžádání pod obrázkem. Falloir zůstává pouze il faut.

Rozhodnutí:
- Míla schválil pokračování vývoje a zahrnutí sedmi původních sloves do tréninku.
- Původní dodané věty a knihovna časování zůstaly zachované.

Další krok:
- Ručně projít nový Trénink sloves na Macu a Linuxu; vizuální retest není
  v této relaci doložen, protože macOS nepovoluje snímání obrazovky.

Navrhované další kroky:
- Po retestu připravit izolovanou distribuci.
- Případně navázat předem nahraným audiem.

Technický důkaz:
- 31 cílených testů; plná Cockpit brána 1 518/1 518; skutečné Tk callbacky
  pro aller/falloir/acheter, pauzu, vzpomínání a zavření; Thomas exit 0.
- 107/107 dekódovaných obrázků, 12 nových ilustrací zkontrolováno.
- Rizika: Linuxový poslech ještě neověřen, distribuce neprovedena; známý
  nesouvisející test řazení mapping.json selhává (společný audit 5/6).
- Push, nasazení Cockpitu a zásah do živých Janiných dat neproběhly.
