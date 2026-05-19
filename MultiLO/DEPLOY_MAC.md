# MultiLO - build a prenos na druhy Mac

Tento postup pouzivej po kazde uprave aplikace.

## 1) Build na tvem hlavnim Macu

```bash
cd ~/Desktop/PythonMF/MultiLO
./build_and_zip.sh
```

Po dokonceni vznikne soubor:

- `MultiLO.app.zip`

Poznamka:

- Build je uz v cistejsi `onedir` variante `PyInstaller`.
- Pokud na tvem Macu selze automaticky `codesign`, build skript to uz neblokuje.
- ZIP se vytvori i tak; pripadny ad-hoc podpis se da dodelat az na cilovem Macu.

## 2) Prenes ZIP na druhy Mac

Prenes `MultiLO.app.zip` (AirDrop, iCloud, USB, ...).

## 3) Spusteni na druhem Macu

```bash
mkdir -p ~/Desktop/MultiLO_Run
cd ~/Desktop/MultiLO_Run
rm -rf MultiLO.app
unzip -q ~/Desktop/PythonMF/MultiLO/MultiLO.app.zip
xattr -dr com.apple.quarantine MultiLO.app
open MultiLO.app
```

Dulezite:

- pouzij vzdy cerstvy `MultiLO.app.zip`
- nerozbaluj starou kopii pres starou kopii
- pred novym testem smaz predchozi `MultiLO.app`

## Kdyz se app nespusti hned napoprve

```bash
cd ~/Desktop/MultiLO_Run
xattr -dr com.apple.quarantine MultiLO.app
open MultiLO.app
```

## Kdyz se po `open MultiLO.app` porad nic nestane

Spust aplikaci primo z terminalu a zkopiruj vystup:

```bash
~/Desktop/MultiLO_Run/MultiLO.app/Contents/MacOS/MultiLO
```

To je nejdulezitejsi diagnosticky krok.

## Jen kdyz je to nutne: rucni podpis

Nejdriv zkus:

```bash
cd ~/Desktop/MultiLO_Run
xattr -cr MultiLO.app
codesign --force --deep --sign - MultiLO.app
open MultiLO.app
```

Pokud by `codesign` vypsal chybu typu:

- `resource fork, Finder information, or similar detritus not allowed`

znamena to problem s metadata souboru na danem systemu, ne s Python kodem aplikace.
V takovem pripade:

```bash
cd ~/Desktop/MultiLO_Run
rm -rf MultiLO.app
unzip -q ~/Desktop/PythonMF/MultiLO/MultiLO.app.zip
xattr -dr com.apple.quarantine MultiLO.app
open MultiLO.app
```

Tedy:

- nesnaz se zachranovat starou rozbitou kopii
- smaz ji
- rozbal znovu cerstvy ZIP
- zkus nejdriv spusteni bez dalsich zasahu

## Poznamka k aktualni funkcni verzi

Overeno na Janine Macu:

- funkcni je novy ZIP z buildu, ne starsi testovaci archiv
- aktualni funkcni archiv je:
  - `MultiLO.app.zip`
  - cas buildu: `Apr 4 22:30:50 2026`

## Kde jsou data aplikace

Po zabalení app uz nepracuje primo se soubory vedle `.app`.
Uzivatelska a průběžná data jsou v:

- `~/Library/Application Support/MultiLO/`

Typicky:

- `vocab_master.csv`
- `users.csv`
- `user_item_prefs.csv`
- `progress.json`

Pri prvnim spusteni se tyto soubory inicializuji z bundle aplikace, pokud v `Application Support` jeste neexistuji.

## Jak prekopirovat aktualni data na cilovy Mac

```bash
DST_DIR="$HOME/Library/Application Support/MultiLO"
mkdir -p "$DST_DIR"

cp "/cesta/k/vocab_master.csv" "$DST_DIR/vocab_master.csv"
cp "/cesta/k/users.csv" "$DST_DIR/users.csv"
cp "/cesta/k/user_item_prefs.csv" "$DST_DIR/user_item_prefs.csv"
cp "/cesta/k/progress.json" "$DST_DIR/progress.json"
```

Kontrola:

```bash
ls -lh "$HOME/Library/Application Support/MultiLO"
```

## Obrazky a cockpit ikonky

Runtime assety jsou zabalené primo uvnitr `MultiLO.app`, tedy normalne neni treba nic kopirovat zvlast.
To se tyka hlavne:

- `Foto_normalized/`
- `cockpit_icons/`

Po update appky se tedy kvuli obrazkum nic rucne nepresouva.

## Poznamky

- Vzdy prenasej ZIP, ne samotnou `.app`.
- Pri update appky zustanou uzivatelska data zachovana, pokud zustane adresar:
  - `~/Library/Application Support/MultiLO/`
- Pokud budes chtit na cilovem Macu vymazat progres a zacit ciste, smaz:
  - `~/Library/Application Support/MultiLO/progress.json`
