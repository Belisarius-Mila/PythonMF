# Lessons Learned (LL)

Tento soubor je stručný registr ověřených řešení problémů, které se mohou vrátit
nebo jejichž princip lze znovu použít v jiné části projektu.

## Jak LL používat

- Při známém, podobném nebo opakovaném problému nejdřív prohledej tento soubor.
- Nový záznam přidej až po prakticky ověřeném řešení, ne při pouhém návrhu.
- Stejný problém neduplikuj; nové upřesnění doplň k existujícímu záznamu.
- Záznam drž krátký. Provozní historii nech v handoffu nebo TVBCP.
- Neukládej sem hesla, tokeny, soukromý obsah ani jiné citlivé údaje.

## Šablona

### LL-NNN — Stručný název

- Problém:
- Typ: opakující se | jednorázový
- Řešení nalezeno: DDMMRRRR
- Řešení:

## Záznamy

### LL-001 — Lokální kontrola sovy znečišťovala pracovní strom

- Problém: Opakované lokální generování sovího MP3 zapisovalo dvě MP3 a měnilo
  dva produkční `app.js`. `main` pak nebyl čistý, profilové workspaces se
  zablokovaly a bylo nutné soubory ručně uklízet a znovu dorovnávat.
- Typ: opakující se
- Řešení nalezeno: 29072026
- Řešení: Pro místní kontrolu používat `daily_3am.py --local-preview`. MP3 vznikne
  jen v ignorované složce `data/daily_3am/previews/`; produkční soubory ani denní
  stav se nezmění. Produkční MP3 vytváří až GitHub Pages workflow ve svém
  dočasném runneru.

### LL-002 — Lokální slovníkové obrázky blokovaly dorovnání profilů

- Problém: Commit neprodukčního obrázku z `PictNew/` do `main` zablokoval
  bezpečné dorovnání Human–Adam a Knihovna workspace. Profilová pojistka správně
  odmítá běžné mediální soubory mimo výslovně povolené veřejné cesty.
- Typ: opakující se
- Řešení nalezeno: 29072026
- Řešení: Obrázky určené jen pro lokální servis nebo externí iCloud držet
  fyzicky v pracovním adresáři, ale mimo Git pomocí přesného lokálního exclude.
  Nerozšiřovat kvůli nim mediální allowlist profilů. Pokud už byl takový soubor
  omylem commitnutý, zachovat pracovní soubor, bezpečně ho přestat trackovat a
  teprve potom profily dorovnat.

### LL-003 — Pythonista používala starý mapping navzdory kopírování souborů

- Problém: AppFR na iPhonu nezobrazovala jen některé nové obrázky. Opakované
  úpravy AppFR a převody WebP na PNG nepomohly, protože oba skutečně načítané
  `mapping.json` zůstaly ve staré verzi a odkazovaly na neexistující názvy
  obrázků.
- Typ: opakující se
- Řešení nalezeno: 29072026
- Řešení: Nejdřív spustit diagnostiku přímo v Pythonistě a ověřit skutečný
  `AppFR.py`, `BASE_DIR`, oba mappingy, počet záznamů, velikost souboru, konkrétní
  vazby a dekódování obrázků. Staré mappingy nemaž; přejmenuj je a finální
  mapping nahraj a přejmenuj na `mapping.json` v kořeni aplikace i v `Pict/`.
  Teprve potom řeš formát nebo metadata obrázků.

### LL-004 — Hlavní a Janiččina AppFR jsou záměrně oddělené varianty

- Problém: `MBSoft/AppFR.py` pro Mílův iPhone a
  `MBSoft/JanaIphoneFR/AppFR.py` pro Janičku byly chybně považovány za dvě kopie
  stejné aplikace a oprava byla omylem přenesena i do Janiččiny varianty.
- Typ: opakující se
- Řešení nalezeno: 29072026
- Řešení: Před změnou vždy potvrdit cílového uživatele a přesný zdrojový soubor.
  Mílova běžná verze je `MBSoft/AppFR.py`; `MBSoft/JanaIphoneFR/AppFR.py` zůstává
  samostatná a smí se měnit jen při výslovné práci na Janiččině variantě.
  Přenosovou kopii před předáním ověřit kontrolním součtem proti správnému
  zdroji.
