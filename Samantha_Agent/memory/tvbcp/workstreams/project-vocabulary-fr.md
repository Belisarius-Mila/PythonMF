<!-- SAMANTHA_CURRENT_STATUS_START -->
## 2026-11-24 21:13 CET — Bezplatný soukromý provoz přes Tailscale

Hotovo: Místně připravený soukromý Tailscale Serve pro pexeso: vlastní
HTTPS8443 → loopback8792, samostatný per-user LaunchAgent a databáze na Macu.
Přesný plán drží commit, export, definici služby a snímek původní sítě.
Aktivace zachovává Cockpit443/8770 a Camino a odmítne jakýkoli Funnel,
cizí port/LaunchAgent či změněný podklad. Jediná trvalá účtenka brání
opakování nejasného startu; verify ověří původní výsledek bez nové akce.
Klient a Cockpit mají připravený vstup z ověřené soukromé služby.

Rozhodnutí: Míla odmítl měsíční placený hosting, potvrdil zapnutý Mac,
souhlasí s Tailscale a výslovně potvrdil funkční Tailscale i Cockpit u Jany.
Volíme soukromý Serve bez dalšího hostingového poplatku, nikoli veřejný
Funnel. Render zůstává neaktivním historickým podkladem; žádná placená
aktivace není schválená. Soukromý hostname se neukládá do Gitu.

Další krok: Předložit hotový přesný plán k povinnému potvrzení globální
brzdy pro Tailscale/LaunchAgent; po souhlasu p+n přes Terru a odpovídající
nasazení Cockpitu, potom aktivovat plán a ověřit HTTPS i oba hráče.
Navrhované další kroky: Fyzicky ověřit port8443 z Janina Macu. Případné
omezení ACL navrhnout zvlášť, žádné granty automaticky neměnit. Hostitelský
Mac musí při hraní zůstat online, neuspaný a přihlášený.

Technický důkaz:70 cílených Python kontrol PASS,64 FR JS a20 online JS.
Syntetický Tailscale/launchd ověřuje plán bez mutace, přesnou frázi/digest,
zachování ostatních cest, vlastnictví služby, cizí port/soubor/PID label,
aktualizaci s uchovanou databází a důkaz ztracené odpovědi bez replay.
Živý čtecí audit potvrdil soukromý Cockpit, vypnutý Funnel a volný8443;
8792 nemá cizí listener. Tailscale1.104.7 zachovává původní HTTP Host pro
TCP proxy podle zdroje stejné verze. Dosavadní služba se nespustila ani
síť/LaunchAgents nebyly změněné. Skutečná přejímka HTTPS/Jana čeká.
Finální brána, SHA a plán v private vocabulary_fr_tailnet_20261124/completion.json.
TXT v Downloads: Vocabulary_FR_Tailscale_bezplatny_provoz_a_aktivace_2026-11-24.txt.
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


## 2026-11-14 10:36 CET — Nová Janina slovíčka

Hotovo:18 nových FR/CZ příkladových dvojic, Jana469/469 úplných;4 české
opravy. Šest nových ilustrací v obou Pict, další existující znovu použité.
Mapping1136 (+17), český/abecední, distribuční kopie shodné; staré vazby
a všechny L/HT/Order zachované. Míla FR477 / IT471 beze změny.

Rozhodnutí: Výslovné pověření Míly zahrnuje věty, potřebné obrázky a mapping.
Existující bezpečný CSV store a zálohy, žádné použití starého Order helperu.
Žádné přepsání obrázků, mazání, app build ani p+n.

Technický důkaz:6 kanonických testů a statická brána PASS; celý audit
FR Míla477 / FR Jana469 / IT Míla471, všechny věty úplné, skutečné desktopové i Pythonista resolvery bez chybějících obrázků;1517 obrazových cest dekódováno,0 chybějících mapování/souborů. NSURL upload všech8 souborů potvrzený. Podrobnosti
reports/vocabularyfr_jana_refresh_20261114.md; privátní účtenky
data/private/vocabularyfr_refresh_20261114/.

