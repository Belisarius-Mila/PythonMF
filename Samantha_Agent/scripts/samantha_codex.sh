#!/bin/zsh
set -eu

PROJECT_DIR="$HOME/Desktop/PythonMF/Samantha_Agent"
SESSION_NAME="${SAMANTHA_SCREEN_SESSION:-samantha_codex}"
ENTRY_SCRIPT="$PROJECT_DIR/scripts/samantha_screen_entry.sh"

export LANG="${LANG:-cs_CZ.UTF-8}"
export LC_ALL="${LC_ALL:-cs_CZ.UTF-8}"
export LC_CTYPE="${LC_CTYPE:-cs_CZ.UTF-8}"

if screen -list | grep -q "[.]${SESSION_NAME}[[:space:]]"; then
  exec screen -U -r "$SESSION_NAME"
fi

cd "$PROJECT_DIR"
exec screen -U -S "$SESSION_NAME" "$ENTRY_SCRIPT"
