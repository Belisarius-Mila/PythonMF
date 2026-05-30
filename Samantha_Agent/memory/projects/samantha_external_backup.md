# Samantha external backup

Projekt zalozen 2026-05-19.

## Aktualni stav 2026-05-29

Posledni uspesna ostra recovery zaloha je podle
`Samantha_Agent/data/backup/activity_state.json` z 2026-05-29:

```text
/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/20260529_225518/PythonMF
```

Zaloha probehla po odemceni kontejneru `SamanthaSecureBackup`. Behem behu se
ukazalo, ze `Samantha_Agent/data/session_autosave/` narostlo zhruba na 30 GB a
zbytecne prodlouzilo zalohu. Od 2026-05-29 se proto session autosave vynechava
v `backup_rsync_filter_always.rules`, tedy i v recovery profilu. Autosave je
nouzovy reconnect log, ne kanonicka disaster-recovery data.

Do te doby ma Samantha/Codex pri kazdem startu nebo navazani zkontrolovat stav:

```bash
.venv/bin/python scripts/backup_status.py
```

Pokud posledni zaloha chybi nebo je starsi nez 3 dny, ma to rict v prvni odpovedi
kazdy den, dokud neprobehnou nova uspesna zaloha. Nejde o automaticke kopirovani:
pripominka sama nic nekopiruje, nemaze ani necte tajemstvi.

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
- vynechava `Tax/`,
- zalohuje jen `~/.codex/config.toml`, nikdy `~/.codex/auth.json`.

`recovery` profil je urceny pro plnou obnovu pouze do sifrovaneho cile:

- zahrnuje lokalni citliva data projektu,
- muze zahrnout `.env`, e-mailove lokalni archivy, reminders a Tax,
- zahrnuje `~/.codex/config.toml`, `~/.codex/history.jsonl` a `~/.codex/sessions/`,
- nikdy nezalohuje `~/.codex/auth.json`.

Oba profily vzdy vynechavaji `Samantha_Agent/data/session_autosave/`, protoze jde
o nouzove logy relaci s vysokym rizikem rychleho narustu velikosti.

## Pripomenout pri pristi recovery zaloze

Pri pristim pripojeni disku udelat novou recovery zalohu uz s opravenym filtrem,
tedy bez `Samantha_Agent/data/session_autosave/`.

Postup:

1. Spustit dry-run recovery zalohy do pripojeneho sifrovaneho kontejneru.
2. Spustit ostrou recovery zalohu az po uspesnem dry-runu.
3. Overit, ze novy snapshot ma `backup_manifest.txt` a `READ_ME_FIRST_RECOVERY.md`.
4. Overit, ze `.venv/bin/python scripts/backup_status.py` ukazuje nove datum
   posledni uspesne zalohy.
5. Teprve potom se samostatnym potvrzenim od Mily smazat jen stary nafouknuty
   snapshot `20260529_225518`.

Stary snapshot `20260529_225518` nemazat pred vznikem a overenim noveho snapshotu.

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

Pro Codex relace, ktere nemusi spoustet runtime Samanthy, je povinny startovni
fallback prikaz:

```bash
.venv/bin/python scripts/backup_status.py
```

Tento prikaz cte jen lokalni stav `data/backup/activity_state.json` a podle data
vypise, zda je zaloha v 3dennim intervalu nebo se ma pripomenout.

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
