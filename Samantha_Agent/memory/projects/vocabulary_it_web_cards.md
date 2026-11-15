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
VocabularyIT/vocabulary_it_catalog.json:471 identit, všechna metadata návrhy.
VocabularyIT/vocabulary_it_input_manifest.json: otisky777 původních vstupů.
VocabularyIT/vocabulary_it_catalog.py: pouze čtení a ověření, žádný CSV writer.
VocabularyIT/vocabulary_it_review_queue.txt:112 prioritních karet k revizi.
VocabularyIT/WEB_FOUNDATION.txt: identita, přesné kontrolní příkazy a další bod.
Celý uzavřený snímek je pouze private/vocabulary_it_foundation_20261115/inputs.
Worktree má745 obrazů oproti761 v kanonickém zdroji;16 rozdílů je ve snímku.
Bez úplného zdroje kontrola záměrně selže. Soukromé kopie nepatří do Gitu.

První bod nevybírá hotové obrázky ani nevydává návrhy za jazykovou přejímku.
Historický bod1 měl všech471 imageFile=null/pending-review; aktuální obrazová revize je níže. Metadata jsou nadále needs-review. Návrh má
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
