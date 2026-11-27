# Vocabulary FR — současný klient a historický prototyp

<!-- SAMANTHA_CURRENT_STATUS_START -->
## 2026-11-25 13:08 CET — Změna filtru bez ztráty společné místnosti

Hotovo: Zakladatel rozehrané i dokončené partie má přímo ve společné
místnosti „Změnit filtr a začít znovu“. Volí okruh, slovní druh, obtížnost,
typ výrazu, posledních20/50 nebo hledání FR/CZ. Náhled12 dvojic lze zrušit
návratem do původní hry. Potvrzení rozehrané hry výslovně vynuluje skóre,
vymění24 karet a zachová místnost, jména, přístupy i původní pozvánku.
Druhý hráč dostane nové kolo synchronizací; sám filtr měnit nemůže.

Rozhodnutí: Míla požádal o změnu filtru u zakladatele bez dalšího posílání
odkazu i před dohráním. Stávající rematch po dokončení zůstává. Nová akce
restart používá12 veřejných UID, žádný osobní seznam se neposílá.
Míla následně výslovně zadal p+n i spuštění aktualizovaného serveru.
Dřívější Tailscale aktivace be9aeaa8 běží podle živého čtecího statusu;
tento nový krok nemění síť, LaunchAgent ani běžící export.

Další krok: Dokončit výslovně zadané p+n přes Terru a připravit přesný
plán aktualizace samostatné herní služby se zachováním databáze. Pages samotné server
restart nerozšíří; současná živá verze stále be9aeaa8 tuto akci neumí.
Navrhované další kroky: Na Janině a Mílově Macu ověřit zrušení filtru,
potvrzený restart uprostřed hry a další partii bez nového odkazu.

Technický důkaz:23 cílených Python kontrol včetně23 JS scénářů PASS před
finální programovou bránou; doplněný HTTP test dvou přístupů a nové routy.
Testy drží idempotenci po obnově databáze, host-only, chybné výběry,
staré kolo/poslech, zrušení bez leave a ukončení starého odměnového zvuku.
Finální brána a commit: private vocabulary_fr_filter_restart_20261125/completion.json.
Doplněná izolace staršího testu katalogu od živého Tailscale statusu.
Fyzická přejímka a provedení schválené publikace tohoto kroku otevřené.
<!-- SAMANTHA_CURRENT_STATUS_END -->

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

## 2026-11-25 13:08 CET — Změna filtru bez ztráty společné místnosti

Hotovo: Zakladatel rozehrané i dokončené partie má přímo ve společné
místnosti „Změnit filtr a začít znovu“. Volí okruh, slovní druh, obtížnost,
typ výrazu, posledních20/50 nebo hledání FR/CZ. Náhled12 dvojic lze zrušit
návratem do původní hry. Potvrzení rozehrané hry výslovně vynuluje skóre,
vymění24 karet a zachová místnost, jména, přístupy i původní pozvánku.
Druhý hráč dostane nové kolo synchronizací; sám filtr měnit nemůže.

Rozhodnutí: Míla požádal o změnu filtru u zakladatele bez dalšího posílání
odkazu i před dohráním. Stávající rematch po dokončení zůstává. Nová akce
restart používá12 veřejných UID, žádný osobní seznam se neposílá.
Míla následně výslovně zadal p+n i spuštění aktualizovaného serveru.
Dřívější Tailscale aktivace be9aeaa8 běží podle živého čtecího statusu;
tento nový krok nemění síť, LaunchAgent ani běžící export.

Další krok: Dokončit výslovně zadané p+n přes Terru a připravit přesný
plán aktualizace samostatné herní služby se zachováním databáze. Pages samotné server
restart nerozšíří; současná živá verze stále be9aeaa8 tuto akci neumí.
Navrhované další kroky: Na Janině a Mílově Macu ověřit zrušení filtru,
potvrzený restart uprostřed hry a další partii bez nového odkazu.

