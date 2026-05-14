# PythonMF - prehled projektu

Pracovni katalog hlavních aplikaci a datovych celku v adresari `PythonMF`.
Stav je overeny podle struktury slozek, vstupnich souboru a existujici dokumentace k 2026-04-29.

## Verejne / webove vystupy

| Projekt | Slozka | Typ | Hlavni soubory | Web / vystup | Stav / poznamka |
| --- | --- | --- | --- | --- | --- |
| MMTX Web | `docs/` | HTML/CSS/JS web | `docs/index.html`, `docs/script_intro_v2.js`, `docs/styles_intro_v2.css` | `https://belisarius-mila.github.io/PythonMF/` | Hlavni publikovany web. Podle handoffu obsahuje tok Intro, Houby, Benji/Bunny, OwlGarden, MeetingOul2 a HouseBunny. |
| Vocabulary EN web | `docs/vocabulary-en/` | HTML/CSS/JS web | `index.html`, `app.js`, `styles.css`, `docs/data/vocabulary-en.json` | `/vocabulary-en/` | Webova verze anglicke slovni zasoby. Data se synchronizuji ze `VocabularyEN/`. |
| Vocabulary EN83 web | `docs/vocabulary-en83/` | HTML/CSS/JS web | `index.html`, `app.js`, `styles.css`, `docs/data/vocabulary-en83.json` | `/vocabulary-en83/` | Druha anglicka datova sada, pravdepodobne Centrum 83. |
| Restaurace PTKL web | `docs/restaurace-ptkl/` | HTML/CSS/JS web | `index.html`, `app.js`, `styles.css`, `assets/` | `/restaurace-ptkl/` | Webovy vyukovy projekt s dialogem v restauraci a obrazky postav. |
| Colors and Numbers web | `docs/colors-numbers/` | HTML/CSS/JS web | `index.html`, `app.js`, `styles.css`, audio a obrazky | `/colors-numbers/` | Webova verze treninku barev a cisel. |

## Desktopove a lokalni aplikace

| Projekt | Slozka | Typ | Hlavni vstup | Data / assety | Stav / poznamka |
| --- | --- | --- | --- | --- | --- |
| MultiLO | `MultiLO/` | Python desktop, CustomTkinter | `step2_cockpit.py` | `vocab_master.csv`, `users.csv`, `Foto_normalized/`, `cockpit_icons/` | Vetsi cockpit pro vice jazyku a okruhu. Ma testy, build, deploy dokumentaci a vlastni `.app` vystup. |
| Vocabulary EN | `VocabularyEN/` | Python desktop, Tkinter | `vocab_trainer_en.py` | `VocabularyEN.csv`, `VocabularyEN83.csv`, `Pict/`, `docs/data/*.json` | Trener anglicke slovni zasoby. Obsahuje dve datove sady: `Vnuci` a `Centrum 83`; umi web update. |
| Vocabulary FR | `VocabularyFR/` | Python desktop, Tkinter | `vocab_trainer_fr.py` | `VocabularyFR.csv`, `VerbeFR.csv`, `Pict/` | Francouzsky slovnik a slovesa. Ma PyInstaller spec, build skript a deploy dokumentaci. |
| Vocabulary IT | `VocabularyIT/` | Python desktop, Tkinter | `vocab_trainer_it.py` | `VocabularyIT.csv`, `VerbeIT.csv`, `docs/assets/vocabulary-it/` | Italsky slovnik a slovesa. Ma build skript, reporty pro obrazky a synchronizaci do webovych dat. |
| Vocabulary ES | `VocabularyES/` | Python desktop, Tkinter | `vocab_trainer_es.py` | `VocabularyES.csv` | Spanelky slovnik s macOS TTS hlasy. Mensi samostatna aplikace. |
| Vocabulary LA | `VocabularyLA/` | Python desktop, Tkinter | `vocab_trainer_la.py` | `VocabularyLA.csv`, `LA_Slovicka.csv` | Latinsky slovnik, vcetne volby TTS pres macOS `say` nebo eSpeak. |
| Colors and Numbers | `ColorsAndNumbers/` | Python desktop, Tkinter | `colors_numbers.py` | `assets/openmoji_numbers/`, audio | Lokalni trenink barev a cisel; existuje take webova verze. |
| To Be Training | `ToBeTraining/` | Python desktop, Tkinter / Pygame varianta | `tobe_trenink.py`, `tobe_trenink_pygame.py` | `tobevety.csv`, `verb_conjugation.csv` | Trenink anglickych vet a sloves `be`, `have`, `go`. |
| Animals Quiz | `Animals/` | Python desktop, Tkinter | `animal_quiz.py` | PNG obrazky zvirat | Jednoduchy vyukovy kvíz na anglicka zvirata s TTS. |
| Animals Film | `AnimalsFilmPY/` | Python desktop, Tkinter | `animals_film.py` | `Our Life with Animals KPTL_Program.txt`, `A1` az `A6` obrazky | Sekvencni vyukovy film/program se scenami a TTS. |
| Restaurace PTKL | `RestauracePTKL/` | Python desktop + web podklady | `restaurace_lines.py` | `NavstevaRestaurace.txt`, obrazky postav, `SlovnikKPLT.csv` | Dialogova aplikace pro navstevu restaurace; ma i webovy export. |
| MMTX Pygame | `MatysekANJ/` | Python Pygame | `MMTX.py` | `NumCol1.JPG`, sceny, audio | Lokalni Pygame verze nebo prototyp projektu MMTX. Produkcni web je v `docs/`. |
| Anglictina Matysek | `MatysekANJ/` | Python desktop / vyukova app | `anglictina_matysek.py`, `anglictina_matysek_V2.py`, `anglictina_matysek_V3.py` | obrazky Intro, Benji/Bunny, audio | Rodina prototypu pro detskou anglictinu. Stav je potreba jeste rucne rozlisit mezi aktivni a historickou verzi. |
| MBSoft FR/IT | `MBSoft/` | Pythonista / iOS styl | `AppFR.py`, `AppIT.py`, `launcher.py`, `launcher_it.py` | CSV slovniky, `datafresh_sync.py` | Aplikace pouzivaji moduly `ui`, `speech`, `console`; vypadaji jako Pythonista/iPad/iPhone varianta slovniku. |
| VocabFR LockScreen | `iOS/VocabFRLockscreen/` | SwiftUI iOS MVP | `VocabFRLockscreenApp.swift`, `ContentView.swift` | `VocabularyFR.csv` v iOS projektu | Minimalni iOS aplikace pro FR slovnik a audio cyklus na zamcene obrazovce. |

