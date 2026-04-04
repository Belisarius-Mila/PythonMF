# MMTX Project Notes

## Ucel projektu

Webova interaktivni hra pro Matyska. Cilem je jednoducha, obrazkova, pribehova vyuka anglictiny bez cteni.

Aktualni smer:
- jednotny pribehovy web
- minimum textovych menu
- sceny se oteviraji z obrazkovych rozcestniku
- audio ma prednost pred textem

## Kde je web

GitHub Pages publikuje obsah ze slozky:
- `docs/`

Repo:
- `https://github.com/Belisarius-Mila/PythonMF.git`

Verejny web:
- `https://belisarius-mila.github.io/PythonMF/`

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
- `docs/BenjiBunnyScene.png`
- `docs/MeetingOul1.PNG`
- `docs/ClickMAT.PNG`

Pozor:
- `index.html` aktualne nacita `styles_intro_v2.css` a `script_intro_v2.js`
- po zmene `docs/styles.css` a `docs/script.js` je potreba je zkopirovat i do verzovanych souboru, jinak se zmena v prohlizeci neprojevi

Lokalni pracovni zrcadlo:
- `MatysekANJ/web_mmtx/`

Archiv puvodni houbove verze:
- `MatysekANJ/web_mmtx_houby_v1/`

## Aktualni funkcionalita

### Intro

Tok:
- `Intro1 -> Intro2 -> Intro3 -> Intro4`

Chovani:
- `Intro1`: uvodni obrazek, prvni klik odemyka audio
- `Intro2`: Benzi mluvi z rucne nahranych souboru
- `Intro3`: kratka veta a prechod dal
- `Intro4`: lesni rozcestnik pro dalsi sceny

Pouzita ceska audia:
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
- zvukovou napovedu pres `🔊`

Ovlada se plovouci ikonou:
- `↩` zpet
- `🔊` napoveda
- `🎨` barvy
- `123` cisla

Logika:
- v `barvy` klik na skupinu hub precte `Red / Blue / Green / Orange`
- v `cisla` kazda nova houba dane barvy dostane poradi `One / Two / Three...`
- po odkryti vsech cisel se scena sama resetuje, aby se dalo pocitat znovu

Pouzita audia:
- `docs/audio/mushrooms_colors_intro.m4a`
- `docs/audio/mushrooms_numbers_intro.m4a`

### Benji a Bunny

Z `Intro4` vede ikona zajicka do sceny `benjiBunny`.

Scena `benjiBunny` aktualne funguje takto:
- nejdriv automaticky nabihaji dialogove bubliny
- po kazde anglicke vete se prehraje i cesky preklad
- bubliny jsou cislovane `1-9`
- po dokonceni uvodni sekvence se objevi pulzujici mikrofon `🎤`
- klik na mikrofon prehraje ceskou instrukci:
  - `docs/audio/czech/benji_bunny_scene_help_cz1.m4a`
- dite musi kliknout na vsech 9 bublin, muze v libovolnem poradi
- po kliknuti na vsechny bubliny se objevi zelene pulzujici dvere
- klik na zelene dvere otevre scenu `owlGarden`

Klik na bublinu v procvicovaci fazi:
- znovu prehraje anglickou vetu
- hned potom prehraje cesky preklad

Pouzita obrazova aktiva:
- `docs/BenjiBunnyScene.png`
- `docs/MeetingOul1.PNG`

Pouzita audia:
- `docs/audio/english/benji_bunny_*.mp3`
- `docs/audio/czech/benji_bunny_*.m4a`
- `docs/audio/czech/benji_bunny_scene_help_cz1.m4a`

### Sova a jeji zahradka

Scena `owlGarden` je uz zapojena jako dalsi krok po Benji/Bunny scene.

Aktualni stav:
- po kliknuti na zelene dvere v `benjiBunny` se otevre obrazek
- pouzity asset:
  - `docs/MeetingOul1.PNG`
- scena zatim nema dalsi interaktivni logiku

## Lokalni spousteni

Obecny prikaz:

```bash
python3 -m http.server 8802 -d /Users/miloslavfalta/Desktop/PythonMF/docs
```

Pak otevrit:

```text
http://127.0.0.1:8802/
```

Port je mozne menit podle potreby.

## Publikace na web

GitHub Pages:
- publikuje z vetve `main`
- slozka `/docs`

Bezpecny workflow:

```bash
git add docs
git commit -m "Popis zmeny"
git push origin main
```

Pozor:
- do verejne verze jdou jen commitnute zmeny
- necommitnute lokalni soubory push neovlivni
- po pushi muze GitHub Pages potrebovat 1-3 minuty

## Dulezite technicke poznamky

- aktivni web aktualne pouziva verzovane soubory `script_intro_v2.js` a `styles_intro_v2.css`, aby se omezil problem s cache
- obrazky v JS a HTML maji query suffix `?v=...` kvuli cache
- geometrii hotspotu ladime rucne podle screenshotu
- nejpresnejsi zpetna vazba je screenshot se sipkami
- pro ceske promluvy se pouzivaji prednostne rucne nahrane soubory
- anglicka jednotliva slova v houbach jsou zatim pres browser speech synthesis

## Vybrane anglicke hlasy

Aktualni volba pro OpenAI TTS:
- `Benji = fable`
- `Bunny = echo`

Rezervni hlasy pro dalsi postavy:
- `onyx`
- `ash`
- `shimmer`

## Co delat v novem chatu

Pro bezpecne navazani staci napsat:

```text
Pokracuj na MMTX a precti si MatysekANJ/PROJECT_NOTES_MMTX.md, MatysekANJ/MMTX_STRUCTURE_PLAN.md a MatysekANJ/BENJI_BUNNY_SCENE_PLAN.md
```

## Doporuceny dalsi postup

1. Dodelat interaktivni logiku sceny `owlGarden`.
2. Pridavat dalsi sceny z `Intro4` nebo z `owlGarden` jako samostatne bloky.
3. Velky refaktor struktury zatim neprovadet.
4. Postupne rozdelit `script.js` az po dalsim stabilnim checkpointu.
