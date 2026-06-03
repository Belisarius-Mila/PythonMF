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

Od 2026-06-03 je hlavni implementace backup workflow Pythonovy inkrementalni
nastroj bez `rsync/mmap`:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups
```

Stary `scripts/backup_samantha.command` zustava jen jako fallback.

## Souvisejici systemove reporty

Systemove reporty nejsou primarne shell workflow prikazy. Jsou to registrovane
Python tooly Samanthy se samostatnym registrem v:

```text
Samantha_Agent/app/system_reports.py
Samantha_Agent/memory/technical/system_reports.md
```

Rucni CLI spusteni existuje hlavne pro testovani a lidsky provoz:

| Report | CLI prikaz | Samantha tool |
| --- | --- | --- |
| Prehled reportu | `.venv/bin/python scripts/samantha_system_reports.py` | `samantha_system_reports()` |
| Health check | `.venv/bin/python scripts/samantha_health_check.py --mode quick` | `samantha_health_check(mode="quick")` |
| Kvantitativni status | `.venv/bin/python scripts/samantha_quantitative_status.py` | `samantha_quantitative_status(save=False)` |
| Kvantitativni snapshot | `.venv/bin/python scripts/samantha_quantitative_status.py --save` | `samantha_quantitative_status(save=True)` |
| Capability audit | `.venv/bin/python scripts/samantha_capability_audit.py` | `samantha_capability_audit()` |
| Knowledge inbox inventory | `.venv/bin/python scripts/samantha_knowledge_inbox.py` | `samantha_knowledge_inbox_inventory()` |
| Downloads inventory | `.venv/bin/python scripts/samantha_downloads_to_knowledge_inbox.py --list` | `samantha_downloads_inventory()` |
| iPhone shortcuts status | `.venv/bin/python scripts/samantha_iphone_shortcuts.py --status` | `iphone_shortcuts_playground_status()` |
| Memory status | `.venv/bin/python -m app.samantha_agent "Ukaz stav lokalni pameti Samanthy."` | `memory_status()` |

Pravidlo: pokud novy report zacne byt opakovane uzitecny, Samantha se zepta:
"Udelame z toho novy systemovy report?" Teprve po souhlasu se prida do registru
reportu, dokumentace a testu.

Kopirovani ze Stazenych do knowledge inboxu neni shell workflow. Je to Python
tool `copy_downloads_files_to_knowledge_inbox`, protoze zapisuje do soukromeho
inboxu a ma vlastni potvrzovaci gate.

## Kandidati k registraci

### PictNew / slovnikove obrazky

Kanonicky postup je popsany v:

```text
Samantha_Agent/memory/technical/vocabulary_image_generation_workflow.md
```

Stav 2026-05-20:

- workflow je rucne overeny na `VocabularyIT`,
- neni jeste registrovany v `app/workflows/commands.py`,
- Samantha ho proto nesmi spoustet jako volny ad hoc shell podle jedne vety.

Doporucene command/tool kroky:

- `pictnew_prepare_request` - bez API, priprava request JSON,
- `pictnew_generate_batch_preview` - dry-run bez API,
- `pictnew_generate_batch_confirmed` - placene generovani jedne davky po potvrzeni,
- `pictnew_copy_approved_to_pict` - kopie schvalenych `.webp` bez prepisu,
- `pictnew_update_mapping_preview` a `pictnew_update_mapping_apply` - mapping jen se zalohou a potvrzenim.

Bezpecnostni brany:

- placene API generovani vyzaduje explicitni potvrzeni rozsahu,
- `Pict/mapping.json` se neupravuje bez samostatneho potvrzeni a zalohy,
- API klice se nesmi ukladat do repo souboru ani memory,
- nepouzivat `git add .`.
