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
