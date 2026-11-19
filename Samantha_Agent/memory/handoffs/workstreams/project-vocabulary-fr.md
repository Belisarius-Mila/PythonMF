<!-- SAMANTHA_CURRENT_STATUS_START -->
## 2026-11-19 — Zveřejněná optimalizace Janiných vět

Hotovo:23 obsahových přepisů, oprava apostrofu v #092,4 doplnění obrazových vazeb a17 nových karet vfr-0465–0481. Otázka #070 zní „Tu es prête pour le cours de maths ?“, české znění je také otázka. #259 beurre zachovává původní FR/CZ text i obě větné MP3, využije však nový obrázek pain.

Rozhodnutí: Míla schválil návrh z TXT s těmito dvěma upřesněními. Místní implementace zahrnuje vlastní ilustrace/náhledy a všechny4 hlasové reference nových karet. Hlasy Henri/Vlasta a tempo−10 % zachované. Původní CSV a uzavřená v003 zůstávají zdrojem pro přesné ověření.

Důkaz:481 aktivních karet,1924 platných zvukových odkazů,1141 obrazových vazeb,362 různých ilustrací.115 nových MP3, celá knihovna1898 MP3 dekódovaná. Skutečný klient přijal všechny481 položky i481 čtyřmožnostních otázek;164 HTTP odpovědí bajtově přesných. Vizuální Safari přejímka otevřená kvůli nedostupnému ovládání prohlížeče.

Stav a další krok: Zveřejněno na Francouzštině Jana přes Terru. Commit aedb8b69, job74d9ba485996e7b5c9c0db4befaeb87a completed, push/deploy confirmed. Pages deployment7910994188 a workflow44509422262 odpovídají přesnému commitu. Všech164 veřejných souborů včetně nových médií má HTTP200 a přesné bajty zdroje, katalog481 karet. Otázka #070 i původní věta #259 ověřené na veřejných datech. Podrobné důkazy jsou v private/vocabulary_fr_loop_refresh_release_20261119. Další krok je fyzická přejímka na Janině zařízení. Závěrečný dokumentační checkpoint patří do příštího GitHub balíčku.
<!-- SAMANTHA_CURRENT_STATUS_END -->

## 2026-11-17 20:21 CET — Společné předání osobního režimu a Datových commitů k p+n

Hotovo: Uzavřené Datovy a5f11f68/c07df87b jsou začleněné včetně úplné
historie a aktuálního dokladu soukromého předání souboru přes sdílený iCloud.
Klientský1e7c8bd7 zůstává funkčně beze změny: Všechna464 / Jen obtížná203,
18 okruhů, soukromé UID, výslovné potvrzení importu a zachování A–D.
Rozhodnutí: Míla nyní výslovně zadal převzít hotové Datovy commity a vše p+n.
Souhlas nezahrnuje zveřejnění osobních označení. Datův soukromý soubor je
jednorázový import, pozdější přenos používá Janin poslední export; žádný autosync.
Další krok: Registrované submit_release(wait=True) pro FR Pages a Cockpit,
přesný integrační SHA, pak jediná kontrola účtenek a veřejných klientských bajtů.
Navrhované další kroky: Jana importuje soubor ze sdílené Web_Jana na svém
zařízení; fyzicky ověří přepínání, uložení a export do Zalohy.
Technický důkaz: Předchozí klientská doménová brána151 PASS,44 cílených
Python/35 JS, skutečný464/203, Safari reload. Převzetí mění jen dokumentaci;
programová brána a přesný commit/p+n jsou v private
vocabulary_fr_personal_hard_release_20261117/completion.json. Skutečný seznam,
původní CSV a Janino zařízení nejsou součástí publikačního stromu ani přejímky.


## 2026-11-17 20:17 CET — Osobní obtížná slova Jany v prohlížeči

