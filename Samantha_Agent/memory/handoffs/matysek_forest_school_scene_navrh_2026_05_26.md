Nazev: Matysek MMTX Forest School - navrh a rozpracovana webova scena
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-26

Co se resilo:
- Navazani na Matysek English / MMTX po QN navrhu nove sceny `Forest School`.
- Soukromy navrh je ulozen mimo git v `data/private/matysek_english/matysek_forest_school_scene_navrh_2026-05-26.txt`.
- Cil sceny: lesni skola se sovou ucitelem, Bunnym a Benym; sova kouzli predmety a Matysek odpovida YES/NO na otazky typu `Is this a ...?`.
- Pracovni kodovy nazev sceny je `forestSchool`.

Co je hotove:
- Ve webove MMTX verzi je doplnena nova scena `forestSchool`.
- Hlavni produkcni soubory jsou v `../docs/`.
- Mirror je v `../MatysekANJ/web_mmtx/`.
- Pridane assety:
  - `../docs/ForestSchool1.PNG`
  - `../docs/assets/forest_school_ball.png`
  - `../docs/audio/czech/forest_school_help_cz.mp3`
  - stejne soubory v `../MatysekANJ/web_mmtx/`
- `forestSchool` jde otevrit primo pres `?scene=forestSchool`.
- Po peti spravnych barvach v `houseBunny` hra prejde do `forestSchool`.
- Implementovane MVP: 5 YES/NO kol, otazka `Is this a ...?`, odpovedi `YES` / `NO`, odmenova kolecka, lokalni ceska napoveda pres mikrofon.
- Prvni petka predmetu je `ball`, `book`, `apple`, `car`, `house`.
- Predmety jsou napojene jako PNG assety v `assets/forest_school_*.png`.
- `ball` byl prevzaty z rozpracovane relace; `book`, `apple`, `car` a `house` byly 2026-05-26 znovu vygenerovane pres AI workflow `image_generator.py` do `PictNew/generated/20260526_forest_school_batch001/`, potom prevedene z chroma-key pozadi na pruhledne 1254x1254 PNG pomoci `scripts/apply_forest_school_ai_assets.py`.
- `memory/projects/mmtx_story_hotspot_app.md` uz obsahuje kratky technicky stav ForestSchool.

Co neni hotove:
- Nebyl udelan automaticky screenshot/Playwright test, protoze Playwright nebyl v relaci dostupny.
- Neni rucne overene realne zobrazeni v prohlizeci po padu terminalu.
- Demo faze, kde Bunny a Beny zkouseji odpovidat a pletou se, zatim neni plne implementovana.
- Neni jeste rucne potvrzene, ze nove AI PNG obrazky `book`, `apple`, `car`, `house` sedi velikosti primo ve scene na iPhonu.
- Technicka kontrola potvrdila pruhledne rohy, 1254x1254 RGBA format, JS syntaxi a HTTP 200 pro assety.
- Neni rozhodnuto, jestli se po dokonceni sceny ma pokracovat dalsi davkou, odmenou, nebo prechodem na dalsi scenu.

Dalsi krok:
- Spustit nebo overit lokalni server v `../docs/` a rucne otevrit:
  `http://127.0.0.1:8010/index.html?scene=forestSchool`
- Zkontrolovat, jestli se zobrazi lesni skola, sova polozi otazku, funguji `YES`/`NO`, mikrofon prehraje ceskou napovedu a pribyvaji kolecka.

Navrhovane dalsi kroky:
- Okamzite: vizualne doladit polohu predmetu, tlacitek a odmen podle realneho prohlizece.
- Potom podle rucniho testu doladit velikost/sytost jednotlivych PNG obrazku.
- Potom pridat kratkou demo fazi Bunny/Beny: ukazka chybne odpovedi, `Try again`, spravna odpoved, `Excellent`.
- Po potvrzeni funkcnosti udelat tematicky git checkpoint jen pro MMTX/web assety a memory zmeny, bez `git add .`.

Zmenene nebo relevantni soubory:
- `../docs/index.html`
- `../docs/script_intro_v2.js`
- `../docs/styles_intro_v2.css`
- `../docs/ForestSchool1.PNG`
- `../docs/assets/forest_school_ball.png`
- `../docs/assets/forest_school_book.png`
- `../docs/assets/forest_school_apple.png`
- `../docs/assets/forest_school_car.png`
- `../docs/assets/forest_school_house.png`
- `../docs/audio/czech/forest_school_help_cz.mp3`
- `../MatysekANJ/web_mmtx/index.html`
- `../MatysekANJ/web_mmtx/script_intro_v2.js`
- `../MatysekANJ/web_mmtx/styles_intro_v2.css`
- `../MatysekANJ/web_mmtx/ForestSchool1.PNG`
- `../MatysekANJ/web_mmtx/assets/forest_school_ball.png`
- `../MatysekANJ/web_mmtx/assets/forest_school_book.png`
- `../MatysekANJ/web_mmtx/assets/forest_school_apple.png`
- `../MatysekANJ/web_mmtx/assets/forest_school_car.png`
- `../MatysekANJ/web_mmtx/assets/forest_school_house.png`
- `../MatysekANJ/web_mmtx/audio/czech/forest_school_help_cz.mp3`
- `scripts/generate_forest_school_assets.py`
- `scripts/apply_forest_school_ai_assets.py`
- `data/forest_school_objects_request_20260526.json`
- `data/forest_school_objects_image_config_20260526.json`
- `../PictNew/generated/20260526_forest_school_batch001/` (AI zdroj a review, ne prime runtime assety)
- `memory/projects/mmtx_story_hotspot_app.md`
- `memory/ACTIVE_PROJECTS.md`
- `data/private/matysek_english/matysek_forest_school_scene_navrh_2026-05-26.txt` (soukromy zdroj, necommitovat)

Bezpecnost / neukladat:
- Soukromy QN/textovy navrh z `data/private/` necommitovat a nekopirovat cely do memory.
- Necpat do gitu zadne soukrome inbox/autosave logy.
- Pred commitem nepouzivat `git add .`; vybrat jen MMTX web soubory, assety a schvalene memory zmeny.
