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

### LL-002 — Slovníkové aplikace: konzistence kódu, mappingu a obrázků

- Problém: Obrázky se nemusí zobrazovat, přestože mapping vypadá správně.
  Příčinou může být záměna variant aplikace nebo mappingu, neúplný `Pict`, jiná
  cesta na cílovém zařízení, starý obsah v paměti nebo rozdíl ve formátu či
  názvu souboru. Lokální obrázky navíc nemají znečišťovat Git.
- Typ: opakující se
- Řešení nalezeno: 29072026
- Řešení: Každou variantu aplikace udržovat odděleně. Kontrolovat celý řetězec
  `CSV -> mapping.json -> skutečný soubor v Pict -> dekódování aplikací`,
  ideálně diagnostikou přímo na cílovém zařízení včetně cest, počtů a
  kontrolních součtů. Mapping před změnou zálohovat, na zařízení nahrát do všech
  skutečně používaných míst a aplikaci restartovat. Chybějící obrázky doplňovat
  podle výsledku úplného auditu. Lokální či iCloudové servisní obrázky držet mimo
  Git pomocí přesného lokálního exclude.

### LL-003 — Proměnlivý provozní stav neověřovat jen z projektové paměti

- Problém: Potvrzená aktivace rodinného kalendáře se po runtime kroku
  nepropsala do kanonické git-safe paměti. Pozdější bezpečný audit nečetl
  soukromou konfiguraci a aktivní souhrny proto vedly režim jako neověřený.
- Typ: opakující se
- Řešení nalezeno: 01082026
- Řešení: U dotazů typu `je aktivní`, `běží` nebo `je připraveno` nejprve
  použít dostupný redigovaný read-only live audit. Paměť používat jako
  historický kontext a bezpečnostní pravidla, ne jako důkaz současného runtime
  stavu. Po významné provozní změně zapsat git-safe redigovanou účtenku bez
  tajemství a soukromého obsahu.