Hotovo: Francouzština Jana má Všechna / Jen obtížná bez profilu a PINu,
editor nad celým aktuálním slovníkem a soukromý import/export označení.
Všechna je vždy celý aktuální katalog včetně budoucích karet; žádný uložený
pevný seznam. Všech 18 okruhů zůstává a jejich průnik platí společně pro
galerii, učení, poslech, smyčky i procvičování. Starší data A–D/PIN zůstávají
oddělená a nezměněná. Datův uzavřený obsahový patch a5f11f68 je začleněný.
Rozhodnutí: Míla výslovně zvolil soukromé uložení v Janině prohlížeči bez
synchronizace zařízení. Nový klíč vocabulary-fr.personal-hard.v1 obsahuje
pouze FR UID a metadata schema/kind/language; osobní seznam nikdy do Git/docs.
Import nejdřív validuje a ukáže návrh, vyžaduje volbu Přidat/Nahradit a Uložit.
Neznámá UID přizná a zachová až po výslovném potvrzení. Pozdní čtení souboru,
cizí změna snímku, poškozené úložiště ani neověřený zápis nesmějí oznámit úspěch.
Další krok: Po samostatném pokynu p+n vydat tento klientský krok; pak Jana
na svém zařízení importuje soukromý soubor z Downloads a fyzicky ověří učení.
Navrhované další kroky: Fyzická přejímka Safari na iPhonu; záloha označení exportem.
Technický důkaz:44 cílených Python PASS včetně35 JS scénářů. Skutečný soukromý
soubor proti připnutému otisku:464 Všechna /203 obtížných,0 neznámých UID,
18 okruhů, načtení bez Uložit beze změny a stav zachovaný po reloadu.
Nativní Safari: náhled/import203 a reload203, ruční přidání204 i reload204;
odebrání zpět203 v náhledu. Úzké okno Safari vizuálně ověřené, nikoli emulace
konkrétního telefonu ani fyzický iPhone. Selhání úložiště, pozdní import,
add/replace, export a byte-identická legacy data kryjí syntetické testy.
Brána, finální commit a přesný stav: private vocabulary_fr_personal_hard_20261117/
completion.json (actual_acceptance.json, safari_verification.json, final_gate.log).
Předchozí veřejné vydání059634d2 již dokončené; tento nový krok zatím místní.
Rizika: smazání dat webu nebo jiný prohlížeč označení nepřevezme; používat export.
Původní CSV/média a Datův checkout se nemění. Žádná TTS výroba ani nové p+n.


## 2026-11-17 — Schválené veřejné vydání Francouzština Jana

Hotovo: Míla po výslovné volbě veřejné Pages vs. soukromý Cockpit odpověděl
„Zveřejnit.“ Schválení se vztahuje na konkrétní finální v003:464 karet,
1830 MP3,18 témat,898 obrazových vazeb a všechny4 zvukové kanály u všech karet.
Tím je pro tento obsah překonaná původní hranice kontraktu v1.1 pro veřejný
klientský payload; neveřejné pracovní podklady zůstávají dál mimo docs/Git.
Do docs jsou přenesené pouze5 klientských JSON a2520 médií z payloadu,
celkem2525 souborů/64968870B. Každý soubor má shodnou velikost a SHA-256
s uzavřeným zdrojem. Bez osobních výběrů, PIN, L/HT, klíčů nebo lokálních cest.
Katalog, výrobní plány, souhlasy, účtenky a původní CSV se nezveřejňují.
Neměnný zdrojový soukromý balíček v003 se nepřepisuje; jeho původní
publicPromotionApproved=false zůstává historickou vlastností předání.
Samostatný souhlas s propagací a její přesný manifest jsou v soukromé účtence.
Francouzština Jana je první mezi webovými aplikacemi Cockpitu; Lékárna
(web) a Lékárna−správa jsou poslední. Desktopový FR launcher a ostatní pořadí
zachované. Stejný název používá hlavička aplikace i titulky jednotlivých karet.
Důkaz: předchozí společná brána871 cílených PASS, skutečný obsah1830MP3
plně dekódovaný,1856 audioodkazů/898 vazeb a464 čtyřmožnostních otázek
ověřeno.49 cílených Python PASS a Safari soukromý náhled nového názvu,
galerie464 karet, slova/věty a spuštění FR/CZ bez viditelné chyby.
Další krok: Dokončit programovou bránu přesných veřejných vstupů, commit,
registrované p+n nejprve FR Pages a pak Cockpitu. Finální stav/head a oba joby
určuje private vocabulary_fr_jana_release_20261117/completion.json; neměnit
main během vydání a nejistý požadavek automaticky neopakovat.
Rizika a přejímky: lidský poslech a fyzický iPhone zůstávají samostatné.
Žádná nová TTS výroba, její opakování ani změna Datova checkoutu.


