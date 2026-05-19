# MMTX Project Handoff

Aktualni handoff pro webovou verzi MMTX. Tenhle soubor popisuje novejsi stav nez starsi `PROJECT_NOTES_MMTX.md`, hlavne pro `owlGarden`, `MeetingOul2` a `HouseBunny`.

## Hlavni umisteni

Produkce bezi z:
- `docs/`

Hlavni soubory:
- `docs/index.html`
- `docs/script_intro_v2.js`
- `docs/styles_intro_v2.css`

Lokalni mirror:
- `MatysekANJ/web_mmtx/`

Produkce:
- `https://belisarius-mila.github.io/PythonMF/`

Posledni nasazeny commit:
- `198ebf2`

## Aktualni flow

Hotovy tok:

```text
Intro1 -> Intro2 -> Intro3 -> Intro4 -> mushrooms / benjiBunny -> owlGarden -> MeetingOul2 -> HouseBunny1
```

V `Intro4` jsou dve klikaci karty:
- `Houby`
- `Friends`

## Hotove sceny

- `Intro1`
- `Intro2`
- `Intro3`
- `Intro4`
- `mushrooms`
- `benjiBunny`
- `owlGarden`
- `MeetingOul2`
- `HouseBunny1`
- `HouseBunny2`
- `HouseBunny3`

## Architektura

Projekt je cisty HTML/CSS/JS bez frameworku.

Zakladni principy:
- centralni `state`
- `setScene(sceneName)` pro prechody
- `renderScene()` pro overlaye a HUD
- sekvencni async flow pres `await`, `pauseMs()` a `playAudioFile()`
- ochrana proti starym async callbackum pres `sequenceId`
- cleanup pri opusteni sceny pres `cleanupCurrentScene()`

Kazda scena je stavovy rezim, ne samostatna stranka.

## Audio strategie

Pouzivame kombinaci:
- hotove audio soubory pro dulezite dialogy
- browser TTS jako fallback nebo pro rychle doplnene vety

Prakticky stav:
- `Benji/Bunny` hlavni seznamovaci dialog pouziva hotove EN + CZ soubory
- `owlGarden` pouziva EN TTS se snahou preferovat hlas `ash`
- `owlGarden` CZ preklady a napovedy jsou rucne nahrane soubory
- `MeetingOul2` pouziva hotove EN soubory
- `MeetingOul2` CZ cast ma rucne nahrane soubory
- `HouseBunny` barvy, `Excellent` a `Try again` zatim jedou pres browser hlas

Dulezite:
- web cte audio z `docs/audio/...`
- zdrojove soubory v `MatysekANJ/benji_bunny_audio/...` nejsou produkcni cesta
- pri vymene audia pod stejnym nazvem casto pomaha zmenit `?v=...`

Pouzite hlasy:
- `Benji = fable`
- `Bunny = echo`
- `owlGarden` EN sova preferuje `ash`

## Mushrooms

Scena `mushrooms` je pristupna z `Intro4`.

Umi:
- rezim `colors`
- rezim `numbers`
- navrat zpet na `Intro4`
- zvukovou napovedu

## BenjiBunny

Scena `benjiBunny` je pristupna z `Intro4`.

Chovani:
- automaticky nabeh dialogovych bublin
- po anglicke vete nasleduje cesky preklad
- po dokonceni uvodu se objevi pulzujici mikrofon
- po splneni se objevi zelene dvere
- klik na dvere otevre `owlGarden`

## OwlGarden

`owlGarden` je hotova interaktivni scena na assetu:
- `docs/MeetingOul1.PNG`

Obsahuje:
- automaticky uvod sovy
- EN vetu a hned CZ preklad
- bubliny `apples`, `sunflowers`, `pigs`
- pulzujici mikrofon pro ceskou napovedu
- `thumbs up` pro potvrzeni spravne odpovedi
- nahodna cisla `1-8`
- zobrazeni cisla v bubline
- barevne tecky nad bublinami podle prave receneho cisla
- zelene svetlo, ktere po spravnem splneni zustava svitit
- fanfaru po dokonceni
- prechod na `MeetingOul2`