Další krok: Janin reload dat/obrázků v aplikaci; fyzický telefon dosud
neověřený. Mapping pouze v Pict, nové soubory uvedené v reportu.

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


## Aktuální stav

- Aktualizováno: 2026-11-04 14:40 CET.
- Mílovo FR má 477 řádků po doplnění 243 celých záznamů pro 235 chybějících hesel od Jany. Původních 234 řádků přesně zachovaných; nové obsahují původní příklady, rod i zdrojové L/HT, pouze Order navazuje 235–477. Jana má 451 řádků a IT 471.
- Osm nových ilustrací je v obou Pict, společný český abecední mapping má 1119 vazeb a obě kopie jsou shodné. Janiny věty 451/451 úplné, u cent opraveno sto. Společný audit všech tří slovníků bez mezer, 1007 používaných souborů dekódovaných.
- Terra 6.1/high dokončila p+n čtyř čekajících commitů do b3b302b291d7863a5d5a26796d4f6e5993e5b31c. Účtenka 9ea7a7007816df4117a71a750031c507, project-vocabulary-fr → cockpit, completed, push_state/deployment_state=confirmed.
- Plná publikační brána prošla: evidováno 2273 testů, 449,8 s. Následná kontrola běhu 5/5 a protected_services_unchanged=true. Jedna Adamova kontrola: skutečný GitHub head shodný s vydaným, health HTTP 200, Cockpit PID 67574 a code_stamp ae3b321d9492092a. Slovníková data, mappingy a všech 16 kopií nových obrázků hashově zachované po nasazení.
- Caller převzal konečnou účtenku v této terminálové relaci. returned_to_adam=false je portálový příznak a není důvodem retry. Neproběhlo samostatné sestavení nebo vydání VocabularyFR.app ani nové Pages vydání; Janina sdílená data byla doplněná již před p+n. Následný výsledkový zápis je místní pro další balíček.
- Prompty a náhled: PictNew/generated/20261104_fr_jana_refresh_batch001/generation_report.json a review.html. Soukromé importní důkazy v data/private/vocabularyfr_merge_jana_to_mila_20261104/ a obrazové důkazy ve vocabularyfr_refresh_20261104/; žádná Janina CSV nebo soukromé plány v Gitu.
- Další krok: načíst aktualizovaná slovníková data v používaných aplikacích. Fyzický reload a vzdálené iCloud doručení tímto vydáním NEOVĚŘENO; dvě ostatní soukromé lexikální poznámky zůstávají k případné samostatné revizi.


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


## 2026-11-19 — Zveřejněná optimalizace Janiných vět

Hotovo:23 obsahových přepisů, oprava apostrofu v #092,4 doplnění obrazových vazeb a17 nových karet vfr-0465–0481. Otázka #070 zní „Tu es prête pour le cours de maths ?“, české znění je také otázka. #259 beurre zachovává původní FR/CZ text i obě větné MP3, využije však nový obrázek pain.

Rozhodnutí: Míla schválil návrh z TXT s těmito dvěma upřesněními. Místní implementace zahrnuje vlastní ilustrace/náhledy a všechny4 hlasové reference nových karet. Hlasy Henri/Vlasta a tempo−10 % zachované. Původní CSV a uzavřená v003 zůstávají zdrojem pro přesné ověření.

Důkaz:481 aktivních karet,1924 platných zvukových odkazů,1141 obrazových vazeb,362 různých ilustrací.115 nových MP3, celá knihovna1898 MP3 dekódovaná. Skutečný klient přijal všechny481 položky i481 čtyřmožnostních otázek;164 HTTP odpovědí bajtově přesných. Vizuální Safari přejímka otevřená kvůli nedostupnému ovládání prohlížeče.

