# VocabularyEN web: obrazové kartičky pro opakování slovíček


## Aktuální stav — 2026-11-14 10:33 CET

Předchozí produkční galerie, věty a jejich audio jsou vydané a Míla je přijal.
Nově lokálně sekundová česká nápověda při kliknutí v Poslechu: běžný popisek
se po1000ms vrátí. Směr CZ→EN/EN→CZ původní anglický popisek nemění.
Nativní Safari potvrdilo cat → kočka → cat se zvukem.
Nové Pages vydání je samostatný krok; bez nového TVBCP.
Kanonický handoff: handoffs/workstreams/project-vocabulary-en.md.

## Publikační vazba a věty — 2026-11-13 12:58 CET

- Míla zadal další krok. Místně doplněný projekt `project-vocabulary-en`
  s deklarovaným cílem github_pages a cestou `vocabulary-en/`. Používá
  stávající publisher; žádný fallback přes MMTX ani Cockpit restart.
- Katalog má 34 proudů. Nový záznam sám neotevírá soukromé vlákno, nevytváří
  workspace ani TVBCP. Nový kanonický handoff je
  `handoffs/workstreams/project-vocabulary-en.md`; podrobná historie galerie
  zůstává v původním handoffu v1. TVBCP není založený a Cockpit checkpoint
  tohoto nového proudu zatím není připravený.
- Každá z 425 karet má Sentence i SentenceT, přesně převzaté do sentenceEn
  a sentenceCz. Zobrazí se po odhalení odpovědi. Existujících 845 MP3
  obsahuje slovíčka/překlady, nikoli celé věty. Nové nahrávky nevznikly.
- Cílené ověření: 244 testů PASS / 24,880 s, včetně 18 Node scénářů. Plná brána:
  PASS — 3688 testů / 631,512 s, 5 SKIP, 0 failures/errors. Slovníček ani galerie se tímto krokem nemění.
- Main má 18 jiných commitů a Data tři vlastní před tímto krokem. Cizí změny
  zůstávají zachované; integraci musí převzít vlastník main se servisním
  rozhodnutím. Novou vazbu musí před Pages p+n znát i serverový runtime.
- Další krok: servisní rozhodnutí pro integraci divergentní větve podle
  předání; pak ověřit spojený kód, načíst serverovou vazbu a samostatné p+n.

## Mílova přejímka místní galerie — 2026-11-13

- 2026-11-13 12:41 CET: po odkazu na místní Mac náhled a pěti bodech přejímky Míla
  přijal ovládání galerie a výslovně zadal pokračovat.
- Místní uživatelská přejímka je přijatá. Fyzický iPhone a veřejná publikace
  zůstávají samostatné; tento souhlas nepředstírá poslech všech 845 MP3.
- Finální plná brána PASS — 3685 testů / 566,387 s, 5 SKIP, 0 failures/errors.
  71 cílených SDK/galerie testů PASS / 22,124 s. Příčinou byl krátký RPC limit
  chybně aplikovaný také na inicializaci. Testy nyní inicializují s původní
  standardní 3s mezí a potom měří operaci původními 0,5–0,6 s. Produkční SDK
  adaptér ani provoz se nemění; žádný retry ani modelová inference.
- Finální zdroje 12/12 a náhledy 384/384 odpovídají manifestu; původní CSV
  a audio manifest jsou shodné. Log: vocabulary_en_sdk_phase_full_gate_20261113.log.
- Další krok: samostatně rozhodnout integraci/vydání a fyzický iPhone. Před
  vydáním ověřit přesnou registrovanou vazbu Vocabulary EN na publisher.

## Galerie v1 — místní implementace 2026-11-13 10:53 CET

- Hotová místní galerie **425 karet / 18 skupin** podle schválené přílohy.
  Výchozí Téma, české ovládání, popisky EN/CZ, hledání bez diakritiky, doporučené
  i abecední řazení; širší obrazovka až 8 sloupců, telefon výchozí 2 sloupce.
- Více témat je NEBO, zdroj Benji/slovní druh/náročnost/výběr L nebo HT tvoří
  průnik. Jedna karta je v galerii právě jednou. Náročnost je redakční návrh.
- Velká karta zachovává pořadí galerie a odhalení odpovědi/věty/MP3. Předchozí,
  Další, hranice skupin a konec výběru; náhodné kolo pouze explicitně, bez
  opakování. Návrat nahoře i dole, Escape a browser Zpět; fokus i zvýraznění
  poslední učené miniatury. Obnova karty i galerie zachová původní posloupnost.
- Trvalé UID i dosavadní číselné audio ID jsou v samostatném katalogu;
  desktopové CSV se neměnilo. Neznámý/duplicitní význam export zastaví.
- **384 náhledů, 7,883,044 B**, delší strana nejvýše 384 px, původní média
  zachovaná. Všechna dosavadní pole původních 425 karet obsahově beze změny.
- Galerii vlastní gallery.js/model.js/gallery.css; původní sdílené app.js a
  styles.css jsou beze změny kvůli Vocabulary EN83.
- Ověření: 21 cílených Python testů, v nich 17 Node scénářů skutečného
  controlleru a 10 relevantních starších exportních kontrol. Nativní Safari:
  galerie → cat/cow/crocodile → browser Zpět na krokodýla, úzké 2sloupcové
  zobrazení se zvětšením, odhalení a spodní návrat; původní zoom/okno obnovené.
- Historická brána před opravou SDK (nahrazená finální zelenou výše): NEZELENÁ: 3685 testů / 910,695 s, 5 SKIP; 1 chyba registru (opravena), 2 SDK startup timeouty. Následně 36 cílených kontrol: 35 OK, 1 SDK inicializace s limitem 0,5 s stále ERROR.
- Pět dalších starších MMTX snapshot auditů selhává také na nezměněných HEAD
  zdrojích: nová hesla v dialozích a starý počet mapování. Původní testy ani
  jejich očekávání se nepřepisovaly; samostatně řešit případný obsahový audit.
- Aktuální handoff: `handoffs/vocabulary_en_gallery_v1_2026_11_13.md`.
  Autorský postup: `VocabularyEN/GALLERY_AUTHORING.txt`.
- Tehdejší další krok: Mílova přejímka místního návrhu (nyní přijatá) a samostatné rozhodnutí o vydání.
  Fyzický iPhone, poslech všech MP3 a publikace tím nejsou doložené. Jde o
  samostatný terminálový projekt; nový TVBCP ani proud v Cockpitu nevznikl.

## Galerie v1 — schválená rozhodnutí 2026-11-13

- Míla schválil výchozí galerii a základní pohled **Téma** se stručným českým
  ovládáním. **Další** sleduje pořadí galerie; náhodně pouze po výslovné volbě.
