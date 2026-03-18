#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/5] Cleaning previous build artifacts"
rm -rf build dist VocabularyIT.app.zip

echo "[2/5] Building app with PyInstaller"
python3 -m PyInstaller --noconfirm VocabularyIT.spec

echo "[3/5] Ensuring executable bit"
chmod 755 dist/VocabularyIT.app/Contents/MacOS/VocabularyIT

echo "[4/5] Ad-hoc codesign"
codesign --force --deep --sign - dist/VocabularyIT.app

echo "[5/5] Creating portable ZIP"
ditto -c -k --sequesterRsrc --keepParent dist/VocabularyIT.app VocabularyIT.app.zip

echo "Done: $SCRIPT_DIR/VocabularyIT.app.zip"
