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

## Nasazení 2026-08-10

- Úplná Cockpit quality gate prošla 1334/1334 testy.
- Řízené nasazení bylo svázané s proudem `project-to-be-to-have`.
- Restart vytvořil nový Cockpit proces a povinný smoke prošel 5/5.
- Živý `/api/web-apps` vrátil dlaždici `ToBeToHave` jako desktopovou aplikaci.
- Živý spouštěcí endpoint vrátil `launched` a proces
  `ToBeTraining/tobe_trenink.py` skutečně běžel přes Python 3.12.
- Zdrojový skript, obě výuková CSV a dokumenty v `ToBeTraining/` zůstaly beze
  změny.

## Další krok

Aktuálně probíhá převod do webové podoby podle schváleného zadání Míly.
Lokální prototyp a otevřená ruční revize jsou popsané v navazujícím záznamu.


## Lokální webový prototyp — 2026-09-13 10:35 CEST

Míla schválil převod do samostatného statického webu. Dosavadní desktopový
launcher zůstává historicky platný; web se v tomto kroku do Cockpitu nezapojil.

- Umístění: `ToBeTraining/web/`, návod `ToBeTraining/README_WEB.md`.
- Dva režimy: 107 otázek (91 be / 8 have / 8 go) a 24 skládání vět.
- Zachované texty původních CSV, pouze read-only export do JSON. U konstruovaných
  vět je doplněné úvodní velké písmeno a koncové znaménko. Hash zdrojů blokuje
  nové sestavení při změně CSV do revize přiřazení obrázků.
- 184 anglických MP3, hlas Jenny, sdílení shodných odpovědí. Přesně stejné texty
  v UI a audio manifestu, žádná browser speech synthesis.
- 47 WebP (36 z Pict, 11 nových), všechny do 0,25 MiB, explicitní vazby vět.
  Zvlášť vytvořeny správné barvy psa/kočky/šatů/batohu/očí a skutečný kontext
  Prahy, sourozenců, učitele, školáků a vysokých mužů. `IMAGE_PLAN.md`.
- Barvy slov zůstávají při změně pořadí, příchod Do/Does a has/goes → have/go,
  krátké konfety, pauza řeči/časovačů/animace, omezený pohyb podle systému.
- Ověřeno: 14 JS testů, 184 MP3, 47 WebP, 236 HTTP souborů, rychlá statická brána.
- Neověřeno: skutečné vykreslení a audio Mac/iPhone; Browser native bridge
  v této relaci nebyl dostupný. Lokální náhled binduje jen loopback.
- Kanonický handoff a TVBCP nyní popisují ToBeToHave. Dřívější omylem přiřazené
  KPTL checkpointy zůstávají zachované a označené jako nesouvisející historie.
- Další krok: Mílova revize prototypu, poté samostatně HTTPS hosting/Cockpit odkaz.
  Push, publikování, nasazení a úpravy VocabularyFR/IT nebyly součástí kroku.
