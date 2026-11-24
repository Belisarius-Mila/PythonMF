# Vocabulary FR — současný klient a historický prototyp

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


## 2026-11-19 — Zveřejněná optimalizace Janiných vět

Hotovo:23 obsahových přepisů, oprava apostrofu v #092,4 doplnění obrazových vazeb a17 nových karet vfr-0465–0481. Otázka #070 zní „Tu es prête pour le cours de maths ?“, české znění je také otázka. #259 beurre zachovává původní FR/CZ text i obě větné MP3, využije však nový obrázek pain.

Rozhodnutí: Míla schválil návrh z TXT s těmito dvěma upřesněními. Místní implementace zahrnuje vlastní ilustrace/náhledy a všechny4 hlasové reference nových karet. Hlasy Henri/Vlasta a tempo−10 % zachované. Původní CSV a uzavřená v003 zůstávají zdrojem pro přesné ověření.

Důkaz:481 aktivních karet,1924 platných zvukových odkazů,1141 obrazových vazeb,362 různých ilustrací.115 nových MP3, celá knihovna1898 MP3 dekódovaná. Skutečný klient přijal všechny481 položky i481 čtyřmožnostních otázek;164 HTTP odpovědí bajtově přesných. Vizuální Safari přejímka otevřená kvůli nedostupnému ovládání prohlížeče.

Stav a další krok: Zveřejněno na Francouzštině Jana přes Terru. Commit aedb8b69, job74d9ba485996e7b5c9c0db4befaeb87a completed, push/deploy confirmed. Pages deployment7910994188 a workflow44509422262 odpovídají přesnému commitu. Všech164 veřejných souborů včetně nových médií má HTTP200 a přesné bajty zdroje, katalog481 karet. Otázka #070 i původní věta #259 ověřené na veřejných datech. Podrobné důkazy jsou v private/vocabulary_fr_loop_refresh_release_20261119. Další krok je fyzická přejímka na Janině zařízení. Závěrečný dokumentační checkpoint patří do příštího GitHub balíčku.


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

Starší webový MVP níže je historický samostatný prototyp; tento port jej nemění.

# VocabularyFR Web Trainer pro Janu

Zalozeno: 2026-06-04
Priorita: 2
Stav: webovy MVP prototyp funguje lokalne

## Cil

Preklopit francouzskou slovnikovou aplikaci `VocabularyFR/vocab_trainer_fr.py`
do formy, kterou Jana muze pouzivat bez instalovaneho Pythonu, idealne na Macu
a pozdeji i na iPhonu.

Zakladni datovy zdroj zustava:

```text
VocabularyFR/VocabularyFR.csv
```

CSV schema:

```text
FR,CZ,Order,Sentence,SentenceT,L,HT,gender_fr
```

## Aktualni webovy prototyp

Staticka webova aplikace je v:

```text
VocabularyFR/web/
```

Hlavni soubory:

```text
VocabularyFR/web/index.html
VocabularyFR/web/styles.css
VocabularyFR/web/app.js
VocabularyFR/web/audio/
VocabularyFR/web/pict/
```

Lokalni testovaci server:

```text
cd /Users/miloslavfalta/Desktop/PythonMF/VocabularyFR/web
python3 -m http.server 8788 --bind 127.0.0.1
```

URL:

```text
http://127.0.0.1:8788
```

## Hotove funkce

- Nacteni `VocabularyFR.csv`.
- Editace, pridani, vlozeni a smazani radku.
- Export aktualizovaneho CSV.
- Primy zapis do vybraneho CSV v prohlizecich s File System Access API
  (prakticky Chrome/Edge); Safari ma fallback export.
- Vyhledavani, razeni a filtry `vse`, `neumim`, `HT`, `nauceno`,
  `s vetou`.
- Treninkova karta FR/CZ s preklapenim.
- Lokalni audio cache pro FR slova a cast vet.
- Obrazky podle logiky puvodni desktopove aplikace: presny stem,
  `Pict/mapping.json`, fallback `man/woman`, `verb`, `preposition`,
  `proverbs`, `others`.
- Auto smycka: Start/Stop, nahodne/postupne, interval 2-30 s,
  cteni slovo nebo slovo + veta.

## Audio

Puvodni prohlizecovy Web Speech hlas byl prakticky nepouzitelny.
Lepsi smer je lokalni audio cache generovana na Milove Macu:

