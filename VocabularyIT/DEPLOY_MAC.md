# VocabularyIT - build a prenos na druhy Mac

Tento postup pouzivej po kazde uprave aplikace.

## 1) Build na tvem hlavnim Macu

```bash
cd ~/Desktop/PythonMF/VocabularyIT
./build_and_zip.sh
```

Po dokonceni vznikne soubor:

- `VocabularyIT.app.zip`

## 2) Prenes ZIP na druhy Mac

Prenes `VocabularyIT.app.zip` (AirDrop, iCloud, USB, ...).

## 3) Spusteni na druhem Macu

```bash
cd ~/Desktop/PythonMF/VocabularyIT
# nebo do slozky, kam jsi ZIP ulozil

ditto -x -k VocabularyIT.app.zip .
xattr -dr com.apple.quarantine VocabularyIT.app
open VocabularyIT.app
```

## Kdyz se app nespusti

```bash
cd ~/Desktop/PythonMF/VocabularyIT
chmod 755 VocabularyIT.app/Contents/MacOS/VocabularyIT
codesign --force --deep --sign - VocabularyIT.app
open VocabularyIT.app
```

## Poznamky

- Vzdy prenasej ZIP, ne samotnou `.app` (ZIP zachova prava souboru).
- Pokud je v app tmavy rezim a neni videt text, prepni v macOS `System Settings -> Appearance -> Light`.
