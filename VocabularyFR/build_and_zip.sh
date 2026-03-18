#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/5] Cleaning previous build artifacts"
rm -rf build dist VocabularyFR.app.zip

echo "[2/5] Building app with PyInstaller"
python3 -m PyInstaller --noconfirm VocabularyFR.spec

echo "[3/5] Ensuring executable bit"
chmod 755 dist/VocabularyFR.app/Contents/MacOS/VocabularyFR

echo "[4/5] Ad-hoc codesign"
# Remove Finder/resource-fork metadata that breaks codesign on some Macs.
xattr -cr dist/VocabularyFR.app
codesign --force --deep --sign - dist/VocabularyFR.app

echo "[5/5] Creating portable ZIP"
ditto -c -k --sequesterRsrc --keepParent dist/VocabularyFR.app VocabularyFR.app.zip

echo "Done: $SCRIPT_DIR/VocabularyFR.app.zip"