Uci se tam soucasne:
- cisla
- objekty
- barvy

Typicke fraze:
- `seven purple apples`
- `six yellow sunflowers`
- `eight pink pigs`

## MeetingOul2

Po dokonceni `owlGarden`:
- otevre se `MeetingOul2`
- probehnou 2 dialogove bubliny
- EN + CZ audio
- pak nasleduje automaticky prechod na `HouseBunny1`

Pouzite assety:
- `docs/MeetingOul2.PNG`

CZ soubory:
- `owl_garden_08_benji_do_you_remember_colors_cz.m4a`
- `owl_garden_09_bunny_we_can_train_all_colors_cz.m4a`

EN soubory:
- `owl_garden_08_benji_do_you_remember_colors_en.mp3`
- `owl_garden_09_bunny_we_can_train_all_colors_en.mp3`

## HouseBunny

Scena s tercem pouziva:
- `docs/HouseBunny1.PNG`
- `docs/HouseBunny2.PNG`
- `docs/HouseBunny3.PNG`
- `docs/assets/red_dart.png`

Flow:
- pri vstupu zazni 2 ceske uvodni instrukce
- pak se nahodne ctou anglicke barvy bez opakovani
- dite klikne na spravnou barvu terce
- pri chybe zazni `Try again.`
- pri spravne odpovedi zazni `Excellent.`
- ukaze se `HouseBunny2`
- potom `HouseBunny3` se zapichnutou cervenou sipkou asi na 2 s
- pak navrat na `HouseBunny1`
- pokracuje dalsi barva

Barvy v terci:
- `yellow`
- `red`
- `white`
- `blue`
- `grey`
- `purple`
- `brown`
- `orange`
- `pink`
- `green`

Stred terce:
- `black`

Technicka poznamka:
- detekce kliknuti funguje pres vypocet uhlu a polomeru v jednom kruhovem hotspotu
- nepouzivame 11 rucnich buttonu
- poloha sipky v `HouseBunny3` je ladena geometrii a nekolika uhlovymi override hodnotami

## Debug shortcuty

V levem dolnim rohu jsou neviditelne debug hotspoty:
- `BenjiBunnyScene -> owlGarden`
- `MeetingOul1 -> MeetingOul2`
- `MeetingOul2 -> HouseBunny1`

Pri debug skoku se pred prechodem zastavuji bezici procesy sceny.

## Prakticke poznamky

- Pro web je rozhodujici slozka `docs/`.
- `MatysekANJ/web_mmtx/` ma zustat synchronni mirror.
- Pri zmene CSS/JS nekdy zvedame verzi v `index.html`, aby se nevracela stara cache.
- Pri zmene audia pod stejnym nazvem casto pomuze zmena `?v=...`.
- Geometrie hotspotu a overlayu je ladena rucne podle screenshotu.

## Dulezite assety

- `docs/MeetingOul1.PNG`
- `docs/MeetingOul2.PNG`
- `docs/HouseBunny1.PNG`
- `docs/HouseBunny2.PNG`
- `docs/HouseBunny3.PNG`
- `docs/assets/red_dart.png`

## Jak navazat v novem chatu

Dobra kratka formulace:

```text
Pokracujeme na webove verzi MMTX v docs/. Hlavni soubory jsou:
docs/index.html
docs/script_intro_v2.js
docs/styles_intro_v2.css

Mirror drzime synchronni v:
MatysekANJ/web_mmtx/

Produkce bezi z docs/ pres GitHub Pages.
Posledni nasazeny commit: 198ebf2

Hotovy tok:
Intro1 -> Intro2 -> Intro3 -> Intro4 -> mushrooms / benjiBunny -> owlGarden -> MeetingOul2 -> HouseBunny1

Hotove sceny:
- Intro1-4
- mushrooms
- benjiBunny
- owlGarden
- MeetingOul2
- HouseBunny1-3
```

## Doporuceni pro dalsi praci

- Navazovat na webove verzi v `docs/`, ne na `MMTX.py`.
- Drzet `MatysekANJ/web_mmtx/` synchronni s `docs/`.
- Vetsi refaktor odlozit, pokud neni potreba pro dalsi scenu.
