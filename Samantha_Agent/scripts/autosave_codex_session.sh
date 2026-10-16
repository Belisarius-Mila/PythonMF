#!/bin/zsh
set -eu

PROJECT_DIR="${SAMANTHA_PROJECT_DIR:-$HOME/Desktop/PythonMF/Samantha_Agent}"
OUT_DIR="${SAMANTHA_AUTOSAVE_OUT_DIR:-$PROJECT_DIR/data/session_autosave}"
CODEX_SESSIONS_DIR="${SAMANTHA_CODEX_SESSIONS_DIR:-$HOME/.codex/sessions}"
INTERVAL_SECONDS="${SAMANTHA_AUTOSAVE_SECONDS:-600}"
HISTORY_INTERVAL_SECONDS="${SAMANTHA_AUTOSAVE_HISTORY_SECONDS:-3600}"
KEEP_HISTORY_SNAPSHOTS="${SAMANTHA_AUTOSAVE_KEEP_HISTORY:-12}"
AUTOMATIC_CLEANUP="${SAMANTHA_AUTOSAVE_AUTO_CLEANUP:-1}"
CLEANUP_SCRIPT="$PROJECT_DIR/scripts/cleanup_session_autosave.py"
PYTHON_BIN="${SAMANTHA_AUTOSAVE_PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
WATCH_LOCK_DIR="$OUT_DIR/.watcher.lock"
WATCH_LOCK_PID_FILE="$WATCH_LOCK_DIR/pid"
SLEEP_PID=""

mkdir -p "$OUT_DIR"

if [[ "$HISTORY_INTERVAL_SECONDS" != <-> ]] || [ "$HISTORY_INTERVAL_SECONDS" -lt 1 ]; then
  HISTORY_INTERVAL_SECONDS=3600
fi
if [[ "$KEEP_HISTORY_SNAPSHOTS" != <-> ]] || [ "$KEEP_HISTORY_SNAPSHOTS" -lt 1 ]; then
  KEEP_HISTORY_SNAPSHOTS=12
fi

release_watcher_lock() {
  local owner=""
  if [ -f "$WATCH_LOCK_PID_FILE" ]; then
    owner="$(<"$WATCH_LOCK_PID_FILE")"
  fi
  if [ "$owner" = "$$" ]; then
    rm -f "$WATCH_LOCK_PID_FILE"
    rmdir "$WATCH_LOCK_DIR" 2>/dev/null || true
  fi
}

acquire_watcher_lock() {
  if mkdir "$WATCH_LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "$$" > "$WATCH_LOCK_PID_FILE"
    return 0
  fi

  local owner=""
  if [ -f "$WATCH_LOCK_PID_FILE" ]; then
    owner="$(<"$WATCH_LOCK_PID_FILE")"
  fi
  if [[ "$owner" == <-> ]] && kill -0 "$owner" 2>/dev/null; then
    printf 'Autosave watcher už běží (PID %s); druhou kopii nespouštím.\n' "$owner"
    return 1
  fi

  rm -f "$WATCH_LOCK_PID_FILE"
  rmdir "$WATCH_LOCK_DIR" 2>/dev/null || true
  if ! mkdir "$WATCH_LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "Autosave watcher lock se nepodařilo bezpečně získat; watcher nespouštím."
    return 1
  fi
  printf '%s\n' "$$" > "$WATCH_LOCK_PID_FILE"
  return 0
}

stop_watcher() {
  if [ -n "$SLEEP_PID" ]; then
    kill "$SLEEP_PID" 2>/dev/null || true
  fi
  release_watcher_lock
  exit 0
}

save_once() {
  local -a cleanup_args
  cleanup_args=()
  if [[ "$AUTOMATIC_CLEANUP" == "1" ]]; then
    cleanup_args=(--automatic-cleanup)
  fi
  "$PYTHON_BIN" "$PROJECT_DIR/scripts/autosave_snapshot.py" \
    --project "$PROJECT_DIR" --sessions "$CODEX_SESSIONS_DIR" --output "$OUT_DIR" \
    --history-seconds "$HISTORY_INTERVAL_SECONDS" --keep "$KEEP_HISTORY_SNAPSHOTS" \
    "${cleanup_args[@]}"
}

if [ "${1:-}" = "--watch" ]; then
  if ! acquire_watcher_lock; then
    exit 0
  fi
  trap release_watcher_lock EXIT
  trap stop_watcher INT TERM HUP
  while true; do
    save_once || true
    sleep "$INTERVAL_SECONDS" &
    SLEEP_PID=$!
    wait "$SLEEP_PID" || true
    SLEEP_PID=""
  done
else
  save_once
fi
