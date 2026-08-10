# ToBeToHave

## Kanonický rozsah

- Pracovní proud: `project-to-be-to-have`.
- Zdrojová složka: `ToBeTraining/` v hlavním repozitáři PythonMF.
- Kanonický vstupní skript: `tobe_trenink.py`.
- Původní názvy `To Be Training` a `ToBeTraining` zůstávají vyhledávací aliasy.

## Účel a data

Aplikace je lokální desktopový Tk trenažér angličtiny. Procvičuje věty pro
`to be`, `to have` a `to go` a samostatnou obrazovku časování sloves.

Používá dva existující zdroje pouze ke čtení:

- `tobevety.csv` se sloupci `Lekce`, `Otázka`, `Kladná odpověď`,
  `Záporná odpověď`;
- `verb_conjugation.csv` se sloupci `Pronoun`, `Verb`, `Adverbial`,
  `QuestionAux`, `QuestionVerb`, `Translation`.

Cockpit integrace nesmí tyto CSV kopírovat, migrovat ani upravovat. Změna
výukového obsahu je samostatný úkol.

## Cockpit

V nabídce `Webové aplikace` je ToBeToHave vedená jako desktopová aplikace.
Spuštění používá allowlistované ID `to-be-to-have`, pracovní adresář
`ToBeTraining/`, skript `tobe_trenink.py` a ověřený Python 3.12 s Tk 8.6.
Cockpit sestaví pouze pevný lokální příkaz a otevře aplikaci v Terminalu.

## Bezpečnost a ověření

- Žádné výukové CSV ani dokumenty ve zdrojové složce se při integraci nemění.
- Automatické testy hlídají katalog, allowlistované spuštění a schéma obou CSV.
- Před nasazením se spouští úplná Cockpit quality gate.
- Po nasazení se živě ověří API katalogu a skutečný start procesu aplikace.

## Další krok

Po prvním živém spuštění řešit další úpravy aplikace nebo lekcí jen podle
konkrétního zadání Míly.
