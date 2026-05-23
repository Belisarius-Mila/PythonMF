Nazev: iPhone zkratky - quick notes a dalsi moznosti
Priorita: 2
Stav: rozpracovane / funkcni prvni verze
Pripomenout pri startu: ano
Datum: 2026-05-23

## Co se resilo

Mila chce pokracovat v iPhone zkratkach. Zkratky jsou pro nej dulezite,
protoze umoznuji rychle zachytit napady bez ztraty koncentrace a pozdeji je
prevest do realnych Samantha workflow/toolu.

Aktualni zamer:

- zitra navazat presne zde,
- nacist tento handoff a memory `technical/iphone_shortcuts_playground.md`,
- ukazat aktualni moznosti zkratek,
- pokracovat od zkratky `Rychlá poznámka pro Samanthu`,
- pozdeji se vratit k hlavnim projektum.

## Co je hotove

- Zkratka `Najit auto v3.shortcut` funguje u Mily i Jany.
- Zkratka `Lékárna Jana.shortcut` byla vytvorena a Mile funguje.
- Zkratka `Rychlá poznámka pro Samanthu.shortcut` byla vytvorena, opravena a
  Milou preimportovana z noveho souboru.
- Reálný test quick notes funguje: Samantha/Adam umi nacist poznamky z iCloud
  kontejneru Zkratek na Macu.
- Implementovany jsou tooly:
  - `list_quick_notes`
  - `show_quick_note_detail(note_number=...)`
- CLI:
  - `.venv/bin/python scripts/samantha_quick_notes.py --limit 30`
  - `.venv/bin/python scripts/samantha_quick_notes.py --detail 1`
- Soukromy index je mimo git:
  - `Samantha_Agent/data/private/quick_notes/index.json`
- K 2026-05-23 byly videt tyto poznamky:
  1. `Potřebuju udělat test`
  2. `Test dva`
  3. `Jsi frajer Adame!`
- Testy prosly:
  - `.venv/bin/python -m unittest tests.test_quick_notes tests.test_iphone_shortcuts`
  - vysledek: `6 tests OK`
- Py compile proslo:
  - `.venv/bin/python -m py_compile app/quick_notes.py scripts/samantha_quick_notes.py app/samantha_agent.py`

## Co neni hotove

- Neni jeste implementovana akce typu:
  - `z poznámky č. 7 uděláme tool`
  - `z poznámky č. 7 uděláme projekt`
  - `z poznámky č. 7 uděláme připomínku`
- Zatim existuje jen seznam a detail poznamek.
- Quick notes nejsou zatim v system reports.
- Neni doresene archivovani/oznaceni poznamky jako zpracovane.
- Neni doresene rozklikavaci UI mimo chat; zatim se detail zobrazuje tool/CLI
  prikazem.

## Dalsi krok pri zitrejsim navazani

1. Nejdriv zkontrolovat git:

```bash
git status --short --branch
```

2. Nacist:

```text
Samantha_Agent/memory/technical/iphone_shortcuts_playground.md
Samantha_Agent/memory/handoffs/iphone_shortcuts_quick_notes_continue_2026_05_23.md
```

3. Ukazat Milovi aktualni moznosti zkratek velmi strucne:

- rychla poznamka pro Samanthu,
- dokument do trezoru,
- faktura/nakup do archivu,
- rychla pripominka,
- lekarna rodinne zkratky,
- univerzalni Samantha inbox,
- poslat polohu / rodinne navigace.

4. Spustit quick notes seznam:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent
.venv/bin/python scripts/samantha_quick_notes.py --limit 30
```

5. Navrhnout nejmensi dalsi implementaci:

- bud `mark_quick_note_done`,
- nebo `promote_quick_note_to_tool_candidate`,
- nebo systemovy report `Quick notes status`.

## Navrhovane dalsi kroky

Okamzite:

- rano zobrazit seznam quick notes a overit, zda nove poznamky pribyvaji jako
  samostatne soubory.

Volitelne navazujici:

- doplnit status/system report pro quick notes;
- pridat kategorii/stav poznamky: `inbox`, `tool_candidate`, `project_candidate`,
  `reminder_candidate`, `done`;
- pridat potvrzene presunuti poznamky do `processed`;
- propojit quick notes s obecnym workflow command registry;
- vytvorit dalsi zkratku `Dokument do trezoru`;
- vytvorit zkratku `Faktura / nákup do archivu`.

## Zmenene nebo relevantni soubory

- `Samantha_Agent/app/quick_notes.py`
- `Samantha_Agent/scripts/samantha_quick_notes.py`
- `Samantha_Agent/tests/test_quick_notes.py`
- `Samantha_Agent/app/samantha_agent.py`
- `Samantha_Agent/memory/technical/iphone_shortcuts_playground.md`
- `Samantha_Agent/memory/technical/shopping_research_and_purchase_archive.md`
- `Samantha_Agent/data/private/quick_notes/index.json` - soukromy index, necommitovat.
- `/Users/miloslavfalta/Documents/Shortcuts Playground/Rychlá poznámka pro Samanthu.shortcut` - hotova zkratka mimo git.

## Git stav pri ulozeni handoffu

Pred handoffem byly lokálně hotove commity:

- `9304ccd Add shopping research workflow concept`
- `92db690 Add quick notes inbox tools`

Repo bylo `ahead 2` pred ulozenim tohoto handoffu.

## Bezpecnost / neukladat

- Necommitovat obsah quick notes z `data/private/quick_notes/`.
- Necommitovat skutecne `.shortcut` soubory ani private request drafty.
- Quick notes mohou obsahovat soukrome napady; do memory ukladat jen shrnuti
  workflow, ne plne texty poznamek bez vyslovneho souhlasu.