Technický důkaz:23 cílených Python kontrol včetně23 JS scénářů PASS před
finální programovou bránou; doplněný HTTP test dvou přístupů a nové routy.
Testy drží idempotenci po obnově databáze, host-only, chybné výběry,
staré kolo/poslech, zrušení bez leave a ukončení starého odměnového zvuku.
Finální brána a commit: private vocabulary_fr_filter_restart_20261125/completion.json.
Doplněná izolace staršího testu katalogu od živého Tailscale statusu.
Fyzická přejímka a provedení schválené publikace tohoto kroku otevřené.


## 2026-11-26 16:23 CET — Poslechový duel vydaný

### Hotovo

Poslechový duel je vydaný na veřejném webu Francouzština Jana i v soukromé
herní službě. První dvě sekundy výběru ukazují francouzský text a poslední
sekundu obrázek s textem. Pexeso i původní místnosti zůstaly zachované.

### Rozhodnutí

Dokončeno dříve schválené vydání a aktualizace stejné herní služby.
Zůstává stávající databáze, soukromá adresa a síťové oprávnění.

### Další krok

Míla a Jana obnoví Francouzštinu, otevřou Pexeso → Poslechový duel na dálku
a ověří zobrazení, časování a skutečně slyšitelný zvuk na obou Macích.

### Navrhované další kroky

- Vyzkoušet novou partii a změnu filtru bez nové pozvánky.
- Ověřit návrat do stejné místnosti po přerušení spojení.

### Technický důkaz

Vydaný kód 42f75f44 obsahuje celý duel i úpravu dvou sekund textu a jedné
sekundy obrázku. Registrované Pages vydání je potvrzené, validační účtenka
67 kontrol převzatá; deployment8089183408 a workflow45847718140.
Herní služba má stejný head a hlásí podporu pairs i duel. SQLite záloha
má ověřenou integritu a všech7 původních místností zachovalo přístupy,
pozvánky a expiraci. Přes skutečné HTTPS souhlasí17 soukromých klientských
souborů a5 veřejných souborů. Dva syntetičtí hráči dokončili první kolo,
ověřili skóre a přechod na další otázku; MP3 Range vrátil206. Jedna
oddělená QA místnost zůstává do běžného vypršení. Fyzická přejímka a
slyšitelný zvuk na Janině Macu nejsou touto kontrolou potvrzené.
Autorita provozního stavu: data/private/vocabulary_fr_duel_current_release_20261126/.

## 2026-11-26 — Převzetí vydání nastavitelného časování duelu

Převzat původní checkpoint `d950b94b`: zakladatel mění text 2/3/4 s a obrázek
1/2 s během partie, společně pro oba hráče a od následující otázky. Při
opakování přerušené otázky se nyní zachová její zmrazené časování včetně
starších uložených místností. Důkaz: 42 serverových testů PASS; klientské
hranice všech šesti kombinací a skutečné HTTP zahrnuje programová brána.
Vydání webu přes Terru a aktualizace soukromé služby se připravují; dosavadní
nasazení `42f75f44` ještě nemá nastavení časů. Databáze i pozvánky se zachovají.
Nová aktivace LaunchAgentu vyžaduje přesnou globální brzdu pro konkrétní plán.
Fyzický poslech na Janině Macu zůstává samostatnou přejímkou.
Účtenky: `data/private/vocabulary_fr_duel_timing_20261126/` (mimo Git).

## 2026-11-26 — Časování poslechového duelu vydané


### Hotovo
- Poslechový duel má nastavitelné časy: text 2/3/4 s, obrázek 1/2 s.
- Nastavení mění zakladatel i během hry; platí pro oba hráče od další otázky.
- Přerušená otázka se opakuje s původními časy, včetně starších místností.
- Web i soukromá služba byly vydané a živě ověřené na kódu `de271467`.

### Důkaz
- Programová brána: 257 PASS, receipt `4d1b3ae1f405aca4831cabbbcfde2c21e0163b7813b370951affe447237f6c85`.
- Terra Pages job `c3934866d228faabdd4195bdf380df9f`, deployment `8095444938`, completed.
- HTTPS dva hráči: 4 + 2 s, host-only, změna během otázky zachová limit,
  další otázka 2 + 1 s, skóre 1:1, audio Range 206.