- Mobilní výchozí rozložení: větší dlaždice ve **dvou sloupcích**.
- Příloha návrhu: **425 karet / 18 skupin**, schválená jako výchozí mapa.
  Víceznačnosti se při redakci ověřují podle konkrétního významu, věty a obrázku.
- Podrobný podklad v Downloads:
  `Vocabulary_EN_okruhy_a_obrazova_galerie_navrh_2026-11-12.txt`; obsahuje
  schválení z 13. 11., rozbor filtrů, všech 425 karet a přejímací podmínky.
- Další krok: místní první verze — metadata a stabilní identita karet, galerie
  propojená s velkou kartou a návratem na poslední učenou miniaturu.
- Tento zápis eviduje rozhodnutí; funkční změna ani publikace v něm neproběhly.

## Stav

Vznikl nový malý webový projekt na bázi `VocabularyEN/vocab_trainer_en.py`.

Cílová skupina jsou mentálně postižení studenti, které Míla učí anglická slovíčka.

Původní desktopová aplikace `vocab_trainer_en.py` je bohatá, ale pro tuto skupinu je příliš hustá a textová. Webová verze má být jednodušší: jeden obrázek, jedno slovíčko, velká tlačítka, minimum textu.

Hlavní vytvořené nebo dotčené soubory:

- `VocabularyEN/sync_vocabulary_en_to_docs.py`
- `docs/vocabulary-en/index.html`
- `docs/vocabulary-en/styles.css`
- `docs/vocabulary-en/app.js`
- `docs/data/vocabulary-en.json`
- `docs/assets/vocabulary-en/`
- `Pict/VocabularyEN_missing_nouns_plan.md`
- `Pict/mapping.json`

## Cíl

Cílem je vytvořit jednoduchou webovou learner aplikaci pro opakování anglických slovíček z `VocabularyEN.csv`.

Web nemá být editor slovníku. Má sloužit studentům k procvičování.

Autoring obsahu má zůstat mimo learner web:

1. Míla přidá slovíčko do `VocabularyEN/VocabularyEN.csv`.
2. Přidá obrázek do `Pict/`.
3. Pokud obrázek nemá přímý název podle slovíčka, doplní mapování do `Pict/mapping.json`.
4. Spustí synchronizační skript.
5. Web načte vygenerovaný JSON a obrázky z `docs/`.

## Důležité poznatky

### Co šlo převést z desktopu

Z `vocab_trainer_en.py` je webově dobře přenositelný:

- datový model `EN, CZ, Order, Sentence, SentenceT, L, HT`,
- filtrace slov podle `All / Last / Interval / Not known / HT`,
- náhodné vybírání bez opakování,
- logika mapování obrázků přes `Pict/mapping.json`,
- základní stav `learned` a `hardTraining`,
- hlas přes browser speech nebo později hotová audio data.

### Co nepřenášet 1:1

Do learner webu se nemá přenášet celé desktopové UI:

- hustý panel nastavení,
- editor CSV,
- psací režim jako výchozí režim,
- macOS `say`,
- export PNG do Apple Photos,
- příliš rychlý turbo režim.

Pro cílovou skupinu je lepší:

- jeden úkol na obrazovce,
- velký obrázek,
- velké tlačítko pro přehrání,
- 2–4 velké odpovědi nebo jednoduché odhalení odpovědi,
- minimum checkboxů a vysvětlovacího textu.

## Rozhodnutí

### Sync skript

Vznikl skript:

```text
VocabularyEN/sync_vocabulary_en_to_docs.py
```

Co dělá:

- načte `VocabularyEN/VocabularyEN.csv`,
- použije stejnou nebo obdobnou logiku výběru obrázků jako desktopová aplikace,
- zkopíruje použité obrázky do `docs/assets/vocabulary-en/`,
- vygeneruje manifest `docs/data/vocabulary-en.json`.

Spuštění:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py
```

Volitelně umí zapisovat i do dalšího web rootu:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py \
  --extra-output-root MatysekANJ/web_mmtx
```

Ověření při vzniku:

```bash
python3 -m py_compile VocabularyEN/sync_vocabulary_en_to_docs.py
python3 VocabularyEN/sync_vocabulary_en_to_docs.py
```

Výsledek tehdy:

- 152 položek v JSON,
- 63 zkopírovaných unikátních obrázků,
- JSON obsahuje mimo jiné `learned`, `hardTraining`, `sentenceEn`, `sentenceCz`, `image`, `imageSource`.

### Webová stránka

Vznikla první learner stránka:

- `docs/vocabulary-en/index.html`
- `docs/vocabulary-en/styles.css`
- `docs/vocabulary-en/app.js`

Stránka:

- načítá `docs/data/vocabulary-en.json`,
- ukazuje velký obrázek,
- podporuje režim CZ -> EN a EN -> CZ,
- má akce `Nové slovo`, `Ukaž odpověď`,
- umí přehrát zadání i odpověď přes browser speech,
- ukládá `Umím` a `Těžké` do `localStorage`,
- není editor obsahu.

Lokální spuštění:

```bash
python3 -m http.server 8811 -d docs
```

URL:

```text
http://127.0.0.1:8811/vocabulary-en/
```

### Úprava hlavičky

Po prvním náhledu byla stránka vizuálně upravena:

- nadpis je jen `Obrazkove karticky EN`,
- odstraněn text pro opakovani slovicek,
- odstraněn vysvětlující šedý text,
- hlavička byla zmenšena na výšku,
- font nadpisu byl mírně zmenšen, aby držel v jedné řádce.

### Obrázky a fallbacky

Analýza ukázala, že některá podstatná jména a noun-like fráze padají do obecných fallbacků typu `proverbs`, `others`, `man`, `preposition`, `woman`.

Dobří kandidáti na dokreslení obrázků:

- airport
- animal
- baby elephant
- bus station
- cat
- cow
- crocodile
- doctor
- document
- duck
- elephant
- eyes
- field
- film
- giraffe
- goat
- horse
- lake / pond
- lion
- monkey
- name
- office
- popcorn
- rabbit
- rhino
- teacher
- ticket
- zebra
- orange
- pound

Sporné, ale možné:

- cook
- drawing
- English
- help
- something

Vznikl plánovací soubor:

- `Pict/VocabularyEN_missing_nouns_plan.md`

Obsahuje doporučené názvy souborů do `Pict/`.

Byly také doplněny návrhy mapování do:

- `Pict/mapping.json`

Příklad workflow:

- `Pict/bus_station.png`
- a v `mapping.json` mapování pro:
  - `bus station`
  - `autobusové nádraží`
  - `autobusove nadrazi`

