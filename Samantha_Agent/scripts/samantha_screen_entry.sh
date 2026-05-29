#!/bin/zsh
set -eu

PROJECT_DIR="$HOME/Desktop/PythonMF/Samantha_Agent"
CODEX_BIN="${CODEX_BIN:-/usr/local/bin/codex}"
AUTOSAVE_SCRIPT="$PROJECT_DIR/scripts/autosave_codex_session.sh"

export LANG="cs_CZ.UTF-8"
export LC_ALL="cs_CZ.UTF-8"
export LC_CTYPE="cs_CZ.UTF-8"
export PYTHONUTF8="1"
export PYTHONIOENCODING="utf-8"
export LESSCHARSET="utf-8"

"$AUTOSAVE_SCRIPT" --watch &
AUTOSAVE_PID=$!

cleanup() {
  kill "$AUTOSAVE_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

cd "$PROJECT_DIR"
"$CODEX_BIN" -C "$PROJECT_DIR" .
