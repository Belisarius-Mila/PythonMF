# Samantha external backup

Projekt zalozen 2026-05-19.

## Cil

Pripravit jednoduchou offline zalohu projektu `PythonMF` a Samanthy na externi
disk tak, aby bylo mozne po ztrate nebo havarii Macu obnovit agenta co nejvic do
puvodniho stavu.

## Disk

Aktualni externi disk:

```text
/Volumes/Falta
```

Disk je APFS svazek s rodinnymi fotkami, videi a dalsimi beznymi soubory. Proto
neni vhodne dodatecne sifrovat cely disk jen kvuli Samanthe. Preferovane reseni
je samostatny sifrovany kontejner pro citlivou Samantha zalohu, napr. pripojeny
jako:

```text
/Volumes/SamanthaSecureBackup
```

## Profily zalohy

`safe` profil je urceny pro kontrolu nebo nesifrovany cil:

- vynechava `.env` a `.env.*`,
- vynechava `Samantha_Agent/data/email/`,
- vynechava `Samantha_Agent/data/reminders/`,
- vynechava `Samantha_Agent/data/session_autosave/`,
- vynechava `Tax/`,
- zalohuje jen `~/.codex/config.toml`, nikdy `~/.codex/auth.json`.

`recovery` profil je urceny pro plnou obnovu pouze do sifrovaneho cile:

- zahrnuje lokalni citliva data projektu,
- muze zahrnout `.env`, e-mailove lokalni archivy, reminders a Tax,
- zahrnuje `~/.codex/config.toml`, `~/.codex/history.jsonl` a `~/.codex/sessions/`,
- nikdy nezalohuje `~/.codex/auth.json`.

## Skript

Pripraveny zaklad:

```text
Samantha_Agent/RECOVERY_FROM_BACKUP.md
Samantha_Agent/scripts/create_samantha_secure_backup.command
Samantha_Agent/scripts/backup_samantha.command
Samantha_Agent/scripts/backup_rsync_filter_always.rules
Samantha_Agent/scripts/backup_rsync_filter_sensitive.rules
```

Vychozi spusteni je `dry-run`, tedy nic nekopiruje:

```bash
Samantha_Agent/scripts/backup_samantha.command --dry-run --profile safe
Samantha_Agent/scripts/backup_samantha.command --dry-run --profile recovery
```

Ostra recovery zaloha ma byt az po vytvoreni a pripojeni sifrovaneho kontejneru.
Pri ostre zaloze ma byt recovery navod ulozen i do korene snapshotu jako
`READ_ME_FIRST_RECOVERY.md`.

## Spousteni pres Samanthu

Samantha ma k dispozici obecny workflow registry a v nem prikaz:

```text
backup_project_recovery
```

Kdyz Mila napise kratky pokyn typu:

```text
Zalohuj nas projekt na externi disk.
```

Samantha ma pres tool `run_workflow_command` spustit standardni ostrou recovery
zalohu az po dvoukrokovem potvrzeni. Nejdriv ma ukazat presny prikaz pres
`preview_workflow_command`:

```text
mode=execute
profile=recovery
target=/Volumes/SamanthaSecureBackup/SamanthaBackups
```

Pak ma pockat na Milovo `ano` nebo `potvrzuji` a teprve potom spustit pending
workflow pres `run_workflow_command`.

Pokud neni pripojeny sifrovany kontejner `SamanthaSecureBackup`, ma Samantha
jen vysvetlit, ze je potreba pripojit externi disk a kontejner. Nema vymyslet
jiny cil pro recovery zalohu.

## Pripominka

Stav posledni uspesne ostre zalohy se bude zapisovat do:

```text
Samantha_Agent/data/backup/activity_state.json
```

Samantha ma pri startu pripominat zalohu, pokud posledni uspesna zaloha chybi
nebo je starsi nez 3 dny. Pripominka sama nic nekopiruje, nemaze ani necte
tajemstvi.

## Bezpecnostni pravidla

- Neprovadet ostrou `recovery` zalohu do nesifrovane slozky na disku `Falta`.
- Nevkladat hesla, API klice ani tokeny do memory.
- `~/.codex/auth.json` nezalohovat ani do recovery profilu.
- Pred prvni ostrou zalohou zkontrolovat dry-run statistiku a cil.
- Nepouzivat automaticke mazani na zaloze v prvni verzi.

## Cilena obnova

Samantha ma mit tooly pro cilene vytazeni jednoho souboru nebo slozky ze
snapshotu:

```text
list_backup_snapshots
preview_backup_restore
restore_path_from_backup
```

Obnova musi byt vzdy nejdriv nahled, potom samostatne potvrzeni. Tool smi
obnovovat jen relativni cesty uvnitr `PythonMF`, odmita absolutni cesty a `../`,
pred prepisem vytvari `.before_restore_YYYYMMDD_HHMMSS` kopii a nic nemaze ze
zalohy. Citlive oblasti vyzaduji dodatecne potvrzeni `citlive` nebo `recovery`.
