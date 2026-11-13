# VocabularyEN web: obrazové kartičky pro opakování slovíček

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
