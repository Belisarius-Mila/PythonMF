<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Aktualizováno: 2026-11-16 08:33 CET
- Webová aplikace497 karet/1907 MP3 vydaná na Pages v a53c1757; index nyní HTTP200 a přesný.
- V živém Cockpitu zůstává stará desktopová položka. Nové přepojení katalogu místně připravené.
- Položka Vocabulary IT vede na veřejnou galerii; ID vocabulary-it-trainer zachované.
- Pro promítnutí této nové opravy do běžícího Cockpitu zbývá samostatně schválené p+n.
- Dále obrázková hra, telefonní přejímka a úplná jazyková revize.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Vocabulary IT

Nazev: Vocabulary IT
Pracovni proud: project-vocabulary-it
Typ: Project
Priorita: 2
Stav: rozpracovane — web vydany, katalogove prepojeni mistne pripravene
Pripomenout pri startu: ne
Datum: 2026-11-16 08:33 CET

Co se resilo:
Přepojení Vocabulary IT z desktopové položky na novou webovou galerii.

Co je hotove:
- Webová galerie a IT/CZ audio jsou zveřejněné; index ověřený HTTP200 a SHA.
- Místní katalog má veřejnou adresu a název Vocabulary IT, stabilní ID zachované.

Co neni hotove:
- Nasazení této nové katalogové opravy do Cockpitu čeká na samostatné p+n.
- Obrázková hra, úplná jazyková revize a telefonní přejímka.

Dalsi krok:
Samostatně schválit p+n nové katalogové opravy.

Navrhovane dalsi kroky:
- Prubezne aktualizovat pouze potvrzenymi checkpointy tohoto proudu.

Zmenene nebo relevantni soubory:
- Viz jednotlive checkpointy.

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice ani soukromy obsah.

### Automatický checkpoint 2026-08-04 19:15 CEST

- Pracovní proud: `project-vocabulary-it`
- Hotovo: AppIT nabízí vzájemně výlučné volby posledních 20 nebo 50 slovíček a návrat k celému výběru
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Poslední ověřené nasazení patří jinému commitu než main před tímto checkpointem.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: rychlá Cockpit brána syntaxe a whitespace: 8.2 s, výsledek OK; cílené testy potvrdila dokončovací účtenka vývojového tahu
- Změněné cesty před paměťovým zápisem (1): `MBSoft/AppIT.py`
- Commit: `Add Last 20 and 50 filters to AppIT`
- Další krok: V Pythonistě krátce ověřit tlačítka 20, 50 a jejich vypnutí

### Auditní dorovnání 2026-08-07 14:07 CEST

- Hotovo: Míla potvrdil funkční Last 20/50 v AppIT i funkční lokální VocabularyIT z Cockpitu.
- Rozhodnutí: Původní pokyn k ručnímu testu je splněný; proud je nyní pozastavený.
- Další krok: Až vznikne nový požadavek, zachovat stejný kontrakt Last 20/50/HT jako ve FR aplikacích a zopakovat společný audit dat.
- Navrhované další kroky: Bez nového věcného požadavku nic dalšího neměnit.
- Technický důkaz: Commity `b2355b7` a `ae67bea`; následné potvrzení Míly v reálném používání.

### 2026-09-13 10:12 CEST – Slovíčka a ilustrace z NewWords.txt

Hotovo:
- Doplněno 8 IT položek z NewWords.txt; celkem 471 slovíček.
- Již existující hesla bez duplicit; usi má i infinitiv usare,
  vinti příklad ve správném množném čísle, quelle ukazovací význam.
- Dříve potvrzené Last 20/50/HT a lokální Tk spuštění zůstávají beze změny.
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


### 2026-11-15 20:54 CET — Schválený webový port: bod1, identity a zmrazené vstupy

Hotovo: Na konec původní analýzy v Downloads je připsaný podrobný osmibodový
plán, původní text včetně Mílových SOUHLAS zachovaný. Místně založený katalog
všech471 původních významů s trvalými vit-0001–0471 a návrhy18 témat, slovních
druhů, typu učiva a tří vlastních stupňů obtížnosti. Všech471 zůstává aktivních.
Soukromý uzavřený snímek777 vstupních souborů včetně761 plně dekódovaných obrazů,
celkem121703729 bajtů; kanonické i zmrazené vstupy prošly přesnou kontrolou.
Připravená konkrétní prioritní fronta112 karet, nikoli112 prokázaných chyb.

