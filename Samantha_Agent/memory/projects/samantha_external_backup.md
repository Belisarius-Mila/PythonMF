# Samantha external backup

Projekt zalozen 2026-05-19.

## Aktualni stav 2026-06-07

Posledni uspesna ostra recovery zaloha je podle
`Samantha_Agent/data/backup/activity_state.json` z 2026-06-07:

```text
/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/20260607_092609/PythonMF
```

Zaloha probehla pres Pythonovy inkrementalni nastroj:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups --progress-every 5000
```

Vystup ostreho behu:

```text
files seen: 19398
files copied: 5911
files hard-linked: 13487
files skipped: 0
bytes copied: 4822566601
```

Overeni po behu:

- snapshot ma `backup_manifest.txt`,
- snapshot ma `READ_ME_FIRST_RECOVERY.md`,
- snapshot ma `PythonMF/` a `codex_home/`,
- `scripts/backup_status.py` hlasi, ze posledni zaloha je v 3dennim intervalu
  `2026-06-07`,
- restore drill obnovil `Samantha_Agent/AGENTS.md` jen do
  `/private/tmp/samantha_restore_drill_20260607/Samantha_Agent/AGENTS.md`,
- `cmp` a SHA-256 potvrdily shodu:
  `6432dfe626caaac6970e981c2e193c2d855b8a98f1abc5b02eb75a53e547b0d3`.

Po zaloze ma `/Volumes/SamanthaSecureBackup` zhruba `471Gi` volno.

## Predchozi stav 2026-06-03

Predchozi uspesna ostra recovery zaloha byla podle
`Samantha_Agent/data/backup/activity_state.json` z 2026-06-03:

```text
/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/20260603_175327/PythonMF
```

Zaloha probehla po vymene problemoveho hubu za primejsi propojku a pres novy
Pythonovy inkrementalni nastroj:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups --progress-every 5000
```

Vystup behu:

```text
files seen: 13856
files copied: 1174
files hard-linked: 12682
files skipped: 0
bytes copied: 338166106
```

Overeni po behu:

- snapshot ma `backup_manifest.txt`,
- snapshot ma `READ_ME_FIRST_RECOVERY.md`,
- snapshot ma `PythonMF/` a `codex_home/`,
- `scripts/backup_status.py` hlasi, ze posledni zaloha je v 3dennim intervalu
  `2026-06-03`.

Po samostatnem potvrzeni od Mily byly 2026-06-03 smazany nedokoncene snapshoty
z neuspesnych pokusu:

```text
20260603_162647
20260603_163709
```

Soucasne byl po potvrzeni smazan stary nafouknuty, ale uspesny snapshot z
2026-05-29:

```text
20260529_225518
```

Pouzite misto na `/Volumes/SamanthaSecureBackup` kleslo zhruba z `54Gi` na
`24Gi`. Novy snapshot `20260603_175327` po smazani stareho hardlinkovaneho
snapshotu ukazuje v `du` vetsi vlastni velikost (`18G`), protoze sdilene bloky
jsou ted uctovane jemu.

## Predchozi stav 2026-05-29

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

Restore drill byl dokoncen 2026-06-04 bez prepisu zivych dat.

Overeny snapshot:

```text
20260603_175327
```

Postup:

1. Overeno, ze `/Volumes/SamanthaSecureBackup` je pripojeny a snapshot ma
   recovery profil.
2. Vybran maly bezpecny soubor:
   `Samantha_Agent/AGENTS.md`.
3. Soubor obnoven pouze do:
   `/private/tmp/samantha_restore_drill/Samantha_Agent/AGENTS.md`.
4. `cmp` proti aktualnimu souboru prosel bez rozdilu.
5. SHA-256 obou souboru byl shodny:
   `6b50675b800c6b4c4eee8f60c02b660bfbce958578dbc78180b0a7013d98cd2d`.

Zive projektove soubory nebyly prepsane a ze zalohy nebylo nic mazano.

Pri pristim pripojeni `SamanthaSecureBackup` a pri dalsi recovery zaloze je
vhodne restore drill zopakovat po nove uspesne zaloze.

Minimalni postup po pristi uspesne zaloze:

