# Projekt: Lekarna - domaci leky

## Cil

Vytvorit jednoduchy prehled domacich leku, aby se Samantha/Codex mohl pri dotazu typu
"Potrebuji neco na bolest, co mame doma?" podivat do lokalni evidence a vratit prakticky
prehled toho, co je doma k dispozici.

Projekt nema nahrazovat lekare, lekarnika ani pribalovy letak. Ma pomahat najit a
utridit domaci zasoby leku.

## Zakladni scenare

- Míla se zepta na symptom nebo potrebu, napr. bolest, horecka, kasel, alergie,
  prujem, nevolnost, nachlazeni.
- Samantha vyhleda v evidenci domacich leku vhodne kandidaty podle kategorie/pouziti.
- Samantha vrati:
  - co doma pravdepodobne je,
  - kde to je ulozene,
  - expiraci,
  - komu je lek urcen nebo pro koho neni vhodny,
  - upozorneni, ze davkovani a kontraindikace se musi overit v pribalovem letaku
    nebo u lekarnika/lekare.

## Datove soubory

- `data/lekarna/domaci_leky.csv` - hlavni evidence domacich leku.
- `data/lekarna/README.md` - pravidla, jak evidenci vyplnovat a pouzivat.
- `data/lekarna/Lekarna_zbytky_leku_bez_krabicek.txt` - prvni import z rucnich poznamek.
- `data/lekarna/Leky_v_Krabickach/` - fotky leku v krabickach nebo tubach.
- `data/lekarna/photo_imports/` - manifesty pro opakovatelny import novych fotek.
- `data/lekarna/photo_import_*.md` - reporty z provedenych foto importu.

## Navrzeny format evidence

Kazdy lek ma mit minimalne:

- nazev,
- ucinna latka,
- forma,
- sila,
- kategorie,
- pouziti,
- pro koho,
- nevhodne pro koho,
- expirace,
- mnozstvi,
- umisteni,
- poznamky.

## Bezpecnostni pravidla

1. Neodhadovat davkovani, pokud neni ulozene a overene.
2. U deti, tehotenstvi, chronickych nemoci, alergii, kombinaci leku a silnych priznaku
   vzdy doporucit overeni u lekare nebo lekarnika.
3. Pokud je lek po expiraci, oznacit jako nepouzivat bez overeni.
4. Pokud chybi ucinna latka nebo sila, nevyvozovat zavery podle nazvu naslepo.
5. Neuvadet jistotu tam, kde evidence obsahuje jen domaci poznamku.

## Priklad budouciho dotazu

Dotaz:

> Potrebuji neco na bolest, co mame doma?

Ocekavana odpoved:

- Vypsat leky z evidence s kategorii/pouzitim `bolest`.
- U kazdeho ukazat nazev, ucinna latka, sila, forma, expirace a umisteni.
- Pridat bezpecnostni upozorneni, ze davkovani se ma overit podle pribaloveho letaku
  a ze pri silne, neobvykle nebo pretrvavajici bolesti je lepsi resit lekare.

## Aktualni stav

Evidence v `data/lekarna/domaci_leky.csv` uz obsahuje prvni import:

- zbytky leku bez krabicek z rucnich poznamek,
- leky prectene z fotek v `data/lekarna/Leky_v_Krabickach/`.

K 2026-05-20 je v CSV 56 polozek. Z fotek krabicek byly doplneny:

- Diclofenac Dr. Muller Pharma gel 10 mg/g,
- Heparin AL mast 30000 I.E. pro 100 g masti,
- Acylpyrin 500 mg tablety,
- Carbo medicinalis,
- Stacyl 100 mg enterosolventni tablety.
- dalsich 23 polozek z fotek `IMG_8782.HEIC` az `IMG_8804.HEIC`; fotky byly
  prejmenovane na citelne nazvy a import je zdokumentovany v
  `data/lekarna/photo_import_2026_05_19.md`.
- dalsich 8 polozek z opravenych JPEG fotek `IMG_8808.JPEG` az `IMG_8815.JPEG`;
  fotky byly prejmenovane na citelne nazvy a import je zdokumentovany v
  `data/lekarna/photo_import_20260520_015239.md`.
- dalsi 4 polozky z WhatsApp JPEG fotek `WhatsApp Image 2026-05-19 at 22.11.01*.jpeg`;
  fotky byly prejmenovane na citelne nazvy a import je zdokumentovany v
  `data/lekarna/photo_import_20260520_020238.md`.

U fotek neni spolehlive vyctena expirace, proto je u techto polozek `expirace`
nastavena na `nezjisteno` a `nutno_overit` na `ano`.

## Foto import workflow

Od 2026-05-19 existuje opakovatelny nastroj pro nacitani novych fotek krabicek:

- Python modul: `app/lekarna/photo_import.py`
- Samantha tooly:
  - `prepare_lekarna_photo_import`
  - `apply_lekarna_photo_import`
  - `validate_lekarna_photo_sources`
- CLI:
  - `scripts/lekarna_photo_import.py prepare`
  - `scripts/lekarna_photo_import.py apply --manifest <manifest.csv> --confirm "Potvrzuji import fotek lekarna"`
  - `scripts/lekarna_photo_import.py validate`

Postup:

1. Nove fotky ulozit do `data/lekarna/Leky_v_Krabickach/` jako `IMG_*`.
2. Spustit prepare krok; vytvori CSV manifest v `data/lekarna/photo_imports/`.
3. Prectene udaje doplnit do manifestu: `new_file`, `nazev`, `ucinna_latka`,
   `forma`, `sila`, `kategorie`, `pouziti`, `mnozstvi`, `poznamky`.
4. Nejasne polozky nechat jako `neovereno`, `jistota_cteni=nizka` a
   `nutno_overit=ano`.
5. Apply krok se smi spustit az po vyslovnem potvrzeni vetou:
   `Potvrzuji import fotek lekarna`.
6. Apply krok zalozi zalohu CSV, prejmenuje fotky, prida radky do CSV, vytvori
   report a validuje, ze foto zdroje v CSV existuji.

Bezpecnost:

- Foto import je inventar, ne zdravotni doporuceni.
- Nove polozky maji zustat `nutno_overit=ano`, `overeno_z_letaku=ne`.
- `expirace=nezjisteno`, pokud neni jasne overena z obalu.
- Davkovani se nikdy neodvozuje z nazvu ani fotky.

## Vyrazeni leku workflow

Od 2026-05-20 existuje bezpecny soft-delete postup pro vyradeni leku z aktivni
evidence bez mazani radku:

- Samantha tooly:
  - `preview_vyrazeni_leku`
  - `apply_vyrazeni_leku`
- nejdriv se musi udelat read-only preview konkretni polozky,
- zapisujici apply krok vyzaduje potvrzovaci vetu:
  `Potvrzuji vyrazeni leku`,
- apply krok zalozi zalohu CSV a v radku nastavi:
  - `mnozstvi=vyradeno`,
  - `umisteni=vyradeno`,
  - `nutno_overit=ano`,
  - do `poznamky` prida `Vyradeno YYYY-MM-DD: <duvod>`.

Vyrazene polozky se nemaji nabizet v beznem hledani domaci lekarny. Radek v CSV
zustava kvuli historii a dohledatelnosti.
