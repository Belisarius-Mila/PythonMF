# Obory knih a průběžně rostoucí filtry —14.11.2026

Lokálně vyvinuté oddělené obory Konspektu, žánry/formy, témata a jazyky.
Katalogový snapshot náleží konkrétnímu záznamu a ISBN. Vlastní/původní tagy
jsou samostatné; původních12 provizorních názvů neurčuje nové obory.
Rychlé i podrobné přidání a editace ukládají snapshot až po Uložit.
Stávající knihu lze doplnit jednotlivě katalogovým dohledáním v editoru.
Žádná dávková změna živého archivu, nový placený model ani nová aplikace.

26 hlavních oborů odpovídá živé nabídce Knihovny.cz. Přesný převod MARC072$a
se opírá o veřejnou tabulku MZK recordmanager2; schéma musí být Konspekt.
Pokud je přítomno validní072$9, převezme se jeho číselný obor. Chybějící
údaje se nedovozují z názvu či témat. DTD/entity a nejednoznačné XML se
ignorují. Žánry a témata se berou z typovaných polí stejného záznamu.
Jazyk lze převzít z MARC041$a/008; jazyk originálu041$h není jazykem knihy.

Filtry nabízejí jen skutečně zastoupené hodnoty s počty a Bez zařazení.
Uvnitř skupiny OR, mezi skupinami AND. Počty vylučují vlastní skupinu,
respektují ostatní. Vybrané nulové hodnoty zůstávají viditelné. Přehled se
po uložení rozšíří bez ručního spravování slovníku. Obor a žánr jsou hlavní
filtry, témata/jazyk/původní štítky jsou v dalších filtrech.

Kompatibilita: původní tagy zůstávají beze změny. Staré payloady mají stejné
fingerprinty a pokračují se stejným ID. Nový snapshot je součástí identity
jen při jeho přítomnosti v payloadu. Replay/status neprovádí nový lookup.
Běžný edit snapshot zachová, změna ISBN ho odstraní; s novým ISBN může
výslovné uložení přijmout nový odpovídající snapshot.

Ověření:116 cílených testů PASS včetně Node regresí a archivní kompatibility;
19 parserových testů znovu PASS po závěrečné ochraně dlouhého072$9.
Živý lookup ISBN9788024932460 prokázal Beletrie, české a humoristické příběhy,
téma muži a ženy — humor i zdrojový odkaz vybraného záznamu. Stejné ISBN
má více katalogových výsledků; ostatní záznam ani agregované fasety se
nepoužijí k třídění vybrané knihy.

Skutečný izolovaný headless prohlížeč: OR/AND, závislé počty, zachování
nulového výběru, Bez zařazení, staré štítky, seskupení, uložení snapshotu
v testovacím archivu a okamžité doplnění nového oboru PASS.390/1280 bez
přetékání,0 neodchycených výjimek a0 produkčních POST. Fyzický iPhone zatím
neověřen. Soukromé doklady data/private/book_categories_20261114/;
logy book_taxonomy_*_20261114.log.

Plná povinná brána provedena nad zmrazeným zdrojem:3885 testů za817,2s,
0 selhání kontrol,31 skip a1 chyba syntetického RPC testu při limitu1s
na start/odpověď vlastního procesu. Návratový kód tohoto plného běhu byl1,
nejde o čistý PASS celé brány. Celý nezměněný modul
tests.test_codex_appserver_dispatch následně samostatně42 testů PASS
za1,457s; přesný původní chybující test je mezi nimi. Žádný zásah do
App Serveru ani jeho časových limitů. Úspěšné nesouvisející testy se znovu
neopakují. Pro publikaci zůstává povinná vlastní čerstvá brána.

Opravené původní kontrakty28 PASS, finální knihovní sada116 PASS a samostatný
frontend/inventura retest56 PASS. Browser, živý katalog a podrobný formulář
ověřené; datové soubory po odmítnutí cizího ISBN zůstaly totožné. Závěrečná
statická brána je součástí místního uzavření. Stav lokální, bez push a nasazení.
Míla chce společné vydání až po dokončení souběžné práce Data.

Zdroje:
- https://www.knihovny.cz/swagger-ui/?url=%2Fapi%3Fopenapi
- https://www.knihovny.cz/api?openapi
- https://github.com/moravianlibrary/recordmanager2/blob/master/cz.mzk.recordmanager.server/src/main/resources/mapping/conspectus_category_subcategory.map
- https://github.com/moravianlibrary/RecordManager/blob/master/mappings/conspectus_category.map