Rozhodnutí: Míla schválil analýzu, doplnění plánu a zahájení prvního bodu.
Prázdné IT profily A–D, hotový poslech slov i vět, časování samostatně později.
ID byla přidělená jednou; další čtení používá přesnou NFC IT/CZ dvojici a
výslovné aliasy, nikoli Order. Zachované odlišné významy a konkrétní tvary.
Nová metadata jsou proposals/needs-review, žádné tvrzení o ověřeném CEFR.

Další krok: Bod2 — redakční revize významů a přesné obrazové vazby podle
vět, začít16 rozpory resolverů a piacere/perché/stare, potom tvary a rody.

Navrhované další kroky: Bezpečný export s miniaturami; vlastní IT galerie
a profily; samostatně odsouhlasený zvukový vzorek a knihovna; přejímka/p+n
podle celého plánu. Žádný modelový pomocník ani zvuková výroba nyní neběží.

Technický důkaz:30 cílených testů včetně nových identit a validační domény PASS.
Reverzní pořadí i jiné Order zachovají471 UID; neznámá/dvojitá identita selže,
diakritika a case se neslévají. CSV, rody, L/HT, mapping, obrázky a EN předloha
zůstaly bajtově zachované. Navržených460 Slovíček a11 Interakcí; žádný idiom
a žádné rozdělení/skrytí nyní. Obrázkové vazby všech471 pending-review.
Soukromé důkazy vocabulary_it_foundation_20261115, finální programová brána
v gate.json/gate.log. Worktree má745 obrazů; chybějících16 je bezpečně v úplném
snímku. Vlastní lokální brána se porovnává proti společnému77b5f652, protože
origin mezitím pokročil Willovými bcc548fe/0f059c3e; žádný merge/rebase/push
ani zásah do souběžného main. Nová webová aplikace ani IT audio dosud nejsou
implementované/nasazené. Původní CSV a původní desktop/Pythonista fungují dál.


### 2026-11-15 21:29 CET — Bod2: obrazová revize a návrh významových karet

Hotovo: Prohlédnuto všech471 karet v obrazovém přehledu a cíleně porovnány
sporné ilustrace včetně16 rozdílů resolverů.458 karet má přesnou cestu/case
k383 zdrojovým souborům s SHA;10 konkrétních ilustrací potřebuje náhradu,
u storia/gli/niente předchází významové rozhodnutí. U abstraktních slov je
obraz kontext nebo pomůcka, nikoli záruka jednoznačné odpovědi ve hře.
Do Downloads uložen čitelný návrh24 významových úprav, věty a další významy.
Webový katalog opravuje francouzskou větu u éclair a chybný jmenovat se
u chiamare; původní CSV i alias a vit-0211 zůstávají zachované.

Rozhodnutí: Žádné nové obsahové rozhodnutí od Míly dosud nepřišlo. Návrh
hlavního významu a dalších samostatných karet je výslovně nepoužitý, nepřiděluje
nové UID. Žádné skrytí/smazání ani rozdělení původních471 karet neproběhlo.
Bod2 není uzavřená jazyková korektura všech vět a metadat.

Další krok: Rozhodnout konkrétní významový návrh v Vocabulary_IT_revize_vyznamu_a_obrazku_2026-11-15.txt
(Downloads); poté doplnit10 obrazů a tři významově závislé vazby.

Navrhované další kroky: Export a miniatury; samostatná IT galerie/profily;
odsouhlasený vzorek audio a následné knihovny; přejímka a samostatné p+n.

Technický důkaz: Čtecí audit777/777 původních souborů a471/471 identit PASS,
458 vazeb/383 souborů přesné, complete=false pro13 nehotových karet.
Testy ověřují změněný hash/case, chybějící/vnější cestu, nepřesný manifest,
odmítnutí neúplné obrazové sady a zastaralé opravy zdrojové věty.
Finální doménová brána a otisky zdrojů jsou private/vocabulary_it_review_20261115.
Úplný snímek z bodu1 zůstává neměnný; původní zdroje ani EN se nepřepisují.
Bez nového audio/obrazového generování, push nebo nasazení. Lokální ověření
proti společnému77b5f652; souběžný main a Willova aktivace Human–Adam nedotčené.


### 2026-11-15 21:51 CET — Schválené významy, nové ilustrace a bezpečný export

