# Trénink francouzských sloves

## Dohodnuté chování – 8. 9. 2026

- Samostatný tréninkový screen v desktopové aplikaci; první verze pouze présent.
- Vlevo 107 sloves s českým překladem a výběrem jednoho slovesa. Po výběru se
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
- Zvuk nové obrazovky je místní: macOS `say` / Thomas, Linux `espeak-ng`
  nebo `espeak` s francouzským hlasem. Bez dostupného hlasu lze trénovat
  bez zvuku; aplikace tuto skutečnost zobrazí. Předem nahrané audio není
  podmínkou této verze. Česká řeč se nepoužívá.

## Převzatá data

- `VerbeTraining.csv`: přesný seznam 100 dodaných sloves a českých významů,
  ve stejném pořadí jako zdroj `francouzstina_100_sloves_cesky.csv`, za ním
  sedm původních sloves podle navazujícího Mílova zadání (celkem 107).
- `VerbeFR.csv`: společná knihovna má 107 sloves. Prvních 100 odpovídá novému
  seznamu; sedm původních sloves mimo tento seznam zůstává na konci. Původní
  tvary všech časů i výběrové značky jsou zachované. Nová slovesa mají pouze
  dodané přítomné tvary; chybějící budoucí a minulé tvary zůstávají prázdné.
- `VerbeSentences.csv`: všech 1 800 nezměněných FR/CZ dvojic ze zdroje
  `francouzstina_100_sloves_1800_vet.csv`, doplněných o explicitní vazby;
  následuje 126 nových jednoduchých vět (celkem 1 926). Každé z původních
  sloves vendre, laisser, rentrer, travailler, boire, payer a acheter má
  tři věty pro každou ze šesti osob. Původní CSV prefixy jsou byteově zachované.

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

## Použití

V hlavním okně `vocab_trainer_fr.py` otevři **Trénink sloves**. Vyber sloveso
kliknutím na řádek (nebo Enterem); seznam se zasune a začne první ukázka.
Tlačítko **Slovesa** seznam vrátí a zastaví sekvenci. **Přehrát** začne celou
sekvenci znovu, **Zopakovat** zopakuje aktuální výpověď, **Další osoba**
přejde na další osobu zvoleného čísla. Změna S/P nebo osoby začne novou sekvenci.
Interval 1–15 s určuje pauzu po větě i mezi osobami. Pauza zastaví zvuk;
pokračování znovu přečte přerušenou výpověď od začátku.

Při vzpomínání se skryjí francouzské ukázky i české překlady. Na vlastní
odpověď zbývají nejméně tři sekundy, poté se tvar postupně odhalí.
Výběr osoby může použít také `elle` / `elles` podle vybraných dodaných vět.

Tréninková data se načítají pouze ke čtení z adresáře aplikace, v balíčku
z přibalených prostředků. Nejde o další zapisovanou kopii uživatelských CSV;
`--data-dir` a ochrana skutečných slovníkových dat zůstávají beze změny.
Pro přenos zdrojové aplikace jsou potřeba také `verb_training.py`,
`verb_training_screen.py`, obě tréninková CSV, `verb_training_pictures.json`
a `training_images/`; 95 stávajících obrázků se načítá z obvyklého `Pict/`.
PyInstaller specifikace zahrnuje všechny tréninkové prostředky.

## Obrázky a ověření

- Výslovné vazby v `verb_training_pictures.json` pokrývají 107 sloves.
  95 používá existující kontextové obrázky, 12 má nové ilustrace v
  `training_images/`. Společný `Pict/mapping.json` se neupravuje.
- Nové ilustrace: devenir, sembler, mourir, jeter, montrer, tomber,
  paraître, cacher, tirer, ajouter, tuer a changer. Vznikly přes imagegen
  z veřejných ilustračních zadání; neobsahují soukromé podklady.
- 31 cílených testů prošlo; plná Cockpit brána 1 518/1 518 prošla.
- Skutečný Tk průchod ověřil aller, falloir, acheter, vzpomínání,
  pauzu mezi osobami a zrušení při zavření. Thomas dokončil zkušební řeč.
- Obrázky 107/107 se dekódují. Širší společný obrázkový audit má známé
  nesouvisející selhání abecedního řazení mapping.json (5/6 testů prošlo).
- macOS nepovoluje snímání obrazovky této relaci; vizuální kontrola není
  vydávána za provedenou. Linuxový hlas má testovaný příkazový kontrakt,
  skutečný poslech a GUI na Linuxu zatím neproběhly.
- Nový distribuční build ani výměna živé aplikace u Jany neproběhly.
