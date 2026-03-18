# VocabularyFR - build a prenos na druhy Mac

Tento postup pouzivej po kazde uprave aplikace.

## 1) Build na tvem hlavnim Macu

```bash
cd ~/Desktop/PythonMF/VocabularyFR
./build_and_zip.sh
```

Po dokonceni vznikne soubor:

- `VocabularyFR.app.zip`

## 2) Prenes ZIP na druhy Mac

Prenes `VocabularyFR.app.zip` (AirDrop, iCloud, USB, ...).

## 3) Spusteni na druhem Macu

```bash
cd ~/Desktop/PythonMF/VocabularyFR
# nebo do slozky, kam jsi ZIP ulozil

ditto -x -k VocabularyFR.app.zip .
xattr -dr com.apple.quarantine VocabularyFR.app
open VocabularyFR.app
```

## Kdyz se app nespusti

```bash
cd ~/Desktop/PythonFM/VocabularyFR
chmod 755 VocabularyFR.app/Contents/MacOS/VocabularyFR
codesign --force --deep --sign - VocabularyFR.app
open VocabularyFR.app
```

## Kdyz app pouziva stary VocabularyFR.csv

App pracuje se souborem v:

- `~/Library/Application Support/VocabularyFR/VocabularyFR.csv`

Nepracuje primo s CSV vedle `.app` na plose.

Najdi vsechny kopie:

```bash
find ~ -maxdepth 6 -name "VocabularyFR.csv" 2>/dev/null
```

A prepis aktivni soubor novou verzi:

```bash
cp "/cesta/k/novemu/VocabularyFR.csv" "$HOME/Library/Application Support/VocabularyFR/VocabularyFR.csv"
```

Kontrola:

```bash
diff -q "/cesta/k/novemu/VocabularyFR.csv" "$HOME/Library/Application Support/VocabularyFR/VocabularyFR.csv"
```

Pak app zavri a znovu otevri.

## Obrazky a mapping.json (Pict)

Po novych upravach app cte obrazky a mapovani z adresare `Pict`.

Doporucene stabilni umisteni na Macu:

- `~/Library/Application Support/VocabularyFR/Pict`

V tomto adresari maji byt:

- obrazky (`.png/.jpg/.jpeg/.webp/.gif`)
- `mapping.json`

### Jednorazove nasazeni Pict na cilovy Mac

```bash
SRC_PICT="/cesta/k/PythonMF/Pict"
DST_PICT="$HOME/Library/Application Support/VocabularyFR/Pict"

mkdir -p "$DST_PICT"
rsync -av --delete "$SRC_PICT"/ "$DST_PICT"/
```

Kontrola:

```bash
ls -lh "$HOME/Library/Application Support/VocabularyFR/Pict"
```

Poznamka: pokud zmenis jen mapovani, staci prekopirovat pouze `mapping.json`.

```bash
cp "/cesta/k/PythonMF/Pict/mapping.json" "$HOME/Library/Application Support/VocabularyFR/Pict/mapping.json"
```

## Jednorazova migrace dat ze stare `.app` (kdyz se zapisovalo dovnitr app)

Spust na Macu, kde je stara aplikace:

```bash
APP="/Applications/VocabularyFR.app"
DATA_DIR="$HOME/Library/Application Support/VocabularyFR"
TARGET="$DATA_DIR/VocabularyFR.csv"

mkdir -p "$DATA_DIR"

# Najdi CSV uvnitr app bundle (pokud existuje)
INTERNAL_CSV="$(find "$APP/Contents" -name "VocabularyFR.csv" -print -quit 2>/dev/null)"
echo "INTERNAL_CSV=$INTERNAL_CSV"

if [ -n "$INTERNAL_CSV" ]; then
  # Zalohuj aktualni uzivatelsky soubor (pokud uz existuje)
  if [ -f "$TARGET" ]; then
    cp "$TARGET" "$TARGET.backup.$(date +%Y%m%d-%H%M%S)"
  fi

  # Presun data ze stare app do spravneho umisteni
  cp "$INTERNAL_CSV" "$TARGET"
  echo "Migrace hotova -> $TARGET"
else
  echo "CSV uvnitr app nebylo nalezeno."
fi
```

Kontrola:

```bash
ls -lh "$HOME/Library/Application Support/VocabularyFR/VocabularyFR.csv"
```

## Poznamky

- Vzdy prenasej ZIP, ne samotnou `.app` (ZIP zachova prava souboru).
- Pokud je v app tmavy rezim a neni videt text, prepni v macOS `System Settings -> Appearance -> Light`.
- Pri update appky se uzivatelska data zachovaji, pokud zustane adresar:
  - `~/Library/Application Support/VocabularyFR/`
  (tedy hlavne `VocabularyFR.csv` a `Pict/`).
