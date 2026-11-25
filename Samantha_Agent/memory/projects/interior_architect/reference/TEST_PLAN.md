# Testovací plán

| ID | Scénář | Očekávání |
|---|---|---|
| T01 | Hash originálu před/po editaci | Neměnný soubor |
| T02 | Uložení a načtení masek, zoom/pan | Identické nativní souřadnice |
| T03 | Překryv všech režimů | Přísnější ochrana vítězí |
| T04 | Kandidát mění celý obraz | Nula změn chráněných pixelů |
| T05 | Feathering a PNG round-trip | Žádný únik mimo masku |
| T06 | Odlišné rozměry/perspektiva | Odmítnutí nebo neověřený stav, ne slepý resize |
| T07 | Undo/redo, guma, polygon | Správná historie a rasterizace |
| T08 | Neplatné JSON a migrace | Validace, zachování starých dat |
| T09 | Neznámé rozměry | Žádné vymyšlené hodnoty |
| T10 | Pokus posunout zamčené okno/dveře | Mutace zamítnuta |
| T11 | Dveře dovnitř, závěsy vpravo zvenku | Správný oblouk v 2D i 3D |
| T12 | Překryv nábytku a dráhy dveří | Kolize detekována |
| T13 | Změna kamery | Identická geometrie a dispozice |
| T14 | Uložení a obnovení variant | Bez ztráty historie |
| T15 | Placený nebo neznámý adaptér | Bez souhlasu žádné volání |
| T16 | Adaptér bez masek | Transparentní omezení |
| T17 | Offline režim | Editor, 2D/3D a testy fungují |
| T18 | Cockpit regresní testy | Stávající funkce zachovány |
| T19 | Neověřitelná geometrie fotografie | Stav unverified, nikoli verified |

Použij syntetické RGB/RGBA rastry s jednoznačnými barvami a testovací scény. Testovací kandidát není AI výsledek. Pro každý test zaznamenej příkaz, očekávání, skutečný výsledek a stav. Ručně ověř ovládání, výkon a spotřebu RAM na cílovém hardwaru; nevymýšlej benchmarky. První sprint musí projít T01–T07, T15–T16 a relevantní regresí T18.
