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

## Cockpit a web

Aktuální webový vstup: horní lišta → **Webové aplikace → ToBeToHave**.
Dlaždice `to-be-to-have` míří na https://belisarius-mila.github.io/PythonMF/to-be-to-have/ a otevírá samostatné okno.
Původní desktopový launcher zůstává v allowlistu pro explicitní lokální použití;
dlaždice už jej nespouští. Regrese U06, která katalog schovala do Servisu, je opravená.

Kanonický zdroj je `ToBeTraining/web/`; veřejná kopie je `docs/to-be-to-have/`.
Publikuje ji stávající workflow Samantha Daily 3 AM spolu s ostatními Pages aplikacemi.
Při budoucí změně nejprve ověř zdroj, potom zrcadli jeho veřejné soubory do této
podsložky `docs/` a porovnej hashe. Nekopíruj rodičovské dokumenty, CSV, QA ani skripty.
Bez souhlasu nemaž starší soubory. Ověřený veřejný obsah je jen HTML/CSS/JS/JSON,
184 MP3 a 47 WebP; cílová cesta nemá backend, osobní data ani klíče.

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

Používat webový vstup z Cockpitu. Míla 14. 9. potvrdil lokální prototyp jako dobrý.
Veřejnou audio přejímku na fyzickém iPhonu provést po zveřejnění; C00 Camina
a U07 Cockpitu zůstávají mimo tento meziúkol.

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


### 2026-09-14 21:44 CEST — Web ToBeToHave a přímý vstup z Cockpitu

Hotovo:
- Schválený lokální prototyp má kompletní publikační kopii v `docs/to-be-to-have/`.
- Dlaždice ToBeToHave otevírá web v samostatném okně; Webové aplikace jsou opět
  přímo v horní liště, bez nutnosti hledat je v Servisu.

Rozhodnutí:
- Míla potvrdil, že lokální prototyp je dobrý, a zadal jeho zpřístupnění na webu
  z Cockpitu. Používá se stávající GitHub Pages, cílová adresa https://belisarius-mila.github.io/PythonMF/to-be-to-have/
- Původní aplikace, CSV a zdrojový web se nemění; nejde o vývoj C00 Camina ani U07 Cockpitu.

Další krok:
- Po zveřejnění otevřít Webové aplikace → ToBeToHave a používat oba režimy.

Navrhované další kroky:
- Na fyzickém iPhonu ověřit první tap se zvukem a návrat z pozadí; automatická
  přejímka není důkaz systémové audio politiky Safari.

Technický důkaz:
- 14/14 JS testů trenažéru, 22/22 cílených testů Cockpitu.
- 184/184 MP3, 47/47 WebP a 236/236 místních HTTP odpovědí shodných se zdrojem.
- Regresní test hlídá vstup do aplikací přímo v hlavičce a webový cíl dlaždice.
- Zdrojový checkpoint předchází publikaci; finální head, Pages a nasazení
  ověřují živé GitHub a Cockpit účtenky. Podrobnosti v `reports/to_be_web_release_2026_09_14.md`.