- 17/17 klientských souborů odpovídá commitu na Pages i soukromé službě.
- Zachováno 13 původních místností, přístupy a pozvánky; konzistentní záloha SQLite integrity OK.
- Podrobné soukromé účtenky: `data/private/vocabulary_fr_duel_timing_20261126/completion.json`.

### Otevřeno a rizika
- Fyzický poslech a ovládání na Janině a Mílově zařízení ještě nebyly ověřené.
- Závěrečný dokumentační commit se vydává samostatně; nemění herní kód služby.

### Další krok
- U obou hráčů obnovit stránku, zakladatel nastaví 4 + 2 s a společně ověřit jednu otázku.
- Další partii nebo filtr lze dál měnit bez nové pozvánky.

## 2026-11-27 — Automatické obnovení poslechového duelu

Míla schválil robustnější připojení a následné p+n. Klient zachytí výpadek,
ukáže stav a přihlásí stejnou session přes ready po 1/2/4/8 s, dále po 8 s;
online a návrat viditelného panelu pokus urychlí. Opuštění hry ruší časovače
včetně pozdních odpovědí; 403/404/410 a nekompatibilní katalog pokusy ukončí.
Nikdy se automaticky neopakuje create/join/answer/restart/next/timing.
Uložený stav se načte ze serveru, vyhodnocené skóre zůstává; přerušená otázka
se podle existujícího serverového protokolu zopakuje se zmrazenými časy.
Pokud prohlížeč blokuje automatický zvuk, zůstává výslovné zapnutí/opakování.
Potvrzení poslechu čeká na uvolnění právě probíhajícího požadavku a ověřuje se
serverovým stavem, místo aby jej sending=true zahodilo.

Důkaz: 54 klientských testů PASS včetně nově 8 regresí, 6 celých her /72 otázek,
backoff, viditelnosti, online, vypršení, ztracených odpovědí a souběhu timing/ACK.
Nasazené původní soubory byly před změnou shodné na Pages i soukromé službě.
Přesnou příčinu včerejší uživatelské partie nelze z uloženého stavu prokázat.
Programová brána a finální vydání se dokončují; aktuální účtenky jsou v private
`vocabulary_fr_duel_recovery_20261127/completion.json`. Databáze a pozvánky se
nemění; aktualizace privátního exportu vyžaduje konkrétní potvrzený plán služby.
Fyzická přejímka dvou Maců včetně zvuku zůstává otevřená.

## 2026-11-27 — Automatické obnovení duelu vydané a ověřené

Kód e3968858 vydaný přes Terru (job1d26cf7f871d8169a28c0ba2e6c7bba6) a po přesném
potvrzení aktivovaný v privátní službě. 54 JS, doménové brány199 a145 PASS;
dva klienti se skutečným serverem ověřili návrat po výpadku a ztraceném ACK,
skóre1:1, další otázku a žádnou duplicitní odpověď. Po aktivaci17/17 souborů
na obou původech shodných, všech17 původních místností a přístupů zachovaných,
SQLite integrity OK, audioRange206. Skutečné Mac GUI/zvuk zůstává k přejímce.
Aktuální účtenka: data/private/vocabulary_fr_duel_recovery_20261127/completion.json.


## 27.11.2026 — Příprava obsahového doplnění před La phrase éclair

Míla schválil372 herních vět a nejprve zadal nové karty, věty a MP3 do Janiny
sdílené VocabularyFR, potom do webu. Živý iCloud má469 řádků; web481 karet.
Připraveno42 nových karet s příkladem, navíc17 dosavadních webových karet pro
iCloud: plán528 zdrojových řádků /523 webových karet. Všechna původní data
a osobní příznaky mají zůstat zachovaná. Živé datové soubory zatím nezměněné.

