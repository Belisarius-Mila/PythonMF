Nazev: VocabularyIT PictNew - mapping aplikovan po schvalenem preview
Priorita: 2
Stav: hotovo, ceka na git checkpoint
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Po vygenerovani a zkopirovani 125 obrazku VocabularyIT do `Pict/` probehl read-only audit `VocabularyIT.csv`, `IT_Pict.csv`, `Pict/mapping.json` a fyzickych souboru v `Pict/`.
- Mila potvrdil aplikaci preview do `Pict/mapping.json` se zalohou.
- Pred aplikaci byly srovnane rozdily mezi `VocabularyIT.csv` a `IT_Pict.csv`.

Co je hotove:
- `VocabularyIT/IT_Pict.csv` je srovnany s `VocabularyIT/VocabularyIT.csv`.
- `VocabularyIT/VocabularyIT.csv` ma u `vero` zkraceny cesky vyznam na `pravý, pravdivý, opravdový`.
- `PictNew/mapping_preview_vocabularyit_20260520.md` a `.json` obsahuji preview zmen.
- `Pict/mapping.json` byl potvrzene aktualizovan:
  - pridano 87 novych klicu,
  - opravena vazba `modlit se, prosit`: `prey` -> `pray`,
  - po aplikaci ma mapping 677 zaznamu.
- Byla vytvorena zaloha `Pict/mapping.backup_before_vocabularyit_apply_20260520.json`.
- Byly vytvoreny zalohy CSV:
  - `VocabularyIT/IT_Pict.backup_before_mapping_preview_20260520.csv`
  - `VocabularyIT/VocabularyIT.backup_before_mapping_preview_20260520.csv`
- Kontrolni audit po aplikaci:
  - `added_rows=0`,
  - `mapping_without_image=0`,
  - `unresolved=0`.

Co neni hotove:
- Zmeny jeste nejsou ulozene v gitu samostatnym commitem.
- Neni rozhodnuto, jestli zalohy CSV a mappingu zustanou v commitu, nebo jen lokalne.
- Workflow zatim neni registrovany jako formalni Samantha command v `app/workflows/commands.py`.

Dalsi krok:
- Zkontrolovat `git status` a rozhodnout commit scope.
- Cilene commitnout jen relevantni soubory pro VocabularyIT/PictNew/Pict mapping, nikdy nepouzivat `git add .`.
- Ignorovat nesouvisejici rozpracovane zmeny v `Samantha_Agent/`, pokud nepatri k tomuto checkpointu.

Zmenene nebo relevantni soubory:
- `Pict/mapping.json`
- `Pict/mapping.backup_before_vocabularyit_apply_20260520.json`
- `PictNew/mapping_preview_vocabularyit_20260520.md`
- `PictNew/mapping_preview_vocabularyit_20260520.json`
- `VocabularyIT/IT_Pict.csv`
- `VocabularyIT/VocabularyIT.csv`
- `VocabularyIT/IT_Pict.backup_before_mapping_preview_20260520.csv`
- `VocabularyIT/VocabularyIT.backup_before_mapping_preview_20260520.csv`

Bezpecnost / neukladat:
- Neukladat API klice ani tokeny.
- Negenerovat dalsi obrazky bez vyslovneho potvrzeni placeneho rozsahu.
- Nemazat obrazky ani zalohy bez vyslovneho souhlasu.
- Soubory `Samantha_Agent/data/session_autosave/` necommitovat.
