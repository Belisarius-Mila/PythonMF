#!/bin/zsh
set -eu

PROJECT_DIR="$HOME/Desktop/PythonMF/Samantha_Agent"
SESSION_NAME="${SAMANTHA_SCREEN_SESSION:-samantha_codex}"
ENTRY_SCRIPT="$PROJECT_DIR/scripts/samantha_screen_entry.sh"
NETWORK_PREFLIGHT_SCRIPT="$PROJECT_DIR/scripts/network_preflight.sh"
BACKUP_STATUS_SCRIPT="$PROJECT_DIR/scripts/backup_status.py"
CODEX_SESSION_REPORT_SCRIPT="$PROJECT_DIR/scripts/codex_session_report.py"
WORK_CONTEXT_GUARD_SCRIPT="$PROJECT_DIR/scripts/work_context_guard.py"
SCREENRC="$PROJECT_DIR/scripts/samantha_screenrc"
START_REQUEST="$*"

export LANG="cs_CZ.UTF-8"
export LC_ALL="cs_CZ.UTF-8"
export LC_CTYPE="cs_CZ.UTF-8"
export PYTHONUTF8="1"
export PYTHONIOENCODING="utf-8"
export LESSCHARSET="utf-8"
if [[ -n "$START_REQUEST" ]]; then
  export SAMANTHA_START_REQUEST="$START_REQUEST"
fi

print_screen_scroll_hint() {
  if [[ "${SAMANTHA_SCREEN_HINT:-1}" == "0" || ! -t 1 ]]; then
    return
  fi
  echo "Tip pro režim samantha/screen: scrollback otevře Ctrl+A potom Esc; ukončí ho Esc."
}

run_work_context_guard_before_attach() {
  if [[ "${SAMANTHA_WORK_CONTEXT_GUARD:-1}" == "0" ]]; then
    return
  fi
  if [[ ! -f "$WORK_CONTEXT_GUARD_SCRIPT" ]]; then
    echo "Work context guard nelze spustit: chybí $WORK_CONTEXT_GUARD_SCRIPT"
    return
  fi

  local python_cmd="$PROJECT_DIR/.venv/bin/python"
  if [[ ! -x "$python_cmd" ]]; then
    python_cmd="python3"
  fi

  local output guard_status
  set +e
  output="$("$python_cmd" "$WORK_CONTEXT_GUARD_SCRIPT" 2>&1)"
  guard_status=$?
  set -e
  echo "$output"

  if [[ "$guard_status" != "0" && -t 0 && "${SAMANTHA_WORK_CONTEXT_GUARD_CONFIRM:-1}" != "0" ]]; then
    echo "Guard hlásí rozpracovanou práci. Před změnou tématu je potřeba checkpoint."
    printf "Pokračovat do Samantha session? [Y/n] "
    local answer normalized
    read -r answer || answer=""
    normalized="${answer:l}"
    case "$normalized" in
      n|no|ne|0|false)
        echo "Start session zastaven kvůli work context guardu."
        exit 1
        ;;
    esac
  fi
}

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

if [[ -f "$CODEX_SESSION_REPORT_SCRIPT" ]]; then
  if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    "$PROJECT_DIR/.venv/bin/python" "$CODEX_SESSION_REPORT_SCRIPT" || true
  else
    python3 "$CODEX_SESSION_REPORT_SCRIPT" || true
  fi
fi

run_work_context_guard_before_attach

if [[ "${SAMANTHA_RESTART_SCREEN:-0}" == "1" ]]; then
  if screen -list | grep -q "[.]${SESSION_NAME}[[:space:]]"; then
    screen -S "$SESSION_NAME" -X quit || true
    sleep 1
  fi
fi

if screen -list | grep -q "[.]${SESSION_NAME}[[:space:]]"; then
  if [[ -n "$START_REQUEST" ]]; then
    echo "Startovní pokyn od Míly:"
    echo "$START_REQUEST"
    echo
    echo "Poznámka: připojuji existující screen session; pokyn se do běžícího Codexu nevloží automaticky."
    echo "Po připojení ho vlož do Codexu ručně, pokud už tam není."
    echo
  fi
  print_screen_scroll_hint
  exec screen -c "$SCREENRC" -U -r "$SESSION_NAME"
fi

cd "$PROJECT_DIR"
print_screen_scroll_hint
exec screen -c "$SCREENRC" -U -S "$SESSION_NAME" "$ENTRY_SCRIPT"