## 2026-11-17 — Francouzština Jana, finální obsah v003 a pořadí aplikací

Hotovo: Převzaté Datovy uzavřené commity210d0e46/13fd015b/49432092/3c2ce8aa;
Willův Henri patch je již shodný, společné soubory se znovu nepřepisují.
Finální v003 proti předanému SHA prošla úplným ověřením:464 karet,18 témat,
345 obrazů,898 větných vazeb a1830 dekódovaných MP3. Všechny4 kanály u všech
karet complete (1856 odkazů), Henri/Vlasta−10 %,166 původních CZ MP3 zachovaných.
Výroba je hotová, neopakovat ji. Skutečné texty, média, souhlasy a plány
zůstávají v uzavřeném soukromém balíčku, tento kódový krok je nepropaguje.
Obecný klient i budoucí webová karta jsou pojmenované Francouzština Jana;
v katalogu je první, obě Lékárny (web/správa) poslední. Desktopový FR launcher
zachovaný. Dokud není dostupný nasazený obsah, webovou kartu dál skrývá pojistka.
Rozhodnutí: Míla výslovně zadal toto pořadí a následné p+n celé hotové práce.
Dřívější potvrzený kontrakt v1.1 však drží skutečný obsah mimo Git/docs a
v003 výslovně uvádí publicPromotionApproved=false. Před propagací byla Mílovi
položena volba veřejné Pages jako EN/IT, nebo soukromé Cockpit/Tailscale.
Odpověď je pro datovou publikaci nutná; p+n kódu ani tento zápis ji nenahrazuje.
Důkaz:49 cílených Python kontrol PASS. Skutečný model.js/practice.js přijal
všech1856 zvukových odkazů,898 kontextových vazeb a464 čtyřmožnostních otázek.
Nativní Safari nad odděleným soukromým stagingem: nový název,464 karet,
karta/věta, spuštění FR/CZ kanálů bez viditelné chyby. Nejde o fyzickou
telefonní nebo lidskou akustickou přejímku. Vlastní okno/server ukončené,
původní okno zachované. Žádné nové TTS ani zásah do Datova checkoutu.
Další krok: Po Mílově volbě napojit přesný schválený payload do odpovídajícího
cíle a dokončit již zadané p+n. Do veřejného stromu nikdy nekopírovat kořen
balíčku s katalogem, plány, schválením nebo podrobnými účtenkami.
Finální checkpoint/brána a další stav: private vocabulary_fr_jana_release_20261117/completion.json;
bundle_verification.json, client_verification.json, safari_verification.json,
targeted_tests.log a final_gate.log. Nový proud ani TVBCP nevzniká.


## 2026-11-17 — Společná integrace FR a opravy přenosu Samanthy