Stav a další krok: Zveřejněno na Francouzštině Jana přes Terru. Commit aedb8b69, job74d9ba485996e7b5c9c0db4befaeb87a completed, push/deploy confirmed. Pages deployment7910994188 a workflow44509422262 odpovídají přesnému commitu. Všech164 veřejných souborů včetně nových médií má HTTP200 a přesné bajty zdroje, katalog481 karet. Otázka #070 i původní věta #259 ověřené na veřejných datech. Podrobné důkazy jsou v private/vocabulary_fr_loop_refresh_release_20261119. Další krok je fyzická přejímka na Janině zařízení. Závěrečný dokumentační checkpoint patří do příštího GitHub balíčku.

## 2026-11-20 23:44 CET — Janino francouzské pexeso 6 × 4

Hotovo: V Janině francouzštině nová část Pexeso se stejnými pravidly jako
EN:24 číslovaných rubů,12 různých dvojic,1–4 krátká jména, skóre a sbírky.
Po otočení obrázek, francouzská MP3 a čeština2 s; porovnání po dočtení,
zelená shoda, dvě šedá místa a pokračování stejného hráče, při neshodě
střídání. Konec/remíza, rozbalení sbírek, stejná/nová zásoba, projektor
a ruční obnova dokončených tahů bez autoplay. PC6×4, úzký displej4×6.

Rozhodnutí: Míla zadal stejné pexeso v Janině Francouzštině. Francouzský
klient používá svůj společný výběr Všechna/Jen obtížná, témata a další
filtry; hra osobní označení ani A–D nemění. Samostatný sessionStorage
vocabulary-fr.memory-pairs.v1, validace FR UID a existujících FR médií.
Přenos současného EN pravidla, bez nových ilustrací, MP3 nebo změn obsahu.
Nové p+n nezadané. Stávající FR TVBCP zůstává kanonický, žádný nový dokument.

Další krok: Dokončit programem vybranou doménovou bránu a jeden lokální
commit; přesný head/bránu určuje private/vocabulary_fr_memory_20261120/
completion.json. Míla může přezkoušet místní náhled; publikace až na p+n.
Navrhované další kroky: Fyzická přejímka na Janině zařízení po vydání.
Technický důkaz:47 klientských JS scénářů PASS včetně12 nových pro pexeso,
FR bez CZ fallbacku, načasování, skóre, obnova, filtry a neměnnost osobních
záznamů. Finální stav po posledním zpřesnění ověří doménová brána v gate.log.
Skutečný481kartový katalog vytvoří12 kompatibilních dvojic se zvukem.
Safari Mac:24 míst6×4,4 jména a skóre současně, FR/krátká CZ, neshoda
Jana→Eva, reload a ruční pokračování Evy. Fyzický iPhone zůstává otevřený.
Veškeré FR datové JSON a EN zdroje hashově zachované. Původní média ani
osobní soubory se neupravují; bez push, nasazení, TTS nebo restartu služeb.

## 2026-11-21 08:39 CET — Velká karta po správné dvojici v Janině pexesu

Hotovo: Po započítání správné dvojice se na2 sekundy otevře velký obrázek
s francouzským zápisem a ještě jednou zazní FR MP3. Český překlad v okně
není. Potom se okno samo zavře; delší nahrávka bezpečně dohraje před dalším
tahem. Stejný hráč pokračuje, skóre a šedá místa zůstávají stejné. Poslední
velká karta předchází výsledku hry. Při odchodu se okno i zvuk zruší;
uložená dvojice přežije reload bez opakování ani dvojího bodu.

