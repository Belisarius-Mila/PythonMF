Nazev: Matysek MMTX Forest School - lekce 2-12 a nove hlasy Benji/Bunny
Priorita: 1
Stav: rozpracovane, pripraveno ke commitu a dalsimu doladeni sceny
Pripomenout pri startu: ano
Datum: 2026-05-27

Co se resilo:
- Navazani po vypadku terminalu na projekt Matysek anglictina / MMTX Forest School.
- Rozsireni zasobniku slov z prvni petky na navrh 12 lekci.
- Generovani a cisteni obrazku predmetu pro lekce 2-12 ve stylu, ktery Mila schvalil jako pekny.
- Vymena anglickych hlasu Benji/Bunny, protoze puvodni hlasy znely jako starsi chlapi a nehodily se k detske hre.

Co je hotove:
- Soubor `Samantha_Agent/data/forest_school_object_candidates_20260526.txt` obsahuje finalni navrh 12 lekci; prvni lekce zustava `ball`, `car`, `book`, `house`, `apple`.
- Vygenerovane a nasazene jsou obrazky lekci 2-12:
  - lekce 2: `train`, `cup`, `shoe`, `tree`, `banana`
  - lekce 3: `boat`, `plate`, `sock`, `flower`, `orange`
  - lekce 4: `bus`, `spoon`, `hat`, `sun`, `carrot`
  - lekce 5: `bike`, `chair`, `bag`, `moon`, `bread`
  - lekce 6: `truck`, `table`, `bed`, `star`, `cake`
  - lekce 7: `plane`, `door`, `box`, `cloud`, `milk`
  - lekce 8: `rocket`, `window`, `key`, `stone`, `water`
  - lekce 9: `robot`, `fork`, `cap`, `leaf`, `cookie`
  - lekce 10: `block`, `pencil`, `pants`, `stick`, `corn`
  - lekce 11: `doll`, `map`, `soap`, `pillow`, `grape`
  - lekce 12: `toy`, `kite`, `lamp`, `boots`, `pea`
- Runtime obrazky jsou v `docs/assets/forest_school_*.png` a v mirroru `MatysekANJ/web_mmtx/assets/forest_school_*.png`.
- Zdrojove AI davky jsou v `PictNew/generated/20260527_forest_school_lesson02/` az `lesson12/`.
- `cloud` byl pregenerovan; `toy` a `boots` byly docisteny po odstraneni chroma-key.
- Anglicke hlasy Benji/Bunny byly pregenerovane:
  - Bunny: `en-US-AnaNeural`
  - Benji: `en-US-EmmaNeural`
- Prepsane jsou intro repliky `benji_bunny_01...09`, dve repliky v owl garden a Forest School demo `Yes, it is.` / `No, it isn't.`.
- Nove MP3 jsou nasazene do:
  - `docs/audio/english/`
  - `MatysekANJ/web_mmtx/audio/english/`
  - `MatysekANJ/benji_bunny_audio/english/`
- Cache odkazy byly navysene na `20260527voice` v `docs/script_intro_v2.js`, `MatysekANJ/web_mmtx/script_intro_v2.js`, starsich `script.js` souborech a v `index.html`.
- Fallback speechSynthesis preference pro Benji/Bunny uz nepouzivaji `fable`, `echo`, `daniel` ani `fred`; misto toho preferuji mladsi/zenske hlasy.

Co neni hotove:
- Nove predmety lekci 2-12 jeste nejsou napojene do herni logiky `forestSchoolObjects`; hra runtime stale pouziva prvni petku.
- Neni jeste udelana navigace mezi lekcemi ani vyber lekce.
- Neni rucne potvrzeno v prohlizeci/iPhonu po posledni vymene hlasu a cache.
- Je potreba rozhodnout, jestli hra ma hned rotovat vsech 60 slov, nebo mit samostatne lekce po peti slovech.
- V repu existuji i unrelated rozpracovane zmeny kolem Samantha/email/document/backup; pri commitu postupovat opatrne a bez `git add .`.

Dalsi krok:
- Nejdive commit a push aktualniho stavu podle Milovy zadosti, ale bez `data/session_autosave/` a bez soukromych `data/private/`.
- Potom pokracovat v lesni skole:
  - napojit lekce 2-12 do JS,
  - navrhnout jednoduchy mechanismus lekci,
  - rucne otestovat `http://127.0.0.1:8011/index.html?scene=forestSchool`.

Navrhovane dalsi kroky:
- Okamzite: commit/push soucasneho checkpointu.
- Hned potom: zmenit `forestSchoolObjects` z jedne petky na strukturu lekci po peti slovech.
- Prakticka varianta pro Matyska: po dokonceni peti slov prejit na dalsi lekci, nebo nechat vyber lekce pres maly dospely/debug ovladac.
- Pozdeji: doplnit zvukove potvrzeni lekce, jemnejsi animaci paprsku a pripadne samostatne odmeny za celou lekci.

Zmenene nebo relevantni soubory:
- `docs/index.html`
- `docs/script_intro_v2.js`
- `docs/script.js`
- `docs/assets/forest_school_*.png`
- `docs/audio/english/benji_bunny_*.mp3`
- `docs/audio/english/owl_garden_08_benji_do_you_remember_colors_en.mp3`
- `docs/audio/english/owl_garden_09_bunny_we_can_train_all_colors_en.mp3`
- `docs/audio/english/forest_school_bunny_yes_it_is.mp3`
- `docs/audio/english/forest_school_benji_no_it_isnt.mp3`
- `MatysekANJ/web_mmtx/` mirror se stejnymi runtime zmenami.
- `MatysekANJ/benji_bunny_audio/english/` zdrojova sada Benji/Bunny MP3.
- `PictNew/generated/20260527_forest_school_lesson02/` az `PictNew/generated/20260527_forest_school_lesson12/`.
- `Samantha_Agent/data/forest_school_object_candidates_20260526.txt`
- `Samantha_Agent/data/forest_school_bunny_project_voice_tts_20260527.csv`
- `Samantha_Agent/data/forest_school_benji_project_voice_tts_20260527.csv`
- `Samantha_Agent/memory/handoffs/matysek_forest_school_lessons_voices_checkpoint_2026_05_27.md`

Bezpecnost / neukladat:
- Necommitovat `Samantha_Agent/data/session_autosave/`.
- Necommitovat `data/private/` ani citlive dokumenty, cele e-maily, hesla, tokeny nebo API klice.
- Nepouzivat `git add .`; staging delat pres explicitni cesty nebo peclive zvolene pathspecy.
- Pred pushem zkontrolovat staged diff/stat a pripadne `git diff --cached --check`.
