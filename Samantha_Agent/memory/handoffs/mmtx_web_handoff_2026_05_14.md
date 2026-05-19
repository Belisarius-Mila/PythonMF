# Handoff: MMTX webová aplikace

## Stav

Projekt `MMTX` teď běží hlavně jako webová aplikace v `docs/index.html` s hlavní logikou v `docs/script_intro_v2.js` a styly v `docs/styles_intro_v2.css`.

Zrcadlová kopie je v `MatysekANJ/web_mmtx/index.html`.

Produkce běží přes GitHub Pages z `docs/`.

Poslední nasazený commit: `198ebf2`.

## Co je hotové

Hotový je tok:

```text
Intro1 -> Intro2 -> Intro3 -> Intro4 -> mushrooms / benjiBunny -> owlGarden -> MeetingOul2 -> HouseBunny1
```

V `Intro4` jsou dvě klikací karty na rozcestí:

- `Houby` pro houby/barvy/čísla
- `Friends` pro Benji/Bunny větev

Hotové scény:

- `Intro1-4`
- `mushrooms` s režimy `colors` a `numbers`
- `benjiBunny` seznamovací dialog
- `owlGarden` se sovou, počítáním `purple apples`, `yellow sunflowers`, `pink pigs`
- `MeetingOul2` s krátkým dialogem
- `HouseBunny1-3` s terčem a procvičováním všech základních barev

## Použitá architektura

Je to čistý HTML/CSS/JS bez frameworku.

Základní principy:

- centrální `state`
- `setScene(sceneName)` pro přechody
- `renderScene()` pro překreslení overlayů a HUD
- sekvenční async flow přes `await`, `pauseMs()` a `playAudioFile()`
- ochrana proti starým asynchronním callbackům přes `sequenceId`
- cleanup při opuštění scény přes `cleanupCurrentScene()`

Každá scéna je stavový režim a ne samostatná stránka.

## Audio strategie

Použili jsme kombinaci:

- hotové audio soubory pro důležité dialogy
- browser TTS jako fallback nebo pro rychle doplněné věty

V praxi:

- `Benji/Bunny` hlavní seznamovací dialog používá hotové EN + CZ soubory
- `owlGarden`:
  - sova EN jde přes TTS, preferovaný hlas `ash`
  - CZ překlady a nápovědy jsou ručně nahrané soubory
- `MeetingOul2` používá hotové EN soubory:
  - `Benji = fable`
  - `Bunny = echo`
- `HouseBunny` barvy, `Excellent`, `Try again` zatím jedou přes browser hlas
- cache u audia řešíme query suffixem typu `?v=20260410a`

Důležité: web reálně čte audio z `docs/audio/...`, ne ze zdrojové složky v `MatysekANJ/benji_bunny_audio/...`.

## OwlGarden detail

`owlGarden` je už hotová interaktivní výuková scéna:

- automatický úvod sovy na `docs/MeetingOul1.PNG`
- EN věta + hned CZ překlad
- bubliny `apples / sunflowers / pigs`
- pulsující mikrofon pro českou nápovědu
- `thumbs up` pro potvrzení správného počtu
- náhodná čísla `1-8`
- zobrazení čísla v bublině
- barevné tečky nad bublinami podle právě řečeného čísla
- zelené světlo po správném splnění zůstává svítit
- po dokončení fanfára
- přechod na `docs/MeetingOul2.PNG`

Učí se tam zároveň:

- čísla
- objekty
- barvy

Pomocí frází typu:

- `seven purple apples`
- `six yellow sunflowers`
- `eight pink pigs`

## MeetingOul2 a přechod dál

Po fanfáře:

- otevře se `MeetingOul2`
- proběhnou 2 dialogové bubliny
- EN + CZ audio
- pak automatický přechod na `docs/HouseBunny1.PNG`

CZ soubory:

- `owl_garden_08_benji_do_you_remember_colors_cz.m4a`
- `owl_garden_09_bunny_we_can_train_all_colors_cz.m4a`

EN soubory:

- `owl_garden_08_benji_do_you_remember_colors_en.mp3`
- `owl_garden_09_bunny_we_can_train_all_colors_en.mp3`

## HouseBunny detail

Scéna s terčem používá:

- `docs/HouseBunny1.PNG`
- `docs/HouseBunny2.PNG`
- `docs/HouseBunny3.PNG`
- `docs/assets/red_dart.png`

Flow:

- při vstupu zazní 2 české úvodní instrukce
- pak se náhodně čtou anglické barvy bez opakování
- dítě kliká na správnou barvu terče
- při chybě zazní `Try again.`
- při správné odpovědi zazní `Excellent.`
- ukáže se `HouseBunny2`
- pak `HouseBunny3` se zapíchnutou červenou šipkou na 2 s
- pak návrat na `HouseBunny1`
- pokračuje další barva

Barvy v terči:

- `yellow, red, white, blue, grey, purple, brown, orange, pink, green`
- střed `black`

Detekce kliknutí funguje přes výpočet úhlu a poloměru v jednom kruhovém hotspotu, ne přes 11 ručních buttonů.

Umístění šipky bylo laděno zvlášť pro `HouseBunny3` přes geometrii a několik úhlových override hodnot.

## Debug zkratky

Přidali jsme neviditelné debug hotspoty v levém dolním rohu:

- `BenjiBunnyScene` -> skok do `owlGarden`
- `MeetingOul1` -> skok do `MeetingOul2`
- `MeetingOul2` -> skok do `HouseBunny1`

Při debug skoku se před přechodem zastavují běžící procesy scény.

## Křižovatka v Intro4

Na `intro4` jsou dvě klikací velké karty:

- `mushroomPortalButton`
- `bunnyPortalButton`

Velikost byla zmenšena asi na polovinu a pozice jsou ručně laděné v CSS v `docs/styles_intro_v2.css`.

## Důležité praktické poznámky

- Pro web je rozhodující složka `docs/`.
- `MatysekANJ/web_mmtx/` je mirror a má zůstat synchronní.
- Při změně audia pod stejným názvem je často potřeba:
  - přepsat soubor v `docs/audio/...`
  - případně přidat nebo změnit `?v=...`
- Při změně CSS/JS se má zvednout verze v `index.html`, aby browser nevzal starou cache.
- Produkce je `https://belisarius-mila.github.io/PythonMF/`.

## Kde navázat v novém chatu

Nejlepší je říct:

- že chceme pokračovat na webové verzi `MMTX`
- že hlavní soubory jsou `docs/index.html`, `docs/script_intro_v2.js`, `docs/styles_intro_v2.css`
- že mirror `MatysekANJ/web_mmtx/` má zůstat synchronní
- že poslední nasazený commit je `198ebf2`
- že hotové jsou `owlGarden` a `HouseBunny`
- co je další plánovaná scéna

## Možný repo handoff soubor

Z tohoto handoffu lze později připravit čistý projektový soubor typu:

```text
PROJECT_HANDOFF_MMTX.md
```

Takový soubor by patřil přímo do repozitáře jako praktické předání pro pokračování práce na webové verzi `MMTX`. Zatím je tento obsah uložený jako memory handoff v `Samantha_Agent/memory/handoffs/`.

## Krátká verze k vložení do nového chatu

```text
Pokračujeme na webové verzi MMTX v docs/. Hlavní soubory jsou:
docs/index.html
docs/script_intro_v2.js
docs/styles_intro_v2.css

Mirror držíme synchronní v:
MatysekANJ/web_mmtx/

Produkce běží z docs/ přes GitHub Pages.
Poslední nasazený commit: 198ebf2

Hotový tok:
Intro1 -> Intro2 -> Intro3 -> Intro4 -> mushrooms / benjiBunny -> owlGarden -> MeetingOul2 -> HouseBunny1

Hotové scény:
- Intro1-4
- mushrooms (colors/numbers)
- benjiBunny dialog
- owlGarden s počítáním apples/sunflowers/pigs a učením barev
- MeetingOul2
- HouseBunny1-3 s terčem, barvami a šipkou

Audio strategie:
- důležité dialogy hlavně přes hotové audio soubory v docs/audio/
- některé pomocné EN věty přes browser TTS
- při výměně audia často používáme ?v=... kvůli cache

Důležité assety:
- docs/MeetingOul1.PNG
- docs/MeetingOul2.PNG
- docs/HouseBunny1.PNG
- docs/HouseBunny2.PNG
- docs/HouseBunny3.PNG
- docs/assets/red_dart.png

HouseBunny:
- při vstupu 2 české intro nahrávky
- pak náhodné čtení barev bez opakování
- správně = Excellent + HouseBunny2 -> HouseBunny3 + šipka
- špatně = Try again

V několika scénách jsou debug skip hotspoty v levém dolním rohu.
```