Hotovo: Schválených24 hlavních významů je zapracovaných a26 dalších významů
má vlastní kartu/větu, vit-0472–0497. Web497 aktivních karet, starý slovník
zůstává471 řádků. Zachované původní identifikační aliasy; gli jako člen a
niente jako nic nepřevzaly cizí reakci/zájmeno. Běžná slovesná spojení jako
avere ragione zůstávají Slovíčky, Forza/Pronto/Congratulazioni jsou Interakce.
Existující487 vazeb/397 souborů přesně připnutých; další10 obrazů hotových
jako pracovní kandidáti ve PictNew/generated/20261115_it_web_review.
Samostatný HTML přehled10 obrázků je i v Downloads, vložené obrázky fungují
bez závislosti na jiném místním adresáři. Nový exportér vytváří JSON v2,
obrázky do900px a miniatury do240px. Skutečný náhled497 karet/814 assetů.

Rozhodnutí: Míla „Se vším souhlasím, pokračuj…“ schválil významové návrhy
a pokračování. Nové významy se přidávají jen do webového katalogu, původní
CSV se nemigruje. Nové ilustrace byly technicky i obrazově zkontrolované
Adamem; přejímku Mílou tím nenahrazujeme. Kandidátní sada se nedostává do
sdíleného Pict ani mappingu. Původní obrazové knihovny a staré IT/EN výstupy
zůstávají zachované. Datum přidání mají jen26 skutečně nových webových karet.
Obtížnost je vlastní návrh, nikoli CEFR; zbývající stará metadata nejsou plně revidovaná.

Další krok: Míla vizuálně přijme připravenou desetici v
Vocabulary_IT_kontrola_10_obrazku_2026-11-15.html (Downloads); potom dokončit
obrazové vazby a vlastní IT galerii (bod4). Kopírování do sdíleného Pict má
podle vocabulary_image_generation_workflow.md předcházet vizuální schválení.

Navrhované další kroky: Vlastní IT galerie s návratem na kartu a filtry;
oddělené profily A–D; samostatně schválený zvukový vzorek/slova/věty;
italská hra a pozdější samostatně autorizované vydání.

Technický důkaz: Cílené katalogové/exportní/doménové testy ověřují zachování
471 UID/CSV/rodů/L/HT,26 webových významů, odmítnutí změněných dat/case/hash,
změny během konverze, zákaz kandidáta ve finálním režimu, bezpečné cesty,
neměnné assety a přepnutí JSON až nakonec včetně simulace přerušení.
Celý náhled a technická přejímka souborů jsou private/vocabulary_it_export_20261115;
finální programová brána v gate.json/gate.log. Plná sada nezadaná.
Soukromý původní snímek777 vstupů je beze změny. Vestavěný image_gen,10/10,
max103360 bajtů/kandidát; prompty a SHA jsou v generation_report.json.
Není hotová nová galerie, profily, audio ani vydání. Lokální brána proti
společnému77b5f652, žádná automatická integrace souběžného main.


### 2026-11-15 22:20 CET — Přijaté ilustrace, IT galerie a vlastní výběry

Hotovo: Míla přijal desetici „Přijímám, bezchybné…“. Nové obrazy se zkopírovaly
bez přepsání existujících pod10 novými názvy do Pict; mapping beze změny.
Všech497 aktivních karet má hotový obraz,407 unikátních zdrojů. Původní
uzavřený snímek777 souborů zůstal nezměněný, nová úplná pracovní projekce
má navíc právě10 přijatých obrazů. Export v2 je nyní finální datový režim,
imageReviewComplete=true; nejde o potvrzení hotového zvuku nebo publikace.

Místně vznikla samostatná docs/vocabulary-it/ podle osvědčeného EN rozhraní:
Téma jako základ,18 okruhů, dvě dlaždice na mobilu/až osm na šířku, IT/CZ
popisky, hledání a další filtry. Posledních N jde přes celý slovník a pak
se protíná s osobním a tematickým výběrem. Větší karta Slovíčko/Věta v obou
směrech a rod u podstatných jmen, Další podle galerie, náhodně výslovně,
historie/reload a návrat na právě procvičovanou dlaždici.