Po přidání nových obrázků je potřeba spustit:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py
```

## Otevřené otázky

- Přidat druhý režim s 2–4 obrázkovými možnostmi místo pouhého odhalení odpovědi.
- Rozhodnout, zda bude stránka napojená z hlavního webového rozcestníku.
- Zlepšit heuristiku výběru obrázků, aby podstatná jména nepadala do obecných fallbacků.
- Po dokreslení obrázků znovu spustit sync a zkontrolovat, kolik položek ještě padá do fallbacku.
- Rozhodnout, zda pro některé slovníkové položky vytvořit hotové audio soubory místo browser speech.
- Později zvážit backend, pokud bude potřeba editace obsahu přes web.

## Další kroky pro Codex

Před prací na tomto projektu číst:

- `VocabularyEN/vocab_trainer_en.py`
- `VocabularyEN/sync_vocabulary_en_to_docs.py`
- `VocabularyEN/VocabularyEN.csv`
- `Pict/mapping.json`
- `Pict/VocabularyEN_missing_nouns_plan.md`
- `docs/vocabulary-en/index.html`
- `docs/vocabulary-en/styles.css`
- `docs/vocabulary-en/app.js`
- tento memory soubor

Pravidla:

- Neudělat z learner webu editor obsahu.
- Autoring dál držet v CSV, `Pict/` a `mapping.json`.
- Po změně CSV nebo obrázků spustit sync skript.
- Nezapisovat z prohlížeče přímo do CSV bez backendu.
- Pro cílovou skupinu držet UI velmi jednoduché.
- Při změně webu testovat přes lokální HTTP server nad `docs/`.
- Při git operacích nepoužívat slepě `git add .`, protože v repozitáři bývá hodně rozpracovaných souborů.

## Okruh Benji z MMTX - 2026-08-25

- Všech 120 položek importovaných z MMTX, tedy pořadí 187 až 306, má v poli
  `WS` přidanou hodnotu `Benji`.
- Původní okruhy zůstávají zachované. Více okruhů se v CSV odděluje znakem `|`,
  například `Actions|Benji`.
- Web vytváří seznam okruhů dynamicky z manifestu, proto nebyla potřebná změna
  HTML ani JavaScriptu. Po synchronizaci nabízí checkbox `Benji` a jeho filtr
  obsahuje právě 120 nových položek.
- Budoucí import přes `import_mmtx_vocabulary.py` přidá `Benji` automaticky.
- Pro bezpečné doplnění existujících importovaných řádků slouží
  `tag_mmtx_benji_word_set.py`; bez `--apply` pouze audituje.
- Webový export se obnovuje příkazem:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py --preserve-extra-assets
```

## Oprava výslovnosti cat — 2026-09-05 21:40 CEST

- Hotovo: pro `cat` (Order 20) je připravená MP3 hlasu Jenny. Text kartičky,
  české audio i ostatních 305 položek zůstaly stejné.
- Rozhodnutí: generátor má úzkou hlasovou výjimku pro anglické `cat`, takže
  další sestavení opravu zachová. Nový hlas mění adresu MP3 a obchází cache
  původní nahrávky. Staré soubory se nemažou.
- Další krok: push a samostatná publikace GitHub Pages, potom poslech na
  cílovém zařízení. Oprava zatím není doložená na veřejném webu.
- Technický důkaz: veřejná původní MP3 byla bajtově shodná s lokální;
  automatický anglický přepis původního Aria audia vrátil `Kate.`, nového
  Jenny audia `Cat.`. Jde o strojovou kontrolu, nikoli lidský poslech.
  Cílené audio testy prošly 11/11, knihovna má 608 aktivních MP3 pro 306 slov.

## Too a opakování karet — 2026-09-05 22:03 CEST

- Hotovo: odstraněná položka `me too` / `já také`, zachované samostatné
  `too` / `také`. Aktuálně 305 položek, z toho 119 Benji, a 606 aktivních
  MP3. Import z MMTX má výslovnou výjimku, aby frázi znovu nepřidal.
- Rozhodnutí: respektovat stávající průběžné číslování CSV a exportu;
  po odstraněném pořadí 274 se další položky posunuly o jedna. Všechen
  ostatní obsah včetně L/HT, obrázků a zvuků je zachován. Dvě pořadí v
  lokálním hlasovém castingu jsou tomu přizpůsobená.
- Hotovo: přepnutí CZ→EN / EN→CZ už nemaže historii karet. Počítadlo
  ukazuje skutečně dosud nezobrazené karty a na konci nulu; zpráva oznamuje
  dokončení sady. První karta dalšího kola není poslední kartou minulého
  kola, pokud sada obsahuje více než jednu položku.
- Logika: losuje se rovnoměrně mezi dosud nezobrazenými ID. Změna filtru
  nebo okruhů zahajuje novou sadu; obnovení stránky zahajuje novou relaci.
  Různá ID mohou mít shodný text kvůli jinému významu, například
  `orange` = pomeranč / oranžový; tyto legitimní karty zůstávají oddělené.
- Technický důkaz: chyba resetu směrem reprodukována před opravou. Po
  opravě 4 JavaScript testy včetně tří celých kol nad 305 kartami a změn
  směru, 11 audio testů a 13 importních/mapovacích testů OK. Statická
  brána a místní HTTP kontrola OK; Browser bridge nebyl dostupný, proto
  ruční proklik není doložen. Žádná MP3 ani obrázek se nemazaly.
- Další krok: push a publikace Pages, potom ruční zkouška. Předchozí
  oprava `cat` byla zveřejněna z commitu `cc0b2b6`, ověřena veřejným
  manifestem a shodou MP3; aktuální změny zatím veřejně ověřené nejsou.

## Audit MMTX a doplnění dialogů — 2026-09-05 22:42 CEST

- Hotovo: porovnané historické slovníčky i anglické dialogy všech dostupných
  scén, školy, barev a obou narozenin. Devět zdrojů je shodných s veřejným
  MMTX. Doplněno 120 základních hesel s CZ, Sentence, SentenceT a Benji.
- Stav: 425 karet, 239 Benji, 845 aktivních MP3. Všech původních 305 řádků
  zůstalo bajtově zachováno; me too ani jména postav se nevrátily.
- Rozhodnutí: slovní tvary převádět explicitně na základní hesla; nové
  překlady a věty jsou v mmtx_dialogue_supplement.csv. Import nyní rozpozná
  i chybějící slovní zásobu v dialogu bez vlastního slovníčkového panelu.
- Rizika: 49 nových hesel používá obecné ilustrace. Audit není kontrolou
  všech významů každého slova; původní překlady se nepřepisovaly.
- Technický důkaz: následný import 0 chybějících hesel; 15 importních,
  11 audio a 4 JavaScript testy OK; statická brána OK. Všech 239 nových MP3
  se dekóduje bez chyby. Přepis vzorků bridge, brown, birthday a stream
  odpovídá heslům. Výslovnost všech nahrávek lidským poslechem ověřená není.
- Další krok: push a publikace Pages, pak ruční zkouška. Přehled v
  reports/vocabulary_en_mmtx_audit_2026_09_05.md. Předchozí úprava too a
  losování byla už zveřejněna z commitu 10f7e6a; toto doplnění zatím není.

