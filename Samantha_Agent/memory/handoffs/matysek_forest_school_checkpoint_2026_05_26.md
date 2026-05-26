Nazev: Matysek MMTX Forest School - checkpoint po doladeni sceny
Priorita: 1
Stav: rozpracovane, funkcni checkpoint pripraveny k rucnimu testu
Pripomenout pri startu: ano
Datum: 2026-05-26

Co se resilo:
- Webova MMTX scena `forestSchool` pro Matyska v `docs/` a mirroru `MatysekANJ/web_mmtx/`.
- Lesni skola se sovou, Bunnym a Benjim: sova kouzli predmety, zazni otazka `Is this a ...?`, Matysek voli `YES` nebo `NO`.
- Dnes se ladily obrazky predmetu, ceska napoveda, demo Bunny/Benji, neopakovani predmetu, odmeny a vizualni rozlozeni.

Co je hotove:
- Scena jde otevrit pres `?scene=forestSchool`.
- Prechod z `houseBunny` po peti spravnych barvach vede do `forestSchool`.
- Prvni petka predmetu je `ball`, `book`, `apple`, `car`, `house`.
- Vsech pet runtime predmetu je v `docs/assets/forest_school_*.png` a v mirroru.
- `book`, `apple`, `car` a `house` byly vygenerovane pres AI workflow do `PictNew/generated/20260526_forest_school_batch001/` a prevedene pres `scripts/apply_forest_school_ai_assets.py` na pruhledne 1254x1254 PNG.
- Ceska napoveda se zobrazuje jako `Je to správně? Pokud ano klikni jes, pokud ne klikni no.`
- Audio napovedy pouziva foneticky text `klikňi ... nou`, aby TTS nevyslovovalo tvrde `klikny`.
- Pri primem otevreni ForestSchool se hra bez prvniho kliknuti nerozbehne potichu; po kliknuti se spusti od zacatku se zvukem.
- Pred hrou bezi kratke antre:
  - Bunny odpovi spatne `Yes, it is.`
  - Benji odpovi spravne `No, it isn't.`
  - score se v demu nevyplnuje,
  - sova rekne `Will you try?`,
  - pak zacina Matyskovo odpovidani.
- Demo hlasy Bunny/Benji maji lokalni anglicka MP3:
  - `audio/english/forest_school_bunny_yes_it_is.mp3`
  - `audio/english/forest_school_benji_no_it_isnt.mp3`
- Matyskovi se predmety vybiraji z promichane fronty bez opakovani, takze se v petikolovem behu vyststridaji vsechny polozky.
- Odmeny jsou misto tecek male mochomurky, posunute vic vpravo, aby mene kryly sovu.
- Paprsek z hulky sovy byl natocen smerem k predmetu.
- Kandidati na dalsich 40 predmetu jsou lokalne v `data/forest_school_object_candidates_20260526.txt`; `data/` je root `.gitignore`, proto je soubor lokalni a necommitovany.

Co neni hotove:
- Neni rucne potvrzene posledni doladeni na iPhonu po uprave Bunny/Benji hlasu, mochomurek a paprsku.
- Paprsek muze chtit jeste jemne doladit podle oka (`left`, `top`, `rotate` ve `.forest-school-wand-beam`).
- Dalsi predmety nejsou jeste schvalene ani nakreslene.
- Neni implementovana dalsi sada slov po prvni petce.

Dalsi krok:
- Rucne otevrit:
  `http://127.0.0.1:8011/index.html?scene=forestSchool`
  nebo na iPhonu:
  `http://192.168.1.105:8011/index.html?scene=forestSchool`
- Overit: klik spusti zvuk, Bunny ma jiny hlas nez sova, mochomurky nekryji sovu, paprsek smeruje k predmetu a YES/NO hra bezi.

Navrhovane dalsi kroky:
- Okamzite: podle rucniho testu doladit paprsek a polohu mochomurek.
- Potom: projit `data/forest_school_object_candidates_20260526.txt`, vymazat/doplnit slova a schvalit dalsi davku.
- Potom: vygenerovat nove predmety ve stylu soucasne petky a napojit je do `forestSchoolObjects`.

Zmenene nebo relevantni soubory:
- `docs/index.html`
- `docs/script_intro_v2.js`
- `docs/styles_intro_v2.css`
- `docs/ForestSchool1.PNG`
- `docs/assets/forest_school_ball.png`
- `docs/assets/forest_school_book.png`
- `docs/assets/forest_school_apple.png`
- `docs/assets/forest_school_car.png`
- `docs/assets/forest_school_house.png`
- `docs/audio/czech/forest_school_help_cz.mp3`
- `docs/audio/english/forest_school_bunny_yes_it_is.mp3`
- `docs/audio/english/forest_school_benji_no_it_isnt.mp3`
- `MatysekANJ/web_mmtx/` mirror se stejnymi soubory.
- `scripts/apply_forest_school_ai_assets.py`
- `scripts/generate_forest_school_assets.py`
- `memory/projects/mmtx_story_hotspot_app.md`
- `memory/handoffs/matysek_forest_school_checkpoint_2026_05_26.md`
- `data/forest_school_object_candidates_20260526.txt` lokalne, necommitovano kvuli root `.gitignore`.

Bezpecnost / neukladat:
- Necommitovat `data/private/` ani `data/session_autosave/`.
- Necommitovat unrelated e-mail/document rozpracovane zmeny.
- Nepouzivat `git add .`; staging delat jen explicitnim seznamem relevantnich souboru.
