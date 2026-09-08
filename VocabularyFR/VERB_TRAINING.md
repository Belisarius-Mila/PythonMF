# Trénink francouzských sloves

## Dohodnuté chování – 8. 9. 2026

- Samostatný tréninkový screen v desktopové aplikaci; první verze pouze présent.
- Vlevo 100 sloves s českým překladem a výběrem jednoho slovesa. Po výběru se
  seznam zasune, tlačítkem jej lze znovu otevřít.
- Záhlaví: infinitiv a jeho přečtení, S/P, osoby 1/2/3, smyčka a interval.
- Smyčka prochází osoby pouze zvoleného čísla: S nebo P.
- Sekvence: zájmeno a tvar → tři věty postupně zobrazené a přečtené → velké
  zájmeno a postupné odhalení tvaru po písmenech → přečtení celého tvaru.
- Vpravo kontextový obrázek. České věty pouze na vyžádání pod obrázkem,
  bez automatického zobrazení a čtení.
- Pauza a zopakování; volitelný režim „Zkus si vzpomenout“ skryje předchozí
  ukázky a před závěrečným odhalením nechá čas na vlastní odpověď.
- Bez smyčky se po sekvenci čeká. Změna slovesa zastaví zvuk i animace.
- `falloir` má pouze `il faut`: dostupná je jen S/3; smyčka opakuje tento
  tvar s novým výběrem vět, nevytváří neexistující osoby.
- Budoucí zvuk musí fungovat na Macu i Linuxu. Dosavadní macOS `say` není
  linuxovým řešením; přehrávání připravených nahrávek je zatím návrh.

## Převzatá data

- `VerbeTraining.csv`: přesný seznam 100 dodaných sloves a českých významů,
  ve stejném pořadí jako zdroj `francouzstina_100_sloves_cesky.csv`.
- `VerbeFR.csv`: společná knihovna má 107 sloves. Prvních 100 odpovídá novému
  seznamu; sedm původních sloves mimo tento seznam zůstává na konci. Původní
  tvary všech časů i výběrové značky jsou zachované. Nová slovesa mají pouze
  dodané přítomné tvary; chybějící budoucí a minulé tvary zůstávají prázdné.
- `VerbeSentences.csv`: všech 1 800 nezměněných FR/CZ dvojic ze zdroje
  `francouzstina_100_sloves_1800_vet.csv`, doplněných o explicitní vazby.

Sloupce vět: `Id`, `InfFR`, `Tense` (`present`), `Number` (`S`/`P`),
`Person` (`1`/`2`/`3`), `Pronoun`, `Form`, `Sentence`, `SentenceT`.
`Pronoun` zachovává konkrétní zájmeno věty, tedy také `elle` a `elles`.
Zkrácené `j'` se při skládání tvaru připojuje bez mezery.

Zdrojové soubory nemají záhlaví. Obsah je řazen po 18 větách na sloveso,
po třech větách na osobu. Vazby byly ověřeny podle zájmen a shodného tvaru
ve všech větách skupiny, nikoliv pouze podle pořadí. Výjimkou je všech
18 vět pro `falloir`, které patří do S/3.

U běžného slovesa má každá osoba právě tři věty: náhodný výběr tří bez
opakování tedy zatím mění jen jejich pořadí. U `falloir` vybírá tři z 18.
Import kontroluje strukturu a návaznost; není úplnou jazykovou redakcí vět.

## Stav

Hotový je import a kontrola dat. Nový screen, přehrávání, obrázkový audit
a sestavení aplikace ještě nejsou implementované. Příští krok je funkční
screen nad těmito daty a ověření jedné celé sekvence pro `aller` i `falloir`.
Živé uživatelské CSV mimo zdrojový projekt se tímto importem nemění.
