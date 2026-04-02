# MMTX Project Notes

## Ucel projektu

Webova interaktivni hra pro Matyska. Cilem je jednoducha, obrazkova, pribehova vyuka anglictiny bez cteni.

Aktualni smer:
- intro pres obrazky `Intro1 -> Intro2 -> Intro3 -> Intro4`
- z `Intro4` se vstupuje do jednotlivych scen
- prvni funkcni scena jsou houby: barvy a cisla

## Kde je web

GitHub Pages publikuje obsah ze slozky:
- `docs/`

Aktualne dulezite soubory:
- `docs/index.html`
- `docs/styles.css`
- `docs/styles_intro_v2.css`
- `docs/script.js`
- `docs/script_intro_v2.js`
- `docs/audio/`
- `docs/intro1.png`
- `docs/intro2.png`
- `docs/intro3.png`
- `docs/intro4.png`
- `docs/scene.jpg`
- `docs/ClickMAT.PNG`

Lokalni pracovni zrcadlo:
- `MatysekANJ/web_mmtx/`

Archiv puvodni houbove verze:
- `MatysekANJ/web_mmtx_houby_v1/`

## Aktualni funkcionalita

### Intro

- `Intro1`: uvodni obrazek, klik odemyka audio
- `Intro2`: Benzi mluvi z rucne nahranych souboru
- `Intro3`: kratka veta a prechod dal
- `Intro4`: lesni rozcestnik

Pouzita audio nahravka:
- `docs/audio/intro2_short.m4a`
- `docs/audio/intro2_long_1.m4a`
- `docs/audio/intro2_long_2.m4a`
- `docs/audio/intro2_long_3.m4a`
- `docs/audio/intro3_line.m4a`

Poznamka:
- browserovy fallback na cesky TTS byl odstraneny
- kvuli Safari je prvni klik potreba pro odemknuti audia

### Houby

Z `Intro4` vede ikona houby do sceny `mushrooms`.

Scena `mushrooms` umi:
- rezim `barvy`
- rezim `cisla`
- navrat zpet na `Intro4`

Ovlada se plovouci ikonou:
- `↩` zpet
- `🎨` barvy
- `123` cisla

Logika:
- v `barvy` klik na skupinu hub precte `Red / Blue / Green / Orange`
- v `cisla` kazda nova houba dane barvy dostane poradi `One / Two / Three...`

## Lokalni spousteni

Spusteni lokalni verze:

```bash
python3 -m http.server 8787 -d /Users/miloslavfalta/Desktop/PythonMF/docs
```

Pak otevrit:

```text
http://127.0.0.1:8787/
```

## Publikace na web

Repo:
- `https://github.com/Belisarius-Mila/PythonMF.git`

GitHub Pages:
- publikuje z vetve `main`
- slozka `/docs`

Po zmene webu obvykle staci:

```bash
git add docs
git commit -m "Popis zmeny"
git push origin main
```

## Dulezite technicke poznamky

- nove intro pouziva verzovane soubory `script_intro_v2.js` a `styles_intro_v2.css`, aby se omezil problem s cache
- obrazky v JS a HTML maji query suffix `?v=...` kvuli cache
- geometrii hotspotu ladime rucne podle screenshotu
- nejpresnejsi zpetna vazba je screenshot se sipkami

## Doporuceny dalsi postup

1. Pridavat dalsi sceny z `Intro4` jako samostatne moduly.
2. Postupne rozdelit velky `script.js` na mensi soubory podle scen.
3. Drzet dulezite informace v tomto souboru, ne jen v chatu.