Rozhodnutí: Mílův didaktický návrh se týká Janiny francouzštiny. Přesné2 s
platí pro viditelnost okna; čekání na delší zvuk bylo uvedené při zahájení.
Používají se existující velké ilustrace a FR audio bez CZ fallbacku.
EN pexeso a veškerá média/obsah/osobní označení se nemění. Nové p+n nezadané.
Předchozí6e2f1c34 je skutečně vydané: původní workflow44832338166/deployment
7954409332 success a39 veřejných souborů exact; job9988da0cc9996f13fa0b4877e3311e3a
zůstal attention/uncertain, nezávislý důkaz je v private vocabulary_fr_memory_20261120.
Původní vydání neopakovat.

Další krok: Dokončit programovou doménovou bránu a jediný lokální commit.
Přesný head/bránu a výsledný stav určuje private/vocabulary_fr_memory_reward_20261121/
completion.json; následně Mílova přejímka a samostatné p+n přes Terru.
Navrhované další kroky: Fyzická přejímka na Janině zařízení po vydání.
Technický důkaz:53 klientských JS scénářů PASS včetně6 nových pro okno,
přesné2 s, krátký/dlouhý zvuk, neshodu, přerušení/reload, chybu zvuku a
poslední dvojici. Poslední zpřesnění Escape ověří doménová brána v gate.log.
Safari Mac: skutečná shoda alors1+5, velký původní obrázek/FR nápis a zvuk,
automatický návrat, dvě šedá místa a stejný hráč se skóre1. Fyzický iPhone
zůstává otevřený. Přednačtení velkého obrázku při otočení; bez nové výroby médií.

## 2026-11-24 13:20 CET — Místní první verze pexesa na dálku pro dva hráče

Hotovo: Francouzština Jana má vstup „Hrát spolu na dálku“ ze současného
výběru pexesa. Samostatná herní služba spojuje dva klienty soukromou
pozvánkou bez účtů: stejných 24 míst 6×4, 12 dvojic, krátká jména, společné
tahy a skóre. Shoda ponechá hráče a dvě šedá místa. Oba musí dokončit FR
poslech a krátkou 2s CZ nápovědu. Po shodě se na 2 s ukáže velká FR karta
s opakovaným FR poslechem bez CZ; delší zvuk dál zamyká tah. Obrázek se
přednačítá již při otočení. Poslední odměna předchází výsledku.
Při odpojení se fáze pozastaví; ruční návrat zachová stav bez nového bodu.
Ztracená odpověď se ověří čtením stavu, neposílá se znovu další klik.

Rozhodnutí: Míla schválil vývoj jedné partie Jana v Německu ↔ Míla doma,
první rozsah dva hráči a soukromý odkaz. Klient vybírá pouze 12 UID;
osobní označení, původní lokální pexeso pro 1–4 hráče, obsah a všechna média
zůstávají zachované. Backend je izolovaný od Cockpitu/App Serveru,
SQLite transakce drží jednu autoritu. Pozvánka je jen ve fragmentu adresy,
hráčské tokeny v sessionStorage/Bearer a hashované v privátní databázi;
skrytý plán se klientům nepředává. Host/Origin, souběh, identita požadavku,
očekávané kolo/fáze, limity a odmítnutí třetího hráče mají vlastní testy.
Žádná nová výroba médií, modelové volání ani zásah do živé služby.

Další krok: Určit a samostatně schválit konkrétní HTTPS adresu, hosting
a způsob nasazení izolované služby; poté fyzická přejímka obou Maců.
Pouhé FR Pages p+n backend nezprovozní. Při změně původu se osobní data
nepřenášejí automaticky; řešit je existujícím výslovným exportem/importem.
Navrhované další kroky: Projít připravený scénář Německo–domov včetně
výpadku, zvuku, poslední dvojice a další partie. Zde není nové p+n.