## Ilustrace k dialogům — 2026-09-06 00:07 CEST

- Hotovo: dokončeno 49/49 nových ilustrací v pracovní dávce
  PictNew/generated/20260905_en_dialogue_batch001/. Obnova našla 47 hotových
  souborů; generovaly se pouze wide a wish přes vestavěný image_gen.
- Ověření: dekódování 49 WebP, SHA-256, 49 odkazů a úplné české významy
  i oba jazyky vět v review.html. Největší finální obrázek má 297 090 B.
  Pět větších původních WebP je zachováno v originals; finální kopie
  splňují limit 300 kB. Číslovky 10/11/12 vizuálně souhlasí.
- Rozhodnutí: jde o kandidátní sadu ke schválení. Pict, mapping a produkční
  web se tímto krokem nemění. Členy a zájmena vyžadují kontext věty.
- Další krok: Mílova kontrola review.html, poté potvrzené začlenění podle
  vocabulary_image_generation_workflow.md. Handoff:
  vocabulary_en_49_images_review_2026_09_06.md.

## Schválené obrázky v aplikaci — 2026-09-06 00:15 CEST

- Míla schválil 49 ilustrací a zadal p+n. Sada je zkopírována do Pict
  a docs; přesné názvy umožňují přímé přiřazení bez změny mappingu.
- Změnilo se pouze 49 očekávaných obrázkových vazeb. Všech 425 karet
  má platnou obrázkovou vazbu: 361 přímých přiřazení a 64 přes mapping.
- Kontrolní součty 49 exportovaných obrázků odpovídají schválené sadě.
  Věty, překlady, Benji a ostatní data karet zůstaly stejné; audio audit
  845 MP3 / 850 odkazů je v pořádku. Prošlo 15 importních/mapovacích
  a čtyři JavaScript testy.
- Dokončeno 2026-09-06 00:24 CEST: úplná brána 1518/1518, push a Pages
  z d22f25a4; run 33995717491 a deployment 6286494824 jsou success.
  Veřejný manifest, app.js, audio manifest a všech 49 WebP jsou ověřeny
  kontrolními součty. Původní sdílený obrázek man pro brother/son/he zůstává.
  Důkaz: reports/vocabulary_en_images_publish_2026_09_06.json a handoff
  vocabulary_en_49_images_review_2026_09_06.md. Další krok je běžné používání.

## Zdroj

Souhrn ChatGPT/Codex konverzace k převodu části `vocab_trainer_en.py` do jednoduché webové learner aplikace pro mentálně postižené studenty, vytvoření sync skriptu `VocabularyEN -> docs`, prvního webového MVP, zmenšení hlavičky a přípravě seznamu chybějících obrázků v `Pict/`.

Doplnění ověření: povolená cesta vocabulary-en/ je zapsaná také přímo
v publisheru mmtx_pages_deploy.py. Cílený průchod používá skutečný publisher
s injektovaným fake runnerem a HTTP fetcherem, pro nové i již hotové nasazení.
První rozběhnutá plná brána byla kvůli tomuto doplnění zastavená; není
vydávána za finální výsledek. Finální log má příponu full_gate_final.

Finální ověření: PASS — 3688 testů / 631,512 s, 5 SKIP, 0 failures/errors. Všech 12 zmrazených
zdrojů/testů je po bráně shodných. Z původního galerijního manifestu se změnily
pouze dva záměrně rozšířené testy; zbývajících 10 zdrojů, všech 384 náhledů,
CSV a audio manifest zůstávají shodné. Přímý publisher: 67 testů PASS / 6,026 s.
Log: vocabulary_en_publication_binding_full_gate_final_20261113.log
SHA-256: 57d9997b4d3b863a7b7c36fac7c96ced8e7c51185b893ae31fbf5897f09292c6


### 2026-11-13 13:22 CET — Schválená integrace čtyř Datových commitů

Hotovo: Připravený integrační kandidát nad main9857d2e6 spojuje HA-06,
galerii Vocabulary EN, testovou SDK opravu a přesnou Pages registraci.
77 souborů změněných pouze na main zůstává bajtově shodných; konfliktní
registry zachovávají Willovy záznamy a doplňují Datovy. Původní worktree
Data zůstává čistý na 9f113231; integrační výsledek je připravený k převzetí
na main. Skutečné převzetí potvrzuje závěrečná účtenka v Downloads.

Rozhodnutí: Míla schválil všechny Datovy commity a určil nechat Willovy
stranou. Integrace zachová historii main i schválené f95734f5, 9b584b95,
2f16cf66 a 9f113231. Žádný push, nasazení nebo služba tím nejsou povolené.

Další krok: Samostatně rozhodnout o případném publikačním rozsahu.
Závěrečná účtenka uvádí merge SHA a skutečné fast-forward převzetí na main;
Willovy čekající commity se tímto souhlasem nepublikují.

Navrhované další kroky: Samostatné publikování Vocabulary EN vyžaduje vlastní
schválené p+n a serverově načtenou novou vazbu. Fyzický iPhone a případné
nahrávky vět zůstávají otevřené. Žádný nový Vocabulary EN TVBCP nevznikl.

Technický důkaz: 105 cílených kontrol PASS / 22,338 s; plná integrační brána
PASS: 3823 testů / 580,485 s, 8 SKIP; 3 SDK schema kontroly následně PASS / 0,376 s, zbývá 5 původních SKIP. Zachovaný originální main i Datovy soubory,
žádný reset/rebase/force push. Privátní source manifest a porovnání 77 souborů
jsou v data/private/vocabulary_en_integration_20261113/ integračního worktree.

Rozsah souhlasu k další fázi: Míla schválil čtyři Datovy commity a požádal
nechat Willovy stranou. Toto není souhlas s celým čekajícím GitHub balíčkem.
Běžné p+n audituje celý rozsah origin/main..main, takže se v této etapě
nespouští. Před zveřejněním je potřeba samostatně určit a schválit jeho rozsah.

Finální důkaz integrace: PASS: 3823 testů / 580,485 s, 8 SKIP; 3 SDK schema kontroly následně PASS / 0,376 s, zbývá 5 původních SKIP. Všech 40 zmrazených zdrojů/testů/dat
zůstává shodných. Produkční recovery kód ani jeho testy nebyly měněné; první
chybu způsobilo pouze vlastní pomocné .venv. Zkratka je zachovaná privátně,
nový místní kořen je skutečný adresář se stejnými dependency referencemi.
Tři schématové fixture odkazy byly doplněné, jejich přesné testy prošly;
žádný z přeskočených schema testů není vydávaný za provedený plnou branou.
Logy: data_integration_full_gate_final_20261113.log a
data_integration_sdk_schema_final_20261113.log. SHA-256 plné brány:
747854656af7205e4c217866b1976b2bc67772c0862abea23f3c9a99f196e6fb


