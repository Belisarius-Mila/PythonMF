# Samantha external backup

Projekt zalozen 2026-05-19.

## Aktuální záměr 2026-11-07 12:02 CET

Týdenní správce obnovovacího TXT modelem 6.1-Sol; výstup vždy PythonMF +
iCloud Drive/Dokumenty. Podrobný plán REC-01 až REC-06 je na konci tohoto
souboru. Zatím plán, žádný modelový běh, změna TXT, role nebo plánovače.
Historické údaje o zálohách níže nejsou nový živý audit.

## Historický stav 2026-10-25 14:53 CET

- 2026-10-25 14:53 CET: Nová schválená recovery záloha dokončená a ověřená. Projekt `20261025_142837`: 63 143 souborů, 17 050 kopírovaných, 46 092 hardlinků, 1 symlink, 0 skipped; 4 309 588 279 nových B. Skutečně připojený šifrovaný cíl ověřený před/po; starší snapshoty zachované.
- Živé Camino `20261025_143650-abf7e7e5`: 1 647 souborů / 5 167 041 733 B, čtyři DB; 921 operací, 132 Momentů, 4 cesty a 316 originálů / 2379212189 B. Registrovaný běh ověřil úplné SHA, DB i mediální účtenky a shodný zmrazený zdroj.
- Závěrečná kontrola PASS: čtyři projektové SHA a skutečná rekonstrukce do nové dočasné složky; čtyři DB quick_check; auth.json a nouzové autosave vyloučené. Soukromá .env shodná, bez výpisu citlivých dat. Camino owner HTTP/HTTPS zpět, config/Serve a Cockpit PID/stamp shodné.
- backup_status nyní potvrzuje 25. 10. 2026; na šifrovaném cíli ~406 GiB volných. Zdrojový kód ani síť se neměnily, žádná starší data/záloha se nemazala. Není to obraz celého Macu; kompletní instalace a fyzická přejímka náhradního počítače zůstává samostatná.
- Podrobnosti: memory/reports/backup_recovery_20261025.md; shodný souhrn na SSD v recovery_updates, soukromé důkazy v data/private/backup_recovery_20261025/. TXT 1.2 zachovává historické příklady; aktuální dvojici snapshotů určuje dnešní manifest. Další krok: pravidelná další záloha, k původnímu tématu upozornění se vrátit samostatně. Tento výsledkový zápis je jen lokální dokumentační checkpoint, bez push/deploy.

## Historie 2026-10-19 22:13 CEST

Podrobný lidský návod: `../../OBNOVA_SAMANTHY_NOVY_MAC.txt`, verze 1.2,
17 kapitol včetně instalací a přejímky. Projektová kopie, Plocha, kořen
externího disku Falta a kořen iCloud Drive mají shodný SHA-256. Na obou
úložištích je aktuální `OBNOVA_SAMANTHY_NOVY_MAC.txt` verze 1.2. macOS
Foundation potvrzuje iCloud ubiquitous/uploaded true, uploading false,
bez chyby uploadu; přenos textu mimo Mac je dokončený.
Záloha Camina už existuje a její stav se touto úpravou nemění.
Recovery karty směrují na tentýž TXT; Git bundle ve šifrovaném
`SamanthaBackups/recovery_updates/` doplňuje kód od projektového snapshotu
z 18. 10. a zachová i nové nástroje před samostatným pushem.

Projektové jádro: `20261018_210658`, recovery, 90 833 souborů,
12 194 kopírováno, 78 639 hardlinků, 0 přeskočeno; 1 137 947 624 nových B.
Původní manifest, hash 4/4 a obnova AGENTS.md doložené logem z 18. 10.
Snapshot ani datum projektové evidence nebyly dnešním doplňkem přepsány.

Živé Camino mimo PythonMF má nyní skutečný šifrovaný doplněk
`20261019_212828-78238a8a` v `SamanthaBackups/camino_snapshots/`:
1 587 souborů / 5 078 684 995 B; čtyři DB, 304 originálů /
2 339 685 533 B, viewer-copies, film-projects, soukromá konfigurace,
tokenové soubory a pevný nasazený release. Archiv má 893 operací,
124 Momentů a 3 cesty. Dokončený `backup_manifest.json` je soukromý.
Připojení skutečného šifrovaného cíle ověřeno před/po běhu.

Registrované `scripts/backup_camino.py --dry-run|--execute` používá pevný
šifrovaný cíl, filmový zámek, řízený stop vlastní služby a skutečné čekání
na unloaded, offline zámek a SQLite backup API včetně WAL. Venv, cache,
provozní log a zámky se nekopírují. Dokončený manifest vzniká až po
ověření kopie a zdravém návratu původně běžící služby. Aktualizovaný
recovery program jej volá automaticky a zapíše `Camino supplement: <ID>`;
selhání doplňku zabrání označení projektové zálohy jako dokončené.
Profil safe tento soukromý doplněk nevytváří.

Ověření zálohovacího běhu 19. 10.: celý doplněk obnoven do nové soukromé dočasné složky; všechny
soubory SHA-256, čtyři quick_check a kompletní mediální účtenky PASS.
Obnovená kopie nespouštěla druhou službu. Produkce HTTP/HTTPS zdravá,
anonymní přístup odmítnut, archiv/config/Serve/Funnel shodné; Cockpit 200.
34 cílených testů a plná brána 2 133/2 133 PASS. Důkazy v `logs/`:
`camino_backup_execute_20261019_r2.log`, `camino_backup_restore_20261019.log`,
`camino_backup_after_20261019.log`, `camino_backup_full_gate_20261019_final2.log`.
První pokus skončil bez snapshotu a vyžadoval řízený návrat služby;
opravena asynchronní stop/start sekvence, poté jeden kontrolovaný běh.

