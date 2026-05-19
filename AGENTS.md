# PythonMF - projektove instrukce pro Codex

Tyto instrukce plati pri spusteni Codexu z korene projektu `PythonMF`.

## Hlavni pravidlo

Projektova pamet a pravidla pro navazovani prace jsou ve slozce:

```text
Samantha_Agent/
```

Pred dulezitou praci si precti:

```text
Samantha_Agent/AGENTS.md
Samantha_Agent/memory/MEMORY_INDEX.md
```

Relevantni kontext hledej v:

```text
Samantha_Agent/memory/
```

## Rychle prikazy pro handoff

Kdyz Mila napise kratkou vetu jako:

- `uloz handoff`
- `uloz rozpracovano`
- `prerus praci`
- `uloz to jako prioritu 1`
- `uloz handoff a pripomen mi to`

postupuj podle pravidel v:

```text
Samantha_Agent/AGENTS.md
Samantha_Agent/memory/technical/session_recovery_rules.md
```

To znamena hlavne:

1. Vytvor bezpecny handoff z aktualniho kontextu do `Samantha_Agent/memory/handoffs/`.
2. Pokud neni jasne tema, priorita, stav nebo dalsi krok, zeptej se maximalne 3 kratkymi otazkami.
3. Aktualizuj `Samantha_Agent/memory/ACTIVE_PROJECTS.md`.
4. Aktualizuj `Samantha_Agent/memory/MEMORY_INDEX.md`, pokud ma byt handoff dohledatelny nebo pripomenuty.
5. Nikdy neukladej hesla, tokeny, API klice, app-specific passwords, rodna cisla, cele e-maily ani jina citliva data bez vyslovneho souhlasu.

## Bezpecnost

- Neupravuj soubory mimo rozsah aktualniho ukolu, pokud to neni nutne.
- Nikdy nemaz soubory bez vyslovneho souhlasu Mily.
- Pri git operacich nepouzivej slepe `git add .`.
- Soubory v `Samantha_Agent/data/session_autosave/` jsou nouzove logy a nesmi se commitovat.

## Prace nad podprojekty

`PythonMF` obsahuje vice samostatnych oblasti, napriklad:

- `Samantha_Agent/`
- `MultiLO/`
- `MatysekANJ/`
- `VocabularyFR/`
- `VocabularyIT/`
- `Pict/`
- `Tax/`

Pred zmenami v konkretni oblasti najdi a precti odpovidajici memory soubor v
`Samantha_Agent/memory/projects/`, pokud existuje.