## 2026-11-13 15:04 CET — Oprava servisního nalezení Node před společným p+n

Hotovo: Regresní test galerie používá stejné nalezení Node jako kanonická
brána. Funguje také při minimálním launchd PATH, bez změny systémového PATH,
instalace či přeskočení testu. Galerie a její produkční data se nemění.

Rozhodnutí: Míla výslovně schválil p+n všech čekajících commitů; tím je
překonané předchozí omezení publikace pouze na Datovy commity. Nejprve
společný runtime, následně vlastní registrovaný Pages cíl Vocabulary EN.
Nový TVBCP se nezakládá.

Další krok: Commit opravy, zarovnání čistých profilů a nové registrované
p+n opraveného headu. Původní nejisté vydání se neopakuje.
Navrhované další kroky: Po potvrzeném nasazení fyzická iPhone přejímka.

Technický důkaz: Původní účtenka a843815b941d7872bcc6e69bea341829 skončila
attention; 3823 testů / 53 skip / 1 error: FileNotFoundError node v novém
galerijním testu. Brána skončila před _push_exact_head; živý GitHub dál
fb062e34, main498ba91a o12 commitů napřed, žádné nasazení. Oprava:29 testů
PASS/13,193s s PATH=/usr/bin:/bin:/usr/sbin:/sbin, včetně skutečných Node
scénářů; rychlá statická brána PASS. Původní důkaz zachovaný v
logs/all_commits_failed_gate_20261113.log a all_commits_runtime_release_20261113.log.


## 2026-11-13 15:55 CET — Procvičování vět a potvrzené vydání galerie

Hotovo: Na velké kartě je přepínač Slovíčko / Věta. Celé věty jdou
procvičovat CZ → EN i EN → CZ, odhalení ukáže obě jazykové verze. Další
sleduje galerii a návrat zvýrazní poslední miniaturu. Volba přežije historii,
obnovu i pokračování; výchozí režim a staré odkazy zůstávají slovíčkové.

Rozhodnutí: Pokračování navazuje na Mílův dřívější požadavek na věty; nové
placené audio se nevytváří. Zvuk v režimu Věta má jasný popisek Slovíčko;
aplikace nehodnotí správnost ani výslovnost. Nový TVBCP nebyl dohodnutý.

Další krok: Mílova přejímka vět na telefonu v aktualizovaném soukromém náhledu.
Místní checkpoint odděluje novou funkci od již vydané produkční galerie.
Navrhované další kroky: Mílova přejímka vět na telefonu; poté samostatné
rozhodnutí o integraci a Pages vydání této nové funkce. Nahrávky celých vět
zůstávají možným odděleným krokem.

Technický důkaz: 25 Node scénářů PASS / 16,511 s; 22 cílených Python testů
PASS / 17,653 s (včetně Node a původních exportních kontrol). Nativní Safari
potvrdilo odhalení obou vět, oba směry, skrytou odpověď na další kartě, úzké
zobrazení a návrat na cow se zvýrazněním Tady jsme skončili. Fyzický iPhone
není tímto doložený. Plná brána PASS: 3823 testů / 927,757 s, 5 SKIP,
0 failures/errors. Všech pět zmrazených zdrojů/testů po bráně bajtově shodných;
source_manifest.json a final_verification.json jsou v
data/private/vocabulary_en_sentences_20261113/.

Dnešní živá kontrola navíc potvrzuje už hotové Pages vydání původní galerie:
účtenka 63ea606335ef4e37fe02905091edfcd3, completed/done, deployed=true,
cíl project-vocabulary-en / github_pages, zdroj 0ec447e7949e343991ed9dc5ae99152c8aab9384.
Veřejné index.html/gallery.js/gallery.css/model.js odpovídaly tomuto main
bajtově (HTTP i SHA-256). Starší zápisy o čekající publikaci jsou historické.
Tento nový režim vět zatím součástí Pages není.

Nezávislý soukromý náhled galerie je již vydaný na
https://vocabulary-en-layout-20261113.fairfly9.chatgpt.site
Site appgprj_6af70efd30b081919af279ac1930a3a6; pouze vlastník, žádné rozšíření
přístupu. Původní verze zdroje cf9063615487740bf320739ea376eb246a51d754,
deployment appgdep_6af7101f75a48191ab43e28c7e545deb. Aktualizace vět: zdroj
3b9c65861001db8cff8ec739a0ae2466d507564b, deployment
appgdep_6af72635871c8191931e5289107d6820 succeeded. Nativní Safari ověřilo
na vydaném webu cat a přepnutí Slovíčko → Věta s celým českým zadáním.
Přístup zůstává pouze vlastník; archiv má shodné čtyři soubory rozhraní,
média i data jsou beze změny. Main a běžící Cockpit se tímto krokem nemění.

Finální uzavření 2026-11-13 16:17 CET: plná brána vocabulary_en_sentences_full_gate_20261113.log
SHA-256 d7fe52a48a1dec3927907612b479cb7cf852f6a348602792f7c0c1c2cc3aa962. Soukromý Sites náhled je
vydaný a prokliknutý v nativním Safari; fyzický iPhone čeká. Všechny nové
zdroje/testy jsou shodné s bránou; původní manifest karet a audia beze změny.
Příští krok je Mílova přejímka, poté samostatné rozhodnutí o integraci/p+n.
Žádný nový TVBCP; checkpoint je místní v Datově větvi, nikoli Cockpit checkpoint.


## 2026-11-13 17:06 CET — Schválené předání vlastních commitů Terře p+n

Hotovo: Režim vět z checkpointu 9ef50b2f je začleněný nad již publikovaný
main4e7007ae. Všechny čtyři webové zdroje jsou shodné s vlastní zelenou
branou 3823 / 927,757 s, 5 SKIP, OK. Willův ISBN krok už je na GitHubu
a má dokončenou vlastní účtenku; do nového publikačního rozsahu nevstupuje
jako čekající cizí práce. Jeho nezávislé soubory zůstávají bajtově shodné,
paměťový index zachovává oba záznamy.

Rozhodnutí: Míla výslovně zadal Terra p+n pro vlastní commity. Předání
použije jediný submit_release(wait=True), projekt project-vocabulary-en,
cíl github_pages a centrální schválenou roli release_executor Terra/high.
Žádné nové TVBCP a žádný restart Cockpitu nebo služby Camino.

Další krok: Po integrační kontrole zarovnat čisté profily a předat přesný
nový main registrovanému vykonavateli. Samostatná soukromá účtenka je
autoritou výsledku; tento zápis není tvrzením o budoucí publikaci.
Navrhované další kroky: Po potvrzeném Pages vydání Mílova přejímka na iPhonu.