Technický důkaz: 23 cílených Python kontrol PASS; 16 nových online JS a 55 FR
JS včetně 2 nových kontrol předání výběru. Dva nezávislé klienty ověřují
oba poslechy, nižší druhé číslo, přednačtení obrázku, 2s odměnu/delší zvuk,
chybu/retry/skip, reload, síťový timeout i ztracenou odpověď bez další mutace.
Serverové zkoušky pokrývají celou partii s 12 dvojicemi, skóre, opakování,
restart DB, souběhy, přístupy a oddělení HTTP cest. 54/54 místních HTTP souborů
bajtově přesných; 25 původních klientských/datových souborů zachovaných.
GUI Safari nebylo dostupné: cgWindowNotFound, browser access host unavailable.
Není to fyzická ani přeshraniční přejímka. Finální brána a commit jsou
autoritativně v private vocabulary_fr_online_20261124/completion.json.
Návod: technical/vocabulary_fr_online.md; přejímací TXT v Downloads.

## 2026-11-24 14:10 CET — Oddělené HTTPS nasazení pexesa: připravený večerní pilot

Hotovo: Připravený registrovaný provozní postup pro samostatnou FR službu.
Do soukromého běhového adresáře kopíruje výhradně schválený commit veřejného
FR klienta, médií a serveru. Ověřený cloudflared otevře dočasnou HTTPS adresu;
herní služba poslouchá jen na 127.0.0.1:8791. Nebyla změněna VPN, firewall,
LaunchAgents ani provoz Cockpitu/Camina. Pro Safari doplněné dílčí HTTP požadavky na média (Range/206/416/HEAD).
Skutečné spuštění ještě čeká na finální bránu.

Rozhodnutí: Míla nyní výslovně schválil zprovoznění adresy a nasazení služby.
Pro večerní pilot použít dočasný Cloudflare Quick Tunnel bez účtu či domény,
oddělený od stávajícího privátního Tailscale. Adresa se po novém spuštění změní,
Mac musí zůstat zapnutý, online a neuspaný. Nejde o trvalý hosting.

Další krok: Po doménové bráně a commitu spustit přesný pilot jednou,
ověřit skutečné HTTPS soubory a partii dvěma klienty. Neopakovat nejistý start.
Navrhované další kroky: Předat odkaz a otestovat dva fyzické Macy; trvalou adresu
řešit samostatně podle výsledku večerní zkoušky.

Technický důkaz: Nové testy ověřují oddělení souborů, ověřený konektor,
nezměnitelnost exportu, explicitní souhlas, totožnost procesů a obnovu nejistoty
bez druhého startu. Přesné finální počty, brána, SHA a provozní účtenka jsou
v private vocabulary_fr_hosting_20261124/completion.json. Předběžný živý audit
potvrdil zdravý jediný Cockpit a soukromé HTTPS; Funnel zůstává vypnutý.

## 2026-11-24 14:25 CET — Pexeso na dálku: dočasná HTTPS adresa skutečně nasazená

Hotovo: Francouzština Jana běží na oddělené dočasné HTTPS adrese. Dva klienty
přes veřejný internet ověřily společný plán, oba poslechové protokoly,
neshodu i shodu, správné skóre a šedá místa, odměnu a návrat po přerušení.
Přesná URL a provozní procesy zůstávají v soukromé účtence a TXT Downloads.
Původní osobní označení se mezi odlišnými adresami automaticky nepřenášejí.

Rozhodnutí: Platí výslovné schválení adresy a nasazení. Jde o večerní pilot
přes Cloudflare Quick Tunnel, nikoli trvalou adresu nebo automatický start
po restartu. Mac musí zůstat zapnutý, online a neuspaný. Změna Tailscale,
Funnel, firewallu, LaunchAgents, Cockpitu či Camina nebyla provedena.

Další krok: Míla a Jana otevřou nový odkaz, zakladatel založí partii a pošle
součástí hry vygenerovanou pozvánku. Ověřit zvuk a hraní na dvou fyzických Macích.
Navrhované další kroky: Po této přejímce vybrat trvalý hosting a stabilní
adresu. Večerní pilot není důkaz fyzického spojení Německo–domov.

