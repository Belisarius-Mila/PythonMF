# Tax: daňové přiznání 2025

## Stav

Byl řešen projekt `Tax`, konkrétně příprava daňového přiznání fyzické osoby na formuláři `25 5405`, typ B, vzor 30.

Do podkladů byly doplněny:
- správný formulář a poučení,
- potvrzení o příjmu z druhého zaměstnání v Klaudiánově nemocnici,
- příjem z pronájmu bytu ve výši 24 500 Kč.

V projektu vznikly minimálně tyto výstupy:
- `Tax/plan_priznani_2025.md`
- `Tax/checklist_dan_2025_barevny.png`

## Cíl

Cílem bylo připravit praktický přepisovací checklist pro vyplnění daňového přiznání, aby Míla mohl hodnoty rovnou přepisovat do příslušných řádků formuláře.

## Důležité poznatky

Souhrnný výpočet podle dodaných podkladů:

- příjmy ze zaměstnání celkem: `451 908 Kč`
- příjem z nájmu podle §9: `24 500 Kč`
- výdaje z nájmu paušálem 30 %: `7 350 Kč`
- dílčí základ z nájmu: `17 150 Kč`
- základ daně před zaokrouhlením: `469 058 Kč`
- základ daně po zaokrouhlení: `469 000 Kč`
- daň 15 %: `70 350 Kč`
- sleva na poplatníka: `30 840 Kč`
- daň po slevě: `39 510 Kč`
- zálohy sražené zaměstnavateli: `37 065 Kč`
- doplatek daně: `2 445 Kč`

Příjem z pronájmu bytu `24 500 Kč` byl do výpočtu zahrnut.

## Rozhodnutí

### Příloha č. 2, §9 nájem

Zaškrtnout:
- uplatňuji výdaje procentem z příjmů, 30 %

Řádky:
- `201 = 24500`
- `202 = 7350`
- `203 = 17150`
- `204 = 0`
- `205 = 0`
- `206 = 17150`

Tabulka §10:
- `207–209 = 0`

### Hlavní formulář, strana 2

Vyplnit:

- `31 = 451908`
- `34 = 451908`
- `36 = 451908`
- `39 = 17150`
- `41 = 17150`
- `42 = 469058`
- `45 = 469058`
- `55 = 469058`
- `56 = 469000`
- `57 = 70350`
- `60 = 70350`

Ostatní relevantní nulové řádky podle připraveného checklistu:
- `32 = 0`
- `33 = 0`
- `35 = 0`
- `37 = 0`
- `38 = 0`
- `40 = 0`
- `43 = 0`
- `44 = 0`
- `46–54 = 0`
- `58 = 0`
- `59 = 0`
- `61 = 0`

### Hlavní formulář, strana 3

Vyplnit:

- `64 = 30840`, počet měsíců `12`
- `70 = 30840`
- `71 = 39510`
- `74 = 39510`
- `75 = 39510`
- `77 = 39510`
- `84 = 37065`
- `91 = 2445`, doplatek

Ostatní relevantní nulové řádky:
- `62 = 0`
- `62a = 0`
- `63 = 0`
- `65a–69b = 0`
- `72 = 0`
- `73 = 0`
- `74a = 0`
- `76 = 0`
- `77a = 0`
- `78–83 = 0`
- `85–90 = 0`

### Strana 1, identifikační část

Vyplnit:

- Finanční úřad: `Finanční úřad pro Středočeský kraj`
- Územní pracoviště: `Mladá Boleslav`
- ř. `02 Rodné číslo`: neukládat do memory; použít z originálního formuláře/podkladů
- ř. `03 DAP`: řádné
- ř. `06 Příjmení`: Falta
- ř. `08 Jméno`: Miloslav
- ř. `09 Titul`: Ing. volitelně
- ř. `10 Státní příslušnost`: Česká republika
- ř. `12–18 Adresa v den podání`: vyplnit aktuální adresu podle reálného stavu
- ř. `30 Transakce se zahraničními spojenými osobami`: ne, pokud žádné nebyly

Adresy byly v chatu zmíněny ve variantách, ale do memory je neukládat jako závazný údaj. Před podáním ověřit aktuální adresu.

### Strana 4, přílohy a podpis

Vyplnit:

- Příloha č. 2: `1 list`
- Potvrzení o zdanitelných příjmech: `2 listy`
- Počet listů příloh celkem: `3`
- Datum: den podpisu
- Podpis: vlastnoručně

## Otevřené otázky

- Ověřit aktuální adresu pro stranu 1.
- Ověřit, zda Míla skutečně nemá DIČ jako fyzická osoba.
- Ověřit, zda nebyly zahraniční spojené osoby nebo jiné speciální daňové situace.
- Před odesláním provést finální kontrolu proti originálním podkladům a aktuálnímu formuláři.

## Další kroky pro Codex

- Neprovádět nové daňové výpočty bez výslovného zadání.
- Při práci v projektu `Tax` nejdříve přečíst:
  - `Tax/plan_priznani_2025.md`
  - případné obrázky/podklady v `Tax/`
  - tento memory soubor
- Pokud má Codex upravovat výstupy, má se omezit na soubory v `Tax/` nebo `Samantha_Agent/memory/`, pokud Míla neřekne jinak.
- Nevkládat rodné číslo, adresu, API klíče ani jiné citlivé údaje do veřejně verzovaných souborů.
- Při gitu nepoužívat slepě `git add .`; přidávat jen konkrétní vybrané soubory.

## Zdroj

Souhrn z ChatGPT konverzace k projektu `Tax`, téma daňové přiznání 2025, příjem ze zaměstnání, příjem z nájmu, checklist polí formuláře a vytvoření barevného PNG checklistu.