Technický důkaz: Živý GitHub audit před integrací byl aligned4e7007ae,
0 čekajících commitů. Willova účtenka d4e292cadfbff224094fd22cb4614ccd
completed/done, pushed=true, deployed=true. Původní Datův worktree
zůstává zachovaný a čistý na 9ef50b2f. Přesný merge SHA a konečnou účtenku
p+n doplní bezpečný TXT výsledek v Downloads a privátní release receipt.


## 2026-11-13 18:39 CET — Schválené větné audio, generování a přehrávač

Hotovo: Prvních šest skutečných MP3 vět je vytvořených a dekódovatelných;
Aria pro EN a Vlasta pro CZ, tempo -10 %. Oddělený generátor navazuje
na původní CSV a 425 párů vět. Rozhraní přehrává celé zadání a po odhalení
pouze cílový překlad, v obou směrech. Původní slovíčkový režim zůstává.

Rozhodnutí: Míla výslovně zadal začít větným audiem a po vysvětlení hlasů
a rozsahu 425 EN + 425 CZ řekl „OK, jdeme na to!“. Jde o pokračování
vlastního vývoje, bez nového souhlasu s Pages p+n. Registrovaný Edge TTS
se používá pro veřejné věty; žádný přechod na placené Azure ani nové modely.
Chybějící edge-tts7.3.1 doplněné jen do privátního generačního prostředí.
První lokální pokus skončil před sítí kvůli chybějící knihovně; nebyla
provedená externí syntéza ani opakovaný nejistý požadavek.

Další krok: Dokončit všech 850 nahrávek, ověřit celou sadu i návrat/obnovu
v aplikaci a uložit vlastní checkpoint. Soukromý Sites náhled se aktualizuje
při zachování publika; nové Pages vydání vyžaduje samostatné p+n.
Navrhované další kroky: Mílův poslech vět a fyzická iPhone přejímka.

Technický důkaz: 13 Python testů generátoru/slovníčkového audia PASS /0,187s;
27 Node scénářů PASS /12,087s, včetně ochrany překladu před odhalením,
neshodných vět a zastavení při navigaci. Šest MP3 dekódovaných ffmpeg,
délka 2,06–3,67s; dvě ukázky přehrané afplay. To nenahrazuje lidskou
přejímku přirozenosti a výslovnosti. Trvalý stav běžící dávky je
data/private/vocabulary_en_sentence_audio_20261113/generation.json.

Předchozí režim vět je už produkčně vydaný z9c6cc825; účtenka
1e2d90febc09702a5538f43a75e50228 completed/done, Terra/high, push i
Pages confirmed, plná brána3823/637,9s a šest HTTP/SHA souborů shodných.
Starší zápisy o čekající integraci/publikaci tohoto režimu jsou historické.
Nové větné MP3 tímto předchozím vydáním zahrnuté nebyly.

Doplnění 2026-11-13 18:47 CET: Všech850 MP3 vytvořených, všech850 dekódovaných ffmpeg,
žádné chybějící. Celkem16 445 376B, délky1,872–5,496s. Původní CSV,
JSON425 karet, slovíčkový manifest a845 slovíčkových MP3 bajtově shodné
s původním manifestem. Safari: obě jazyková zadání, odhalený cílový
překlad, přechod na cow, původní slovíčkový zvuk i návrat na poslední
dlaždici. 29 cílených Python testů (včetně27Node scénářů) PASS /12,853s.
Plná brána běží nad13 zmrazenými zdroji/testy/daty; MP3 mají samostatné
otisky v audio_verification.json. Soukromý náhled se aktualizuje.

Soukromý Sites náhled aktualizovaný, audience pouze vlastník:
https://vocabulary-en-layout-20261113.fairfly9.chatgpt.site
Zdroj4eb3854dff55272de031acba563dbc38908cb3db, deployment
appgdep_6af74d752cac8191a325f8c7e4f74b07 succeeded. Archiv ověřený proti
všem850 MP3 i třem změněným JSON/JS souborům. Lokální Safari přehrávání
ověřené; následné otevření vzdáleného náhledu nemohlo být dokončené,
protože se nativní okno Safari souběžně měnilo. Fyzický iPhone čeká.


## 2026-11-13 18:56 CET — Větné audio dokončené a ověřené

Hotovo:425 anglických a425 českých vět mají vlastní nahrávky Aria/Vlasta
při tempu -10 %. Věta přehraje zadání; po odhalení odpovědi lze přehrát
cílový překlad. Původní slovíčka i845 MP3 jsou zachované. Soukromý náhled
je vydaný na stejné adrese a přístupný pouze vlastníkovi.

Rozhodnutí: Dokončený schválený vývoj s externí syntézou přes původní Edge
TTS. Žádné nové placené Azure/modelové volání, žádný nový TVBCP a žádné
PythonMF p+n nebo změna Willova main.

Další krok: Mílův lidský poslech a fyzická iPhone přejímka soukromého náhledu.
Navrhované další kroky: Po přejímce samostatné schválené Pages p+n audia.

Technický důkaz: Plná brána3831 testů /646,379s, 5 SKIP, OK. Dříve29
cílených Python včetně27Node PASS /12,853s. Všech13 zmrazených vstupů
po bráně shodných;850/850 MP3 dekódovaných a beze změny, původní CSV,
karty, slovíčkový manifest a845 MP3 rovněž shodné. Celkem16 445 376B nového
audia; délky1,872–5,496s. Nativní Safari lokálně potvrdilo obě jazyková
zadání, oba cílové překlady, skrytou odpověď po Další, slovíčkový zvuk
a návrat na poslední miniaturu. To není fyzická iPhone ani lidská přejímka.

Soukromý Sites: zdroj4eb3854dff55272de031acba563dbc38908cb3db, deployment
appgdep_6af74d752cac8191a325f8c7e4f74b07 succeeded,850 MP3 a3 změněné
JSON/JS soubory v archivu bajtově ověřené. Pokus o následné zobrazení
vzdálené verze v Safari zastavený při souběžně se měnícím okně; úspěšný
nativní deployment je ověřený a místní browser přehrávání potvrzené.

Log: vocabulary_en_sentence_audio_full_gate_20261113.log
SHA-256:7a55c1ad64af68f438134840913d5fcc12db6917aa1171dd26679e3754baed42
Privátní důkazy: data/private/vocabulary_en_sentence_audio_20261113/.
Scénář v Downloads: Vocabulary_EN_vetne_audio_2026-11-13.txt.


## 2026-11-13 20:54 CET — Poslech anglických slovíček přímo z galerie

Hotovo: Galerie má přepínač Učení / Poslech dostupný i při posouvání.
V Učení klik otevře kartu, v Poslechu přehraje existující anglickou MP3
a zůstane v galerii. Opakovaný klik zvuk zopakuje, jiná dlaždice zastaví
předchozí zvuk. České popisky ani režim vět jazyk poslechu neovlivní.