Technický důkaz: 694 doménových testů PASS, 74 cílených kontrol PASS;
54/54 veřejných HTTPS souborů bajtově přesných, včetně skutečných
obrázků a MP3. Veřejné MP3 Range/206 ověřené; lokálně také suffix/open-range,
416 a HEAD. Dva samostatné HTTP klienty prošly partii s neshodou/shodou,
FR odměnou, skóre, šedými místy a pause/resume. Neplatný původ, třetí hráč
ani soukromé routy nejsou přijaty. Stejný zdravý Cockpit PID a přesně stejná
Serve konfigurace před/po. Grafické ovládání prohlížeče nebylo dostupné;
fyzická GUI přejímka zůstává otevřená. Přesný runtime SHA, veřejná URL,
procesy, finální head a účtenka: private vocabulary_fr_hosting_20261124/completion.json.

## 2026-11-24 14:49 CET — Přímý vstup do společného pexesa z Francouzštiny v Cockpitu

Hotovo: Místně připravené propojení stávajícího vstupu „Francouzština Jana“
v Cockpitu s tlačítkem „Hrát spolu na dálku“ uvnitř jejího pexesa. Jana
nemusí ručně kopírovat adresu herní služby. Společná hra se otevře v nové
kartě se 12 právě vybranými slovíčky; původní Francouzština zůstane otevřená
na své adrese se stejnými osobními označeními a filtry. Kopíruje se už jen
pozvánka pro spoluhráče. Běžící dočasný pilot zůstává beze změny.

Rozhodnutí: Míla požádal o integraci přímo do Francouzštiny otevírané
z Cockpitu. Zachovat její dosavadní Pages původ a osobní data. Cockpit
předá aktuální adresu pouze ověřené běžící hry ve fragmentu vstupního
odkazu; konkrétní dočasná adresa se neukládá do Gitu. Katalog nic nespouští.
Nové vydání webu ani restart Cockpitu tímto vývojem ještě neproběhly.

Další krok: Samostatně schválit p+n FR Pages a Cockpitu přes registrované
předání Terře; potom ověřit skutečný katalog, publikovaný klient a vstup
Jany do nové partie. Stávající HTTPS pilot mezitím zůstává použitelný.
Navrhované další kroky: Fyzicky ověřit jeden vstup z Cockpitu a poslání
pozvánky druhému Macu/Linuxu. Trvalou adresu řešit až po večerní přejímce.

Technický důkaz: 39 cílených Python kontrol PASS včetně 60 FR JS scénářů
(5 nových pro vstup z Cockpitu) a 16 online JS scénářů. Výběr a osobní
stav zůstávají zachované, adresu lze obnovit po změně filtrů/reloadu,
nové spuštění z Cockpitu nahradí starou dočasnou adresu. Neplatné adresy,
cizí původ, credentials, port, cesta, query či fragment se nepoužijí jako
cíl. Při chybě či zastavené službě zůstane běžná Francouzština dostupná.
Lokální katalog poskytuje propojený odkaz, živý Cockpit má ještě původní
odkaz: vydání je nutné. Stávající hra přes HTTPS odpovídá200 a její procesy
nebyly restartovány. Kontrola totožnosti procesů je nezávislá na LC_ALL/TZ
volající služby a rozpozná starší české i nové anglické datum startu.
První doménová brána1377 PASS; finální brána, SHA a počet čekajících commitů:
private vocabulary_fr_cockpit_entry_20261124/completion.json.

## 2026-11-24 19:39 CET — Další partie s jinými slovíčky ve stejné místnosti

Hotovo: Místně doplněné tlačítko „Další partie s jinými slovíčky“. Zakladatel
vybere okruh, zkontroluje návrh 12 nových slov, případně výběr změní, a zahájí
hru pro oba dosavadní hráče. Předchozích 12 UID se vynechá; malý okruh nabídne
rozšíření místo tichého opakování slov. Zůstávají jména, hráčské přístupy,
místnost i pozvánka. Skóre a plán se obnoví pro další kolo. Původní tlačítko
pro stejná slova zůstává. Soukromý osobní seznam se nepřenáší.