```text
VocabularyFR/generate_web_audio.py
```

Generator pouziva macOS:

```text
say -v Thomas
afconvert
```

Aktualni stav 2026-06-04:

- `web/audio/fr_words/`: 193 souboru, pokryva vsechna aktualni FR slovicka
  v CSV; nizsi pocet nez 206 radku je kvuli duplicitnim FR slovum.
- `web/audio/fr_sentences/`: 127 souboru.
- Web nejdriv hleda `.m4a`; kdyz chybi, spadne na nouzovy prohlizecovy hlas.

Pri novem slovu nebo nove vete audio automaticky nevznikne ve statickem webu.
Je nutne bud obcas spustit generator u Mily, nebo zvolit robustnejsi architekturu
s lokalnim/helper serverem.

## Obrazky

Priprava webovych obrazku:

```text
VocabularyFR/prepare_web_pict_assets.py
```

Generator bere:

```text
Pict/mapping.json
Pict/
VocabularyFR/MaleFox.PNG
VocabularyFR/FemaleFox.PNG
VocabularyFR/VocabularyFR.csv
```

A vytvori:

```text
VocabularyFR/web/pict/manifest.json
VocabularyFR/web/pict/images/
```

Aktualni stav 2026-06-04:

- `web/pict/images/`: 174 souboru.
- `missing_stems`: 0.
- `VocabularyFR/web/` ma celkem cca 39 MB.

Pro Janin Mac je prakticky nutne dodat celou slozku `VocabularyFR/web/`,
protoze obsahuje aplikaci, audio i obrazky.

## Otevrene architektonicke varianty

### Varianta A: staticky web + servis u Mily

Jana pouziva web a CSV. Pri novych slovech/vetach se obcas vezme aktualni CSV
a u Mily se spusti:

```text
python3 VocabularyFR/generate_web_audio.py
python3 VocabularyFR/prepare_web_pict_assets.py
```

Vyhoda: jednoduche.
Nevyhoda: pro denni praci v zahranici je servisni cyklus otravny.

### Varianta B: mala macOS aplikace bez Pythonu

Webove UI zustane, ale pribude lokalni helper nebo zabalena `.app`, ktera umi
volat macOS `say`/`afconvert` a generovat audio primo na Janine Macu.

Vyhoda: Jana muze denne pridavat slova a audio vznikne hned lokalne.
Nevyhoda: slozitejsi prvni build/deploy.

### Varianta C: Samantha server pres Tailscale

Jana by otevrela web pres zabezpeceny pristup k Milovu Macu/serveru.
Server by ukladal CSV, generoval audio a spravoval assets.

Vyhoda: vse se generuje automaticky.
Nevyhoda: Miluv Mac/server musi byt dostupny a musi se resit bezpecny pristup.

### Varianta D: iPhone / Pythonista 3

Pro iPhone je nejrealistictejsi Pythonista verze nad stejnym CSV.
Pythonista umi pracovat se svou iCloud slozkou `Pythonista 3`, ale je nutny
prakticky test s Janou:

1. Vytvorit v Pythonista iCloud maly `samantha_test.txt`.
2. Overit, ze je videt ve Files na iPhonu.
3. Overit, ze je videt na Janine Macu.
4. Pripadne slozku/soubor nasdilet Milovi.

Riziko: jeden CSV editovany z Mac webu i iPhonu muze mit iCloud konflikty.
Pred servisnim zasahem musi byt zaloha CSV.

## Dalsi doporuceny krok

1. Rucne otestovat prototyp na Milove Macu: CSV load, obrazky, audio, auto smycka,
   editace a export.
2. Rozhodnout, zda primarni cil je Janin Mac nebo iPhone.
3. Pokud Janin Mac: navrhnout malou `.app`/helper variantu pro lokalni generovani
   audia bez Pythonu.
4. Pokud iPhone: vikendovy test Pythonista iCloud slozky a konfliktniho chovani
   CSV.

## Bezpecnost

- Skutecne Janino aktualni CSV pred servisem zalohovat.
- Nepouzivat iCloud/Git jako soucasne editovane uloziste bez konfliktni kontroly.
- Pri commitech davat pozor, ze vedle VocabularyFR existuji nesouvisejici
  rozpracovane zmeny v Samantha memory (`Family Memory Films`).
