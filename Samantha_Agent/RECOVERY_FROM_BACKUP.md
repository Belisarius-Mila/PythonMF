# Recovery from Samantha backup

Tento navod je pro situaci, kdy puvodni Mac neni dostupny, ale existuje externi
disk se zalohou `PythonMF` / `Samantha_Agent`.

Navod je psany pro cloveka i pro Codex. Pokud obnovu dela Codex, nejdriv mu dej
tento soubor jako instrukce a rekni mu, aby nic nemazal a pred kazdym prepisem
existujici slozky se zeptal.

## Bezpecnostni pravidla

- Nikdy nekopirovat `~/.codex/auth.json` ze zalohy. Codex se musi znovu prihlasit.
- `.env` obsahuje tajemstvi. Obnovovat ho jen ze sifrovane `recovery` zalohy a jen
  na pocitaci, kteremu duverujes.
- E-mailove archivy, reminders, session autosave a `Tax/` jsou citliva lokalni
  data. Obnovovat je jen ze sifrovaneho cile.
- Pred prepisem existujiciho `~/Desktop/PythonMF` nejdriv prejmenuj starou slozku,
  napr. na `PythonMF_before_restore_YYYYMMDD`.
- Pokud nevis, jestli je zaloha `safe` nebo `recovery`, zachazej s ni jako s
  citlivou a nejdriv zkontroluj `backup_manifest.txt`.

## Co musi byt na novem Macu

Minimalni priprava:

```bash
xcode-select --install
python3 --version
git --version
```

Dale nainstaluj:

- VS Code nebo jiny editor, pokud ho chces pouzivat.
- Codex CLI.
- Python 3.12 nebo kompatibilni Python 3.

Po instalaci Codexu udelej nove prihlaseni:

```bash
codex login
```

## Najdi posledni snapshot

Pripoj externi disk. Pokud je Samantha zaloha v sifrovanem kontejneru, nejdriv ho
odemkni ve Finderu nebo prikazem `open`.

Typicke umisteni snapshotu:

```text
/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/YYYYMMDD_HHMMSS/
```

Najdi posledni snapshot:

```bash
ls -1 "/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots"
```

V poslednim snapshotu by melo byt:

```text
PythonMF/
codex_home/
backup_manifest.txt
READ_ME_FIRST_RECOVERY.md
```

Pokud je zaloha jinde, hledej slozku `snapshots` a soubor `backup_manifest.txt`.

## Vytvoreni sifrovaneho kontejneru na puvodnim Macu

Kontejner se vytvari jednorazove na externim disku. Klikaci skript:

```text
Samantha_Agent/scripts/create_samantha_secure_backup.command
```

Skript:

- vytvori `/Volumes/Falta/SamanthaSecureBackup.sparsebundle`,
- pouzije AES-256,
- nastavi vnitrni svazek `/Volumes/SamanthaSecureBackup`,
- heslo se zadava skryte v Terminalu, ne do chatu,
- existujici kontejner nikdy neprepisuje.

Vychozi maximalni velikost je `500g`. Sparsebundle realne zabira jen ulozena
data a lze ho pozdeji zvetsit.

## Zkontroluj manifest

Pred obnovou si precti:

```bash
cat "/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/YYYYMMDD_HHMMSS/backup_manifest.txt"
```

Dulezite hodnoty:

- `Profile: recovery` znamena plna obnova vcetne lokalnich citlivych dat.
- `Profile: safe` znamena, ze chybi `.env`, e-mailova lokalni data, reminders,
  session autosave a `Tax/`.

## Obnova projektu PythonMF

Vytvor `Desktop`, pokud neexistuje:

```bash
mkdir -p "$HOME/Desktop"
```

Pokud uz `PythonMF` existuje, nejdriv ho odloz stranou:

```bash
mv "$HOME/Desktop/PythonMF" "$HOME/Desktop/PythonMF_before_restore_$(date +%Y%m%d_%H%M%S)"
```

Potom obnov projekt:

```bash
rsync -a "/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/YYYYMMDD_HHMMSS/PythonMF/" "$HOME/Desktop/PythonMF/"
```

