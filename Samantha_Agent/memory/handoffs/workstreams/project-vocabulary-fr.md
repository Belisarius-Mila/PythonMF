<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-11-04 13:21 CET.
- Mílovo VocabularyFR/VocabularyFR.csv má 477 řádků místo 234: doplněno 243 celých záznamů pro 235 chybějících francouzských hesel z Janina připojeného iCloud CSV. Všech 234 původních řádků přesně zachovaných.
- Přejaté všechny sloupce včetně Sentence/SentenceT, gender_fr a zdrojových L/HT podle pokynu přidat celou datovou větu. Jen Order nově 235–477; žádné kolize. Odlišné české významy chybějícího hesla zachované samostatně; dva opakované FR/CZ páry nepřidány.
- Porovnání ignoruje velikost písmen, mezery/interpunkci a běžné ligatury œ/oe, æ/ae; diakritiku zachovává. Existující francouzská hesla se nepřepisují. Všechna Janina hesla mají nyní v Mílově souboru odpovídající normalizovaný protějšek. Janino CSV 451 řádků i IT 471 řádků zůstaly beze změny.
- Společný audit FR Míla 477 / FR Jana 451 / IT Míla 471 bez chybějících vět a obrázků, 1007 používaných obrazových souborů dekódovaných. Mapping 1119, obě kopie shodné a nezměněné; žádné nové obrázky ani mapování nebyly potřeba. U Jany zachovaný přijatý chez fallback. Šest kanonických testů a rychlá statická brána PASS.
- Dříve doplněných 38 Janiných párů vět, osm ilustrací a devět vazeb zůstává zachovaných. U cent správně sto. Prompty/náhled obrázků: PictNew/generated/20261104_fr_jana_refresh_batch001/generation_report.json a review.html.
- Bezpečný CSV store, snímky obou zdrojů, ověřená záloha a přesná kontrola výsledku. Soukromé plány a důkazy v data/private/vocabularyfr_merge_jana_to_mila_20261104/ (plan.json, apply_receipt.json, audit_after_import.json). Janina CSV ani plány nejsou v Gitu.
- Další krok: znovu načíst Mílův slovník v používané aplikaci. Praktický reload a vzdálené doručení na zařízení tímto souborovým auditem NEOVĚŘENO. Bez push, změny aplikací nebo nasazení Cockpitu.
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

### 2026-09-13 10:12 CEST – Slovíčka a ilustrace z NewWords.txt

Hotovo:
- Doplněno 7 FR položek z NewWords.txt; Míla má celkem 234 slovíček.
- U Jany doplněno 7 chybějících párů vět a dva české překlepy;
  nyní všech 413 řádků kompletních. Nová Mílova hesla se Janě nepřidávala.
- Dříve potvrzená samostatná Janina aplikace a trénink 107 sloves /
  1 926 vět zůstávají zachované; tato aktualizace mění jen slovníková data.
- Společný audit: FR Míla 234 / FR Jana 413 / IT Míla 471 řádků,
  žádné chybějící obrázky v desktopových ani Pythonista resolverech.
- Doplněno také devět starších Janiných českých vazeb chybějících v Pythonistě.
- Osm nových ilustrací WebP do 250 kB; kanonické české abecední mapování
  1 082 položek (+27) je bajtově shodné s Janinou sdílenou kopií.
- Šest testů kanonického mappingu i rychlá statická brána prošly; původní řádky Míly včetně L/HT
  zachované. Všechny nové položky mají Sentence/SentenceT a L=ne, HT=ne.


Rozhodnutí:
- Realizován výslovný pokyn Míly od A do Z včetně generování, přiřazení
  a c+p. Kontrola ilustrací delegovaná Adamovi; galerie se nevyžaduje.

Další krok:
- Načíst nová data v používaných aplikacích; vzdálený přenos a iPhone retest
  se tímto místním ověřením nepotvrzují.

Navrhované další kroky:
- Další dávku opět ověřit napříč třemi slovníky.

Technický důkaz:
- Původní CSV hodnoty a mapovací vazby zachované, soukromé zálohy ověřené.
- Skutečné desktopové/Pythonista resolvery, dekódování Pillow, SHA-256 obou
  obrazových kopií, shoda mappingů a úplnost Janiných vět prošly.