Připravená volitelná podpora MP3 pro desktop s přesným textem, FR/CZ kanálem,
SHA kontrolou a návratem k dosavadnímu say při chybě. Builder přibaluje modul;
11 cílených testů PASS. App zatím není sestavená ani instalovaná. Herní vývoj,
publikace a placená výroba nezačaly. Audio nových karet:165 nových MP3,
7639 znaků, odhad0,115 USD bez daně; čeká potvrzení stropu0,20 USD a rozsahu.
Volitelně včetně372 herních vět:531 nových MP3,28306 znaků, odhad0,425 USD,
navržený strop0,50 USD. Nejistá výroba se nikdy automaticky neopakuje.

Důkaz a pokračování: reports/vocabulary_fr_content_additions_20261127.md;
privátní vocabulary_fr_content_additions_20261127 obsahuje přesné karty,
návrh CSV, živé výchozí SHA, retail sazbu a oba rozsahy audia. Cílenou bránu,
commit a aktuální stav určuje completion.json. Po cenovém potvrzení dokončit
média, aktualizovat iCloud přes zálohu/SHA kontrolu, ověřit bundle a upload,
pak stejný webový přírůstek. Fyzická Janina přejímka se nepředstírá.

## 27.11.2026 — Nové karty a média vyrobené, iCloud instalace a místní web

Míla schválil výrobu všeho včetně372 herních vět a strop0,50 USD bez daně.
Vyrobeno531 MP3,28305 účtovaných znaků, odhad0,424575 USD; žádný automatický
opakovaný požadavek.11 ilustrací vytvořených a zkontrolovaných. Nová hra se
neimplementovala;372 vět se zvukem je neveřejná příprava LaPhraseEclair.

Janin iCloud CSV469→528: všech469 původních řádků/vět/L/HT zachovaných,
přidáno17 starších webových karet a42 nových. Nová .app, Audio a Pictures
instalované; stará .app/CSV v datované záloze. Reálný bundle check528/107
slovesných obrázků/recall a podpis PASS. Všech168 nových zvukových referencí
a59 přesných dvojic obrázek/význam dohledatelných; bez anglického the pro thé.
Mílovo FR477 i IT471 hashově beze změny;1175 mapování v obou Pict shodně,
39 nových klíčů, žádná původní vazba přepsaná. Sdílený audit0 chybějících.

Web je místně523 karet /2092 zvukových referencí /1206 obrazových vazeb.
Všech481 předchozích karet zachováno; reálný klient523 čtyřmožnostních otázek
PASS,248 HTTP souborů přesně. Zdrojová v006 uzavřená; pracovní data a herní
odpovědi zůstávají mimo docs/Git. Není to publikace ani upgrade herní služby.

iCloud upload dokončený:2743 použitelných položek uploaded=true,0 uploading,
0 chyb; celý .app balíček ověřen zvlášť. Vnitřní binární soubor má samostatná
metadata nil a kryje ho potvrzený balíček. Úvodní chyba4355 odezněla bez zásahu
do účtu/DNS/služeb a bez nového kopírování. Důkaz icloud-upload-confirmed.json.
Fyzické spuštění na Janině Macu se tím nepotvrzuje.
Browser access host nebyl dostupný; lidský poslech na Janině Macu čeká.
12 cílených mediálních testů a6 kanonických mapping testů PASS; programovou
bránu/commit/pending count dokládá completion.json stejného privátního kořene.

Další krok: po výslovném p+n
vydat web registrovanou cestou a připravit přesný upgrade soukromého herního
serveru se zachováním místností/SQLite a jeho systémovými oprávněními.
Handoff rozlišuje místní dokončení, cloudové doručení a veřejné vydání.
Podrobně reports/vocabulary_fr_content_additions_20261127.md; privátní důkazy
vocabulary_fr_content_additions_20261127/{current-bundle,completion}.json.

## 27.11.2026 — P+n523 a kompatibilní přechod existujících místností

Míla zadal p+n a aktualizaci herní služby. Původní předání567563bef skončilo
před potvrzením push; původní worker i transport jsou ukončené a GitHub
zůstává0068a369. Není provedena publikace ani aktivace plánu v1.

