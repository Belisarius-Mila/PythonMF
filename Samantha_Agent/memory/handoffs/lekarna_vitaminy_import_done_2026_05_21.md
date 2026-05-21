Nazev: Lekarna - vitaminy a prirodni pripravky import hotovy
Priorita: 1
Stav: ceka na sifrovany webovy export
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Navazani na webovy cockpit Lekarny s novou modrobilou dozou vlevo.
- Import fotek novych vitaminu, mineralu a prirodnich pripravku z `data/lekarna/photo_imports/`.
- Zmenseni fotek, prejmenovani, doplneni radku do `data/lekarna/domaci_leky.csv` a priprava `PIL_Short`.

Co je hotove:
- Zmenseno 7 novych fotek na cca 100 kB v `data/lekarna/Leky_v_Krabickach/`.
- Originaly novych fotek jsou zalohovane v `data/media/image_resize_backups/20260521_065902/`.
- Manifest `data/lekarna/photo_imports/lekarna_photo_import_manifest_20260521_vitaminy_dozicka.csv` byl potvrzene aplikovan. Pri kontrole byla zachycena chyba rucne psaneho CSV s neescapovanymi carkami; CSV evidence byla obnovena ze zalohy `domaci_leky.backup_before_photo_import_20260521_065921.csv`, manifest byl prepsan pres CSV writer a import byl zopakovan korektne.
- Do CSV bylo pridano 7 polozek:
  - Vitamin D (neovereno)
  - Celaskon Vitamin C 250 mg
  - Magne B6
  - Helvetia Apotheke Vitamin K2 Complex
  - Dr.Max Magnesium 375 mg Citrate
  - Kneipp Třezalka
  - Vitar Soda
- Vsechny nove polozky maji umisteni `Horní koupelna - dóza vitamíny/minerály/přírodní spánek`.
- Vygenerovan lokalni nesifrovany webovy export `../docs/lekarna/private-data/lekarna.json`; obsahuje box `supplements` s 12 polozkami.
- Finalni report korektniho importu: `data/lekarna/photo_import_20260521_070447.md`.
- Validace `scripts/lekarna_photo_import.py validate` prosla s `missing_sources=0`.
- Testy `python -m unittest tests.test_lekarna_service` prosly.

Co neni hotove:
- Verejny sifrovany balicek `../docs/lekarna/encrypted-data/lekarna.enc.json` zatim nebyl pregenerovan, protoze vyzaduje zadani hesla do lokalniho skryteho promptu.
- Zmeny zatim nejsou commitnute.
- Stare zdrojove kopie `IMG_8882.JPG` az `IMG_8891.JPG` stale zustavaji v `data/lekarna/photo_imports/` jako prichozi kopie.

Dalsi krok:
- Pokud ma nova doza fungovat i na verejne GitHub Pages aplikaci, spustit lokalne `scripts/encrypt_lekarna_web_bundle.py` a zadat heslo pouze do skryteho promptu.
- Potom cilene commitnout verejne bezpecne webove zmeny: cockpit asset, HTML/CSS/JS, export skript a novy `encrypted-data/lekarna.enc.json`.
- Necommitovat `data/lekarna/`, `docs/lekarna/private-data/` ani zalohy.

Zmenene nebo relevantni soubory:
- `data/lekarna/domaci_leky.csv` lokalne, ignorovano gitem.
- `data/lekarna/Leky_v_Krabickach/` lokalne, ignorovano gitem.
- `data/lekarna/photo_imports/lekarna_photo_import_manifest_20260521_vitaminy_dozicka.csv` lokalne, ignorovano gitem.
- `data/lekarna/photo_import_20260521_070447.md` lokalne, ignorovano gitem.
- `data/media/image_resize_backups/20260521_065902/` lokalne, ignorovano gitem.
- `../docs/lekarna/private-data/lekarna.json` lokalne, ignorovano gitem.
- `../docs/lekarna/app.js`
- `../docs/lekarna/styles.css`
- `../docs/lekarna/index.html`
- `../docs/lekarna/assets/lekarna-cockpit.png`
- `scripts/export_lekarna_web_private_data.py`

Bezpecnost / neukladat:
- Neulozit heslo ani hash hesla do chatu, memory, dokumentace ani gitu.
- Necommitovat soukroma data lekarny ani nesifrovany private-data export.
- Web nesmi davat davkovaci doporuceni; `PIL_Short` je jen orientacni domaci evidence.
