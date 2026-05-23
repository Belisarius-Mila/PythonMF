Nazev: Lekarna - stav po doplneni vitaminu, kokpitu a fotek
Priorita: 1
Stav: hotovo / ceka na dalsi doplnovani
Pripomenout pri startu: ano
Datum: 2026-05-21

Co se resilo:
- Webova aplikace Lekarna dostala novy cockpit obrazek s klikaci dozou vlevo.
- Doza otevira seznam vitaminu, mineralu a prirodnich pripravku.
- Bylo importovano 7 novych vitaminu/mineralu/prirodnich pripravku, potom 2 dalsi leky/pripravky a nakonec byly doplneny fotky pro KOZLIK KNEIPP a VIGANTOLVIT / VIGANTOVLIT.
- Byl pridan obrazek `Vit_Doporuceni` jako tlacitko `Doporučení pro Janu a Mílu` v panelu vitaminove dozy.
- Byla opravena chyba, kdy polozky bez vlastni fotky zobrazovaly falesnou ukazkovou fotku.

Co je hotove:
- Evidence ma 65 polozek.
- Lokalni `data/lekarna/domaci_leky.csv` ma u `KOZLIK KNEIPP` a `VIGANTOLVIT / VIGANTOVLIT` doplnene vlastni fotky.
- `SILYMARIN PREMIUM` zustava bez vlastni fotky; v dostupnych lekarnickych fotkach nebyla nalezena presna fotka Silymarinu.
- Lokalni private export byl pregenerovan a verejny sifrovany bundle byl pregenerovan pres Milovo lokalni zadani hesla.
- GitHub `main` obsahuje verejny webovy stav:
  - `2aec989 Update pharmacy cockpit and encrypted data bundle`
  - `712be7d Add vitamin recommendation panel`
  - `0a7fbe9 Fix missing medicine photo fallback`
  - `e6949c5 Refresh pharmacy app cache version`
  - `fa791b5 Update pharmacy bundle with supplement photos`

Co neni hotove:
- `SILYMARIN PREMIUM` nema vlastni fotku. Pokud Mila doplni fotku, pripojit ji ke stavajicimu radku, ne vytvaret novy duplicitni lek.
- Po dalsich zmenach dat znovu spustit private export, sifrovani bundle a cilene commitnout jen git-safe soubory.
- V pracovnim stromu stale existuji nesouvisejici rozpracovane e-mailove zmeny; pri dalsim commitu je nebrat omylem do lekarna commitu.

Dalsi krok:
- Pri dalsim doplnovani leku pouzit `memory/technical/lekarna_photo_import_intake.md`.
- Pokud prijde fotka Silymarinu, zmensit ji po potvrzeni `Potvrzuji zmenseni obrazku`, pripojit k existujicimu radku `SILYMARIN PREMIUM`, pregenerovat export/bundle a commitnout encrypted bundle.

Zmenene nebo relevantni soubory:
- `docs/lekarna/` - verejna aplikace a encrypted bundle.
- `data/lekarna/domaci_leky.csv` - soukroma evidence, necommitovat.
- `data/lekarna/Leky_v_Krabickach/` - soukrome fotky, necommitovat.
- `memory/technical/lekarna_photo_import_intake.md` - checklist pro dalsi foto import.

Bezpecnost / neukladat:
- Necommitovat `data/lekarna/` ani `docs/lekarna/private-data/`.
- Heslo k bundle nikdy nepsat do chatu, memory ani gitu; sifrovat pouze pres skryty lokalni prompt.
