#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PYTHON_BIN="${PYTHON_BIN:-/usr/local/bin/python3.12}"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Python interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi

echo "[1/5] Cleaning previous build artifacts"
rm -rf build dist MultiLO.app.zip

echo "[2/5] Building app with PyInstaller"
"$PYTHON_BIN" -m PyInstaller --noconfirm MultiLO.spec

echo "[3/5] Ensuring executable bit"
chmod 755 dist/MultiLO.app/Contents/MacOS/MultiLO

echo "[4/5] Best-effort ad-hoc codesign"
xattr -cr dist/MultiLO.app || true
if codesign --force --deep --sign - dist/MultiLO.app; then
  echo "Codesign OK"
else
  echo "Codesign skipped: current macOS metadata prevents ad-hoc signing on this machine."
  echo "ZIP will still be created; if needed, sign manually on the target Mac."
fi

echo "[5/5] Creating portable ZIP"
(
  cd dist
  COPYFILE_DISABLE=1 zip -qry "$SCRIPT_DIR/MultiLO.app.zip" MultiLO.app
)

echo "Done: $SCRIPT_DIR/MultiLO.app.zip"
