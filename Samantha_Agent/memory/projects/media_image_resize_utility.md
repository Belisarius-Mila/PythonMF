# Projekt: Media image resize utility

## Cil

Mit obecnou bezpecnou utilitu pro zmensovani obrazku podle cilove velikosti
souboru v kB, aby ji mohly pouzivat ruzne projekty, napriklad Lekarna nebo
slovnikove obrazky.

## Aktualni rozhodnuti

- Obecny vychozi cil: cca `250 kB` na obrazek.
- Preset `lekarna`: cca `100 kB` na obrazek pro fotky krabicek leku.
- U jinych projektu s fotografiemi se ma Samantha nejdriv zeptat na cilovou
  velikost, pokud ji Mila neurci.

## Implementace

- Modul: `app/media/image_resize.py`
- Samantha tooly:
  - `preview_zmenseni_obrazku`
  - `apply_zmenseni_obrazku`
- CLI:
  - `scripts/resize_images.py preview --path <slozka> --target-kb 250`
  - `scripts/resize_images.py preview --project lekarna`
  - `scripts/resize_images.py apply --project lekarna --confirm "Potvrzuji zmenseni obrazku"`

## Bezpecnost

1. Nejdriv vzdy read-only preview.
2. Apply krok vyzaduje potvrzovaci vetu:
   `Potvrzuji zmenseni obrazku`.
3. Apply krok prepisuje jen vybrane obrazky v povolene ceste uvnitr
   `Samantha_Agent`.
4. Pred prepisem uklada originaly do:
   `data/media/image_resize_backups/`.
5. Zaloha se automaticky nemaze.
6. Pokud Pillow/pillow-heif chybi, preview funguje, apply upozorni na chybejici
   zavislost.

## Provedene zmenseni Lekarny

K 2026-05-20 byly fotky v `data/lekarna/Leky_v_Krabickach/` zmenseny pres
preset `lekarna` na cil cca `100 kB` za obrazek.

- Pred preview: 40 obrazku, cca `46.14 MB`.
- Po dokonceni: 40 obrazku, cca `3.70 MB`, kandidatu nad 100 kB: 0.
- Zaloha originalu je rozdelena do dvou behu:
  - `data/media/image_resize_backups/20260520_025659/`
  - `data/media/image_resize_backups/20260520_030427/`
- Validace zdroju v lekarne po zmenseni: `missing_sources=0`.

Poznamka: prvni HEIC beh byl pomaly, proto byl algoritmus upraven tak, aby pro
male cilove velikosti nejdrive zmensil rozmery a teprve potom ladil kvalitu.