1. Overit, ze `/Volumes/SamanthaSecureBackup` je pripojeny a ze novy snapshot ma
   `backup_manifest.txt` a `READ_ME_FIRST_RECOVERY.md`.
2. Vybrat maly bezpecny soubor, napr. `Samantha_Agent/AGENTS.md`.
3. Obnovit ho pouze do `/private/tmp/samantha_restore_drill/`, ne do ziveho
   projektu.
4. Porovnat obnoveny soubor s aktualnim souborem pres `cmp`.
5. Zapsat vysledek restore drillu do teto memory.

## USB checkpoint 2026-06-03

Dne 2026-06-03 byla nova zaloha pozastavena jeste pred dry-runem, protoze Mac
nevidel externi disk ani beznou flashku pripojenou pres stejny USB hub.

Pred restartem platilo:

- `/Volumes` ukazovalo jen `Macintosh HD`,
- `diskutil list` videl jen interni disk,
- `hdiutil info` neukazal pripojeny image/kontejner,
- `system_profiler SPUSBDataType SPThunderboltDataType` neukazal externi hub ani
  storage zarizeni,
- Thunderbolt porty hlasily `No device connected`.

Navazani po restartu:

1. Nejdriv overit fyzicke pripojeni pres `/Volumes`, `diskutil list`,
   `system_profiler SPUSBDataType SPThunderboltDataType` a `hdiutil info`.
2. Pokud se objevi `/Volumes/Falta`, najit a odemknout sifrovany kontejner
   `SamanthaSecureBackup.sparsebundle`.
3. Pokud se objevi `/Volumes/SamanthaSecureBackup`, spustit nejdriv recovery
   dry-run.
4. Ostrou recovery zalohu spustit az po kontrole dry-runu a Milove potvrzeni.

Aktualizace po pokusu o zalohu 2026-06-03:

- Disk `Falta` i sifrovany svazek `/Volumes/SamanthaSecureBackup` byly po
  pripojeni videt.
- Stary `/usr/bin/rsync` (`openrsync`, kompatibilita 2.6.9) neumel spolehlive
  udelat presny dry-run s `--link-dest`; padal na `Bad file descriptor`.
- Ostre recovery pokusy nedobehly:
  - snapshot `20260603_162647` spadl na `mmap: Operation timed out` uvnitr
    `.venv_f5tts2`,
  - filtr byl opraven o `.venv_*/`,
  - snapshot `20260603_163709` spadl na `mmap: Operation timed out` na malem CSV.
- `scripts/backup_status.py` stale spravne ukazuje posledni uspesnou zalohu
  `20260529_225518`; novy uspesny stav se nezapsal.
- `scripts/backup_samantha.command` byl opraven tak, aby jako predchozi snapshot
  vybiral jen adresare s `backup_manifest.txt` a ignoroval nedokoncene snapshoty.

Dokud se nevyjasni stabilita I/O, nepoustet dalsi stejny pokus pres stejny
hub/kabel. Dalsi rozumny krok je zkusit stabilnejsi pripojeni disku nebo pripravit
alternativu k `/usr/bin/rsync` pro recovery profil.

Optimalizace 2026-06-03:

- Vznikla alternativni Pythonova inkrementalni zaloha:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups
```

- Nastroj nepouziva `rsync` ani `mmap`; soubory kopiruje po blocich a nezmenene
  soubory hardlinkuje z posledniho dokonceneho snapshotu.
- Dokonceny snapshot je rozpoznany jen podle `backup_manifest.txt`; nedokoncene
  adresare z neuspesnych pokusu se nepouziji jako reference.
- Manifest a stav posledni uspesne zalohy se zapisi az po uspesnem dobehu.
- Lokalni testy prosly pres:

```bash
.venv/bin/python -m unittest tests.test_backup_incremental tests.test_backup_activity_state tests.test_backup_restore_tools tests.test_backup_run_tools
```

- Dalsi ostry pokus ma jit prednostne pres Pythonovy nastroj, ale az po
  stabilnejsim fyzickem pripojeni disku.

Podrobny handoff je v:

```text
memory/handoffs/backup_usb_hub_restart_checkpoint_2026_06_03.md
```

## Skript

Pripraveny zaklad:

```text
Samantha_Agent/RECOVERY_CARD_NEW_MAC.md
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
