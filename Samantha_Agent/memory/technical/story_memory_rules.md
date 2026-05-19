# Story memory rules: ukládání pohádek do memory

## Stav

Tento soubor ukládá pravidla pro ukládání pohádek do memory pro Codex CLI a budoucího Samantha agenta.

## Pravidla

- Ukládat vždy celé texty pohádek, ne jen stručná shrnutí.
- Jako kanonickou verzi ukládat finální verzi po uživatelských opravách.
- Pokud existuje varianta vhodná pro automatické předčítání, uložit ji také nebo ji jasně označit v metadatech.
- U postav respektovat pozdější opravy uživatele.
- Pokud uživatel později odstraní postavu z finální verze, v kanonické verzi ji nechat odstraněnou.

## Strukturovaná pravidla

```json
{
  "store_full_text": true,
  "store_summary_only": false,
  "prefer_final_user_corrected_version": true,
  "track_tts_clean_version": true,
  "preserve_character_corrections": true
}
```

## Příklady

### Dělat

- Uložit celou finální pohádku.
- Uložit poznámku, že postava vyřazená uživatelem do finální verze nepatří.
- Označit, že existuje clean-text verze vhodná pro předčítání.

### Nedělat

- Neukládat jen krátké shrnutí děje.
- Nenechávat v kanonické verzi postavy, které uživatel později vyřadil.
- Neignorovat pozdější opravy uživatele.

## Zdroj

Memory preference předaná Mílou 2026-05-14 ve formátu JSONL.