Rozhodnutí: Míla potvrdil jednu skutečně odehranou společnou partii a upozornil,
že jiná slova vyžadují novou pozvánku. Příčina byla potvrzená v kódu: rematch
pouze zamíchal původní balíček. Řešení mění výběr uvnitř stávající místnosti.
Předchozí p+n a nasazení vstupu Cockpit → FR byly dokončené na5205fc43;
následná samostatná oprava dočasného tunelu je doložená v private
vocabulary_fr_dns_repair_20261124/completion.json. Nový vývoj sám nové
publikování ani nasazení nepovoluje.

Další krok: Po samostatném souhlasu vydat tuto změnu přes Terru a registrovaně
aktualizovat pouze herní server na stávající adrese. Oba hráči pak obnoví
svůj herní panel a výslovně zapnou zvuk; nový odkaz nebude potřeba.
Navrhované další kroky: Fyzicky ověřit druhou partii s jinými slovy; trvalou
adresu nadále řešit zvlášť. Cockpit se pro tuto změnu nemusí restartovat.

Technický důkaz: Dosavadních44 cílených Python kontrol PASS, včetně60 FR JS
scénářů a20 online JS scénářů. Skutečný veřejný katalog481 karet: výběry pro
všechny okruhy prošly společnou kompatibilitou klient/server, žádné navržené
UID není z předchozí partie. Dva samostatné JS klienty zachovají místnost,
URL, soukromý přístup i jména, po ztracené odpovědi neopakují rematch. Server
ověřuje zakladatele, dokončenou hru, očekávané kolo/fázi a12 kompatibilních UID;
opakovaná stejná akce nepřelosuje karty. Registrované Pilot.upgrade zachová
konektor, původ a databázi, vyžaduje stejné katalogové vstupy a explicitní
souhlas, před jediným restartem ukládá účtenku. Selhání/nejistota se neopakuje.
Živý server5205fc43 a původní procesy zůstaly během vývoje beze změny.
Fyzická přejímka nové druhé partie čeká. Finální brána, cílené počty, commit
a provozní stav jsou v private vocabulary_fr_rematch_20261124/completion.json.

## 2026-11-24 20:44 CET — Příprava trvalého hostingu Francouzštiny

Hotovo: Místně připravený samostatný cloudový balíček pro Render: placená
jedna instance ve Frankfurtu, disk1GB, přidělená stabilní HTTPS adresa,
izolovaný export veřejné FR části z přesného commitu a start bez Samanthy.
Health kontroluje i databázi, korektní SIGTERM/restart zachová úložiště,
SQLite backup vytváří novou soukromou kopii. Připravený trvalý vstup z Pages
Francouzštiny i Cockpitu má přednost před starým tunelem; vyžaduje přesnou
schválenou konfiguraci. Ta nyní obsahuje origin=null, nic se neaktivuje.

Rozhodnutí: Míla výslovně zadal připravit trvalý hosting po opakovaném zániku
Quick Tunnel při usnutí Macu. Render je doporučený podklad přípravy, jeho
placená aktivace ani účet nebyly schválené. Návrh7,25USD/měsíc před daněmi
(7 compute +0,25 disk), případný přenos navíc; žádný cenový strop. Stávající
hra má zůstat funkčně stejná. Nepřenáší se soukromá lokální databáze.

Další krok: Potvrdit poskytovatele/účet a placený základ; pak registrovaně
vydat přípravu, aktivovat schválenou službu, ověřit její skutečný release a
teprve potom vydat přesný cloudový původ v konfiguraci FR Pages/Cockpitu.
Navrhované další kroky: Dva skutečné hráče a restart ověřit na nové službě;
nezávislou off-site zálohu řešit jako další vymezený krok. První přechod
na jiný původ vyžaduje jednu novou místnost a pozvánku, další kola již ne.

