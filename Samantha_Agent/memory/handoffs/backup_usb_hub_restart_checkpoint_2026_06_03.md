Nazev: Zaloha Samanthy - USB hub selhal, Python recovery zaloha hotova
Priorita: 1
Stav: hotovo, ceka jen na potvrzeny uklid starych snapshotu
Pripomenout pri startu: ano
Datum: 2026-06-03

Co se resilo:
- Mila chtel spustit novou recovery zalohu Samanthy na externi sifrovany kontejner.
- Pred zalohou se zjistilo, ze externi disk ani sifrovany kontejner nejsou pripojene.
- Nasledne se ukazalo, ze pres stejny USB hub nenabiha ani bezna pametova flashka.
- Mila si vzpomnel na nedavnou macOS hlasku ve smyslu, ze USB prislusenstvi bude odpojeno.

Co je hotove:
- Prvni USB problem byl vyreseny natolik, ze disk i sifrovany kontejner byly videt.
- Dva pokusy o ostrou zalohu byly spustene, ale ani jeden nedobehl uspesne.
- Nic se nemazalo.
- Po vymene problemoveho hubu za primejsi propojku probehla uspesna recovery
  zaloha pres Pythonovy inkrementalni nastroj bez `rsync/mmap`.
- Novy kanonicky snapshot:
  - `/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/20260603_175327/PythonMF`
- Overeno:
  - snapshot ma `backup_manifest.txt`,
  - snapshot ma `READ_ME_FIRST_RECOVERY.md`,
  - snapshot ma `PythonMF/` a `codex_home/`,
  - `scripts/backup_status.py` hlasi posledni zalohu v 3dennim intervalu
    `2026-06-03`.
- Vystup uspesneho behu:
  - files seen: 13856
  - files copied: 1174
  - files hard-linked: 12682
  - files skipped: 0
  - bytes copied: 338166106
- Po samostatnem potvrzeni Mily byly smazany:
  - nedokonceny snapshot `20260603_162647`,
  - nedokonceny snapshot `20260603_163709`,
  - stary nafouknuty snapshot `20260529_225518`.
- Pouzite misto na `/Volumes/SamanthaSecureBackup` kleslo zhruba z `54Gi` na
  `24Gi`.
- Na disku zustaly dokoncene snapshoty:
  - `20260519_194802`,
  - `20260519_195232`,
  - `20260519_200917`,
  - `20260603_175327`.
- Git byl pred timto checkpointem cisty po commitu/pushi `864470d Improve email work queue deletion flow`.
- Nactena pravidla zalohy:
  - recovery zaloha smi standardne jen do `/Volumes/SamanthaSecureBackup/SamanthaBackups`,
  - nedelat recovery zalohu do nesifrovaneho `/Volumes/Falta`,
  - stary nafouknuty snapshot `20260529_225518` nemazat pred novou overenou zalohou a samostatnym potvrzenim.
- Overeno, ze `Samantha_Agent/data/session_autosave/` je ve `scripts/backup_rsync_filter_always.rules`, tedy se vynecha v `safe` i `recovery` profilu.
- Diagnostika pred restartem:
  - `/Volumes` ukazovalo jen `Macintosh HD`,
  - `diskutil list` videl jen interni disk,
  - `hdiutil info` neukazal pripojeny image/kontejner,
  - `system_profiler SPUSBDataType SPThunderboltDataType` neukazal externi hub ani storage zarizeni,
  - Thunderbolt porty hlasily `No device connected`.
- Po restartu/pripojeni 2026-06-03:
  - `/Volumes/Falta` byl videt,
  - `/Volumes/Falta/SamanthaSecureBackup.sparsebundle` byl odemceny,
  - `/Volumes/SamanthaSecureBackup` byl pripojeny a zapisovatelny.
- Zaloha byla zkusena, ale neuspesne:
  - prvni ostry snapshot `20260603_162647` skoncil chybou `mmap: Operation timed out` na souboru ve `.venv_f5tts2`,
  - filtr `scripts/backup_rsync_filter_always.rules` byl opraven o `.venv_*/`,
  - druhy ostry snapshot `20260603_163709` skoncil chybou `mmap: Operation timed out` na malem CSV souboru,
  - `scripts/backup_status.py` stale ukazuje posledni uspesnou zalohu 2026-05-29, takze se nezapsal falesny uspech.
- `scripts/backup_samantha.command` byl opraven tak, aby jako `Previous snapshot` pouzil jen dokonceny snapshot s `backup_manifest.txt`; nedokoncene adresare z dnesnich pokusu se tak priste nemaji pouzit jako link-dest reference.
- Pro optimalizaci vznikl Pythonovy fallback `scripts/backup_samantha_python.py` a modul `app/backup/incremental.py`:
  - nepouziva `rsync` ani `mmap`,
  - kopiruje soubory po blocich,
  - nezmenene soubory hardlinkuje z posledniho dokonceneho snapshotu,
  - manifest a stav posledni uspesne zalohy zapise az po uspesnem dobehu.
- Lokalni testy prosly:
  - `.venv/bin/python -m unittest tests.test_backup_incremental tests.test_backup_activity_state tests.test_backup_restore_tools tests.test_backup_run_tools`

Co neni hotove:
- Nic kritickeho k zaloze neni rozpracovane.
- Zmeny v projektu jsou zatim necommitnute, pokud nebude nasledovat git checkpoint.

Dalsi krok:
- Bezpecne vysunout `SamanthaSecureBackup` i `Falta` ve Finderu.
- Pokud Mila chce, udelat git checkpoint noveho Python backup nastroje a memory
  aktualizaci.

Navrhovane dalsi kroky:
- Okamzity krok po restartu: zkontrolovat, zda Mac vidi hub nebo flashku.
- Pokud hub stale neni videt:
  - zkusit macOS nastaveni `Privacy & Security -> Security -> Allow accessories to connect`,
  - zkusit hub bez dalsich zarizeni,
  - zkusit jiny port/kabel/hub,
  - neresit zalohovaci skript, dokud `diskutil list` nevidi externi zarizeni.
- Okamzity krok: bezpecne vysunout oba svazky.
- Volitelny dalsi krok: commit/push zmen backup nastroje a memory.

Zmenene nebo relevantni soubory:
- `memory/projects/samantha_external_backup.md`
- `scripts/backup_samantha.command`
- `scripts/backup_samantha_python.py`
- `scripts/backup_rsync_filter_always.rules`
- `app/backup/incremental.py`
- `tests/test_backup_incremental.py`
- `scripts/backup_rsync_filter_sensitive.rules`
- `RECOVERY_FROM_BACKUP.md`

Bezpecnost / neukladat:
- Neposilat do chatu heslo k sifrovanemu kontejneru.
- Nic neinicializovat, neformatovat ani nemazat, pokud macOS zobrazi dotaz na necitelny disk.
- Nespoustet recovery zalohu do nesifrovaneho cile.
- Nemazat `20260529_225518`, dokud neni nova zaloha hotova a overena.
