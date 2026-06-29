Nazev: MMTX scena 2 - oprava prvniho spusteni audia
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-29

Co se resilo:
Mila nahlasil, ze ve webove scene 2 `Sunny's Lost Nuts` / cesta k jezeru se pri prvnim spusteni prvni repliky chovaji jinak nez pri opakovani: anglicky original se na prvnim behu neprehral spolehlive, zatimco po opakovani sceny uz vse fungovalo.

Co je hotove:
- Overeno, ze anglicke MP3 pro prvni repliky fyzicky existuji v `docs/` i v mirroru `MatysekANJ/web_mmtx/`.
- Opraveno prvni spusteni sceny: prvni klik uz pred pribehem nepousti hlavni ceskou napovedu a neceka na nacteni systemovych TTS hlasu.
- Ceska napoveda zustava dostupna pres tlacitko napovedy.
- Zvednut cache-busting na `script.js?v=20260629a`.
- Zmena je v produkci `docs/` i v mirroru `MatysekANJ/web_mmtx/`.
- Verejny GitHub Pages web uz serviroval opravenou verzi a verejne MP3 pro prvni repliky vracely HTTP 200.

Co neni hotove:
- Neni automaticky overen slyšitelny zvuk v prohlizeci, protoze v teto relaci nebyl dostupny Playwright/browser automation.
- Mila ma rucne potvrdit realny poslech prvniho behu na webu.

Dalsi krok:
Rucne otevrit verejnou scenu a potvrdit, ze pri prvnim kliknuti zacina anglicky pribeh hned od prvni repliky.

Navrhovane dalsi kroky:
- Pokud se chyba jeste projevi, zkontrolovat konkretni prohlizec a zarizeni a pripadne doplnit viditelny debug stav audia pro prvnich par vterin sceny.
- Pokud je poslech v poradku, povazovat opravu sceny 2 za uzavrenou.

Zmenene nebo relevantni soubory:
- `docs/scene02_sunnys_lost_nuts/script.js`
- `docs/scene02_sunnys_lost_nuts/index.html`
- `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/script.js`
- `MatysekANJ/web_mmtx/scene02_sunnys_lost_nuts/index.html`

Commity:
- `498be9b Fix MMTX scene 2 first-run audio`

Bezpecnost / neukladat:
Neukladat citlive hlasove texty ani soukrome udaje. Tato prace se tykala jen verejne webove vyukove sceny a lokalni pameti projektu.