Technický důkaz:56 cílených Python kontrol PASS včetně63 FR JS scénářů a20
online JS. Cloudové testy ověřují export bez tajemství/ostatních aplikací,
Git identity, symlinky, disk/HTTPS/port, databázový health503, konzistentní
zálohy, SIGTERM a restart se stejnou databází. Nový klient přijímá pouze
konkrétní konfigurovaný Render původ; fragment s libovolnou Render adresou
neaktivuje cizí službu. Pozdní konfigurace neblokuje slovník. Předchozí
3d1d4483 je na GitHubu a Pages; místní herní upgrade i druhá partie jsou
ověřené v private vocabulary_fr_rematch_20261124/completion.json. Veřejný
Quick Tunnel je stále nedostupný. Nová cloudová služba ani účet nejsou
vytvořené. Finální brána, SHA, export a limity přejímky jsou v private
vocabulary_fr_cloud_20261124/completion.json. Návrh a plný postup jsou
v Downloads/Vocabulary_FR_trvaly_hosting_navrh_a_nasazeni_2026-11-24.txt.

## 2026-11-24 21:13 CET — Bezplatný soukromý provoz přes Tailscale

Hotovo: Místně připravený soukromý Tailscale Serve pro pexeso: vlastní
HTTPS8443 → loopback8792, samostatný per-user LaunchAgent a databáze na Macu.
Přesný plán drží commit, export, definici služby a snímek původní sítě.
Aktivace zachovává Cockpit443/8770 a Camino a odmítne jakýkoli Funnel,
cizí port/LaunchAgent či změněný podklad. Jediná trvalá účtenka brání
opakování nejasného startu; verify ověří původní výsledek bez nové akce.
Klient a Cockpit mají připravený vstup z ověřené soukromé služby.

Rozhodnutí: Míla odmítl měsíční placený hosting, potvrdil zapnutý Mac,
souhlasí s Tailscale a výslovně potvrdil funkční Tailscale i Cockpit u Jany.
Volíme soukromý Serve bez dalšího hostingového poplatku, nikoli veřejný
Funnel. Render zůstává neaktivním historickým podkladem; žádná placená
aktivace není schválená. Soukromý hostname se neukládá do Gitu.

Další krok: Předložit hotový přesný plán k povinnému potvrzení globální
brzdy pro Tailscale/LaunchAgent; po souhlasu p+n přes Terru a odpovídající
nasazení Cockpitu, potom aktivovat plán a ověřit HTTPS i oba hráče.
Navrhované další kroky: Fyzicky ověřit port8443 z Janina Macu. Případné
omezení ACL navrhnout zvlášť, žádné granty automaticky neměnit. Hostitelský
Mac musí při hraní zůstat online, neuspaný a přihlášený.

Technický důkaz:70 cílených Python kontrol PASS,64 FR JS a20 online JS.
Syntetický Tailscale/launchd ověřuje plán bez mutace, přesnou frázi/digest,
zachování ostatních cest, vlastnictví služby, cizí port/soubor/PID label,
aktualizaci s uchovanou databází a důkaz ztracené odpovědi bez replay.
Živý čtecí audit potvrdil soukromý Cockpit, vypnutý Funnel a volný8443;
8792 nemá cizí listener. Tailscale1.104.7 zachovává původní HTTP Host pro
TCP proxy podle zdroje stejné verze. Dosavadní služba se nespustila ani
síť/LaunchAgents nebyly změněné. Skutečná přejímka HTTPS/Jana čeká.
Finální brána, SHA a plán v private vocabulary_fr_tailnet_20261124/completion.json.
TXT v Downloads: Vocabulary_FR_Tailscale_bezplatny_provoz_a_aktivace_2026-11-24.txt.