Převzatý osobní modul je oddělený pro IT: prázdné A–D, vlastní výběr a obtížná
slova, PIN, jazykově označená záloha bez PINů. Import mění jen odemčeného
uživatele a jeho zdejší PIN i ostatní profily zachovává. EN zálohy/ven UID
jsou odmítnuté, EN localStorage nedotčený. Žádná migrace původních L/HT.
Zvuk má vlastní IT UID/textové smlouvy a adresáře; současné manifesty
obsahují status=not-generated a nula nahrávek. UI to přiznává, nevytváří hlas
prohlížečem a nespouští cizojazyčný fallback. Obrázková hra zatím není zapnutá.

Rozhodnutí: Mílovo přijetí pokrývá10 konkrétních ilustrací. Vývoj pokračuje
podle již schváleného plánu, bod4 a navazující5 jsou místně implementované.
Původní EN soubory a starý IT web se nemění. Žádné povolení k p+n nevzniklo.
Novou hlasovou knihovnu budeme vyrábět až po konkrétním schválení zvukové etapy.

Další krok: Fyzicky projít galerii na Macu a úzkém displeji podle krátkého
TXT v Downloads. CUA skončilo chybou browser access host is unavailable;
automatické DOM testy a HTTP200 tuto vizuální přejímku nenahrazují.

Navrhované další kroky: Malý IT vzorek hlasu/slov i vět; celé vlastní audio
IT/CZ; italská obrázková hra; samostatná registrace publikačního cíle a p+n.

Technický důkaz:15 scénářů skutečného JS galerie a profilů PASS (node DOM
harness):497 karet, filtry/N, věty/směry/rod, Další/návrat, historie/reload,
chybějící zvuk, česká1s nápověda s testovým zvukem, blokované úložiště,
PIN/CAS, oddělení EN a skutečný import jen jednoho profilu. Čtecí audit
777 původních +10 nových připnutých,497 UID a obrazových vazeb PASS.
814 webových souborů ověřených podle case/SHA/dekódování/rozměrů; celá sada
miniatur4968584 B, plné obrazy34034462 B. Prohlížeč načítá miniatury lazy,
plný obraz až po otevření karty. HTTP stránka, moduly/data a zkoušený obraz200.
Finální programová brána a shoda zdrojů jsou private/vocabulary_it_gallery_20261115.
Lokální ověření proti společnému77b5f652, žádný merge/rebase/push souběžného main.
Fyzický Safari/iPhone/Android proklik a poslech nejsou tímto milníkem přijaté.


### 2026-11-15 23:08 CET — Italský hlas a úplná knihovna slov i vět

Hotovo: Všech497 aktivních karet má hotové nahrávky slovíčka i příkladové
věty v italštině a češtině.1988 vazeb používá1907 unikátních MP3 (26920656 B).
Italský hlas Elsa, český Vlasta, rychlost-10 %. Poslech v galerii přehraje
italské slovo a krátce ukáže češtinu; větší karta přehrává slovo nebo celou
větu v právě zvoleném směru. Hotová knihovna přežije nový export dat.

Rozhodnutí: Míla schválil pokračování „italský hlas a zvuková knihovna…“
a potvrdil, že nemá jinou hlasovou preferenci. Použit stávající registrovaný
Edge generátor; žádné nové placené Azure volání. Původní EN ani CSV/mapping
se nemění. Souhlas s vývojem není p+n.

Další krok: Italská obrázková hra podle bodu7 schváleného plánu.

Navrhované další kroky: Přesná revize italských obrazových kolizí pro hru;
telefonní poslech/přejímka; samostatně registrovaný publikační cíl a vydání.

Technický důkaz:1907/1907 souborů má přesnou SHA, kladnou délku, MP3 codec,
plné dekódování a netichý signál. 1801 nových nahrávek, 106 přesně
shodných českých převzatých z EN do vlastní IT knihovny. Manifesty mají
status=complete,497 UID každý, přesné zdrojové texty a oddělené word/sentence
cesty.10 audio testů bez online syntézy a16 JS scénářů v doménové bráně:
nejistá žádost blokuje opakování, souběh drží zámek, před každým novým
voláním se kontrolují zdroje a veřejný index vzniká až po úplné kontrole.
Fyzický Safari na Macu: galerie,2/4/6 sloupců při100 %,8 při zmenšení,
věta/odhalení/Další/návrat, posledních20 a reload; reálné MP3 přehrávání
slova IT a věty IT/CZ s modrou ikonou přehrávání Safari, CZ nápověda a návrat
italského popisku. Veškeré audio nebylo ručně poslechnuto; jazyková korektura
všech vět/metadat a skutečný iPhone/Android zůstávají otevřené.
Původní browser bridge je nedostupný, nativní Safari CUA funguje. Vlastní QA
okno a lokální server po testu uzavřené. Fyzický profil/PIN se neměnil.
Finální programová brána a shoda zdrojů: private/vocabulary_it_audio_20261115.
Lokální checkpoint proti společnému77b5f652; žádný push, nasazení ani zásah
do divergentního main/Willovy práce.


