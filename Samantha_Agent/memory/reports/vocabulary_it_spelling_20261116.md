# Vocabulary IT — Slovo a obrázek


### 2026-11-16 11:09 CET — Slovo a obrázek: zápis, zvuk a čtyři možnosti

Hotovo: Místně vznikl samostatný dospělý režim Slovo a obrázek. Převzal
všechny právě nastavené filtry Přehledu včetně A–D/obtížných, více témat,
hledání, slovního druhu, obtížnosti a posledních N. Čtyři velké bezejmenné
obrázky2×2; dole postupné úseky la · var · si, plynulé spojení lavarsi a
existující italská MP3. Odpovědi se zpřístupní po poslechu. Chybná volba
zešedne, přeškrtne se a vyřadí; zbývající pokusy zůstávají. Po správné volbě
jedna velká karta, přesný italský zápis, český význam a znovu italský hlas.
Karta zůstává do Další. Jednou chybované heslo má ještě jedno opakování na
konci kola; souhrn nabízí nové kolo z chyb. Profily ani obtížné příznaky
se automaticky nepřepisují. Další vlastní psaní zpaměti je pozdější etapa.

497 explicitních jazykových záznamů zachovává přesně původní IT/CZ zápis,
interpunkci/case/diakritiku;495 redakčně rozdělených, éclair/brioche zatím
výslovně celé. Zdroje Crusca/Treccani a poznámky u sporných slov v katalogu.
Každý význam umí ve společném výběru vytvořit čtveřici, posledních20 také20/20.
Stejné heslo/obraz, shodný český význam, related a ručně vymezené obrazové
kolize se nekladou proti sobě; barvy soutěží s barvami. Příliš úzký filtr
vysvětlí chybějící čtveřici, nepůjčuje si možnosti zvenku. V okruhu Barvy
jsou samostatně vhodné4 ze6; zbývající2 jsou dostupné v širším výběru.

Rozhodnutí: Míla schválil celý návrh a vývoj první verze. Slabiky se v této
verzi zobrazují, při spojení se čte celé slovo současným hlasem Elsa.
Žádná nová syntéza, změna původních CSV/obrazů/EN ani povolení nového p+n.
Předchozí oprava odkazu Cockpitu je již vydaná2f6c783a, jobae50fd8846bee6e2839b23b1d756a0e1,
774 testů převzatých, smoke5/5; tuto starší publikaci neopakovat.

Další krok: Fyzický proklik nového režimu a poslech podle TXT v Downloads;
potom samostatně schválené Pages p+n tohoto nového herního kroku.

Navrhované další kroky: Doladit obrazové kolize podle používání; později
navazující psaní slova zpaměti; pokračovat jazykovou revizí metadat/vět.

Technický důkaz:29 JS scénářů skutečné galerie/profilů/procvičování PASS;
6 Python testů dat/assetů včetně JS wrapperu PASS. Všech497 UID má přesné
pieces.join('')==it; homografy konzistentní, nesprávné texty/cesty/slabiky
odmítnuté. HTTP17/17 zdrojů a ukázkových obrázků/MP3 přesných. Zkoušené
chyby zvuku/obrázku,15s obrazový a20s zvukový timeout, přímý replay po blokovaném autoplay,
pozdní callbacky, opakované kliky, klávesy1–4, reduced motion, návrat,
historie a bfcache. Výběry A–D/původní poslední karta se nemění.
Fyzická vizuální/přehrávací přejímka tohoto nového režimu není doložená:
CUA Safari i Finder vracejí cgWindowNotFound, browser access host unavailable.
Nepovažovat DOM/HTTP za skutečný render nebo iPhone/Android přejímku.
Finální brána, otisk zdrojů a lokální checkpoint: private/vocabulary_it_spelling_20261116.

Implementace
- VocabularyIT/vocabulary_it_spelling.json: explicitní jazyková revize všechUID.
- VocabularyIT/vocabulary_it_practice.py: přesná validace a lokální --write výstupu;
  žádná síť ani TTS. Volání z kořene PythonMF:
  python3 VocabularyIT/vocabulary_it_practice.py --write
- docs/data/vocabulary-it-quiz.json: UID+IT/CZ+image+thumbnail+pieces/format/conflicts.
- docs/vocabulary-it/practice.js: samostatný IT namespace; bez zápisů do úložiště.
- Gallery používá getSelection/buildSelection, nikoli druhé nezávislé filtry.
- Každá nová otázka/odchod ruší časovače a přehrávání; token ignoruje pozdní callback.
- I zaseknuté audio po20s dovolí explicitní replay/přeskočení; odchody nikdy nečekají na ended.
- Tlačítko Přehled/Změnit výběr vždy otevírá galerii, i při vstupu ze studijní karty.
- Reload otevře přípravu kola s uloženým filtrem; rozběhnuté kolo se neobnovuje.
- Builder po změně slovníku potřebuje jazykově doplnit nové UID a zdrojový hash;
  neověřené dělení se nikdy automaticky neoznačí jako reviewed.
- Obrazové skupiny jsou konzervativní redakční rozhodnutí, nepředstavují úplnou
  lidskou sémantickou přejímku všech možných čtveřic abstraktních významů.