## Datove, pomocne a experimentalni celky

| Projekt | Slozka | Typ | Hlavni soubory | Stav / poznamka |
| --- | --- | --- | --- | --- |
| Sportka | `Sportka/` | Python analyza / generator | `navrh_sportka_alchymie_v3.py`, `stahni_sportku_2025.py`, `sportka_2025.csv` | Edukativni generator navrhu cisel; sam popisuje, ze historie nezvysuje sanci na vyhru. |
| Tax 2025 | `Tax/` | Dokumenty / plan | `DanovePriznani2025/`, `financni_urad_datovka.txt` | Danove podklady a plan; neni jazykova aplikace. |
| TTS scripts | `scripts/` | Pomocne skripty | `generate_tts.py`, `tts_gui.py` | Pomocne nastroje pro generovani a testovani hlasu. |
| Pict | `Pict/` | Asset knihovna | obrazky, `mapping.json` | Aktivni obrazkova knihovna pro slovniky, hlavne EN/FR/IT. |
| PictSource | `PictSource/` | Zdrojove assety | obrazky, mappingy, plany | Zdrojova/zalohova obrazkova knihovna. Velka slozka, vhodna k pozdejsimu uklidu podle aktivniho pouziti. |
| `assets/` | `assets/` | Sdilene assety | `openmoji_numbers/`, audio | Sdilene podklady pro barvy/cisla a zvuky. |
| `ZalohyPY/` | `ZalohyPY/` | Zaloha | starsi kopie treneru a CSV | Pravdepodobne archiv starsich funkcnich verzi. |
| `build/`, `dist/`, vystupy v podslozkach | ruzne | Build vystupy | `.app`, PyInstaller build adresare | Generovane vystupy. Nemely by byt povazovane za zdrojovy kod, pokud neni duvod. |
| `tmp/`, `output/` | ruzne | Docasne vystupy | reporty, imagegen JSONL, exporty | Pracovni a docasne soubory. |

## Build a publikace

| Oblast | Soubor | Poznamka |
| --- | --- | --- |
| GitHub Pages | `docs/README_GITHUB_PAGES.md` | `docs/` je nastavena jako verejna slozka pro GitHub Pages. |
| MultiLO macOS build | `MultiLO/build_and_zip.sh`, `MultiLO/DEPLOY_MAC.md` | Postup pro vytvoreni a prenos `MultiLO.app.zip`. |
| Vocabulary FR macOS build | `VocabularyFR/build_and_zip.sh`, `VocabularyFR/DEPLOY_MAC.md`, `VocabularyFR/VocabularyFR.spec` | Build a deploy francouzske aplikace. |
| Vocabulary IT macOS build | `VocabularyIT/build_and_zip.sh`, `VocabularyIT/DEPLOY_MAC.md`, `VocabularyIT/VocabularyIT.spec` | Build a deploy italske aplikace. |
| Restaurace app build | `NavstevaRestaurace.spec`, `build/`, `dist/` | PyInstaller vystup pro restauracni aplikaci. |

## Dalsi doporuceny krok

1. Rucne oznacit u kazdeho projektu stav: `aktivni`, `funkcni-hotovo`, `rozpracovane`, `archiv`.
2. Rozhodnout, co ma byt videt ve verejnem webovem kokpitu v `docs/`.
3. Vytvorit `README.md` jako kratky vstupni rozcestnik.
4. Pozdeji pridat automaticky `scripts/inventory.py`, ktery tento katalog doplni o pocty souboru, velikosti a datum posledni zmeny.
5. Vyhodnotit `OPENAI_ROADMAP.md`: hlasove cviceni pres Realtime API, generovani obrazku pres GPT Image 2 a lepsi Codex workflow.
