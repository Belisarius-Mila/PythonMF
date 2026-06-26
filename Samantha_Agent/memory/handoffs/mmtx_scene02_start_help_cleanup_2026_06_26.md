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
- Pri nacteni sceny se vola `startGame()` automaticky.
- Pred samotnym pribehem se prehraje hlavni ceska napoveda.
- Anglicky preklad hlavni napovedy byl odstranen; napoveda tlacitkem mimo tap krok cte jen cesky text.
- HTML nacita `styles.css?v=20260626a` a `script.js?v=20260626a`, aby web nevzal starou cache.

Co neni hotove:
- Nebyl proveden plny rucni browser test s poslechem v realnem prohlizeci. V sandboxu nebyl k dispozici Playwright/Chromium a lokalni HTTP server nebyl dostupny z dalsiho sandbox procesu.

Dalsi krok:
- Po pushi rucne otevrit webovou scenu 2 a overit: zadne velke start tlacitko, nejdrive ceska napoveda, potom zacina pribeh.

Navrhovane dalsi kroky:
- Pokud prohlizec zablokuje automaticke cteni bez uzivatelskeho gesta, resit samostatne designem navazani z predchozi sceny tak, aby klik na cestu k jezeru predal audio gesto bez viditelneho start overlaye.

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
