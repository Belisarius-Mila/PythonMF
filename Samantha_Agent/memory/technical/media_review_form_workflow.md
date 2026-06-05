# Media review form workflow

Zalozeno: 2026-06-05
Priorita: 1
Typ: znovupouzitelny workflow / kandidat na tool

## Smysl

Opakovatelny lokalni formular pro rucni trideni fotek a videi v rodinnych
projektech. Vznikl pri USA 2019 jako detailni review smesnych videi, ale ma se
pouzivat i pro dalsi projekty, kde je potreba rozhodovat po jednotlivych
souborech.

## Co ma formular umet

- Nacist lokalni CSV s radky pro jednotlive soubory nebo bloky.
- Ukazat nahled/thumbnail.
- U videi nabidnout tlacitko `Přehrát video` pres lokalni read-only server.
- Prubezne ukladat rozpracovany stav do `localStorage` v prohlizeci.
- Pri znovuotevreni formulare automaticky obnovit autosave, pokud odpovida
  poctu radku v CSV.
- Nabidnout samostatne `Stáhnout autosave CSV`, aby bylo mozne zachranit
  rozpracovanou praci i pred finalnim exportem.
- Umoznit editovat rozhodovaci pole:
  - `use_in_film`
  - `correct_day`
  - `title`
  - `confidence`
  - `notes`
- Filtrovat podle pouziti a textu.
- Stahnout upravene CSV.

## Bezpecnost

- Originaly nikdy nemazat, neprejmenovavat ani nepresouvat.
- Formular pracuje jen s kopii rozhodovaciho CSV.
- Autosave je lokalni v danem prohlizeci a profilu; neni to zaloha v gitu ani
  na disku projektu, dokud Mila nestahne CSV.
- Fotky, videa, realne manifesty, GPS data, thumbnails a rodinne poznamky patri
  do `data/private/` nebo mimo repo, ne do gitu.
- Do gitu patri jen generatory, sablony, workflow a git-safe souhrny.
- Po rucni editaci formulare brat nejnovejsi odpovidajici CSV z `~/Downloads/`
  jako zdroj pravdy, aby se neprepsaly rucni poznamky.

## Lokalne servery

Review formular a nahledy mohou bezet napr. na:

```text
http://127.0.0.1:8789/
```

Originalni videa pro prehravani mohou bezet read-only nad zdrojovou slozkou na:

```text
python3 -m http.server 8790 --bind 127.0.0.1
```

Formular pak sklada URL videa z relativni cesty v CSV a video base URL, napr.:

```text
http://127.0.0.1:8790/iphonemila/IMG_1040.MOV
```

## Aktualni exemplar

Soukromy exemplar pro USA 2019 je mimo git:

```text
data/private/family_memory_films/usa_2019/02_review/mixed_2019_08_05/mixed_2019-08-05_form.html
data/private/family_memory_films/usa_2019/02_review/mixed_2019_08_05/mixed_2019-08-05_review.csv
```

URL v aktualni relaci:

```text
http://127.0.0.1:8791/mixed_2019_08_05/mixed_2019-08-05_form.html?v=20260605-1710
```

## Dalsi krok pro zobecneni

Vytvorit git-safe generator nebo sablonu, ktera vezme:

- vstupni CSV,
- nazev formulare,
- cestu k nahledum,
- video base URL,
- seznam editovatelnych poli,

a vyrobi HTML formular do `data/private/...`.