Rozhodnutí: Míla odsouhlasil návrh jedním klikem v explicitním režimu;
dvojklik se nepoužívá. Výchozí Učení, Poslech platí pro otevřenou stránku
a nepřepisuje uložený učební kontext. Mód se přepíná bez překreslení
dlaždic, posunu, změny filtrů nebo poslední učené karty.

Další krok: Aktualizovat stejný soukromý náhled a dokončit vlastní checkpoint.
Navrhované další kroky: Mílova iPhone přejímka; potom samostatné Pages p+n
obou vlastních kroků, větného audia a poslechu dlaždic.

Technický důkaz: 30 cílených Python testů včetně 34 Node scénářů PASS
/ 14,959 s. Pokrytý EN poslech s CZ popisky a režimem vět, opakování,
zastavení, neměnná historie/scroll/storage/bookmark, chybějící či neshodné
audio, pozdní chyba a návrat k učení. Safari desktop potvrdilo cat/cow
bez otevření karty, CZ popisky a stále dostupný přepínač ve středu galerie.
Pokus o úzké okno skončil noWindowsAvailable; fyzický iPhone není doložený.
Původní CSV, data karet a oba audio manifesty jsou shodné; nové TTS volání
nevzniklo. Nový krok mění pouze UI, bez nové persistence nebo workflow;
ověřuje se cílenou sadou a statickou branou. Předchozí plná brána 3831
patří checkpointu větného audia 3ca7bf0d, nikoli tomuto novému UI.


## 2026-11-13 20:58 CET — Poslech dlaždic dokončený v soukromém náhledu

Hotovo: Přepínač Učení / Poslech je dostupný i uprostřed dlouhé galerie.
Kliknutí v Poslechu přehraje existující EN slovíčko, v Učení otevře kartu.
Opakování, vystřídání zvuku a neměnný učební bookmark jsou ověřené.
Soukromý náhled obsahuje i předchozí větné audio; původní publikum zachované.

Rozhodnutí: Hotový vlastní terminálový krok, bez nových MP3, modelových
volání, persistence, TVBCP a PythonMF p+n. Cizí main/Will beze změny.

Další krok: Mílova iPhone přejímka přepínače a poslechu v soukromém náhledu.
Navrhované další kroky: Samostatné schválené Pages p+n obou vlastních kroků.

Technický důkaz: 30 cílených Python testů včetně 34 Node scénářů PASS
/14,959s. Safari desktop: cat/cow, opakování, CZ popisky a přepínač při
posunu; žádné otevření velké karty. Úzké okno nebylo dokončené po
noWindowsAvailable, fyzický iPhone čeká. Všechny čtyři zmrazené zdroje/testy
jsou shodné; CSV, data425 karet a oba audio manifesty jsou beze změny.
Log vocabulary_en_gallery_listen_targeted_final_20261113.log
SHA-256:d0f373de623d554609758e7533f62664e4c49fb7c48a1af12ec9e41e63d58b1f

Sites zdroj6592f7771f0f0004163cafd508e20843e63879ca, deployment
appgdep_6af76cd6193081918923335752327ec6 succeeded. Přesně tři změněné
frontend soubory, archiv bajtově shodný, audio se neměnilo.
https://vocabulary-en-layout-20261113.fairfly9.chatgpt.site
Scénář v Downloads: Vocabulary_EN_poslech_dlazdic_2026-11-13.txt.

Závěrečné doladění: hláška v přepínači má min-width:0 a zalamování dlouhých
slov, aby na úzkém displeji nevynucovala vodorovný posuv. Finální Node retest:
34/34 PASS /14,441s. Finální statická brána PASS, soukromá verze obsahuje
tuto stejnou CSS.


## 2026-11-13 23:33 CET — Kandidát pro schválené p+n obou vlastních kroků

Hotovo: V izolovaném integračním worktree jsou spojené vlastní commity
3ca7bf0d (850 větných MP3) a581fbed3 (Poslech/Učení dlaždic) nad main908a6aee.
Všechny vlastní zdroje a média zůstávají bajtově shodné, nezávislé Willovy
soubory také. Jediný konflikt v dodatcích Lessons Learned vyřešen zachováním
celých obou bloků; index zachovává oba proudy. Původní Data zůstává čistý.

Rozhodnutí: Míla zadal „OK, prosím p+n...“ pro navazující dva vlastní kroky.
Předchozí hranice ponechat Willovy commity stranou zůstává platná. Živý
GitHub audit našel originbb05bf8f a jeden cizí nepublikovaný commit908a6aee
(Knihovna: místní miniatury a katalogové žánry). Registrované p+n odesílá
celý origin/main..main; tento cizí commit nelze přeskočit.

Další krok: Po ověření kandidáta samostatně potvrdit, zda lze k odeslání
na GitHub zahrnout i908a6aee, nebo zachovat vlastní rozsah a počkat na jeho
vydání. Do té doby žádný main fast-forward, push, modelové předání ani deploy.
Navrhované další kroky: Schválené Pages vydání Vocabulary EN, potom fyzická
iPhone přejímka; publikace Knihovny do Cockpitu je jiný cíl.

Technický důkaz: Živý audit ready,1 pending cizí commit, poslední runtime
releasebb05bf8f completed/pushed/deployed. Po případném schválení širšího
GitHub rozsahu použít jediný submit_release(wait=True), projekt
project-vocabulary-en, centrálního release_executor a cíl github_pages.
Nový TVBCP nevzniká, běžící Cockpit ani Camino se tímto Pages krokem nenasazují.

Integrační přejímka: 30 cílených Python testů včetně34Node scénářů
PASS /23,001s; statická brána PASS. Kandidát je připravený k rozhodnutí
o přesném GitHub rozsahu, produkce ani main zatím nezměněné.


## 2026-11-13 23:45 CET — Schválený celý čekající GitHub balíček

Hotovo: Integrační kandidát b5a2383a je ověřený, vlastní větné audio
a poslech dlaždic i nezávislé Willovy zdroje jsou zachované.

Rozhodnutí: Na přesný dotaz k cizímu pending908a6aee Míla odpověděl
„Vezmi všechny commity prosím...“. Tím výslovně rozšířil GitHub rozsah
a překonal předchozí omezení ponechat Willův commit stranou. Schválené
jsou vlastní3ca7bf0d+581fbed3, integrační mergeb5a2383a a čekající908a6aee
včetně nutného dokumentačního potvrzení tohoto rozhodnutí. Nasazovaný
cíl zůstává project-vocabulary-en / github_pages. Nejde o nový runtime
deploy Knihovny/Cockpitu ani změnu služby Camino.

