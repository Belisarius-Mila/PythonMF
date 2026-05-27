#!/bin/zsh
set -eu

PROJECT_DIR="$HOME/Desktop/PythonMF/Samantha_Agent"
SESSION_NAME="${SAMANTHA_SCREEN_SESSION:-samantha_codex}"
ENTRY_SCRIPT="$PROJECT_DIR/scripts/samantha_screen_entry.sh"
NETWORK_PREFLIGHT_SCRIPT="$PROJECT_DIR/scripts/network_preflight.sh"
BACKUP_STATUS_SCRIPT="$PROJECT_DIR/scripts/backup_status.py"

export LANG="${LANG:-cs_CZ.UTF-8}"
export LC_ALL="${LC_ALL:-cs_CZ.UTF-8}"
export LC_CTYPE="${LC_CTYPE:-cs_CZ.UTF-8}"

if [[ -x "$NETWORK_PREFLIGHT_SCRIPT" ]]; then
  "$NETWORK_PREFLIGHT_SCRIPT" || true
fi

if [[ -f "$BACKUP_STATUS_SCRIPT" ]]; then
  if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    "$PROJECT_DIR/.venv/bin/python" "$BACKUP_STATUS_SCRIPT" || true
  else
    python3 "$BACKUP_STATUS_SCRIPT" || true
  fi
fi

if screen -list | grep -q "[.]${SESSION_NAME}[[:space:]]"; then
  exec screen -U -r "$SESSION_NAME"
fi

cd "$PROJECT_DIR"
exec screen -U -S "$SESSION_NAME" "$ENTRY_SCRIPT"
