Nazev: MMTX Forest Journey 2 - odstraneni start tlacitka a ceska vstupni napoveda
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-26

Co se resilo:
- MMTX Forest Journey 2 / `Sunny's Lost Nuts` mela pri vstupu do druhe sceny velke spousteci tlacitko.
- Mila chtel, aby sceny pusobily konzistentne: bez samostatneho start tlacitka a s hlavni vstupni napovedou jen cesky.

Co je hotove:
- Publikovana webova kopie v `docs/scene02_sunnys_lost_nuts/` ma odstraneny `startScreen` / `startButton`.
- Mirror v `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/` ma stejnou zmenu.
- Pri nacteni sceny uz neni videt velke start tlacitko; prvni klik do obrazu odemkne audio a spusti `startGame()`.
- Pred samotnym pribehem se po tomto kliknuti prehraje hlavni ceska napoveda.
- Anglicky preklad hlavni napovedy byl odstranen; napoveda tlacitkem mimo tap krok cte jen cesky text.
- Anglicke MP3 repliky pribehu a tap kroku zustavaji zachovane.
- HTML nacita `styles.css?v=20260626b` a `script.js?v=20260626b`, aby web nevzal starou cache.
- Layout byl zkompaktnen podle sceny 1: bez samostatneho zahlavi a zapati, ovladani je plovouci primo nad obrazem.

Co neni hotove:
- Nebyl proveden plny rucni browser test s poslechem v realnem prohlizeci. V sandboxu nebyl k dispozici Playwright/Chromium.

Dalsi krok:
- Po pushi rucne otevrit webovou scenu 2 a overit: zadne velke start tlacitko, scena se vejde do obrazovky, prvni klik do obrazu pusti hlavni ceskou napovedu a potom pribeh s anglickymi MP3.

Navrhovane dalsi kroky:
- Pokud se pozdeji scena 2 integruje primo do hlavni MMTX aplikace bez samostatne HTML stranky, zvazit predani audio gesta z kliknuti na cestu k jezeru.

Zmenene nebo relevantni soubory:
- `docs/scene02_sunnys_lost_nuts/index.html`
- `docs/scene02_sunnys_lost_nuts/script.js`
- `docs/scene02_sunnys_lost_nuts/styles.css`
- `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/index.html`
- `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/script.js`
- `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/styles.css`

Bezpecnost / neukladat:
- Zmena neobsahuje soukroma data, tokeny ani exporty.
- Necommitovat `data/private/` ani `data/session_autosave/`.