Další krok: Převzít ověřenou integraci na čistý main, zarovnat čisté profily
a předat přesný head registrovanému submit_release(wait=True). Role
release_executor se bere z centrálního JSON; očekávaná Terra/high.
Navrhované další kroky: Po potvrzeném Pages vydání fyzická iPhone přejímka.

Technický důkaz: Integrační30 Python testů včetně34Node PASS /23,001s,
statická brána PASS. Předpoklad před převzetím: main908a6aee, originbb05bf8f,
profily zarovnané a žádná aktivní release úloha. Konečný výsledek autoritativně
v privátní release účtence a závěrečném TXT v Downloads; tento zápis
sám budoucí push ani nasazení nepotvrzuje. Nový TVBCP nevzniká.


### 2026-11-14 00:03 CET — Oprava testovacího přípravku před vydáním

Hotovo: Příčina zastaveného vydání je dohledaná. Sedm testů následných
změn e-mailové služby selhalo při pomocném Git commitu, kterému chyběla
syntetická identita. Doplněny stejné lokální parametry -c jako u ostatních
commitů přípravku; produkční kód ani konfigurace Gitu se nemění.

Rozhodnutí: Platí Mílův výslovný souhlas se všemi čekajícími commity včetně
Willova908a6aee; cílem nasazení zůstává pouze Vocabulary EN GitHub Pages.
Předchozí job d8a4ccdf718ec01252b852bf3bb7d1d7 je zachován jako attention.

Další krok: Po cílených testech a statické bráně předat opravený přesný
main registrovanému vykonavateli s novou identitou vydání.

Navrhované další kroky: Dokončit Pages ověření a Mílův poslech na iPhonu.
Bez nového TVBCP; jeho založení nebylo dohodnuté.

Technický důkaz: Původní plná brána3858 testů /731,197s skončila právě
7 chybami ve followup_install, před push. Čerstvý ls-remote potvrdil původní
origin bb05bf8f; publikace nezačala. Původní log zachovaný v soukromém
vocabulary_en_audio_listen_release_20261114_fixture_fix/failed_gate_20261113.log.
Cílená sada30 testů PASS /19,618s a statická brána PASS; vlastní
logs/vocabulary_en_release_fixture_* protokoly. Konečný provozní výsledek patří do privátní účtenky a Downloads.


## 2026-11-14 10:33 CET — Sekundová česká nápověda při poslechu

Hotovo: Kliknutí na dlaždici v Poslechu přehraje původní EN slovíčko
a na1000ms ukáže český popisek. Potom se vrátí původní popisek.
Míla upřesnil zachovat anglický název i v českém směru procvičování;
CZ→EN ani EN→CZ proto jazyk běžného popisku nemění. Stávající samostatný
přepínač popisků EN/CZ zůstává zachovaný. Míla předchozí produkční
slovník i nalezené věty přijal; nejde o novou syntézu nebo úpravu obsahu.

Rozhodnutí: Nový klik obnoví celou sekundu. Jiná dlaždice vrátí předchozí
popisek hned. Změna režimu, filtrů, jazyka popisků, otevření učení
a opuštění stránky krátkou nápovědu ukončí. Poslech nemění bookmark,
historii, filtry ani uložený učební kontext.

Další krok: Samostatné Pages p+n nové české nápovědy. Předchozí souhlas se všemi commity patřil dokončenému
vydání9ab2c87b a nepředstírá publikaci tohoto nového kroku.

Navrhované další kroky: Po schváleném vydání ověřit délku nápovědy na iPhonu.
Nový TVBCP není dohodnutý, proto nevzniká.

Technický důkaz: Nativní Safari v místním náhledu zobrazilo po kliknutí
kočka a následně znovu cat se zvukem, bez otevření karty. Node sada má
37 scénářů PASS /35,520s včetně časování999/1000ms v obou směrech,
opakovaného kliknutí a rušení nápovědy. Statická brána PASS. Finální protokol: vocabulary_en_translation_flash_node_final_20261114.log.
Původní CSV,425 karet, oba audio manifesty, obrázky i MP3 zůstávají beze změny.
Fyzický iPhone a nové produkční vydání tímto krokem nejsou potvrzené.


## 2026-11-14 10:39 CET — Schválené produkční vydání české nápovědy

Hotovo: Izolovaná integrace c372ada6 nad publikovaným main e53dd971.
JS, testy a návod jsou bajtově shodné s37 scénáři PASS. Obě historie
paměťových zápisů jsou zachované, původní média i cizí práce také.

Rozhodnutí: Míla zadal „OK, prosím dej na produkce jestli je to možné...“.
Cíl project-vocabulary-en / github_pages, cesta vocabulary-en/.
Bez runtime nasazení Cockpitu, bez syntézy a bez nového TVBCP.

Další krok: Po bezpečné připravenosti kanonického main a profilů
převzít přesnou integraci a jednou zavolat submit_release(wait=True).

Navrhované další kroky: Fyzická přejímka krátké nápovědy na iPhonu.

Technický důkaz: Při přípravě main e53dd971 odpovídá GitHubu, ale má
cizí rozpracované Vocabulary FR a nezařazený agent_supervisor 2.md.
Živý github-batch-audit: audit_failed; deploy-audit: ready=false.
Cizí obsah se nemění, nezařazuje ani neodkládá. Release nebyl spuštěný.
Konečný výsledek patří do privátní účtenky a Downloads.


## 2026-11-14 10:41 CET — Připravené přesné vydání, čeká rozhodnutí o okolním stavu

Hotovo: Kandidát obsahuje českou nápovědu c372ada6 a aktuální kanonický
main4ad82a7f. Vlastní gallery.js,37scénářový test i návod jsou stále
bajtově shodné s otestovaným checkpointem; cizí FR změny se neupravovaly.

Rozhodnutí: Produkční Vocabulary EN vydání je výslovně schválené.
Nový cizí pending commit4ad82a7f vznikl souběžně a nebyl součástí
předchozího konkrétního publikačního balíčku. Jeho GitHub zahrnutí
vyžaduje potvrdit rozsah. Samotné nasazení zůstává Vocabulary EN Pages.

Další krok: Potvrdit zahrnutí4ad82a7f do GitHub balíčku a zachování
starší nezařazené kopie agent_supervisor 2.md v ignorovaném privátním
archivu. Teprve pak čistý main/profily a registrované p+n.

Navrhované další kroky: Krátká fyzická iPhone přejímka po publikaci.

Technický důkaz: Cizí nezařazený soubor je7777B, SHA-256
08bf3f5c2fa41d235ea9678e978cfe6dce9700863e0dbe8e2bb1b78c17717f12.
Nemá se mazat ani commitovat; navržený archiv zachová přesné bajty.
Živá publikační brána odmítá nečistý main a nezarovnané profily.
Dosud žádný push, modelové předání ani deploy. Konečné provozní důkazy
patří do privátní účtenky a Downloads, nikoli do dalšího pending commitu.
