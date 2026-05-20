Nazev: PictNew - dalsi faze obrazku, mappingu a CSV
Priorita: 2
Stav: ceka na pozdejsi navazani
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Dokoncili jsme overeny workflow pro tvorbu slovnikovych obrazku.
- Pro `VocabularyIT` bylo pripraveno a vygenerovano 125 obrazku v batchich 001 az 013.
- Mila vsechny obrazky vizualne schvalil jako skvele.
- Vsechny obrazky byly zkopirovane do `Pict/`.
- Workflow byl zdokumentovan jako kanonicky postup pro dalsi projekty.
- Tato poznamka je presny handoff pro pozdejsi pokracovani na dalsich obrazcich, mappingu a CSV.

Co je hotove:
- `Pict/` obsahuje 125 novych `.webp` obrazku z aktualni VocabularyIT vlny.
- `PictNew/generated/20260520_it_batch001/` az `20260520_it_batch013/` obsahuje zdrojove batch vystupy.
- `PictNew/generated/.../generation_report.json` a `review.html` jsou zachovane pro kontrolu.
- Git checkpointy existuji:
  - `20825ad Add VocabularyIT generated image batches`
  - `cc196ec Document vocabulary image workflow`
- Kanonicky workflow je ulozeny v:
  - `Samantha_Agent/memory/technical/vocabulary_image_generation_workflow.md`
- Workflow je dohledatelny z:
  - `Samantha_Agent/memory/MEMORY_INDEX.md`
  - `Samantha_Agent/memory/technical/project_capability_map.md`
  - `Samantha_Agent/memory/technical/workflow_command_registry.md`

Co neni hotove:
- `Pict/mapping.json` zatim nebyl aktualizovan pro nove obrazky.
- Neni hotove porovnani `Pict/mapping.json` proti CSV souborum.
- Nejsou doplnene dalsi anglicke nazvy obrazku pro dalsi vlnu.
- Nejsou pripravene dalsi request JSON soubory pro nove obrazky.
- Nejsou registrovane Samantha workflow prikazy v `app/workflows/commands.py`; postup je zatim rucne overeny a zdokumentovany.

Dalsi krok:
- Pri pozdejsim navazani nejdrive otevrit:
  - `Samantha_Agent/memory/technical/vocabulary_image_generation_workflow.md`
  - `Samantha_Agent/memory/projects/pictnew_vocabulary_image_pipeline.md`
  - tento handoff
- Zkontrolovat aktualni `git status`.
- Zkontrolovat aktualni stav:
  - `Pict/mapping.json`
  - `Pict/`
  - `PictNew/`
  - relevantni CSV soubory, hlavne `VocabularyFR/`, `VocabularyIT/`, pripadne dalsi slovniky.
- Udelat read-only porovnani:
  - slovicka v CSV,
  - existujici vazby v `Pict/mapping.json`,
  - fyzicke obrazky v `Pict/`,
  - chybejici nebo podezrele obrazky.
- Vytvorit navrh novych anglickych nazvu obrazku.
- Pred jakoukoliv zmenou `Pict/mapping.json` vytvorit zalohu a ukazat preview.
- Nove obrazky generovat jen podle kanonickeho workflow:
  - request,
  - dry-run,
  - vyslovne potvrzene placene generovani po davkach,
  - `review.html`,
  - Milova vizualni kontrola,
  - kopie do `Pict/`,
  - mapping az po samostatnem potvrzeni,
  - cilene `git add`, nikdy `git add .`.

Zmenene nebo relevantni soubory:
- `Pict/`
- `Pict/mapping.json`
- `PictNew/`
- `PictNew/NewPicturesRequest20052026.json`
- `PictNew/generated/20260520_it_batch001/` az `PictNew/generated/20260520_it_batch013/`
- `VocabularyIT/IT_Pict.csv`
- `VocabularyIT/VocabularyIT.csv`
- `VocabularyFR/`
- `Samantha_Agent/memory/projects/pictnew_vocabulary_image_pipeline.md`
- `Samantha_Agent/memory/technical/vocabulary_image_generation_workflow.md`
- `Samantha_Agent/memory/technical/project_capability_map.md`
- `Samantha_Agent/memory/technical/workflow_command_registry.md`

Bezpecnost / neukladat:
- Neukladat API klice, tokeny ani jina tajemstvi.
- Nevolat placene image API bez vyslovneho potvrzeni rozsahu.
- Neupravovat `Pict/mapping.json` bez zalohy, preview a samostatneho potvrzeni.
- Nemazat obrazky ani batch vystupy bez vyslovneho souhlasu.
- Nepouzivat `git add .`.
- Soubory `Samantha_Agent/data/session_autosave/` necommitovat.