Hotovo: Začleněný uzavřený Datův commit a119e84f, obecné exportéry a obsahové
syntetické testy včetně Willovy registrace. Soukromý balíček v001 ověřen proti
předanému SHA-256, všech166 MP3 dekódováno. Skutečný klient v odděleném
soukromém stagingu přijal464 karet/18 témat/898 větných vazeb, český zvuk
161 slov a7 vět, žádný FR zvuk.31 cílených Python kontrol PASS.
Rozhodnutí: Míla zadal po Datově commitu p+n všech čekajících commitů.
Publikuje se obecný kód a klient, nikoli soukromý katalog nebo média.
Webová FR karta se v Cockpitu objeví až s veřejným datasetem; desktop zůstává.
Další krok: Programová společná brána, integrační commit a registrované p+n
Cockpit + FR Pages pro přesný schválený kódový balíček. Finální stav, head,
účtenky a kontrola skutečně načtených bajtů: private fr_mint_release_20261117/completion.json.
Rizika a otevřeno: veřejné schválení konkrétního soukromého obsahu, FR hlas/výroba,
obsahová a fyzická telefonní přejímka. publicPromotionApproved=false;
žádná změna Azure, živých CSV ani placená výroba. Datova kopie zachovaná.
Technický důkaz: private fr_mint_release_20261117/{private_bundle_verification.json,
actual_client_verification.json,targeted_tests.log,final_gate.log}.



## 2026-11-17 — Henri v registrovaném Azure adaptéru

Hotovo: fr-FR-HenriNeural je povolený v obecném Azure adaptéru při−10 %;
SSML správně používá fr-FR. Původní hlasy, přesný text/escapování, limit10000
znaků, rezervace před POST a nulové automatické opakování jsou zachované.
11 syntetických testů PASS včetně ztracené odpovědi, rezervace před přenosem,
nepovoleného hlasu/tempa a překročeného rozpočtu; bez skutečného Azure volání.
Rozhodnutí: Míla předal Datovo konkrétní zadání z Downloads. Volba Henriho
je potvrzená; výroba1664 MP3 ani navržený cenový limit dosud potvrzené nejsou.
Celý soukromý plán připnutý v Datově13fd015b byl ověřen offline:1664 požadavků,
88682 escapovaných účtovaných znaků,9 bloků do10000;166 hotových MP3 se nepřepisuje.
Rozlišujeme kanonický planSha256 (bez vlastního pole) a otisk JSON souboru;
oba jsou v soukromé účtence. Plán, texty, klíče a média nejsou v tomto commitu.
Předchozí společné kódové p+n ccae8064 je dokončené: Cockpit5/5,7/7 FR
klientských souborů exact; skutečný obsah zůstává soukromý, telefon/Mint čeká
na Mílovu přejímku. Datův13fd015b zůstává na jeho větvi, bez zásahu do ní.
Další krok: Předat Datovi přesný commit/patch adaptéru a testu. Před výrobou
samostatně potvrdit celkový cenový limit a připnutý plán; tento krok nevyrábí
audio, nepushuje, nepublikuje, nenasazuje ani nerestartuje Cockpit.
Důkaz: private vocabulary_fr_henri_adapter_20261117/{targeted_tests.log,
plan_compatibility.json,final_gate.log,completion.json}; finální bránu a commit
určuje completion.json. Obsahová, akustická a fyzická přejímka zůstávají otevřené.


# Handoff pracovního proudu: Vocabulary FR

Nazev: Vocabulary FR
Pracovni proud: project-vocabulary-fr
Typ: Project
Priorita: 2
Stav: společný osobní režim a Datovy commity připravené pro schválené p+n
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

### 2026-11-04 14:40 CET — Terra p+n aktualizace Vocabulary FR dokončené

Hotovo:
- Schválený slovníkový balíček je na GitHubu a registrované nasazení Samanthy/Cockpitu prošlo následnou kontrolou.
- Data zůstala zachovaná: Míla FR 477, Jana FR 451, Míla IT 471, osm nových obrázků v obou Pict a shodné mapování.

Rozhodnutí:
- Míla výslovně zadal „OK, předej terra p+n, děkuju.“ Jediné nové submit_release(wait=True) předalo čtyři čekající commity, projekt Vocabulary FR a centrálně schválenou Terru 6.1/high. Vydávací kontext před startem bezpečně přepnut z MMTX na Vocabulary FR registrovanou cestou.
- Samostatná aplikace VocabularyFR.app ani web Pages se tímto standardním p+n nevydávaly; konkrétní registrovaný cíl tohoto proudu je Cockpit. Žádná změna rolí, vývoje, dat nebo dalšího vydání.

