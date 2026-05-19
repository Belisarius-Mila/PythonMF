# Workflow command registry

Zalozeno 2026-05-19.

## Smysl

Samantha ma spoustet lokalni workflow lidskymi pokyny, ale technicky jen pres
predem schvalene presne prikazy. Model nema vymyslet shell prikaz ad hoc.

Priklad lidskeho pokynu:

```text
Zalohuj nas projekt na externi disk.
```

Samantha ho namapuje na znamy workflow command z registru a spusti ulozene
`argv`, ne novy shell string vygenerovany z odpovedi.

Zapisujici workflow ma byt dvoukrokove:

1. Samantha ukaze presny shell prikaz a zepta se na potvrzeni.
2. Mila napise `ano`, `potvrzuji` nebo podobne.
3. Samantha spusti presne ten ulozeny pending prikaz.

## Implementace

Registry je v:

```text
Samantha_Agent/app/workflows/commands.py
```

Agent ma tooly:

```text
list_workflow_commands
preview_workflow_command
run_workflow_command
```

`preview_workflow_command` u zapisujicich prikazu uklada cekajici potvrzeni do:

```text
Samantha_Agent/data/workflows/pending_command.json
```

`run_workflow_command` smi jednoduche `ano` pouzit jen tehdy, kdyz pending prikaz
stale odpovida stejnemu `command_id` a stejnemu presnemu shellu.

Kazdy workflow command ma mit:

- `command_id`,
- lidsky nazev a ucel,
- nekolik prikladovych formulaci, ne vycet vsech moznych vet,
- vyznamove pojmy a povinne skupiny zameru,
- presny `argv`,
- `cwd`,
- popis rizika,
- popis, kam zapisuje,
- volitelny preflight,
- test.

## Bezpecnostni pravidla

- Nespoustet libovolny shell prikaz podle volneho textu.
- Nejednoznacny nebo slaby fuzzy match se nesmi spustit.
- Nemapovat rucne kazdou vetu. Registrovat schopnost/workflow a jeho vyznam,
  aby Samantha mohla z bezne cestiny odvodit zamer.
- Zapisujici workflow se nema spoustet v prvnim kroku; nejdriv ukazat shell a
  cekat na potvrzeni.
- Workflow, ktere zapisuje mimo projekt nebo pracuje s citlivymi daty, musi mit
  preflight a podle rizika i potvrzovaci gate.
- Recovery zaloha smi standardne smerovat jen do
  `/Volumes/SamanthaSecureBackup/SamanthaBackups`.
- Nove workflow pro e-maily nesmi obchazet existujici potvrzovaci pravidla pro
  cteni tel, archivaci, URL ani reminders.

## Aktualni prikazy

```text
backup_project_recovery
backup_project_dry_run
```

Zaloha je prvni pilotni workflow. Dalsi strukturální projekty maji pouzit stejnou
vrstvu misto pridavani dlouhych manualnich prikazu do chatu.
