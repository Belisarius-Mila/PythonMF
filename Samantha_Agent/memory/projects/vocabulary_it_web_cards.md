# Vocabulary IT — samostatná webová aplikace podle EN

Projekt/proud: project-vocabulary-it. Kanonický handoff i existující TVBCP jsou
ve workstreams/project-vocabulary-it.md. Schválená analýza a detailní plán:
Vocabulary_IT_analyza_proveditelnosti_2026-11-15.txt v Downloads, doplněk C.

Přijatá pravidla
- Vlastní IT adresa, české ovládání a18 stejných témat jako EN.
- Zachovat původních471 řádků, rody, věty, L/HT, obrazy i staré aplikace.
- IT/CZ identity vit-…; přesné významové aliasy. NFC zachovává diakritiku/case.
- Order je počáteční podklad, nikdy náhradní identita při pozdějším přiřazení.
- Vlastní prázdné profily A–D, jazykově oddělené zálohy; L není osobní zásoba.
- Hotové nahrávky slov i vět, po samostatně schválené malé zvukové zkoušce.
- Časování sloves je pozdější samostatná funkce, ne stovky základních dlaždic.
- Posledních N viditelně v Přehledu pro Učení i Poslech. Obrázková hra podle
  současné EN včetně všech aktivních hesel; posoudit italské konflikty.

Základní soubory a hranice
VocabularyIT/vocabulary_it_catalog.json:497 identit (471 původních a26 webových);24 schválených hlavních významů a26 nových, ostatní metadata dále návrhy.
VocabularyIT/vocabulary_it_input_manifest.json: neměnné otisky777 původních vstupů.
Aktuální stav:497 obrazových vazeb/407 zdrojů, nová galerie a profily místně; viz poslední záznam.
VocabularyIT/vocabulary_it_catalog.py: pouze čtení a ověření, žádný CSV writer.
VocabularyIT/vocabulary_it_review_queue.txt:112 prioritních karet k revizi.
VocabularyIT/WEB_FOUNDATION.txt: identita, přesné kontrolní příkazy a další bod.
Celý uzavřený snímek je pouze private/vocabulary_it_foundation_20261115/inputs.
Worktree má745 obrazů oproti761 v kanonickém zdroji;16 rozdílů je ve snímku.
Bez úplného zdroje kontrola záměrně selže. Soukromé kopie nepatří do Gitu.

První bod nevybírá hotové obrázky ani nevydává návrhy za jazykovou přejímku.
Historický bod1 měl všech471 imageFile=null/pending-review; aktuální obrazová revize je níže. Zbývající metadata jsou needs-review;24 hlavních a26 nových významů jsou po schválení reviewed. Historický návrh měl
460 Slovíček/11 Interakcí, žádné Fráze automaticky. Všechny tvary zůstávají.
Původní vstupní CSV SHA-256:
ed9b24c3f9cda8e7873f37adea3e71070d388fd00890b67b34c29a93d30a3ec5
Mapping SHA-256:
b6c15a68c4d8777d36d3882dff0c76e39d391929796d7daf8bd20dbfdef14db1

Původní resolverové rozpory jsou náměty ze schválené analýzy, ne automatické
opravy. Publikace později potřebuje registrovaný IT Pages cíl a živé ověření;
samotná starší registrace projektu zatím existenci nové galerie nedokládá.


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