## 2026-11-16 00:31 CET — Schválená integrace a vydání Datovy Vocabulary IT

Hotovo: Připraven společný balíček HA-09 a šesti hotových Datových commitů
bbda9145,52ee1517,aebde8bf,22835377,a431fdea,cac18b4d. Obsah IT:497 karet,
přijaté ilustrace, galerie/profily a1988 zvukových vazeb/1907 MP3. Obrázková
hra není součástí této dávky. EN commit pouze doplňuje již ověřený doklad.
Registrace váže project-vocabulary-it na společný Pages publisher a přesnou
cestu vocabulary-it/ v katalogu, vykonavateli i allowlistu HTTP smoke.
Rozhodnutí: Míla výslovně zadal p+n Datových commitů. Zveřejní se připravená
galerie se zvukem; nejdřív společný Cockpit (HA-09/registrace), potom Pages
Vocabulary IT na totožném headu. Data worktree se nepřepisuje ani nesynchronizuje.
Konflikt ACTIVE_PROJECTS obsahoval jen starý IT souhrn; převzat aktuální
Datův stav, ostatní novější main a HA-09 zachované. Žádná plná brána.
Další krok: Programové cílené ověření celého balíčku, integrační commit,
zarovnání čistých profilů a registrované submit_release(wait=True) obou cílů.
Navrhované další kroky: Telefonní poslech/proklik; jazyková korektura;
obrázková hra podle Datova plánu. Tailscale App Store stále jen1.104.6.
Technický důkaz:97 smluvních testů katalogu/předání/Pages PASS; původní
Datovy obsahové, audio a Safari důkazy zachované. Nové testy ověřují přesný
IT cíl a URL, bez záměny s EN nebo nasazením do Cockpitu. Zdroj je zmrazený
na cac18b4d; pozdější Data změny se do balíčku nepřibírají.
Finální důkaz: data/private/data_it_release_20261116/completion.json,
konkrétní cockpit_release.json, it_release.json a public_verification.json.
Rizika: Přejímka všech vět a skutečný telefon zůstávají otevřené. Tento
přípravný zápis sám nepotvrzuje push, nasazení ani úspěšnou fyzickou přejímku.


### 2026-11-16 08:33 CET — Webové Vocabulary IT v katalogu Cockpitu

Hotovo: Položka Vocabulary IT je v místním zdroji katalogu Webové aplikace
přepojená na https://belisarius-mila.github.io/PythonMF/vocabulary-it/.
Název Vocabulary IT, popis kartiček/vět/IT-CZ audia/profilů; původní ID
vocabulary-it-trainer zachované pro existující zkratky. Použije se standardní
nativní odkaz do nové karty; starý desktopový program zůstává dostupný vlastní cestou.

Rozhodnutí: Míla požádal o nahrazení současné desktopové položky novou webovou.
Samostatné p+n této katalogové opravy dosud nezadal.

Další krok: Po samostatném souhlasu vydat tuto katalogovou změnu do Cockpitu.
Navrhované další kroky: Pak pokračovat obrázkovou hrou a telefonní přejímkou.

Technický důkaz: Živý katalog před změnou HTTP200 stále vrací desktopovou
položku. Publikovaný index nové aplikace HTTP200 a bajtově přesně odpovídá
aktuálnímu zdroji. Dřívější vydání a53c1757 dokončené: Cockpit35ac23c2…
a Pages2a7ef1bc…, existující účtenka data_it_release_20261116/completion.json.
Neopakovat předchozí vydání. Aktualizovaný katalogový test zachovává FR
jako desktop; frontend již používá nativní odkazy target=_blank/rel=noopener.
Finální programová brána a shoda zdrojů: private/vocabulary_it_cockpit_20261116.
Nová katalogová změna je pouze místní, běžící Cockpit se v tomto kroku nerestartuje.