Hranice: nový recovery program je lokální zdrojová změna, bez push/deploy.
Předchozí neshoda vlastnické účtenky Serve zůstává k samostatnému posouzení;
skutečné HTTPS funguje a síť se zálohou neměnila. Úplná přejímka nového
Macu neproběhla. Aplikace, interprety, Klíčenka, LaunchAgents, SSH/shell,
kompletní ~/.codex a další externí data nadále nejsou obrazem tohoto backupu.
`data/session_autosave/` je vyloučené; původní Codex sessions jsou jiný rozsah.

Další krok: při obnově otevřít TXT z disku Falta nebo iCloud Drive;
pravidelná recovery záloha a celková instalace nového Macu zůstávají
samostatné kroky. Ověření distribuce návodu je v lokálním logu
`logs/recovery_txt_external_icloud_20261019.log`.

## Historie 2026-09-14 23:26 CEST

Ostrá recovery záloha `20260914_231439` dokončena standardním registrovaným
Pythonovým příkazem po výslovném zadání Míly a kontrole dry-runu.
Cíl: připojený šifrovaný kontejner SamanthaSecureBackup; šifrování ověřeno
přes `hdiutil isencrypted`. Po běhu přibližně 429,65 GiB volných.

- 63 295 souborů: 28 892 kopírováno, 34 360 hardlinků, 43 symlinků; 0 přeskočeno.
- Zkopírováno 11 792 778 198 bajtů, exit 0, manifest a recovery návod existují.
- `auth.json` a nouzové `data/session_autosave/` ve snapshotu nejsou.
- Čtyři dokumenty Camino a AGENTS.md mají shodné SHA-256 se zdrojem.
- AGENTS.md obnoven pouze do nové dočasné složky; shodný SHA-256
  `3ffa4338e1516433e732ac9a8c9715ee730e58ca520955a0a4919ef1b439a318`.
- Stav poslední zálohy aktualizoval nástroj na 2026-09-14. Nic nebylo mazáno.
- Snapshot zachycuje zdroje před následným dokumentačním checkpointem; nejde
  o atomický obraz všech běžících služeb ani o zálohu instalace Xcode mimo PythonMF.
- Zkouška malého souboru není úplný disaster-recovery test celého počítače.

Další krok: pravidelná recovery záloha podle živého `backup_status.py`.
Starší záznamy níže jsou historie, nikoli dnešní stav.

## Aktualni stav 2026-07-29

Posledni uspesna ostra recovery zaloha je podle
`Samantha_Agent/data/backup/activity_state.json` z 2026-07-29:

```text
/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/20260729_154354/PythonMF
```

Zaloha probehla pres Pythonovy inkrementalni nastroj:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups --progress-every 5000
```

Vystup ostreho behu:

```text
files seen: 55798
files copied: 4162
files hard-linked: 51636
files skipped: 0
bytes copied: 3895868304
```

Overeni po behu:

- snapshot ma `backup_manifest.txt`, `READ_ME_FIRST_RECOVERY.md`, `PythonMF/`
  a `codex_home/`,
- `scripts/backup_status.py` hlasi posledni zalohu v 3dennim intervalu,
- `codex_home/auth.json` nebyl zalohovan,
- restore drill obnovil `Samantha_Agent/AGENTS.md` pouze do
  `/private/tmp/samantha_restore_drill_20260729.TRVqG6/`,
- SHA-256 obnoveneho a ziveho souboru je shodny:
  `2ea4fce94dc72d9f10bd663c05a384e10fc41b9411bedb247ead0add7f28684b`.

Prvni ostry pokus skoncil po odpojeni sifrovaneho kontejneru. Nedokonceny
snapshot `20260729_153749` nema manifest, zustal zachovany a nastroj ho
nepouziva jako referenci. `diskutil verifyVolume` nasledne potvrdil APFS bez
chyb a jediny kontrolovany opakovany beh uspesne dobehl. Po zaloze zustalo na
svazku priblizne `451 GiB` volno.

## Starsi dokumentovany stav 2026-07-05

Posledni uspesna ostra recovery zaloha je podle
`Samantha_Agent/data/backup/activity_state.json` z 2026-07-05:

```text
/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/20260705_004846/PythonMF
```

Zaloha probehla pres Pythonovy inkrementalni nastroj:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups --progress-every 5000
```

Vystup ostreho behu:

```text
files seen: 25221
files copied: 284
files hard-linked: 24937
files skipped: 0
bytes copied: 185388847
```

Overeni po behu:

- snapshot ma `backup_manifest.txt`,
- snapshot ma `READ_ME_FIRST_RECOVERY.md`,
- snapshot ma `PythonMF/` a `codex_home/`,
- `scripts/backup_status.py` hlasi, ze posledni zaloha je v 3dennim intervalu
  `2026-07-05`,
- restore drill obnovil `Samantha_Agent/AGENTS.md` jen do
  `/private/tmp/samantha_restore_drill_20260705/Samantha_Agent/AGENTS.md`,
- `cmp` a SHA-256 potvrdily shodu:
  `e2542f4ba9c20415b350b5e5898cd2379db87fa6bb8fc62135681b43ec3cc61d`.

## Predchozi stav 2026-07-01

Posledni uspesna ostra recovery zaloha je podle
`Samantha_Agent/data/backup/activity_state.json` z 2026-07-01:

```text
/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/20260701_203915/PythonMF
```

Zaloha probehla pres Pythonovy inkrementalni nastroj:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups --progress-every 5000
```

Vystup ostreho behu:

```text
files seen: 24998
files copied: 1226
files hard-linked: 23772
files skipped: 0
bytes copied: 300354928
```

Overeni po behu:

- snapshot ma `backup_manifest.txt`,
- snapshot ma `READ_ME_FIRST_RECOVERY.md`,
- snapshot ma `PythonMF/` a `codex_home/`,
- `scripts/backup_status.py` hlasi, ze posledni zaloha je v 3dennim intervalu
  `2026-07-01`,
- restore drill obnovil `Samantha_Agent/AGENTS.md` jen do
  `/private/tmp/samantha_restore_drill_20260701/Samantha_Agent/AGENTS.md`,
- `cmp` a SHA-256 potvrdily shodu:
  `e2542f4ba9c20415b350b5e5898cd2379db87fa6bb8fc62135681b43ec3cc61d`.

## Predchozi stav 2026-06-27

Posledni uspesna ostra recovery zaloha je podle
`Samantha_Agent/data/backup/activity_state.json` z 2026-06-27:

```text
/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/20260627_002457/PythonMF
```

Zaloha probehla pres Pythonovy inkrementalni nastroj:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups
```