Další krok:
- Znovu načíst slovník v používané aplikaci a prakticky ověřit data na zařízení.

Navrhované další kroky:
- Zachované ověření vzdáleného iCloud doručení na Janině zařízení; ostatní lexikální poznámky samostatně.

Technický důkaz:
- Účtenka 9ea7a7007816df4117a71a750031c507 completed, project-vocabulary-fr → cockpit, gpt-6.1-terra/high, push_state/deployment_state=confirmed, čtyři commity do b3b302b291d7863a5d5a26796d4f6e5993e5b31c.
- Plná brána: 2273 evidovaných testů, 449,8 s, passed=true. Smoke 5/5, protected_services_unchanged=true.
- Jedna Adamova kontrola: GitHub main přesně na vydaném headu, health HTTP 200, nový Cockpit PID 67574 / code_stamp ae3b321d9492092a. FR 477/451 a IT 471, všechny CSV/mapping otisky i 16 distribučních kopií nových obrázků přesně shodné s předávacími důkazy.
- Caller účtenku převzal; returned_to_adam=false neprokazuje automatické portálové doručení a není důvodem retry. Bez opakování p+n. Tento výsledkový zápis místně pro další balíček; fyzický reload a vzdálená synchronizace neověřené.


## 2026-11-14 10:36 CET — Janina nová slovíčka, věty a ilustrace

Hotovo: Na výslovný požadavek Míly doplněno18 dvojic Sentence/SentenceT
v aktivním Janině iCloud VocabularyFR.csv. Janin soubor má469 řádků
a všechny dvojice úplné. Zachované všechny původní neprázdné věty, pořadí,
FR hesla, L/HT, gender a další sloupce;4 české opravy: cette → tato/tahle,
porter → nosit/mít na sobě, jupe → sukně, bizarre → bizarní/divné.
Starý helper vázaný na Order nebyl aplikován. Zápis přes existující
vocabulary_csv_store se SHA kontrolou, ověřenou zálohou a atomickou výměnou.

Obrázky: Šest nových samostatných ilustrací přes vestavěný image_gen
(clothes, these, short, tshirt, strange, suitsyou); Adam zkontroloval výstupy
v rámci výslovného pověření vytvořit potřebné obrázky a aktualizovat mapping.
Čtvercové1254×1254 WebP,94 226–229 300 B, bez textu. Ostatní obrázky znovu
použité včetně jacket pro nosit/mít na sobě. Žádná původní ilustrace se
nepřepisovala ani nemazala. Nové soubory v obou Pict mají stejné SHA-256.

Mapping:1119 →1136 českých abecedních vazeb,17 nových klíčů. Zachované
všechny dosavadní vazby. Doplněné i nalezené starší mezery pro křehké,
pozvaného hosta, závody a pst. Kanonický Pict/mapping.json a Janina
distribuční kopie jsou bajtově shodné. Mílovo FR477 a IT471 hashově
beze změny; staré kořenové CSV ani VocabularyFR_Jana.csv se nepoužívají
a neměnily se.

Ověření:6 kanonických testů mappingu PASS, rychlá statická brána PASS.
Společný audit všech tří aktivních slovníků a skutečných desktopových/
Pythonista resolverů: FR Míla477 / FR Jana469 / IT Míla471, všechny věty úplné, skutečné desktopové i Pythonista resolvery bez chybějících obrázků;1517 obrazových cest dekódováno,0 chybějících mapování/souborů.
Foundation NSURL potvrdilo uploaded=true, uploading=false, upload_error=false
pro Janino CSV, mapping a všech6 nových obrázků (8 souborů). Fyzický reload
na Janině iPhonu je samostatná přejímka; samotný upload jej nedokazuje.

