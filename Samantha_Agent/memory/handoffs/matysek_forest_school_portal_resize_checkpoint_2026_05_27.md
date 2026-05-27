Nazev: Matysek ForestSchool po napojeni lekci, portalu a zmenseni obrazku
Priorita: 1
Stav: ceka na rucni retest
Pripomenout pri startu: ano
Datum: 2026-05-27

Co se resilo:
- Matyskova scena `forestSchool` ve webove MMTX aplikaci.
- Napojeni 12 lekci po 5 predmetech.
- Prechody mezi lekcemi pres rekapitulaci a volbu Ano/Ne.
- Mapove okno lekci 1-12 a skok na libovolnou lekci.
- Uvodni demo Bunny/Benji, aby spravna odpoved vizualne blikla na YES/NO.
- Rozcestnik v lese `intro4`, kde pribyl ctverec `ForestSchool`.
- Zmenseni vsech 60 predmetovych PNG obrazku ve trech kopiich.

Co je hotove:
- Relevantni zmeny jsou commitnute a pushnute:
  - `af5516e Expand Matysek Forest School lessons`
  - `734f614 Add Forest School portal and compress assets`
- `docs/` a mirror `MatysekANJ/web_mmtx/` jsou synchronizovane.
- ForestSchool ma 12 lekci:
  1. ball, car, book, house, apple
  2. train, cup, shoe, tree, banana
  3. boat, plate, sock, flower, orange
  4. bus, spoon, hat, sun, carrot
  5. bike, chair, bag, moon, bread
  6. truck, table, bed, star, cake
  7. plane, door, box, cloud, milk
  8. rocket, window, key, stone, water
  9. robot, fork, cap, leaf, cookie
  10. block, pencil, pants, stick, corn
  11. doll, map, soap, pillow, grape
  12. toy, kite, lamp, boots, pea
- Cilem kola je 8 mochomurek.
- Po splneni kola se ukaze rekapitulace 5 predmetu s anglickym slovem a ceskym prekladem.
- Po rekapitulaci se zobrazi volba Ano/Ne: Ano pokracuje na dalsi lekci, Ne opakuje aktualni lekci bez uvodniho Bunny/Benji dema.
- Mapova ikona v levem hornim HUD otevre mapu lekci 1-12; tlacitka uz skacou na vybranou lekci.
- Rozcestnik `intro4` ma nove tlacitko `ForestSchool` se sovou/stromkem.
- Vsech 60 `forest_school_*.png` je zmenseno na 420x420 px a pod 250 kB ve vsech kopiich:
  - `docs/assets/`
  - `MatysekANJ/web_mmtx/assets/`
  - `PictSource/`
- Kontroly pred commitem:
  - `node --check` pro `docs/script_intro_v2.js` i mirror prosel.
  - `git diff --check` pro relevantni JS/CSS/HTML prosel.
  - PNG validace pres Pillow: `bad_count 0`.
  - Hash kontrola: `docs/assets`, mirror a `PictSource` maji shodne `forest_school_*.png`.

Co neni hotove:
- Neni udelany rucni vizualni retest celeho toku v prohlizeci po poslednim commitu.
- Neni rozhodnute, jestli velikost 420x420 px je finalni vizualni kompromis; podle sceny by mela stacit, protoze runtime objekt se kresli zhruba do 75-146 px.
- Zalozni slozky s meziverzemi resize nejsou commitnute a zustavaji lokalne.

Dalsi krok:
- Otevrit a rucne projit:
  - `http://127.0.0.1:8011/index.html`
  - rozcestnik `intro4`
  - tlacitko `ForestSchool`
  - mapu lekci 1-12
  - skok na vybranou lekci
  - 8 mochomurek
  - rekapitulaci a volbu Ano/Ne.

Navrhovane dalsi kroky:
- Okamzity dalsi krok: rucni test v prohlizeci a pripadne doladeni poloh tlacitek/portalu.
- Volitelne potom: zlepsit grafiku mapoveho okna lekci nebo pridat zamky/postup podle urovne.
- Volitelne pozdeji: pridat dalsi lekce nebo zmenit slovni zasobu podle Matyskova testu.

Zmenene nebo relevantni soubory:
- `docs/index.html`
- `docs/script_intro_v2.js`
- `docs/styles_intro_v2.css`
- `docs/assets/forest_school_*.png`
- `MatysekANJ/web_mmtx/index.html`
- `MatysekANJ/web_mmtx/script_intro_v2.js`
- `MatysekANJ/web_mmtx/styles_intro_v2.css`
- `MatysekANJ/web_mmtx/assets/forest_school_*.png`
- `PictSource/forest_school_*.png`
- Lokalni zalohy resize:
  - `Samantha_Agent/data/media/image_resize_backups/forest_school_20260527_204206/`
  - `Samantha_Agent/data/media/image_resize_backups/forest_school_420px_20260527_204751/`

Bezpecnost / neukladat:
- Neobsahuje zadna hesla, tokeny ani API klice.
- Nesouvisejici rozpracovane dokumentove zmeny v `Samantha_Agent/app/documents...` nebyly soucasti commitů ForestSchool.
