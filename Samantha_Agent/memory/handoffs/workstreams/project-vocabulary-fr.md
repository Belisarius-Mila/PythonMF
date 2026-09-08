<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-08 12:06 CEST

### Hotovo
- Desktopový vocab_trainer_fr.py má samostatný Trénink sloves pro přítomný čas.
- Vybírá všech 107 sloves; 1 926 FR/CZ vět zahrnuje 126 nových vět pro sedm
  původních sloves (tři na každou osobu). Původních 1 800 vět je byteově zachovaných.
- Zasunutí seznamu, S/P, osoby 1/2/3, smyčka a interval; řízený poslech,
  tři věty, velký tvar po písmenech, pauza, zopakování a volitelné vzpomínání.
- Vzpomínání čeká před první ukázkou na napsaný tvar nebo Dál/Enter; správná
  odpověď pokračuje automaticky. Odhalování písmen je zpomaleno na 0,44 s.
- České věty pouze na vyžádání pod obrázkem. Falloir nabízí výhradně il faut.
- 107 kontextových obrázků: 95 stávajících, 12 nových projektových ilustrací.
- Místní řeč nové obrazovky: Thomas na Macu, francouzský eSpeak na Linuxu.
  Chybějící hlas je přiznaný a trénink lze používat bez zvuku.

### Rozhodnutí
- Míla upřesnil vzpomínání: jen zájmeno, neomezený čas na psaní, Dál dovolí
  i prázdnou či chybnou odpověď. Písmena se mají odhalovat dvakrát pomaleji.
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
- Míla znovu otevře Trénink sloves a ověří nové psaní, tlačítko Dál
  a pomalejší odhalování; následně pokračovat Linux retestem a distribucí.

### Navrhované další kroky
- Potvrdit vzhled a poslech na Macu i Linuxu.
- Potom izolovaný distribuční balíček bez zásahu do živých Janiných dat.
- Předem nahrané kvalitnější audio zůstává možný samostatný navazující krok.

### Technický důkaz
- Aktuální oprava: 18/18 testů tréninku/dat, rychlá statická brána a skutečné
  Tk ověření vstupu i tlačítka Dál. Předchozí základ: 31 testů a plná brána
  1 518/1 518; plná brána se při této úzké opravě neopakovala.
- Skutečné Tk callbacky: aller, falloir, acheter, vzpomínání, pause/resume
  mezi osobami a zavření; místní Thomas exit 0.
- 107/107 obrázků se dekóduje; 12 nových ilustrací vizuálně ověřeno.
- VerbeFR.csv beze změny; původní prefixy obou tréninkových CSV byteově zachované.
- Společný obrázkový audit 5/6, selhává dříve doložené řazení mapping.json.
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

### Automatický checkpoint 2026-08-07 21:55 CEST

- Pracovní proud: `project-vocabulary-fr`
- Hotovo: Připraven dvoukrokový instalátor oddělené VocabularyFR pro Janin účet včetně návodu a testů; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 9.0 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (4): `VocabularyFR/vocab_trainer_fr.py`, `Samantha_Agent/tests/test_vocabularyfr_jana_remote_install.py`, `VocabularyFR/REMOTE_JANA.md`, `VocabularyFR/install_jana_remote.py`
- Commit: `Prepare safe Jana remote VocabularyFR installer`
- Další krok: Spustit redigovaný náhled instalace s Janiným aktuálním iCloudovým CSV

### 2026-08-09 22:51 CEST – První bezpečnostní vrstva ukládání VocabularyFR.csv

- Hotovo: Před vývojem vznikla ověřená privátní záloha používané aplikace a dat. Hlavní CSV se nově zapisuje přes dočasný soubor, úplnou kontrolu načtení, zálohu původní verze a atomickou výměnu. Hash brání přepsání souboru změněného jiným zařízením; prázdný seznam se uloží správně a neznámé sloupce zůstanou zachované.
- Rozhodnutí: První iterace se omezuje na hlavní VocabularyFR.csv. Běžící Janina aplikace zůstává beze změny, dokud nevznikne a neprojde samostatně ověřený balíček.
- Další krok: Určit jediný kanonický datový soubor a odstranit tiché obousměrné kopírování s bezpečnou migrací.
- Navrhované další kroky: Doplnit znovunačtení po konfliktu; potom malé logické opravy; následně správce zvuku a reprodukovatelný build.
- Technický důkaz: cílené testy 19/19, plná brána 1330/1330, obrazový audit 6/6 a Janin read-only větný audit 391 řádků bez plánované změny.

### 2026-08-09 23:30 CEST – Jeden kanonický datový adresář bez tiché synchronizace

- Hotovo: Zdrojový běh, explicitní `--data-dir` a budoucí zabalená aplikace mají každý právě jeden určený datový adresář. Kopírování mezi přenosným umístěním a Application Support při startu i ukončení bylo odstraněné. První start balíčku umí pouze create-only inicializaci z úplných interních seedů; starší přenosná data bez ověření odmítne migrovat. Instalátor přenáší i podpůrný modul bezpečného CSV zápisu.
- Rozhodnutí: Pro zabalenou `.app` je kanonický Application Support, pro Janin oddělený spouštěč explicitní `--data-dir`. Živá aplikace ani data se v tomto kroku nemění.
- Další krok: Připravit izolovaný testovací build a na pracovní kopii tří CSV ověřit start, zápis a restart.
- Navrhované další kroky: Doplnit bezpečné znovunačtení po konfliktu; potom malé logické opravy; nasazení k Janě řešit až samostatně po reálném testu.
- Technický důkaz: cílené testy 18/18, plná brána 1330/1330, společný audit 6/6 a Janin read-only větný audit 391 řádků bez plánované změny.


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


### 2026-09-08 12:06 CEST – Vzpomínání čeká na odpověď a písmena nabíhají pomaleji

Hotovo:
- Režim Zkus si vzpomenout ukáže před první ukázkou pouze zájmeno a pole
  pro samotný tvar slovesa. Čeká bez časového limitu.
- Správný tvar pokračuje automaticky. Dál nebo Enter pokračuje i s prázdnou
  či chybnou odpovědí; teprve potom se ukáže a přečte tvar a příkladové věty.
- Závěrečné odhalování zpomalilo z 0,22 na 0,44 sekundy mezi písmeny.

Rozhodnutí:
- Míla požaduje aktivní vybavení tvaru před jeho zobrazením a volitelné psaní.
- Dál nesmí vyžadovat správnou ani vyplněnou odpověď. Francouzská diakritika
  se kontroluje, velikost písmen a mezery na okrajích se ignorují.

Další krok:
- Míla znovu otevře trénink a ověří čekání u JE, automatické pokračování po
  vais a možnost přeskočení tlačítkem Dál; ručně posoudí pomalejší odhalování.

Navrhované další kroky:
- Po retestu pokračovat dříve domluveným ověřením na Linuxu a distribucí.

Technický důkaz:
- 18/18 testů tréninku a dat, rychlá statická brána a syntaxe modulů prošly.
- Skutečné Tk políčko a tlačítko ověřily prázdnou/chybnou odpověď, automatický
  přechod při správném tvaru, diakritiku, vymazání po přepnutí, pauzu a zavření.
- Předešlá plná brána měla 1 518 testů; v této úzké UI opravě nebyla opakována.
- Rizika: zbývá ruční vizuální retest; CSV, obrázky a hlasový backend se neměnily.
- Push ani nasazení neproběhly.