Soukromé plány, ověřené zálohy a účtenky:
data/private/vocabularyfr_refresh_20261114/. Nové ilustrace a prompty:
PictNew/generated/20261114_fr_jana_refresh_batch001/generation_report.json
a review.html. Generované obrázky a soukromé CSV zůstávají mimo Git přes
přesný lokální exclude. Do checkpointu patří mapping a bezpečné podklady.
Nesouvisející nezařazený agent_supervisor 2.md zůstává zachovaný.

Další krok: Jana znovu načte sdílená data v používané aplikaci. Nahrát/
synchronizovat VocabularyFR/VocabularyFR.csv a v Pict mapping.json plus
clothes.webp, these.webp, short.webp, tshirt.webp, strange.webp, suitsyou.webp.
Mapping patří pouze do Pict. Kód aplikací, instalace, Cockpit ani Pages se
neměnily; žádné p+n ani externí zpráva nebyly zadané či provedené.

## 2026-11-17 14:55 CET — FR klient pro Janu podle kontraktu v1.1

Hotovo: Samostatný klient Vocabulary FR podle IT31c670bb: galerie18 témat,
slova/věty FR/CZ, vlastní A–D/PIN/zálohy, obrazová hra, psaní s500ms nápovědou,
smyčka Slovíčka / Věta + slovíčko a až5 kontextových obrázků. Testovací obsah
je čistě syntetický; nejde o ověření skutečných464 karet ani hotovou aplikaci
s Janiným obsahem. Český a francouzský zvuk jsou dostupné nezávisle. Chybějící
FR zvuk se přizná, smyčka zůstane pozastavená na stejné kartě, hra takový
hlasový cíl nepoužije. Bez TTS fallbacku nebo automatické výroby.
Rozhodnutí: Míla potvrdil paralelní dělení Data/Will a kontrakt v1.1.
Data vlastní katalog/exporty/média/obsahové testy; Will klient, registry,
společné zápisy a integraci. Skutečný soukromý balíček mimo docs i Git,
nezměněný živý CSV, budoucí publikace a placená výroba samostatně.
Další krok: Převzít uzavřený Datův soukromý balíček s manifestem a SHA spolu
s jeho hotovými obecnými kódovými commity. Teprve při jejich integraci zapojit
existující obsahové testy a ověřit464 skutečných karet mimo publikační strom.
Navrhované další kroky: Mílova/Janina obsahová, akustická a telefonní přejímka
nad skutečným balíčkem; volba FR hlasu a případná výroba až po nové dohodě.
Technický důkaz:24 skutečných JS scénářů a81 cílených Python kontrol PASS.
Nativní Safari nad soukromými syntetickými fixtures ověřilo galerii, odhalení,
kontexty chat/lune, vysvětlení chybějícího FR audia, Stop a návrat/fokus karty.
Vlastní okno i localhost server zavřené, původní okno zachované. Žádná akustická
ani telefonní přejímka. Finální programovou bránu, zmrazené otisky a commit
určuje private vocabulary_fr_client_20261117/completion.json.
Registrace github_pages/vocabulary-fr/ a vlastní validační domény je pouze
místní; desktopový launcher i starý FR prototyp zachované. Běžící Cockpit
se nerestartoval a stále nenačetl tuto změnu registrace/validační mapy.
Před případným budoucím p+n načíst nové registry autorizovaným postupem;
současné zadání není oprávněním k restartu, push ani nasazení. Azure adaptér
beze změny. Nový TVBCP/proud nevzniká, používá se existující FR dvojice.


## 2026-11-17 15:52 CET — Předání registrace prvního Datova FR testu

