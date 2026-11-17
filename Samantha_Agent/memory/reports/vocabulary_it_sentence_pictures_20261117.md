# Vocabulary IT — obrazy ke všem větám a kontinuální procvičování

Stav 2026-11-17 13:26 CET: místně hotový kandidát, jeden vlastní commit, bez push/nasazení.

## Uživatelský výsledek

Všech1096 aktivních vět má1–5 souvisejících obrazových karet. Celkem1963
vazeb na1091 různých existujících významů. Rozložení:448 vět s1 obrazem,
459 se2,161 se3,26 se4 a2 s5. Zejména krátké věty Ecco… vyžadují jeden
pojem; nepřidávají se nevyslovené věci jen pro zaplnění pěti míst.

IT dosud neměla novou kontinuální smyčku EN; přenesena se dvěma režimy:
Slovíčka a Věta + slovíčko. V kombinaci se ukážou IT popisky, celá IT věta
a CZ překlad; po skutečném konci zvuku a celé pauze se obnoví velký cílový
obraz/IT heslo/CZ význam, přečte heslo a pokračuje dál. Výběr se na konci
opakuje. Filtry i již výslovně vybrané pořadí/zamíchání se zachovávají.

Ovládání na velké kartě, bez nové záložky: Smyčka → Věta + slovíčko → Spustit.
Pauzy1/2/4/6 s, default2; pozastavení/pokračování opakuje přerušený úsek od
začátku, Ukončit obnoví ruční otázku. Historie/reload/bfcache nespouští zvuk.

## Významová kontrola

Celý korpus1096 vět prošel čtením a redakčními zásahy před uložením finálních
UID. Čtecí kandidáty navrhl soukromý offline helper; nejde o živou inferenci
ani o pravidlo, podle kterého by prohlížeč hádal význam. Kanonická data
obsahují výsledná explicitní UID, významové snapshoty a skutečné úseky vět.

Příklady důležitých rozhodnutí:
- Porta un anello: portare/nést-nosít, nikoli porta/dveře.
- Mi lavo le mani: lavarsi/umýt se, nikoli praní prádla (lavare).
- a piedi: celé spojení pěšky místo samotného chodidla.
- per favore: zdvořilé prosím místo podstatného jména laskavost.
- libro giallo: detektivka místo samostatné žluté barvy.
- Oggi il tempo è bello: počasí místo času.
- Devo andare via: odejít místo via/ulice, i u staré karty vit-0166.
- accendo la luce: rozsvítit místo falešného tvaru osobního jména Luca.
- znalost/umění, přítel/partner, místo/čas, piano hudba/pomalu a další
  polysemy se neodvozují z podobnosti řetězce.

Titulek obrázku zůstává základní heslo, např. nero při skutečném nera ve větě;
slovo ve větě ani český překlad se tím nepřepisují. Výsledná metadata jsou
připnutá k oběma původním větám a IT/CZ významům. Po driftu je klient odmítne.

## Implementace a hranice

Nový standard-library build_sentence_pictures.py a kanonický
vocabulary_it_sentence_pictures.json. Export do docs/data samostatný,
optional/asynchronní. Builder kontroluje úplné pokrytí,1–5, UID/aktivitu,
pořadí/doslovnost/UTF16, významy, stejné obrazy a přesné bezpečné místní assety.
Elize l'acqua podporuje acqua; hranice slov brání podřetězcům.

Kontexty se ukážou současně nad větou; na desktopu až5 sloupců, v úzkém
pohledu více řádků. Přednačtou se nejvýše10 náhledů pro aktuální/následující
větu. Osobní filtry vybírají cíle, kontext může pocházet z celého slovníku.
Žádný zápis do profilu/pokroku/PIN. Ruční hádání věty a původní hra/psaní
zůstaly zachované; fresh pokusy v IT přehrávači se nesmějí změnit na sdílený
seekovaný prvek. Jeden vyhrazený odemknutý Audio element platí jen pro smyčku.

Výpadek obrazu odstraní jen vadnou miniaturu, bez všech obnoví původní kartu.
Pozdní callback nesmí měnit novou fázi; pozdní metadata čekají další větu.
Vadné audio, zamítnutí nebo90s timeout smyčku pozastaví, tiché přeskočení není.

## Ověření

5 nových Python kontrol PASS; celý skutečný JS modul56 scénářů PASS, včetně
11 nových testů smyčky/kontextů a všech dosavadních kontrol psaní. Kontroluje
se i všech1096 map/1963 spanů a chybné reference, filtry A/hard bez zápisu,
jednokartová smyčka, load/ended/pauza, staré callbacks, chyby, opožděná data,
manual mode, bfcache/reload a výslovný shuffle. Pytest se nově nezavádí.

Safari Mac na samostatném localhost původu skutečně ukázalo4 pojmy
gonna/nero/camicia/bianco nad celou větou Oggi indossa una gonna nera e una
camicia bianca. a českým překladem, potom obnovilo velkou gonna/sukně kartu.
Pauza/pokračování/6s mezera a ukončení ověřené. Vlastní okno/server zavřené,
původní Safari okno zachované. Telefon ani Mílův poslech všech vět se netvrdí.

Původních1096 hesel/vět/rodů,18 témat, katalog/spelling,471 CSV řádků,
mapping, oba audio manifesty/4222 MP3 a všechna média se nemění. EN a FR
produkční soubory nejsou v diffu. Žádné nové nahrávky, ilustrace či placené
API. Finální programem vybranou bránu, zdrojové otisky a jediný checkpoint
určuje private/vocabulary_it_sentence_pictures_20261117/completion.json.

## Předání a další krok

Data ebbd základc6bb0cd4, nový krok jen ve vlastní větvi. Míla požaduje
jeden commit; žádný samostatný dokumentační commit ani p+n se nepřidává.
Po uzavření navázat Janinou FR podle TXT v Downloads, oddílu13/464 karet.
Nová FR aplikace ani zásah do Janina sdíleného CSV nejsou součástí tohoto
IT commitu. Integrace/publikace IT jsou samostatné; dříve Willovi předané
vydání se zde nesmí obnovovat. LEDA audio znovu negenerovat,1–2 odložené.
