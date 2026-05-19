# VocabularyEN Missing Nouns Image Plan

Doporucene nazvy novych souboru do `Pict/` pro podstatna jmena a noun-like fraze, ktere ted padaji do fallbacku.

Pouzij jeden z podporovanych formatu:
- `.png`
- `.jpg`
- `.jpeg`
- `.webp`

Doporuceny naming:
- mala pismena
- bez diakritiky
- vice slov spojit podtrzitkem

## Doporučene soubory

| Order | EN | CZ | Doporučený filename stem |
| --- | --- | --- | --- |
| 2 | airport | letiště | `airport` |
| 3 | animal | zvíře | `animal` |
| 4 | baby elephant | slůně | `babyelephant` |
| 17 | bus station | autobusové nádraží | `busstation` |
| 20 | cat | kočka | `cat` |
| 24 | cow | kráva | `cow` |
| 25 | crocodile | krokodýl | `crocodile` |
| 28 | doctor | lékař | `doctor` |
| 29 | document | dokument | `document` |
| 32 | duck | kachna | `duck` |
| 33 | elephant | slon | `elephant` |
| 36 | eyes | oči | `eyes` |
| 40 | field | pole / louka | `field` |
| 41 | film | film | `film` |
| 47 | giraffe | žirafa | `giraffe` |
| 48 | goat | koza | `goat` |
| 60 | horse | kůň | `horse` |
| 65 | lake / pond | rybník | `lakepond` |
| 68 | lion | lev | `lion` |
| 73 | monkey | opice | `monkey` |
| 75 | name | jméno | `name` |
| 78 | office | kancelář | `office` |
| 82 | popcorn | popcorn | `popcorn` |
| 83 | rabbit | králík | `rabbit` |
| 85 | rhino | nosorožec | `rhino` |
| 95 | teacher | učitel | `teacher` |
| 96 | ticket | lístek | `ticket` |
| 102 | zebra | zebra | `zebra` |
| 118 | orange | pomeranč | `orange` |
| 133 | pound | libra (měna) | `pound` |

## Poznamky

- Pokud ulozis napr. `Pict/cat.png`, anglicke `cat` se chytne i bez dalsiho mapovani.
- `mapping.json` je dulezity hlavne pro ceske tvary a synonymni varianty.
- Po pridani obrazku spust:

```bash
python3 VocabularyEN/sync_vocabulary_en_to_docs.py
```