Hotovo: Will připravil přesný registrační patch pro již existující Datův
syntetický test_vocabularyfr_content.py.27 jeho testů prošlo přímo z Datovy
větve; patch mění pouze validation_domains.py a cockpit_quality_gate.py,
git apply --check i strukturální výběr domény vocabulary_fr_content PASS.
Rozhodnutí: Míla požádal odblokovat Datův checkpoint. Data převezme Willův
konkrétní patch, pak ověří a checkpointuje svůj hotový obecný kód spolu
s registrací. Vlastnictví centrálního návrhu zůstává Willovi; jeho pracovní
kopie nebyla změněná. Na main se registrace přenese až s testem v uzavřeném
Datově commitu. Soukromý obsah není předmětem této registrace ani commitu.
Další krok: Data aplikuje předání Vocabulary_FR_Data_registrace_testu_predani_2026-11-17.txt
z Downloads, spustí vlastní registrovanou bránu a předá přesný checkpoint.
Navrhované další kroky: Potom Willova integrace a zvláštní přejímka soukromého
obsahového balíčku. Skutečných464 karet tímto testem nebylo potvrzeno.
Technický důkaz: uzavřený patch Vocabulary_FR_Data_registrace_testu_2026-11-17.patch
má SHA256446d70dd1ec7c647f0d3f28dffeb99c84775c308f4d74ac2a5ef86fbfc2cd4ad.
Podklad31c670bb,27 syntetických testů PASS/0,706s. Soukromá účtenka
shared_chat_transfer_fix_20261117/data_registration_receipt.json. Žádný
reset/rebase, další checkout, push, nasazení ani zveřejnění Janina obsahu.

## 2026-11-17 14:55 CET — FR klient pro Janu podle kontraktu v1.1

Hotovo: Samostatný klient Vocabulary FR podle IT31c670bb: galerie18 témat,
slova/věty FR/CZ, vlastní A–D/PIN/zálohy, obrazová hra, psaní s500ms nápovědou,
smyčka Slovíčka / Věta + slovíčko a až5 kontextových obrázků. Testovací obsah
je čistě syntetický; nejde o ověření skutečných464 karet ani hotovou aplikaci
s Janiným obsahem. Český a francouzský zvuk jsou dostupné nezávisle. Chybějící
FR zvuk se přizná, smyčka zůstane pozastavená na stejné kartě, hra takový
hlasový cíl nepoužije. Bez TTS fallbacku nebo automatické výroby.
Rozhodnutí: Míla potvrdil paralelní dělení Data/Will a kontrakt v1.1.
Data vlastní katalog/exporty/média/obsahové testy; Will klient, registry,
společné zápisy a integraci. Skutečný soukromý balíček mimo docs i Git,
nezměněný živý CSV, budoucí publikace a placená výroba samostatně.
Další krok: Převzít uzavřený Datův soukromý balíček s manifestem a SHA spolu
s jeho hotovými obecnými kódovými commity. Teprve při jejich integraci zapojit
existující obsahové testy a ověřit464 skutečných karet mimo publikační strom.
Navrhované další kroky: Mílova/Janina obsahová, akustická a telefonní přejímka
nad skutečným balíčkem; volba FR hlasu a případná výroba až po nové dohodě.
Technický důkaz:24 skutečných JS scénářů a81 cílených Python kontrol PASS.
Nativní Safari nad soukromými syntetickými fixtures ověřilo galerii, odhalení,
kontexty chat/lune, vysvětlení chybějícího FR audia, Stop a návrat/fokus karty.
Vlastní okno i localhost server zavřené, původní okno zachované. Žádná akustická
ani telefonní přejímka. Finální programovou bránu, zmrazené otisky a commit
určuje private vocabulary_fr_client_20261117/completion.json.
Registrace github_pages/vocabulary-fr/ a vlastní validační domény je pouze
místní; desktopový launcher i starý FR prototyp zachované. Běžící Cockpit
se nerestartoval a stále nenačetl tuto změnu registrace/validační mapy.
Před případným budoucím p+n načíst nové registry autorizovaným postupem;
současné zadání není oprávněním k restartu, push ani nasazení. Azure adaptér
beze změny. Nový TVBCP/proud nevzniká, používá se existující FR dvojice.


## 2026-11-17 20:17 CET — Osobní obtížná slova Jany v prohlížeči