Vystup ostreho behu:

```text
files seen: 23883
files copied: 1357
files hard-linked: 22526
files skipped: 0
bytes copied: 163569589
```

Overeni po behu:

- snapshot ma `backup_manifest.txt`,
- `scripts/backup_status.py` hlasi, ze posledni zaloha je v 3dennim intervalu
  `2026-06-27`,
- restore drill obnovil `Samantha_Agent/AGENTS.md` jen do
  `/private/tmp/samantha_restore_drill_20260627/Samantha_Agent/AGENTS.md`,
- `cmp` a SHA-256 potvrdily shodu:
  `e2542f4ba9c20415b350b5e5898cd2379db87fa6bb8fc62135681b43ec3cc61d`.

## Predchozi stav 2026-06-11

Posledni uspesna ostra recovery zaloha je podle
`Samantha_Agent/data/backup/activity_state.json` z 2026-06-11:

```text
/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/20260611_235300/PythonMF
```

Zaloha probehla pres Pythonovy inkrementalni nastroj:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups --progress-every 5000
```

Vystup ostreho behu:

```text
files seen: 20383
files copied: 18
files hard-linked: 20365
files skipped: 0
bytes copied: 4965967
```

Overeni po behu:

- snapshot ma `backup_manifest.txt`,
- snapshot ma `READ_ME_FIRST_RECOVERY.md`,
- snapshot ma `PythonMF/` a `codex_home/`,
- `scripts/backup_status.py` hlasi, ze posledni zaloha je v 3dennim intervalu
  `2026-06-11`,
- restore drill obnovil `Samantha_Agent/AGENTS.md` jen do
  `/private/tmp/samantha_restore_drill_20260611_final/Samantha_Agent/AGENTS.md`,
- `cmp` a SHA-256 potvrdily shodu:
  `9113ee653949eaa58c2dd83ade03607b5c93641c8127733602efbece27580dd7`.

Po zaloze ma `/Volumes/SamanthaSecureBackup` zhruba `471Gi` volno.

## Predchozi stav 2026-06-07

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

## Aktualni provozni stav 2026-08-07

- Posledni uspesny recovery snapshot je `20260802_153855`.
- Stav je ulozeny v kanonickem projektu a ctou jej vsechny profilove
  workspaces; nevznikaji oddelene profilove kopie.
- K 2026-08-07 je snapshot starsi nez tri dny, proto `backup_status.py`
  spravne zobrazuje upozorneni.
- Handoff o neviditelnem USB disku z 2026-07-14 je historicky incident, ne
  dukaz aktualniho stavu disku.

Dalsi krok:

- Pripojit sifrovany externi disk, spustit standardni potvrzenou recovery
  zalohu a po dokonceni znovu overit `backup_status.py`.

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

## 2026-11-07 12:02 CET — plán vývoje týdenního správce obnovovacího návodu

### Hotovo
Připravený plán samostatné rutinní úlohy: jednou týdně celý obnovovací návod,
celá vymezená dokumentace Samanthy a kontrolované poznatky o aplikacích a
nastaveních Macu/iPhonu → ověřená nová verze TXT ve dvou cílech.
Jde o plánování, nikoli implementaci nebo aktivaci automatického běhu.

### Rozhodnutí
Míla požaduje model 6.1-Sol, týdenní aktualizaci a ukládání TXT do PythonMF
**a zároveň do Dokumentů na iCloudu**. Výstup má umožnit obnovu Samanthy po
ztrátě či zničení MacBooku bez znalosti původního rozhovoru. Harmonogram,
rozpočet a první provozní oprávnění zatím nejsou schválené. Není založen nový
TVBCP; úloha patří do existujícího proudu project-samantha-infrastructure.

### Další krok
Odsouhlasit tento plán a zahájit REC-01: přesný soupis zdrojů, identity obou
cílových míst, rozsah nastavení a neplacený náhled. Žádný modelový tah nyní.

### Navrhované další kroky
REC-02 čtecí modelový pilot; REC-03 obsahové kontroly; REC-04 uložení obou
kopií; REC-05 plánovač; REC-06 první skutečný běh a fyzická iCloud přejímka.

### Technický důkaz
Ověřený aktuální nález: Desktop TXT 1.2 (19. 10. 2026), SHA-256
 a3659d9cf61ccd9d1c04737060f215ec4b6547da1eb877aa92b793f97e936935.
Shodná kopie je v kořeni iCloud Drive. V PythonMF ani iCloud Dokumentech TXT
zatím není. Známý systémový alias iCloud Documents směřuje na ~/Documents.
Dílčí inventura místního main: 409 textových dokumentů, 5 002 170 B v
memory/docs a základních instrukcích; není to ještě konečný úplný manifest.
Stávající app/routine_tasks.py je omezený čtecí pilot do 12 000 B, nikoli
hotový správce obnovy, writer či scheduler. Model ani plánovač nebyly spuštěné.

#### Cíl a přesné dva výstupy

1. Kanonický projektový soubor:
   /Users/miloslavfalta/Desktop/PythonMF/OBNOVA_SAMANTHY_NOVY_MAC.txt
2. Kopie pro dostupnost mimo Mac:
   /Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/Documents/OBNOVA_SAMANTHY_NOVY_MAC.txt
   (v uživatelském rozhraní iCloud Drive → Dokumenty).

Budoucí program má cíle odvodit z ověřené konfigurace uživatele, nikoli
natvrdo vyžadovat stejné uživatelské jméno na náhradním Macu. Zjištěný
systémový symlink Documents je výslovně schválený typ aliasu; neplatí zákaz
všech symlinků, který by tuto skutečnou cestu zablokoval. Před zápisem se
ověří známá identity obou kořenů a odhalí změna/neočekávaný symlink.

První zavedení vybere původní TXT podle obsahu/verze/hashů, uchová jeho
nezměněnou předchozí verzi a sjednotí odkazy v dokumentaci na tyto dva cíle.
Staré Plocha/kořen iCloudu nebudou třetími nezávisle udržovanými hlavními
kopiemi; způsob jejich archivního označení se dokončí v migračním kroku.
Toto plánování původní TXT nekopíruje ani nepřepisuje.

#### Navržená architektura a autonomie

- Samostatná místní úloha na stávajícím Macu a App Server runtime, nezávislá
  na otevřeném okně Cockpitu. Žádná migrace na jiné SDK/API kvůli plánovači.
- Deterministický řadič načte podklady a řídí model, validátor, writer a stav.
  Sol dostane pouze připravená data a vrátí návrh. Nemá shell, MCP, konektory,
  možnost měnit zařízení, systém, Git nebo cílové cesty. Jako ověřený vzor
  lze použít izolaci start_data_only_thread, nikoli rozšířit existující
  report_documentation_review mimo jeho původní schválený kontrakt.
- Oddělená role recovery_document_maintainer, model gpt-6.1-sol,
  navržené reasoning medium, Standard. Žádná automatická náhrada modelu.
  Role se spravuje pouze v config/agent_roles.json; současné role beze změny.
  Nejdřív kompatibilní parser/kód, potom samostatná aktivace role.
- Povolené budoucí účinky: vytvořit návrh, bezpečné verze a účtenku; po
  jednorázově schváleném rozsahu aktualizovat pouze obě pevné cílové kopie
  a interní stav úlohy. Týdenní úspěšný běh nemá čekat na nové ruční schválení.
  Nové zdroje, širší cíle nebo změna autonomie vyžadují nové rozhodnutí.
- Žádné změny aplikací/nastavení iPhonu/Macu, restart či instalace služeb při
  týdenním auditu, odchozí e-mail, nový backup nebo samočinný Git commit/push.
  Potřebné zásahy popíše návod nebo se předají Mílovi jako neověřené kroky.

#### REC-01 — přesné podklady a rozhraní (Data)

Výstup: registr zdrojů, povolených čtecích kontrol a cílových cest; neplacený
náhled rozsahu a migrace původních kopií.

- Nejprve načíst celý původní TXT. Potom úplný obsah schválené dokumentace
  Samanthy a jejích připojených součástí: instrukce, projektové paměti,
  kanonické handoffy/TVBCP, workflow návody, README, Camino dokumentace a
  související návody aplikací. Historické reporty přečíst s označením stáří.
- Rozsah musí být explicitní a úplný, nelze místo požadovaného čtení celé
  dokumentace bez dohody zavést jen vyhledávání nebo git diff.
- Zmrazit seznam souborů, SHA-256, Git head a označení platnosti: aktuální
  rozhodnutí, doložená instalace/nasazení, plán, historický doklad. Při rozporu
  neprezentovat plán či starý log jako aktuální stav. Zrušené projekty včetně
  placeného hlasového rozhovoru neobnovovat ze starých návodů nebo přítomného
  kódu, který ještě není odstraněný z běžícího runtime.
- Do manifestu doplnit bezpečné výpisy registrovaných čtecích kontrol a
  vybraná nesekretní nastavení. Model nesmí číst .env, auth.json, Keychain,
  e-maily, soukromé dokumenty, autosave či celé transkripty relací.
- Mapa aplikací zahrne: účel, nutnost/volitelnost, instalaci, verzi a její
  důkaz, umístění konfigurace/dat, obnovu přihlášení, potřebná oprávnění,
  start služby a ověření funkce. Popsat zdrojové obnovovací cesty, nikoli
  hodnoty hesel, klíčů nebo tokenů.
- Vyjasnit Git politiku TXT: automatický provozní výstup nesmí špinit pracovní
  main a blokovat vývoj/p+n. Navržené řešení je přesná výjimka pro tento
  provozní TXT + verzovaný řadič/plán; ověřit, že recovery záloha TXT přesto
  zahrnuje. Samotný týdenní writer nemá měnit Git ani globální ignore.

#### REC-02 — čtecí pilot se Solem a změřením ceny (Data + budoucí Sol)

Výstup: návrh aktualizovaného TXT, mapování změn na zdroje, úplný důkaz
pokrytí vstupů a skutečná spotřeba. Nejprve syntetická sada bez tajemství;
skutečný modelový pilot teprve po schválení jeho ceny a rozsahu.

- Před modelem místně změřit tokeny a připravit rozdělení celých souborů do
  dávek. Podrobný původní návod a instrukce platnosti zůstanou společným
  podkladem. Každá dávka vrátí citované zjištění; finální Sol sestaví celý
  návod. Doložit přečtení všech souborů; nikdy tiše nekrátit konce či kapitoly.
- 5 MB nynější dílčí inventury nelze považovat za běžný 12kB rutinní tah.
  Model má v Codex/ChatGPT Work výchozí kontext 500K tokenů; rozdělení a
  opakované vstupy se musejí započítat do rozpočtu celé týdenní úlohy.
- Jednotlivé dávky jsou předem naplánované části jedné úlohy, ne automatické
  opakování nejasného modelového požadavku. Zmrazená role, běh, otisky zdrojů,
  počty tahů, vstup/výstup/cache a stav každé dávky mají vlastní účtenku.
- Oficiální Standard sazby při plánování: GPT-6.1 Sol 50 vstup / 2,5 cached /
  250 výstup kreditů za milion tokenů. To není počet úloh v předplatném ani
  API dolarová cena. Před první aktivací znovu ověřit model, sazby a typ
  autentizace. Náklad pro plán lze odhadnout až z tokenizovaného celku včetně
  syntézy, ne jen z počtu dokumentů; cache úsporu předem neslibovat.
- Po pilotu dohodnout limit na běh a měsíc a limit času/tahů. Nadlimitní
  předběžný odhad zastaví běh před modelem. Měření po dokončení není tvrdý
  fakturační strop. Žádný placený pilot v tomto plánovacím kroku.

#### REC-03 — kontrola kvality obnovovacího návodu (Data)

Výstup: automatické přejímací kontroly a sada případů; nezávislost na
původní konverzaci a test s novým čtenářem/agenty bez soukromé historie.

- Zachovat UTF-8, srozumitelnou úplnou strukturu a potřebné obnovovací kroky.
  Nová či zrušená funkce vyžaduje podloženou změnu, ne pouhou změnu data.
- Každá věcná novinka má doložitelný zdroj a stáří. Ověřené příkazy odkazují
  na registrované workflow; audit příkazy k obnově nespouští. Přístupové údaje
  se popisují místem uložení/získání, nikdy skutečnou hodnotou.
- Mac: Python/prostředí, Codex/App Server, modelové role, Cockpit, launchd a
  PATH, Tailscale HTTPS, zálohy, data mimo Git, Camino/úložiště, Xcode,
  podpis a instalace na iPhone, iCloud, další aktuálně zapojené aplikace.
- iPhone: konkrétní aplikace, propojení s Macem, adresa připojení, oprávnění,
  důvěra vývojáři, instalace/podpis a ověření. Co nelze automaticky přečíst,
  označit jako dokumentované/ručně ověřené s datem nebo neověřené. Model
  nesmí vydávat odhad nastavení telefonu za čerstvé měření.
- Nový OS, chybějící zdroj, neúplné pokrytí, uniklé tajemství, nesprávný příkaz,
  starý důkaz přepsaný jako aktuální, vynechaná podstatná kapitola nebo
  rozpor kritický pro obnovu zabrání vydání a zachová předchozí návod.
- Zkoušky: přidaná aplikace, změněná cesta/role/oprávnění, zrušený hlasový
  pilot, chybný výstup, vložené instrukce v podkladu, příliš velký soubor,
  souběžná editace. Bez skutečných zásahů do Macu/iPhonu.

#### REC-04 — přesné uložení do PythonMF a iCloud Dokumentů (Data)

Výstup: writer a obnova přerušeného uložení, oba TXT mají stejné bajty/hash.

- Před aktualizací uchovat původní verzi, potom validovaný kandidát zapsat
  do dočasných souborů, znovu ověřit obsah a provést atomickou výměnu každé
  jednotlivé kopie. Před přepsáním ověřit, že Míla původní TXT mezitím neupravil.
- Nelze slibovat jednu atomickou operaci nad oběma soubory a cloudem. Stav
  rozliší přípravu, místní uložení, druhou místní kopii a potvrzený upload.
  Při selhání druhého cíle obnovit předchozí místní verzi, pokud je to bezpečné,
  jinak ponechat přesný stav čekajícího doručení a upozornit. Nikdy úspěch napůl.
- Nejprve ověřit, že cíl je skutečná iCloud ubiquitous položka; pouhý alias
  Documents nezaručuje zapnutou synchronizaci této složky.
- Po iCloud zápisu ověřit nejen shodný hash, ale podporovaným macOS metadata
  auditem též uploaded, uploading a chybu uploadu. Bez potvrzení je stav
  čeká na iCloud, ne hotovo. Místní zápis v synchronizované složce sám o sobě
  není důkaz dostupnosti souboru po ztrátě Macu.
- Po ztrátě spojení neopakovat modelový rozbor, pokud již existuje hotový
  kandidát s hash/účtenkou. Lze bezpečně dokončit přenos přesně týchž bajtů
  po kontrole cíle; žádné nové generování nebo přepsání ruční změny.
- Historie verzí se přidává, její mazací retenci schválit zvlášť. První
  fyzická přejímka musí soubor najít a otevřít v Souborech na iPhonu.

#### REC-05 — týdenní plánovač a dohled (Data)

Výstup: registrované preview/run/status workflow, izolované oprávnění,
připravený LaunchAgent a viditelný stav. Instalace až při samostatné aktivaci.

- Návrh času k odsouhlasení: neděle 09:00, Europe/Prague. Zámek a trvalé ID
  ISO týdne zajistí nejvýše jeden běh; řešit změnu času, souběh ručního
  spuštění, restart a výpadek. Při vypnutém Macu provést po dostupnosti jen
  jeden aktuální zameškaný běh, nikoli lavinu všech minulých týdnů.
- Nejisté placené volání zastaví úlohu do attention, další tick ho nezopakuje.
  Opakovaná kontrola cloudového uploadu nepotřebuje další modelový tah.
- Místní běh vyžaduje dostupný Mac, přihlášeného uživatele a připojení.
  Plánovač neobchází FileVault ani vypršené přihlášení Codexu/iCloudu; při
  nedostupnosti vrátí attention a zachová ověřený návod.
- Program používá absolutní schválené binární cesty a ověřené prostředí
  služby; interaktivní PATH není důkaz pro launchd. Nemění e-mailového agenta.
- Poslední běh, verze/otisk, počet přečtených zdrojů, pokrytí, náklad a stav
  obou kopií viditelné v Cockpitu nebo návratové účtence pracovního proudu.
  Upozornění je pro Mílu, ne automatický e-mail nebo zpráva jiným lidem.
- Běh může skončit bez věcné změny. Potvrzení úplné revize je v účtence,
  obsahové datum se neposouvá tak, aby předstíralo nové ověřené nastavení.

#### REC-06 — přejímka a aktivace (Data, Will, Míla; poté Sol)

1. Neplacené jednotkové a integrační testy včetně výpadků, souběhu,
   nedostupného iCloudu, neočekávaného symlinku a známého aliasu Documents.
2. Jeden zvlášť schválený skutečný čtecí pilot; Míla přijme konkrétní vzor
   aktualizovaného TXT, skutečnou spotřebu a pravidla automatických změn.
3. Zkouška writeru na kopii, poté skutečné uložení obou pevných cílů,
   ověření hashů/uploadu a otevření iCloud kopie na iPhonu.
4. Plná projektová brána pro persistenční/scheduler změnu; kompatibilní kód
   převzít do aktuálního main. Teprve po samostatně povoleném p+n a kontrole
   skutečného runtime aktivovat roli a připravený týdenní LaunchAgent.
5. Ověřit jeden plánovaný slot a bezpečné dohánění po odstávce. Potom běžný
   týdenní provoz se schválenými zdroji, dvěma výstupy a rozpočtem.

Vývoj připravuje Data ve vlastní pracovní kopii. Will převezme kompatibilní
změnu do současného main bez přepsání své práce. Sol je budoucí vykonavatel
obsahové týdenní revize, ne nyní spuštěný pomocný vývojový agent.

#### Navržené implementační soubory

app/recovery_guide_sources.py; app/recovery_guide_maintainer.py;
app/recovery_guide_publish.py; scripts/recovery_guide.py;
scripts/recovery_guide_launchd.py a odpovídající testy. Registry schopností,
workflow a centrální modelová role se doplní až v příslušné implementační etapě.
Preferovat existující file_persistence/transport, nepřidávat framework či
závislosti bez konkrétní potřeby. Nejde o rozšíření e-mailové business logiky.

#### Oficiální zdroje ověřené při plánování

- [GPT-6.1 Sol: model a limity](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
- [Codex/ChatGPT Work: Standard kredity](https://learn.chatgpt.com/docs/pricing#token-rates)
- [API changelog: automations](https://developers.openai.com/api/docs/changelog#october-2026)
  — existence cloudového plánovače není důvod migrovat místní Samanthu.

## 2026-11-07 12:23 CET — vývojový základ týdenního správce obnovy

### Hotovo
- Po Mílově pokynu zahájen vývoj podle REC-01 až REC-06. Připraven neaktivní
  izolovaný pilot: úplné soubory/manifest, dávky a syntéza, citace/kapitoly,
  trvalý stav bez automatického opakování, rozpočty, dva jednotlivé atomické
  zápisy s historií a kontrolou iCloud uploadu, návrh plánovače.
- Registrované neplacené preview/status; run/tick zůstává activation_required.
  Nový parser zná budoucí roli, centrální JSON ani modelové role se neměnily.
- Nález: také sledovaný Samantha_Agent TXT je shodný s Plochou a kořenem
  iCloudu. Oba nové cílové TXT stále chybějí. Foundation po rozřešení známého
  aliasu Documents potvrzuje synchronizaci skutečné složky; nikoli nový TXT.

### Rozhodnutí
- Míla schválil zahájení vývoje. Placený pilot, provozní kopírování, aktivace
  role/plánovače a p+n zůstávají samostatné kroky původního plánu.
- Nejde o dokončený bezobslužný agent. Podrobný kontrakt a chybějící části
  jsou v technical/recovery_guide_maintainer.md. Výstup syntézy vždy review.

### Další krok
- Will převezme lokální vývojový balíček do aktuálního main, sjednotí známé
  role se svými novějšími rolemi a nad čistým main vytvoří neplacený manifest.
  Potom dokončit rozsah zdrojů a přesný tokenizační preflight pro cenový pilot.

### Navrhované další kroky
- Doplnit registrované bezpečné důkazy nastavení Mac/iPhone a přijmout korpus.
- Teprve nad konkrétním rozpočtem schválit jeden živý čtecí pilot Solem.
- Přijmout celý návrh TXT, provést samostatně schválenou migraci, upload/iPhone.
- Propojit přijatou účtenku s pevnými cíli a aktivovat týdenní běh až po přejímce.

### Technický důkaz
- Výchozí neplacená inventura před zápisem této etapy: 508 zdrojů,
  5 899 527 B, 114 vynechaných textů; jde o návrh rozsahu, ne přijatý korpus.
- Cílené ověření a plná brána: 65 cílených testů OK (37 nových); plná brána 2 413 testů OK, 5 skipped; po posledním zpřesnění metadat znovu cílené testy a statická brána OK..
- Testy pouze syntetické/dočasné. Foundation audit čtecí; původní iCloud TXT
  i skutečný cíl Documents: ubiquitous/uploaded true, uploading/error false.
- Bez placeného tahu, zápisu provozních TXT, instalace, push či nasazení.

## 2026-11-07 12:39 CET — REC-02: neplacený preflight, živý pilot dosud neproveden

### Hotovo
- Změřen celý zmrazený korpus 509 dokumentů a původní TXT; plán 10 dávek +
  syntéza, úplné pokrytí bez zkrácení souborů. Referenčně 2 222 784 vstupních
  a 112 000 rezervovaných výstupních tokenů, 139,1392 Standard kreditů bez
  cache. Není to potvrzená cena Solu ani tvrdý fakturační strop.
- Tiktoken 0.14.0 nainstalovaný jen do vlastního izolovaného prostředí.
  Nový neplacený preflight/runtime workflow a oddělená rezerva inspekce
  a syntézy; zachování známé ceny i po nadlimitním výstupu.
- Redigovaný manifest/plán/audit je v reports/recovery_guide_rec02_20261107.json,
  praktické vysvětlení v příslušném .md. Žádný placený tah ani nový thread.

### Rozhodnutí
- Míla schválil pokračování fází 2. Nezadaná cena/rozsah živého pilotu se
  nepovažují za schválené utrácení; žádná aktivace rolí, služeb či writeru.
- Fáze REC-02 není celá hotová: upstream tiktoken nezná mapování Solu,
  reference o200k_base není náhradou modelu. Připojený server hlásí 0.163.0,
  lokální CLI 0.166.0; preference runtime nevyhovuje Standard kontrole,
  kontext a účinnost izolace zatím nejsou doložené. Nic se nepřepínalo.

### Další krok
- Will převezme vývoj do současného main a registrovaným read-only auditem
  doloží skutečný kontrakt runtime a možnost izolovaného Standard tahu.
  Případný release/restart potřebuje samostatné oprávnění; Data jej nespouští.

### Navrhované další kroky
- Uzavřít tokenizační důkaz nebo výslovně přijmout poctivý odhad + kalibraci.
- Nad čistým cílovým HEAD přijmout úplný korpus a konkrétní cenový rozsah
  jednoho pevného syntetického Sol/medium kandidátního tahu; bez retry.
- Potom přijmout cenu čtení celého korpusu a konkrétní návrh TXT.
- Migrace dvou kopií, iPhone přejímka a týdenní aktivace zůstávají samostatně.

### Technický důkaz
- Podrobná evidence, oba snapshot/plan otisky a oficiální zdroje v REC-02 reportu.
- Plná projektová brána: 2 423 testů OK, 5 skipped; po doplnění Fast a měsíčního regresního případu znovu 76 cílených testů OK (11 nových v REC-02), závěrečná statická brána OK.
- Bez změny config/agent_roles.json, společné .venv, globálního CLI,
  provozních TXT, služeb, Gitu mimo vlastní větev, push či nasazení.

## 2026-11-07 13:03 CET — REC-03: kontrola kvality a důkazů

### Hotovo
- Povinná kontrola syntézy nyní zachová kapitoly i jejich obsah/úvod, váže
  nové cesty/role/příkazy na přesné citace a blokuje známý zrušený hlas,
  skrytá tajemství, falešné aktuální ověření a změnu pouhého data.
- Samostatná přejímka vyžaduje schválený úplný seznam aplikací, Mac/iPhone
  checklist, zdrojové otisky, autoritu a stáří důkazů. Nový OS/rozpor blokuje.
  Ani úspěšný strojový výsledek sám nepovoluje publikaci.
- Připraven balíček bez soukromé historie a otestované čtení novým izolovaným
  procesem pouze přes stdin. Nejde o lidskou/modelovou přejímku skutečného TXT.
- Stávající TXT pouze čtecí kontrolou prošel a vrací se přesně 62 778 B;
  žádné umělé přidání newline ani změna verze při běhu beze změn.

### Rozhodnutí
- Míla schválil třetí etapu REC-03. Rozsah nadále nezahrnuje placený pilot,
  publikaci provozních TXT, aktivaci role/služby, push ani nasazení.
- Checklist a důkazy smějí schválit pouze důvěryhodný řadič/operátor,
  nikoli model. Úplný skutečný seznam aplikací zatím schválený není.

### Další krok
- REC-04: svázat konkrétně přijatou kvalitativní účtenku, checklist, kandidát
  a oba pevné cíle s writerem; testovat přerušení a souběžné úpravy na kopiích.

### Navrhované další kroky
- Will převezme vývoj do aktuálního main s uchováním své práce/rolí.
- Dořešit dosud otevřený REC-02 tokenizer/Standard/runtime kontrakt a cenový pilot.
- Přijmout skutečný úplný korpus/aplikace a doložená nastavení včetně iPhonu.
- Po skutečném návrhu provést lidskou přejímku čtenářem bez soukromé historie.

### Technický důkaz
- 38 nových REC-03 testů; závěrečná cílená sada 114/114 OK. Plná projektová brána: 2 459 testů OK, 5 skipped. Po závěrečných zpřesněních znovu cílená sada a statická brána OK; nezměněné testy se zbytečně neopakovaly..
- Podrobný kontrakt/scénáře v reports/recovery_guide_rec03_20261107.md;
  bezpečný syntetický balíček v recovery_guide_rec03_example_20261107.json.
- Chybná syntéza -> attention + quality_issue, bez kandidáta/retry.
  Bez změny produkčního klienta/runtime/Cockpitu/e-mailu, rolí a služeb.

## 2026-11-07 13:45 CET — REC-04: přijatý kandidát a dvojí zápis na kopiích

### Hotovo
- Připraven PublicationStore: přesný kandidát, REC-03 účtenka/checklist,
  úplné vstupy, verze validátoru a oba připnuté cíle mají jeden neměnný binding.
  Výslovné sandboxové přijetí vzniká poslední; pouhý hash textu nestačí.
- Převod uchová zdrojový TXT i staré verze obou cílů, včetně CRLF. Po pádu
  pokračuje stejnými bajty bez modelu. Čekající upload neopakuje hotové výměny.
- Zámek/aktivní marker chrání souběh a novější verze. Ruční změny včetně
  návratu k původním bajtům se nepřepíšou. Selhání rollbacku je pozorovatelné.
- Nový vstup povoluje pouze izolované testovací cíle v podadresáři vlastní
  .venv nebo systémového temp. Produkční režim je výslovně vypnutý.

### Rozhodnutí
- Míla schválil REC-04 vývoj a ověření na kopiích. Testovací přijetí není
  skutečná přejímka nového produkčního TXT ani souhlas se zápisem do iCloudu.
- Živý REC-02 pilot, úplný produkční korpus/aplikace a fyzická přejímka na
  iPhonu zůstávají otevřené; nic se nenasazovalo ani neaktivovalo.

### Další krok
- REC-05: připojit trvalý plánovač k registrovanému preview/run/status,
  před novou analýzou řešit čekající přenos, připravit samostatnou aktivaci.

### Navrhované další kroky
- Will převezme lokální změny do aktuálního main bez přepsání svých rolí/práce.
- Dořešit REC-02 runtime/Standard/tokenizer a konkrétní placený pilot.
- Přijmout skutečný návrh a autoritativní seznam aplikací/nastavení.
- REC-06 teprve povolí přesné provozní cíle, skutečný upload/iPhone a týdenní běh.

### Technický důkaz
- 38 nových REC-04 testů; cílená sada 152/152 OK. Závěrečná plná projektová brána nad poslední verzí writeru: 2 501 testů OK, 5 skipped. Dřívější mezibrána 2 498 OK; po zpřesnění written/manifest se plná brána opakovala..
- Report recovery_guide_rec04_20261107.md a redigovaný syntetický JSON příklad.
- Testované uploady jsou simulované; žádný skutečný iCloud zápis/audit v této
  etapě, modelový tah, služba, push ani nasazení. Provozní TXT beze změny.

## 2026-11-07 14:21 CET — REC-05: trvalý plánovač a dohled bez aktivace

### Hotovo
- Připraven trvalý sandboxový plánovač: společný ISO týden pro ruční/timer
  vstup, zámek, jeden poslední doháněný týden, DST/rok a restart. Nejasná
  analýza zastaví i další týdny; známá místní účtenka se připojuje bez retry.
- Přenos REC-04 má přednost před novou analýzou. Čekající cloud dokončí
  stejné bajty bez dalšího modelu. Běh beze změn vyžaduje nové konečné
  ověření kopií/snapshotu, nikoli jen starý předběžný údaj.
- Registrované schedule-preview/status a launchd/environment preview;
  neaktivní plist má absolutní cesty, minimální PATH a umask 077.
  Čtecí CLI bootstrap pod minimálním prostředím prošel.

### Rozhodnutí
- Míla schválil REC-05 vývoj, ne instalaci/aktivaci či placený modelový tah.
  Neděle 09:00 Europe/Prague zůstává návrh, rozpočty nejsou schválené.
- Běžná budoucí automatika má fungovat v jednorázově schváleném úzkém
  rozsahu; současné syntetické callbacky tuto produkční autoritu nenahrazují.
- Produkční CLI run/tick zůstávají activation_required. Centrální role,
  globální Codex, společné služby i provozní TXT se neměnily.

### Další krok
- REC-06 nejprve uzavře předpoklady živého REC-02 pilotu a konkrétní přejímku
  skutečného TXT; potom teprve autorizovaný produkční adapter/role/cíle,
  reálný iCloud/iPhone důkaz a samostatně povolenou aktivaci jednoho slotu.

### Navrhované další kroky
- Will převezme balíček do aktuálního main s uchováním svých rolí/práce.
- Fresh audit runtime/Standard/tokenizer, konkrétní cenový syntetický pilot.
- Přijetí skutečného korpusu/aplikací, návrhu a omezené automatické politiky.
- Po schválení dne/času a limitů ověřit launchd session/auth a bezpečný catch-up.

### Technický důkaz
- 42 nových REC-05 scénářů; cílená sada 194/194 OK. Finální plná projektová brána nad posledním kódem: 2 543 testů OK, 5 skipped. Čtecí CLI bootstrap pod minimálním PATH OK; skutečná launchd/auth session a produkční model zůstávají neověřené..
- Report recovery_guide_rec05_20261107.md a redigovaný syntetický JSON příklad.
- Minimální CLI PATH ověřený; skutečný launchd/auth kontext neověřený,
  služba neinstalovaná, žádný placený model, iCloud zápis, push či nasazení.

## 2026-11-07 14:56 CET — REC-06: konkrétní jednorázová kalibrace před placeným pilotem

### Hotovo
- Čtecí audit připojeného App Serveru, účtu a přesného Sol/medium. Standard
  pro jeden tah doložen oficiální dokumentací a schématem přesného peeru .163.0.
- Nový oddělený kandidátní vstup s pevným syntetickým podkladem, přesnou
  kartou souhlasu, kontrolou oprávnění/socketu, trvalým slotem a bez retry.
- Testy výpadků/souběhu, neznámé spotřeby a obsahu; konkrétní cenová karta
  a reprodukční omezení jsou v recovery_guide_rec06_20261107.md.

### Rozhodnutí
- Pokyn k REC-06 autorizuje přípravu přejímky. Samostatný souhlas s konkrétní
  placenou zkouškou podle schváleného plánu zatím chybí; živé modelové tahy 0.
- Návrh první kalibrace: jeden Sol/medium Standard tah, pět syntetických
  záznamů bez skutečného návodu; rezerva 1,6 Standard kreditu a přijímací
  mez 2 kredity. Nejde o tvrdý fakturační/výstupní strop. Karta není souhlas.
- Přesný tokenizer Solu zůstává nedoložený; referenčních 500 tokenů není
  fallback pro celý korpus. Produkční run/tick, role a služba neaktivované.

### Další krok
- Míla přijme přesnou kartu jediné syntetické kalibrace; poté ji Data může
  jednou provést nad stejným digestem. Nejasný výsledek se neopakuje.

### Navrhované další kroky
- Vyhodnotit skutečnou spotřebu a odděleně přijmout úplný korpus/cenový pilot TXT.
- Will převezme nový modul/testy/zápis do aktuálního main, uchová své role/práci.
- Přijmout celý návrh, povolený produkční adaptér a dvě kopie; upload/iPhone zvlášť.
- Samostatně schválit p+n, centrální roli, den/čas/rozpočet a launchd/auth přejímku.

### Technický důkaz
- 28 nových testů; cílená sada 193/193 OK. Plná brána persistenčního vstupu: 2 570 testů OK, 5 skipped.
  Po malé čtecí normalizaci peer verze dalších 28/28 cílených testů OK;
  závěrečná statická brána OK.
- Globální CLI .166.0, připojený peer .163.0; stará ownership sidecar není
  důkaz současného listeneru. Žádná změna služby, globálního CLI, závislostí
  projektu, modelových rolí či provozních TXT; žádný push/nasazení/integrace.
