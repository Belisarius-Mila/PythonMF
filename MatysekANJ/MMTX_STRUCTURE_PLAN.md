# MMTX Structure Plan

## Proc menit strukturu

Aktualni web funguje, ale logika je soustredena hlavne v jednom JS souboru. To je dobre pro prototyp, ale pro dalsi sceny bude lepsi rozdelit projekt po modulech.

## Doporucena cilova struktura

```text
docs/
  index.html
  css/
    main.css
    intro.css
    mushrooms.css
  js/
    app.js
    audio.js
    intro.js
    mushrooms.js
    scene-registry.js
  assets/
    intro/
      intro1.png
      intro2.png
      intro3.png
      intro4.png
      ClickMAT.PNG
    mushrooms/
      scene.jpg
    icons/
  audio/
    intro2_short.m4a
    intro2_long_1.m4a
    intro2_long_2.m4a
    intro2_long_3.m4a
    intro3_line.m4a
```

## Jak by se rozdelila logika

### `app.js`

Hlavni startup aplikace:
- nacteni scen
- globalni stav
- prepinani mezi scenami

### `audio.js`

Spolecne funkce:
- odemknuti audia
- prehrani rucnich nahravek
- anglicke TTS pro jednotliva slova
- pripadne pozdeji preload

### `intro.js`

Pouze intro:
- `Intro1`
- `Intro2`
- `Intro3`
- `Intro4`
- klikaci ikony na rozcestniku

### `mushrooms.js`

Pouze houby:
- hotspoty
- rezim `barvy`
- rezim `cisla`
- HUD ovladani

### `scene-registry.js`

Jednoducha mapa scen:
- jmeno sceny
- obrazek sceny
- render
- handlery

## Prakticky plan refaktoru

Nemigrovat vse najednou. Udelat to po krocich:

1. Zachovat funkcni verzi.
2. Vytahnout audio helpery do `audio.js`.
3. Vytahnout houby do `mushrooms.js`.
4. Vytahnout intro do `intro.js`.
5. Teprve pak upravit `index.html` na novou slozkovou strukturu.

## Co je vyhoda

- nove sceny pujdou pridavat samostatne
- v git commitech pujde menit jen konkretni modul
- novy chat se bude v projektu lepe orientovat
- bude mensi riziko, ze rozbijeme jinou cast hry pri ladeni jedne sceny

## Co ted nedelat

- nedelat velky refaktor pred dalsi funkcni scenou
- nejdriv dodelat dalsi obsah
- restrukturalizaci delat az po dalsim stabilnim checkpointu