- Report `reports/vocabulary_fr_it_refresh_2026_09_13.md`; soukromé důkazy
  `vocabulary_refresh_20260913/audit_result.json` a `apply_manifest.json`.
- Riziko: stav na vzdáleném iPhonu/Macu závisí na následném přenosu dat.

### 2026-11-04 12:01 CET — Janiny příkladové věty a existující obrázkové vazby

Hotovo:
- Janě doplněno 38 párů francouzských vět s českými překlady, nyní všech 451 hesel úplných.
- Doplněno 28 českých vazeb k existujícím obrázkům; oba mappingy shodné. Opravené také mezery mezi desktopovým a Pythonista výběrem, včetně šesti existujících IT aliasů při povinném společném auditu.

Rozhodnutí:
- Míla zadal doplnění Janiných příkladů, chybějících obrázků a mappingu. Použít vhodné existující obrázky, zachovat ostatní data a nové placené generování potvrdit podle kanonického postupu. Dřívější souhlas pro zářijovou dávku nepřenášet na novou.
- Starý helper má historická Order, a proto se nepoužil pro zápis. Existující bezpečný CSV store uložil jen chybějící věty podle ověřených aktuálních hesel a otisku souboru.

Další krok:
- Získat odpověď na konkrétní připravenou žádost o 8 nových obrázků a případné pověření Adama k jejich vizuálnímu výběru.

Navrhované další kroky:
- Po generování doplnit devět vazeb a provést společný audit; následně načíst data na Janině zařízení.
- Samostatně projít tři soukromé lexikální poznámky bez tichého přepisu hesel.

Technický důkaz:
- FR Míla 234 / FR Jana 451 / IT Míla 471, žádné chybějící příkladové páry. Janiny změny pouze 38 dvojic Sentence/SentenceT; původní hodnoty ostatních sloupců a existující věty zachované, Mílova CSV hashově beze změny.
- Pict/mapping.json 1082 → 1110, pouze 28 přidaných českých klíčů, původní vazby zachované, abecední a bajtově shodné s Janinou kopií. Obrázkové soubory nebylo nutné kopírovat. Skutečné desktopové/Pythonista resolvery a 902 používaných souborů prověřené.
- Zbývá 9 Janiných řádků / 8 nových ilustrací; chez má záměrný gramatický fallback. FR Míla a IT Míla bez obrazových mezer. 6 kanonických testů a rychlá statická brána PASS. Nová osmička pouze request/dry-run, bez API volání.
- Soukromé důkazy prepared_plan.json, apply_receipt.json, audit_after_existing.json a image_requests.json ve vocabularyfr_refresh_20261104. Zálohy CSV i mappingů ověřené. Lokální servisní mapping.json.lock zachovaný a přesně vyloučený v místním Git exclude, nic smazáno.
- Kód aplikací, Janina app, Mílovy CSV a existující obrázky beze změny; vzdálený iCloud přenos a fyzické zařízení neověřené. Bez push/nasazení.

### 2026-11-04 12:21 CET — Osm obrázků pro Janu doplněných do obou Pict

Hotovo:
- Všech devět zbývajících Janiných řádků dostalo správný obrázek; osm nových ilustrací je v obou používaných Pict a společné mapování je shodné.
- Číselné karty mají jasné 50 a 100. Chybný význam cent opraven na sto; příkladové věty a značky učení zachované.

Rozhodnutí:
- Míla odpověděl „OK, vše jasné, doplň prosím 8 nových obrázků...“ na připravenou konkrétní žádost o generování, Adamův vizuální výběr a distribuci do Pict/mappingu.
- Použít vestavěný image_gen podle dovednosti imagegen, jeden obrázek na volání. U čísel jasný jediný údaj bez doplňkových počítacích objektů; žádné přepnutí na placený CLI/API fallback. Všech osm výstupů přijato bez opakování generování.

Další krok:
- Načíst aktualizovaná data na Janině zařízení a ověřit praktické zobrazení.