## Obnova bezpecne casti Codex konfigurace

Zaloha nikdy nema obsahovat `auth.json`. Ten se neobnovuje.

Obnovit lze jen bezpecne a pomocne casti:

```bash
mkdir -p "$HOME/.codex"
rsync -a "/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/YYYYMMDD_HHMMSS/codex_home/" "$HOME/.codex/"
rm -f "$HOME/.codex/auth.json"
codex login
```

Pokud `codex_home/` chybi, nevadi. Codex se znovu nastavi prihlasenim.

## Obnova Python prostredi

```bash
cd "$HOME/Desktop/PythonMF/Samantha_Agent"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Pokud recovery zaloha obsahovala `.env`, bude uz v projektu. Pokud ne, vytvor ho
znovu podle `.env.example`:

```bash
cp .env.example .env
```

Pak rucne dopln hodnoty. Nikdy neposilej obsah `.env` do chatu ani do gitu.

## Overeni Samanthy

Spust testy:

```bash
cd "$HOME/Desktop/PythonMF/Samantha_Agent"
source .venv/bin/activate
python -m unittest discover -s tests
```

Spust jednoduchy dotaz:

```bash
python -m app.samantha_agent "Zkontroluj stav pameti a pripominky."
```

Pokud funguje prikaz `samantha`, muzes ho pouzit:

```bash
samantha
```

Pokud prikaz `samantha` na novem Macu neni nastaveny, spust Codex primo ve slozce:

```bash
cd "$HOME/Desktop/PythonMF/Samantha_Agent"
codex
```

## Co delat, kdyz neco chybi

- Chybi `.env`: dopln ho rucne podle `.env.example`.
- Chybi e-mailove archivy nebo reminders: pravdepodobne byla obnovena `safe`
  zaloha, ne `recovery`.
- Chybi Codex historie: v `safe` profilu se `history.jsonl` a `sessions/`
  zamerne nezalohuji.
- Chybi `auth.json`: je to spravne. Spust `codex login`.
- Nefunguji testy kvuli zavislostem: znovu spust instalaci `pip install -r
  requirements.txt`.

## Cílena obnova jednoho souboru nebo slozky

Toto je pro situaci, kdy Mac funguje, ale v projektu se rozbil jeden soubor nebo
slozka, napr. `VocabularyFR/VocabularyFR.csv`.

Preferovana cesta je pres Samanthu:

```text
Rozbil se soubor VocabularyFR/VocabularyFR.csv, obnov ho ze zalohy.
```

Samantha ma postupovat takto:

1. Vypsat dostupne snapshoty pomoci `list_backup_snapshots`.
2. Udelat pouze nahled pomoci `preview_backup_restore`.
3. Vyzadat samostatne potvrzeni s relativni cestou a snapshotem.
4. Teprve potom pouzit `restore_path_from_backup`.

Bezpecnostni pravidla cilene obnovy:

- cesta musi byt relativni uvnitr `PythonMF`,
- absolutni cesty a `../` jsou zakazane,
- pred prepisem se aktualni cil vzdy odlozi jako
  `.before_restore_YYYYMMDD_HHMMSS`,
- citlive cesty (`.env`, `Tax/`, e-mailova data, reminders, session autosave)
  vyzaduji potvrzeni obsahujici i slovo `citlive` nebo `recovery`,
- ze zalohy se nic nemaze.

Rucni varianta bez Samanthy:

```bash
SNAPSHOT="/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/YYYYMMDD_HHMMSS"
REL="VocabularyFR/VocabularyFR.csv"
cp "$HOME/Desktop/PythonMF/$REL" "$HOME/Desktop/PythonMF/$REL.before_restore_$(date +%Y%m%d_%H%M%S)"
cp "$SNAPSHOT/PythonMF/$REL" "$HOME/Desktop/PythonMF/$REL"
```

## Po uspesne obnove

Spust novou zalohu az po kontrole, ze projekt funguje:

```bash
cd "$HOME/Desktop/PythonMF"
Samantha_Agent/scripts/backup_samantha.command --dry-run --profile recovery
```

Ostrou zalohu spust az po pripojeni sifrovaneho cile.
