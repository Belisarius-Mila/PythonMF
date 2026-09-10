<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-09-10 08:22 CEST

### Hotovo
- Míla potvrdil novou aplikaci i vzpomínání jako funkční.
- Trénink présent: 107 sloves, 1 926 FR/CZ vět, 107 ilustrací. Správně napsaný
  tvar pokračuje automaticky; Dál dovolí i prázdnou odpověď, písmena po 0,44 s.
- Nová samostatná VocabularyFR.app je připravená ve sdíleném iCloud PythonMF.
  Obsahuje vlastní Python/Tk/Pillow a čte výslovně Janiny CSV vedle aplikace.
- Nejdřív ověřená záloha původního slovníku, sloves, aplikace a distribuce.
  Janiných 406 řádků má všechna Sentence/SentenceT: doplněno 15 párů,
  opraveny dva zjevné FR překlepy. Ostatní pole a již hotové věty zachované.
- Janin VerbeFR.csv zachován. Doplněn FR_Pict.csv, 119 chybějících obrázků
  a 86 novějších vazeb stávajícího kanonického mappingu; obě mapování shodná.
- Původní aplikace i CSV jsou také ve sdílené Zaloha_pred_aktualizaci_20260908_164413.
  Připraven distribuční ZIP a CTI_ME_nova_verze_20260908.txt.

### Rozhodnutí
- Míla výslovně požádal o zálohu, doplnění vět, izolované sestavení a výměnu
  Janiny aplikace ve sdíleném PythonMF. Přímý přenos byl tímto autorizovaný.
- Janina přenosná edice používá jediný explicitní --data-dir vedle .app;
  obecná politika zdrojové aplikace / Application Support se neměnila.
- Balíček x86_64 navazuje na architekturu původní Janiny .app. Bez Git push.

### Otevřeno a rizika
- Míla 10. 9. potvrdil, že aktualizace u Jany fungovala na první pokus;
  distribuční retest je splněný.
- Na sdíleném CSV má pracovat vždy jedna aplikace / zařízení. ZIP obsahuje
  datový snímek; nesmí později nahradit novější Janin slovník.
- Obrázkový audit pokryl FR Míla 227, FR Jana 406 a IT Míla 463 řádků,
  bez chybějících výsledných souborů. Jana má 16 obecných kategoriálních
  fallbacků; výběr lepších ilustrací zůstává samostatné téma.
- Historický dluh řazení mapping.json a reloadu po konfliktu CSV zůstává.
- Linuxový poslech dosud neověřený na skutečném Linux PC.

### Další krok
- Distribuční krok je uzavřený. Další změna až podle nového požadavku.

### Navrhované další kroky
- Nové nasazení teď není potřeba.
- Samostatně Linux poslech a případné přesnější obrázky nových slovíček.

### Technický důkaz
- 50 cílených testů; plná Cockpit brána 1 518/1 518.
- Skutečná zabalená aplikace z výstupu i sdílené složky: 406 řádků,
  107 sloves, 107 načtených obrázků, správná psaná odpověď pokračuje; Tk 8.6.13.
- Build mimo Desktop prošel i strict codesign; přenesená kopie deep codesign.
- 1 203 položek obsahu / odkazů aplikace porovnáno po přenosu, ZIP SHA-256 shodné.
- Mílovy slovníky i kanonický mapping beze změny. Obě distribuční mapování
  mají 1 055 položek a žádný cíl bez fyzického obrázku.
- Soukromý receipt: data/private/vocabularyfr_jana_release/20260908_1635/TRANSFER_RECEIPT.json.
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


### 2026-09-08 16:47 CEST – Samostatná aplikace pro Janu ve sdíleném PythonMF

Hotovo:
- Záloha před úpravami, 15 doplněných párů Sentence/SentenceT a dvě pravopisné
  opravy; všech 406 řádků kompletních. Stávající věty a ostatní hodnoty zachované.
- Izolovaný balíček s vlastním Pythonem a novým tréninkem byl přenesen jako
  VocabularyFR.app. Původní aplikace i data zachované v datované sdílené záloze.
- Distribuční ZIP a stručný návod připravené; společné mapování dorovnáno
  přidáním 86 položek, zkopírováno 119 chybějících obrázků.

Rozhodnutí:
- Realizován Mílův výslovný pokyn k přípravě a výměně. Janina portable edice
  předá explicitní datový adresář vedle .app. Žádné přepínání autority ani
  synchronizační kopírování do Application Support.

Další krok:
- Jana po iCloud synchronizaci ověří spuštění, trénink a zvuk na svém Macu.
  Tento vzdálený běh zatím nepotvrzený; místní sdílená kopie je ověřená.

Navrhované další kroky:
- Později samostatně Linux poslech a přesnější ilustrace obecných fallbacků.

Technický důkaz:
- 50 cílených testů a plná brána 1 518/1 518. Dva skutečné frozen Tk průchody
  (build a sdílená .app): 406 řádků, 107 sloves / obrázků a typed recall OK.
- Podpisy ověřené; 1 203 položek aplikace a SHA-256 ZIPu porovnáno po přenosu.
- Tři slovníkové zdroje auditované: 227 / 406 / 463 řádků, všechny výsledné
  obrazové soubory existují. Shodné mapování 1 055 položek; Jana 16 obecných fallbacků.
- Soukromá záloha: vocabularyfr_backups/20260908_162815_jana_upgrade.
- Soukromá pracovní složka: vocabularyfr_jana_release/20260908_1635;
  TRANSFER_RECEIPT.json uchovává přesné součty a obnovovací umístění.


### 2026-09-10 08:22 CEST – Potvrzení Janiny aktualizace

Hotovo:
- Míla potvrdil, že se aktualizace povedla na první pokus. Retest Janiny
  samostatné aplikace je splněný a distribuční krok uzavřený.

Rozhodnutí:
- Bez další změny aplikace nebo dat.

Další krok:
- Navázat až při novém věcném požadavku.

Navrhované další kroky:
- Dříve otevřené samostatné náměty (Linux poslech, ilustrace) se tím nemění.

Technický důkaz:
- Výslovné potvrzení Míly v konverzaci 10. 9. 2026; návaznost na distribuci
  připravenou 8. 9. z commitu 581eb3db.