Hotovo: Francouzština Jana má Všechna / Jen obtížná bez profilu a PINu,
editor nad celým aktuálním slovníkem a soukromý import/export označení.
Všechna je vždy celý aktuální katalog včetně budoucích karet; žádný uložený
pevný seznam. Všech 18 okruhů zůstává a jejich průnik platí společně pro
galerii, učení, poslech, smyčky i procvičování. Starší data A–D/PIN zůstávají
oddělená a nezměněná. Datův uzavřený obsahový patch a5f11f68 je začleněný.
Rozhodnutí: Míla výslovně zvolil soukromé uložení v Janině prohlížeči bez
synchronizace zařízení. Nový klíč vocabulary-fr.personal-hard.v1 obsahuje
pouze FR UID a metadata schema/kind/language; osobní seznam nikdy do Git/docs.
Import nejdřív validuje a ukáže návrh, vyžaduje volbu Přidat/Nahradit a Uložit.
Neznámá UID přizná a zachová až po výslovném potvrzení. Pozdní čtení souboru,
cizí změna snímku, poškozené úložiště ani neověřený zápis nesmějí oznámit úspěch.
Další krok: Po samostatném pokynu p+n vydat tento klientský krok; pak Jana
na svém zařízení importuje soukromý soubor z Downloads a fyzicky ověří učení.
Navrhované další kroky: Fyzická přejímka Safari na iPhonu; záloha označení exportem.
Technický důkaz:44 cílených Python PASS včetně35 JS scénářů. Skutečný soukromý
soubor proti připnutému otisku:464 Všechna /203 obtížných,0 neznámých UID,
18 okruhů, načtení bez Uložit beze změny a stav zachovaný po reloadu.
Nativní Safari: náhled/import203 a reload203, ruční přidání204 i reload204;
odebrání zpět203 v náhledu. Úzké okno Safari vizuálně ověřené, nikoli emulace
konkrétního telefonu ani fyzický iPhone. Selhání úložiště, pozdní import,
add/replace, export a byte-identická legacy data kryjí syntetické testy.
Brána, finální commit a přesný stav: private vocabulary_fr_personal_hard_20261117/
completion.json (actual_acceptance.json, safari_verification.json, final_gate.log).
Předchozí veřejné vydání059634d2 již dokončené; tento nový krok zatím místní.
Rizika: smazání dat webu nebo jiný prohlížeč označení nepřevezme; používat export.
Původní CSV/média a Datův checkout se nemění. Žádná TTS výroba ani nové p+n.


## 2026-11-17 20:21 CET — Společné předání osobního režimu a Datových commitů k p+n

Hotovo: Uzavřené Datovy a5f11f68/c07df87b jsou začleněné včetně úplné
historie a aktuálního dokladu soukromého předání souboru přes sdílený iCloud.
Klientský1e7c8bd7 zůstává funkčně beze změny: Všechna464 / Jen obtížná203,
18 okruhů, soukromé UID, výslovné potvrzení importu a zachování A–D.
Rozhodnutí: Míla nyní výslovně zadal převzít hotové Datovy commity a vše p+n.
Souhlas nezahrnuje zveřejnění osobních označení. Datův soukromý soubor je
jednorázový import, pozdější přenos používá Janin poslední export; žádný autosync.
Další krok: Registrované submit_release(wait=True) pro FR Pages a Cockpit,
přesný integrační SHA, pak jediná kontrola účtenek a veřejných klientských bajtů.
Navrhované další kroky: Jana importuje soubor ze sdílené Web_Jana na svém
zařízení; fyzicky ověří přepínání, uložení a export do Zalohy.
Technický důkaz: Předchozí klientská doménová brána151 PASS,44 cílených
Python/35 JS, skutečný464/203, Safari reload. Převzetí mění jen dokumentaci;
programová brána a přesný commit/p+n jsou v private
vocabulary_fr_personal_hard_release_20261117/completion.json. Skutečný seznam,
původní CSV a Janino zařízení nejsou součástí publikačního stromu ani přejímky.