Připravená úzká oprava: kontroluje totožnost všech481 původních významů a
quiz metadat před rozšířením523. Po zastavení služby a SQLite záloze převede
v jedné transakci pouze verzi katalogu; ostatní stav/přístupy/skóre/pozvánky
zůstanou stejné. Skutečná kopie17 původních místností a2 rozehraných QA her
PASS, v obou režimech fungují původní tokeny i pozvánka. Živá DB se neměnila.
6 mediálních testů je zachovaných v již registrované FR obsahové sadě, bez
nové validační domény/registru.63 content/tailnet a60 release testů PASS.

Další krok: programová brána/commit, nové registrované vydání opraveného
balíčku a po přesné globální větě aktivace nového plánu s migrací. Konečný
stav, SHA a všechny účtenky určuje privátní
vocabulary_fr_content_release_20261127/completion.json; zdrojové médium v006
zůstává beze změny. Podrobně reports/vocabulary_fr_content_release_20261127.md.


## 2026-11-27 18:16 CET — Slovník523 a herní služba společně aktualizované

Hotovo: Jana má nová slovíčka, věty, obrázky a MP3 ve webu i soukromých hrách.
Stejná adresa a všechny původní17 místnosti zachovávají pozvánky, přístupy,
skóre i rozehraný stav. Ověřené dva HTTPS klienty v Pexesu i duelu s12 novými slovy.

Rozhodnutí: Míla potvrdil přesnou globální brzdu pro připravený plán v2;
aktivace provedena jednou z f6d16ded. Žádné nové architektonické rozhodnutí.

Další krok: oba hráči obnoví stránku a provedou společnou fyzickou přejímku zvuku.
Navrhované další kroky: navázat na již dohodnutou přípravu nové hry LaPhraseEclair.

Technický důkaz: Pages workflow46038924063 a deployment8115378758 potvrzené;
265 souborů přesně na obou adresách, MP3 Range206. SQLite integrity OK;
porovnání se skutečnou zálohou dokládá pouze změnu catalog u17 místností.
Finální služba running f6d16ded,523 karet. Účtenky zůstávají soukromé v
vocabulary_fr_content_release_20261127/completion.json; původní release
attention zachovaná, úspěch původního workflow nezávisle potvrzen bez retry.
Fyzická dvě zařízení a poslech nejsou nahrazené automatickým ověřením.


## 2026-11-27 18:59 CET — La phrase éclair, první místní implementace

Hotovo: Samostatná hra pro dva s372 větami, dvěma nezávislými volbami,
serverovým skóre, přípravou2s, volitelným časem, potvrzením obou mezi koly,
francouzským vzorem a obnovením stejného přístupu. Vstup přímo z hlavní
navigace i od Pexesa. Všechny předem vyrobené zvuky a použité obrázky zapojené.

Rozhodnutí: Míla výslovně zadal vývoj první verze ze schválených372 vět.
Zůstává stejný backend, pozvánky a autentizace. Klíč odpovědí se nepodává jako
veřejný JSON; soukromý export nově připíná obsahový manifest do plánu aktivace.

Další krok: Samostatné p+n a aktualizace herní služby s private approved-v1.
Navrhované další kroky: Fyzická společná přejímka dvou Maců včetně zvuku.

Technický důkaz: dva klienty proti skutečnému HTTP enginu dokončily20 kol;
chyby, duplicity, deadline, skóre, handshake, ztracená odpověď a opakované audio
jsou kryté regresními scénáři. Skutečný korpus372/62/494 a všech550 médií
ověřený; další dvě reálné datové HTTP relace získaly2:2 a pokračovaly ve stejné
místnosti. Pexeso i duel funkční. Finální brána/SHA jsou v soukromé účtence
la_phrase_eclair_implementation_20261127/completion.json; nativní browser
nedostupný, fyzická přejímka otevřená. Produkční služba vývojem neměněná.


## 2026-11-27 19:01 CET — Práce přerušená na výslovné přání Míly

