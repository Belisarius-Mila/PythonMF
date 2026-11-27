# Vocabulary FR — obsah před novou hrou, 27. 11. 2026

Míla přijal základní sadu372 herních vět. Před vývojem hry zadal doplnění
nových hesel, příkladových vět a MP3 nejdříve do Janiny sdílené iCloudové
VocabularyFR, následně do webové Francouzštiny Jana.

Příprava

- Živý iCloud CSV má469 úplných řádků. Webový katalog má481 karet; posledních
  17 webových karet dosud ve sdíleném desktopovém slovníku chybí.
- Připraveno42 nových karet s FR/CZ příkladem:40 navržených hesel, druhý
  význam carte a billet de train z redigované věty. Nová stabilní ID jsou
  vfr-0482 až vfr-0523; přidělená v redakčním podkladu, nikoli podle CSV Order.
- Návrh iCloud CSV zachovává všech469 původních řádků a osobních příznaků,
  přidává17 dosavadních webových karet a42 nových; výsledkem bude528 řádků.
  Web po přírůstku bude mít523 karet. Rozdíl pěti zdrojových duplicit zůstává.
-42 nových karet má168 zvukových referencí (slovo/věta × FR/CZ),2 již existují;
  po sdílení identického textu jde o165 nových unikátních MP3 /7639 znaků SSML.
  Henri/Vlasta−10 %, žádná změna dosavadního hlasového profilu.
- Ověřená veřejná retail sazba Azure pro germanywestcentral je15 USD/1M;
  odhad nového slovníkového audia0,114585 USD bez daně, navržený strop0,20 USD.
  Není to ověřené vyúčtování účtu ani příslib bezplatné kvóty.
- Volba navíc namluvit již nyní také372 herních vět má po společné deduplikaci
  531 nových MP3 /28306 znaků /0,42459 USD; navržený strop0,50 USD.
  Herní věty nelze prostě připojit jako372 slovních karet k CSV s jednou větou.

Desktopový kód

Dosavadní aplikace používá systémový say, nikoli soubory MP3. Připravený
LocalAudio načítá volitelný manifest Audio/manifest.json vedle aktivního CSV.
Vyžaduje přesný text/kanál a SHA-256, odmítá traversal, symlinky a konflikty;
chybějící/poškozené/změněné médium vrací k dosavadnímu systémovému hlasu.
Běžná karta s oběma FR klipy je přehraje mimo UI vlákno; turbo rozlišuje
FR/CZ slovo a větu. Tréninkové čtení vlastním tempem zůstává systémové.
Builder přibaluje nový modul. Nová .app zatím není sestavená ani instalovaná.
11 testů builderu a přehrávání PASS; doménovou bránu a commit určuje privátní
completion.json po uzavření přípravného kroku.

Stav a další krok

Příprava je soukromá v data/private/vocabulary_fr_content_additions_20261127.
Čitelný redakční TSV je v Downloads. Živé iCloud CSV, Pict a webová data
se zatím nemění. Nevznikly nové MP3 ani ilustrace; nic není vydané či nahrané.

Čeká konkrétní potvrzení rozsahu audia a cenového stropu, vyžadované výrobním
nástrojem VocabularyFR. Za pracovní výchozí rozsah se považují nové slovníkové
karty s jednou větou, zatímco372 herních vět zůstává v připravené herní sadě.
Po potvrzení: dokončit média, uzavřený obsahový export, bezpečný append CSV
přes vocabulary_csv_store se zálohou/SHA kontrolou, místní MP3 manifest,
ověřený nový desktopový bundle a iCloud upload; pak shodný webový přírůstek,
obrazové vazby a4 zvukové kanály. Samostatně doložit publikaci a fyzický poslech.
Původní app/CSV, L/HT a osobní webový výběr se zachovají. Hra se nevyvíjí.
