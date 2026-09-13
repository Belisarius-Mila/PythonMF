# Vocabulary FR / IT — aktualizace z NewWords.txt, 13. 9. 2026

Hotovo: Mílovo FR má 234 řádků (+7), IT 471 (+8). Každá nová položka má
český překlad, Sentence a SentenceT. Původní řádky včetně L/HT jsou zachované;
nové používají výchozí L=ne, HT=ne. U Jany doplněno 7 chybějících párů vět
a opraveny dva české překlepy; všech 413 řádků má obě věty.

## Přidané položky

| Jazyk | Slovíčko | Česky | Obrázek |
| --- | --- | --- | --- |
| FR | faim | hlad | hunger |
| FR | chut ! | psst, ticho, tiše | hush |
| FR | sommeil | spánek, ospalost | goodnight |
| FR | durer | trvat | duration |
| FR | tout le monde | všichni, každý | team |
| FR | vol | let | flight |
| FR | couverture | deka, přikrývka | blanket |
| IT | piano | pomalu, tiše | slow |
| IT | attore | herec | actor |
| IT | usi | používáš | mobilephone |
| IT | usare | používat | mobilephone |
| IT | sito | webová stránka, web | website |
| IT | attrice | herečka | actress |
| IT | vinti | vyhrané (mužský rod množného čísla) | win |
| IT | quelle | ty, tamty (ženský rod množného čísla) | those |

Existující položky domenica, vincere, viaggio, vecchio, già, perché, mai
a auguri se neduplikovaly. Poslední oprava v zadání má přednost: chut ! = psst,
nejde o chute. Couverture patří do FR. Pro ilustraci jsou použité významy
vol = let, piano = pomalu/tiše a couverture = deka. Usi doplňuje infinitiv
usare; příklad s vinti zachovává mužský rod množného čísla. Quelle je ukazovací tvar.

## Obrázky a distribuce

- Osm nových ilustrací: hush, duration, blanket, actor, actress, website,
  those a yoga. Vytvořeno vestavěným ImageGen v dosavadním stylu a vizuálně
  posouzeno Adamem podle výslovného pověření Míly; bez schvalovací galerie.
- Každý WebP má 1 254 × 1 254 px a nejvýše 250 000 B; dohromady 1 555 244 B.
- Prompty, kontrolní součty a parametry:
  [generation_report.json](../../../PictNew/generated/20260913_fr_it_refresh/generation_report.json).
  Obrázky jsou v Pict; pracovní výstupy v PictNew/generated/20260913_fr_it_refresh.
- Kanonické české mapování má 1 082 vazeb (+27), je abecední a zachovává
  všechny původní klíče i hodnoty. Janina sdílená kopie je bajtově shodná;
  všech osm nových obrázků je zkopírovaných také do jejího Pict.
- Zápis CSV a mapování měl soukromé zálohy, kontrolu nezměněného vstupu
  a atomické nahrazení. Janiny CSV ani soukromé zálohy nepatří do Gitu.
- NewWords.txt je uložený se zadáním; odstraněny jen koncové mezery a
  nadbytečný prázdný poslední řádek, slovní obsah zachován.

## Starší Janiny vazby

Společný audit navíc našel devět starších řádků bez obrázku v Pythonistě.
Doplněné české vazby: sympatická → likeable, recept → cook, vejce → breakfast,
ukázat → those, dodávka zboží → delivery, tým/družstvo → team,
lepší → good, hráč → team, boty/obutí → shoes. Jde o existující ilustrace;
recept, lepší a hráč používají obecnější tematické obrázky. Všechny původní
mapovací vazby zůstaly zachované. Starší obecné ilustrace jsou samostatný námět.

## Ověření a hranice

- Skutečné resolvery desktopu i všech tří Pythonista variant ověřily
  FR Míla 234, FR Jana 413 a IT Míla 471 řádků: žádný chybějící obrázek.
- Všechny dotčené položky vybírají zamýšlenou ilustraci na obou platformách.
- Celkem 790 použitých obrazových souborů se dekóduje pomocí Pillow; shoda SHA-256 osmi nových
  obrázků v obou knihovnách a bajtová shoda mappingů potvrzená.
- Zachování všech původních Mílových řádků a pouze plánovaných změn u Jany
  ověřeno proti zálohám. Janina kontrola vět: 413 řádků, 0 dalších oprav.
- Šest existujících testů kanonického mappingu i rychlá statická brána prošly.
- Místní data a sdílená iCloud složka jsou ověřené. Doručení iCloudem na
  vzdálená zařízení a skutečný běh na iPhonu se tím nepotvrzují.
- Kód aplikací se neměnil; nové sestavení ani nasazení Cockpitu nejsou potřeba.

Další krok: načíst aktualizované CSV a Pict v používaných aplikacích.
Při ručním přenosu na iPhone patří příslušné CSV do datové složky aplikace,
mapping.json do jejího Pict a osm nových WebP také do Pict. Existující
synchronizace může tento přenos provést; poté aplikaci znovu otevřít.

Lexikální podklady: [Larousse — chut](https://www.larousse.fr/dictionnaires/francais/chut/15925),
[Larousse — couverture](https://www.larousse.fr/dictionnaires/francais/couverture/20048),
[Treccani — quello](https://www.treccani.it/vocabolario/quello/),
[Treccani — vincere](https://www.treccani.it/vocabolario/vincere/).