Nazev: La phrase éclair — dokončení první implementace
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-11-27 19:01 CET

Co se resilo: Nový režim podle schváleného zadání a372 vět.
Co je hotove: Herní server, soukromý runtime korpus approved-v1, UI a vstup
z hlavní navigace, audio a reconnect. Poslední klientská sada9 Node scénářů
proti skutečnému HTTP serveru PASS;20kolová partie a obnova, celkem původní
backendová integrační regrese142 PASS před závěrečnými doplněními. Skutečný
372-kolový korpus,550 médií a2 datové HTTP relace2:2/2.kolo ověřené.
Nový test pin manifestu PASS. Celé aktuální vstupy ještě nemají finální účtenku.
Co neni hotove: Finální programová validační brána byla na přání Míly zastavená.
Změny nejsou commitnuté, pushnuté ani nasazené. Browser host nedostupný;
fyzické UI/poslech na dvou Macích čekají. Běžící produkční služba f6d16ded zachovaná.
Dalsi krok: Po Mílově pokynu obnovit práci kontrolou git status a tohoto zápisu;
spustit scripts/validation_gate.py bez --full, opravit případné skutečné chyby,
zkontrolovat diff, vytvořit lokální commit a zarovnat pouze čisté profily.
Navrhovane dalsi kroky: Samostatné p+n a aktivace hry s privátním korpusem;
poté společná fyzická přejímka obou Maců a zvuku.
Zmenene nebo relevantni soubory: vocabulary_fr_multiplayer.py,
vocabulary_fr_cloud.py, vocabulary_fr_tailnet.py, VocabularyFR/vocabulary_fr_eclair.py,
docs/vocabulary-fr/eclair.html/.js/.css, index.html, memory.js, FR testy
včetně test_vocabularyfr_eclair.js a fixtures/vocabulary_fr_eclair_browser.js.
Podrobnosti: reports/la_phrase_eclair_implementation_20261127.md a soukromé
la_phrase_eclair_implementation_20261127/completion.json. Runtime korpus:
data/private/vocabulary-fr-eclair/approved-v1; zdroj v006 už se znovu nevyrábí.
Bezpecnost / neukladat: Klíč odpovědí, tokeny a soukromá data nepatří do Git/docs.
Nespouštět publikaci ani restart jen při obnově. Vývoj zůstává pozastavený,
dokud Míla nepožádá pokračovat. Žádný nový placený požadavek.


## 2026-11-27 20:19 CET — Obnovení a dokončení La phrase éclair

Hotovo: Míla obnovil vývoj z uloženého checkpointu. Implementace, soukromý
372-kolový korpus a dosavadní důkazy zůstaly zachované. Doplněné ověření
nejistého založení po reloadu používá původní identitu i nastavení; ovládání
jasně ukazuje Ověřit původní vstup a zabraňuje změně původního požadavku.

Rozhodnutí: Pokračovat závěrečným ověřením a lokálním commitem. Samostatné
publikování a změna běžící herní služby zatím nejsou součástí tohoto dokončení.

Další krok: Po úspěšné programové bráně připravit samostatně autorizované p+n
nové hry a aktualizaci služby s privátním balíčkem; pak přejímka dvou Maců.
Navrhovane dalsi kroky: Fyzické vykreslení úzkého okna a poslech obou klientů.
Pripomenout pri startu: ne

Technický důkaz: Závěrečné přesné vstupy/brána/SHA a počet čekajících commitů
jsou v la_phrase_eclair_implementation_20261127/completion.json. Obnova
neopakuje výrobu médií a neaktivuje službu. Původní přerušení zůstává historické.

Závěrečná kontrola rozložení doplnila kompaktní herní režim pro notebooky:
při hře se schová hotová pozvánka a úvodní popis, zmenší se svislé mezery
a při nižším desktopovém okně výška karet. Oba sloupce zůstávají vedle sebe;
telefon zachovává větší dotykové plochy. Fyzické vykreslení zůstává k přejímce.
