#!/bin/zsh
set -eu

PROJECT_DIR="$HOME/Desktop/PythonMF/Samantha_Agent"
CODEX_BIN="${CODEX_BIN:-/usr/local/bin/codex}"
AUTOSAVE_SCRIPT="$PROJECT_DIR/scripts/autosave_codex_session.sh"
AUTOSAVE_RESUME_SCRIPT="$PROJECT_DIR/scripts/autosave_resume_prompt.py"
WORK_CONTEXT_GUARD_SCRIPT="$PROJECT_DIR/scripts/work_context_guard.py"
MARK_CURRENT_CODEX_TTY_SCRIPT="$PROJECT_DIR/scripts/mark_current_codex_tty.py"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"

export LANG="cs_CZ.UTF-8"
export LC_ALL="cs_CZ.UTF-8"
export LC_CTYPE="cs_CZ.UTF-8"
export PYTHONUTF8="1"
export PYTHONIOENCODING="utf-8"
export LESSCHARSET="utf-8"

CODEX_START_PROMPT=""

append_codex_start_prompt() {
  local extra="$1"
  if [[ -z "$extra" ]]; then
    return
  fi
  if [[ -n "$CODEX_START_PROMPT" ]]; then
    CODEX_START_PROMPT="${CODEX_START_PROMPT}"$'\n\n'"${extra}"
  else
    CODEX_START_PROMPT="$extra"
  fi
}

offer_autosave_resume_if_relevant() {
  if [[ "${SAMANTHA_AUTOSAVE_RESUME_CHECK:-1}" == "0" ]]; then
    return
  fi
  if [[ ! -t 0 || ! -f "$AUTOSAVE_RESUME_SCRIPT" ]]; then
    return
  fi
  local python_cmd="$PYTHON_BIN"
  if [[ ! -x "$python_cmd" ]]; then
    python_cmd="python3"
  fi
  if "$python_cmd" "$AUTOSAVE_RESUME_SCRIPT" --quiet; then
    "$python_cmd" "$AUTOSAVE_RESUME_SCRIPT" || true
    printf "Navázat na poslední autosave? [y/N] "
    local answer normalized
    read -r answer || answer=""
    normalized="${answer:l}"
    case "$normalized" in
      y|yes|a|ano)
        append_codex_start_prompt "$("$python_cmd" "$AUTOSAVE_RESUME_SCRIPT" --prompt)"
        ;;
      *)
        echo "Autosave se nenačte automaticky."
        ;;
    esac
  fi
}

offer_autosave_resume_if_relevant
if [[ -n "${SAMANTHA_START_REQUEST:-}" ]]; then
  append_codex_start_prompt "STARTOVNÍ POKYN OD MÍLY:
$SAMANTHA_START_REQUEST"
fi

AUTOSAVE_PID=""
if [[ "${SAMANTHA_AUTOSAVE_WATCH:-1}" != "0" ]]; then
  "$AUTOSAVE_SCRIPT" --watch &
  AUTOSAVE_PID=$!
fi

cleanup() {
  if [[ -n "$AUTOSAVE_PID" ]]; then
    kill "$AUTOSAVE_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

cd "$PROJECT_DIR"

run_work_context_guard_on_start() {
  if [[ "${SAMANTHA_WORK_CONTEXT_GUARD:-1}" == "0" ]]; then
    return
  fi
  if [[ ! -f "$WORK_CONTEXT_GUARD_SCRIPT" ]]; then
    echo "Work context guard nelze spustit: chybí $WORK_CONTEXT_GUARD_SCRIPT"
    return
  fi
  local python_cmd="$PYTHON_BIN"
  if [[ ! -x "$python_cmd" ]]; then
    python_cmd="python3"
  fi
  local output guard_status
  set +e
  output="$("$python_cmd" "$WORK_CONTEXT_GUARD_SCRIPT" 2>&1)"
  guard_status=$?
  set -e
  echo "$output"
  if [[ "$guard_status" == "0" ]]; then
    append_codex_start_prompt "STARTUP WORK CONTEXT GUARD:
$output

Guard je čistý. Pokud je ve startovním pokynu změna tématu, můžeš navázat."
  else
    append_codex_start_prompt "STARTUP WORK CONTEXT GUARD:
$output

Nezačínej nové téma, dokud není vyřešený checkpoint: commit/push hotové práce, WIP větev nebo handoff s dalším krokem."
  fi
}

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

  if [[ -x "$PYTHON_BIN" ]]; then
    "$PYTHON_BIN" "$MARK_CURRENT_CODEX_TTY_SCRIPT" || true
  else
    python3 "$MARK_CURRENT_CODEX_TTY_SCRIPT" || true
  fi
}

run_work_context_guard_on_start
mark_voice_tty_if_requested

while true; do
  set +e
  if [[ -n "$CODEX_START_PROMPT" ]]; then
    "$CODEX_BIN" -C "$PROJECT_DIR" "$CODEX_START_PROMPT"
  else
    "$CODEX_BIN" -C "$PROJECT_DIR" .
  fi
  CODEX_EXIT_STATUS=$?
  set -e

  echo
  echo "Codex skončil (návratový kód $CODEX_EXIT_STATUS). Screen relace zůstává otevřená."
  printf "Znovu spustit Codex v této screen relaci? [Y/n] "
  read -r answer || answer="n"
  normalized="${answer:l}"
  case "$normalized" in
    n|no|ne|0|false)
      echo "Codex zůstává vypnutý. Screen přechází do shellu; znovu se připojíš příkazem samantha."
      exec /bin/zsh -l
      ;;
  esac

  CODEX_START_PROMPT=""
  echo "Spouštím nový Codex v zachované screen relaci. Voice marker se automaticky nemění."
done
