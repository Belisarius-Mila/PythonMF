Nazev: Matysek MMTX Forest School - post-commit checkpoint
Priorita: 1
Stav: rozpracovane, relevantni ForestSchool zmeny commitnute a pushnute
Pripomenout pri startu: ano
Datum: 2026-05-26

Co se resilo:
- Ulozeni checkpointu po praci na webove MMTX scene `forestSchool`.
- Relevantni soubory ForestSchool byly oddeleny od unrelated rozpracovanych zmen v repu.
- Byl proveden commit a push pouze pro ForestSchool/MMTX soubory, obrazky, audio, skripty, data podklady a handoffy.

Co je hotove:
- Commit `9850298 Add Matysek Forest School scene` byl pushnut na `origin/main`.
- Commit obsahuje runtime v `docs/` a mirror `MatysekANJ/web_mmtx/`.
- Commit obsahuje prvni petku predmetu: `ball`, `book`, `apple`, `car`, `house`.
- Commit obsahuje lokalni audio pro ceskou napovedu a demo hlasy Bunny/Benji.
- Commit obsahuje AI zdrojovou davku v `PictNew/generated/20260526_forest_school_batch001/`.
- Commit obsahuje skripty:
  - `scripts/generate_forest_school_assets.py`
  - `scripts/apply_forest_school_ai_assets.py`
- Commit obsahuje podklady v `data/forest_school_*`, vcetne seznamu 40 kandidatu na dalsi predmety.
- Pred commitem prosly kontroly:
  - `node --check ../docs/script_intro_v2.js`
  - porovnani `docs/` vs `MatysekANJ/web_mmtx/` pro `index.html`, JS a CSS
  - `git diff --cached --check`

Co neni hotove:
- Neni rucne potvrzeny posledni stav v prohlizeci/iPhonu po commitu.
- Dalsich 40 predmetu je zatim jen navrh v TXT; Mila je ma projit a pripadne promazat/doplnit.
- Dalsi predmety jeste nejsou nakreslene ani napojene do hry.
- V repu zustavaji unrelated lokalni rozpracovane zmeny kolem Samantha/email/document/backup/memory; nejsou soucasti ForestSchool commitu.
- `memory/ACTIVE_PROJECTS.md` a `memory/MEMORY_INDEX.md` obsahuji i starsi rozpracovane zmeny, proto se s nimi pri dalsim commitu musi zachazet opatrne a necommitovat naslepo.

Dalsi krok:
- Rucne otestovat:
  `http://127.0.0.1:8011/index.html?scene=forestSchool`
- Pokud se testuje z iPhonu na stejne siti:
  `http://192.168.1.105:8011/index.html?scene=forestSchool`
- Overit hlavne start po kliknuti, Bunny/Benji hlasy, ceskou napovedu, mochomurky, paprsek a neopakovani predmetu.

Navrhovane dalsi kroky:
- Okamzite: po rucnim testu doladit pripadne jen vizualni drobnosti ve `forestSchool`.
- Potom: projit `data/forest_school_object_candidates_20260526.txt` a potvrdit dalsi predmety.
- Potom: generovat dalsi davku predmetu ve stejnem stylu jako soucasna petka.
- Pri dalsim git uklidu oddelit ForestSchool zmeny od unrelated Samantha/email/document zmen; nepouzivat `git add .`.

Zmenene nebo relevantni soubory:
- `docs/index.html`
- `docs/script_intro_v2.js`
- `docs/styles_intro_v2.css`
- `docs/ForestSchool1.PNG`
- `docs/assets/forest_school_*.png`
- `docs/audio/czech/forest_school_help_cz.mp3`
- `docs/audio/english/forest_school_bunny_yes_it_is.mp3`
- `docs/audio/english/forest_school_benji_no_it_isnt.mp3`
- `MatysekANJ/web_mmtx/` mirror
- `PictNew/generated/20260526_forest_school_batch001/`
- `data/forest_school_*`
- `scripts/generate_forest_school_assets.py`
- `scripts/apply_forest_school_ai_assets.py`
- `memory/projects/mmtx_story_hotspot_app.md`
- `memory/handoffs/matysek_forest_school_checkpoint_2026_05_26.md`
- `memory/handoffs/matysek_forest_school_post_commit_checkpoint_2026_05_26.md`

Bezpecnost / neukladat:
- Necommitovat `data/private/` ani `data/session_autosave/`.
- Necommitovat unrelated e-mail/document rozpracovane zmeny bez samostatneho prehledu.
- Nepouzivat `git add .`.
- Nezapisovat hesla, tokeny, API klice ani cele e-maily do handoffu.
