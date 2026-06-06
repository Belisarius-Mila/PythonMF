#!/bin/zsh
set -eu

PROJECT_DIR="$HOME/Desktop/PythonMF/Samantha_Agent"
CODEX_BIN="${CODEX_BIN:-/usr/local/bin/codex}"
AUTOSAVE_SCRIPT="$PROJECT_DIR/scripts/autosave_codex_session.sh"
MARK_CURRENT_CODEX_TTY_SCRIPT="$PROJECT_DIR/scripts/mark_current_codex_tty.py"

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

mark_voice_tty_if_requested() {
  local answer="${SAMANTHA_MARK_VOICE_TTY:-}"
  local normalized="${answer:l}"
  local should_mark=""

  case "$normalized" in
    1|true|yes|y|ano|a)
      should_mark="1"
      ;;
    0|false|no|n|ne)
      should_mark="0"
      ;;
  esac

  if [[ -z "$should_mark" ]]; then
    if [[ -t 0 ]]; then
      printf "Mám nastavit voice marker na tuto relaci? [Y/n] "
      read -r answer || answer=""
      normalized="${answer:l}"
      case "$normalized" in
        ""|1|true|yes|y|ano|a)
          should_mark="1"
          ;;
        0|false|no|n|ne)
          should_mark="0"
          ;;
        *)
          should_mark="1"
          ;;
      esac
    else
      should_mark="1"
    fi
  fi

  if [[ "$should_mark" != "1" ]]; then
    echo "Voice marker ponechán beze změny."
    return
  fi

  if [[ ! -f "$MARK_CURRENT_CODEX_TTY_SCRIPT" ]]; then
    echo "Voice marker nelze nastavit: chybí $MARK_CURRENT_CODEX_TTY_SCRIPT"
    return
  fi

  if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    "$PROJECT_DIR/.venv/bin/python" "$MARK_CURRENT_CODEX_TTY_SCRIPT" || true
  else
    python3 "$MARK_CURRENT_CODEX_TTY_SCRIPT" || true
  fi
}

mark_voice_tty_if_requested
"$CODEX_BIN" -C "$PROJECT_DIR" .