Navrhované další kroky:
- Ostatní dvě soukromé lexikální poznámky řešit samostatnou revizí; nyní beze změny.

Technický důkaz:
- Osm WebP 1254 × 1254, max. 234496 B, celkem 1616214 B; zdroje zachované. Všech 16 distribučních souborů má očekávané SHA-256. Mapping 1110 → 1119, devět nových českých klíčů, všechny původní vazby a abecední řazení zachované; obě kopie přesně shodné.
- Společný audit FR Míla 234 / Jana 451 / IT Míla 471 bez chybějících vět a obrázků; záměrný chez fallback zachovaný. Všech devět cílových řádků má shodný správný výběr na desktopu a v Pythonistě. 907 používaných souborů načtených a dekódovaných, šest kanonických testů a rychlá statická brána PASS.
- Jediný nový CSV rozdíl vůči ověřené záloze: Order 448, CZ „sto, setina“ → „sto“. Jde o opravu nutnou k pravdivému významu a korektnímu iPhone lookupu; bez zavedení chybného aliasu setina → hundred. Ověřeno podle Larousse cent/centième, soukromý bezpečný CSV store a záloha. Mílova CSV a všechny existující věty i L/HT zachované.
- Prompty, rozměry a otisky v PictNew/generated/20261104_fr_jana_refresh_batch001/generation_report.json, náhled review.html. Úplné soukromé důkazy images_apply_receipt.json, cent_meaning_correction.json a audit_completed_images.json ve vocabularyfr_refresh_20261104.
- Vzdálené doručení a fyzický Mac/iPhone běh nejsou tímto místním auditem potvrzené. Kód aplikací se neměnil; bez sestavení, push nebo nasazení Cockpitu.

### 2026-11-04 13:21 CET — Chybějící Janina hesla doplněná do Mílova FR

Hotovo:
- Mílův slovník rozšířen ze 234 na 477 řádků. Přibylo 235 dosud chybějících francouzských hesel v 243 úplných řádcích včetně variant českého významu.
- Původní záznamy beze změny; všechna přidaná hesla mají příklad, překlad i funkční obrázek.

Rozhodnutí:
- Míla zadal porovnat Janin iCloud VocabularyFR.csv s jeho PythonMF/VocabularyFR/VocabularyFR.csv a přidat celé chybějící datové věty.
- Přenést všechny původní sloupce nových řádků, tedy také gender_fr a Janiny zdrojové L/HT; pouze Order přečíslovat návazně. Neupravovat vlastní existující věty ani jejich L/HT.
- Ignorovat při srovnání velikost písmen, interpunkci/mezery a œ/oe, æ/ae; zachovat významotvornou diakritiku. Mezi dosud chybějícími hesly zachovat každý různý FR/CZ pár jednou. Nepřevádět další významy již existujících FR hesel automaticky.

Další krok:
- Znovu načíst Mílův rozšířený slovník v aplikaci.

Navrhované další kroky:
- Zachované praktické ověření dřívější aktualizace na Janině zařízení; jiné rozšíření nevzniklo.

Technický důkaz:
- Atomický CSV store s ověřenou privátní zálohou a konfliktní kontrolou. 243 přidaných / 0 změněných původních řádků; nové Order 235–477 jedinečné. Všechny přenesené hodnoty kromě Order přesně odpovídají zdroji, včetně 22 zdrojově naučených řádků. Dva opakované FR/CZ páry nepřidány, existující duplicity v původním souboru nedotčené.
- Jana 451 a IT 471 hashově beze změny; oba mappingy 1119 beze změny a shodné. Společný audit 477/451/471 přes skutečné desktopové/Pythonista resolvery, 1007 obrazových souborů plně dekódováno, žádné chybějící věty či obrázky; u Jany záměrný chez fallback.
- Šest kanonických testů a rychlá statická brána PASS. Soukromé důkazy vocabularyfr_merge_jana_to_mila_20261104/plan.json, apply_receipt.json, audit_after_import.json; žádný export Janina CSV nebo plánů do Gitu.
- Kód aplikací, obrázky a mapování se neměnily; bez push, nasazení nebo ověření fyzického reloadu.
