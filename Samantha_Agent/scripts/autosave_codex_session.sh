#!/bin/zsh
set -eu

PROJECT_DIR="${SAMANTHA_PROJECT_DIR:-$HOME/Desktop/PythonMF/Samantha_Agent}"
OUT_DIR="${SAMANTHA_AUTOSAVE_OUT_DIR:-$PROJECT_DIR/data/session_autosave}"
CODEX_SESSIONS_DIR="${SAMANTHA_CODEX_SESSIONS_DIR:-$HOME/.codex/sessions}"
INTERVAL_SECONDS="${SAMANTHA_AUTOSAVE_SECONDS:-600}"
HISTORY_INTERVAL_SECONDS="${SAMANTHA_AUTOSAVE_HISTORY_SECONDS:-3600}"
KEEP_HISTORY_SNAPSHOTS="${SAMANTHA_AUTOSAVE_KEEP_HISTORY:-12}"
CLEANUP_SCRIPT="$PROJECT_DIR/scripts/cleanup_session_autosave.py"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
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

latest_session_file() {
  find "$CODEX_SESSIONS_DIR" -type f -name 'rollout-*.jsonl' -print0 2>/dev/null \
    | xargs -0 ls -t 2>/dev/null \
    | head -n 1
}

historical_snapshot_due() {
  local -a snapshots
  snapshots=("$OUT_DIR"/session_????????_??????.jsonl(N.om))
  if [ "${#snapshots}" -eq 0 ]; then
    return 0
  fi

  local latest_epoch now_epoch
  latest_epoch="$(stat -f '%m' "${snapshots[1]}" 2>/dev/null || printf '0')"
  now_epoch="$(date '+%s')"
  [ $((now_epoch - latest_epoch)) -ge "$HISTORY_INTERVAL_SECONDS" ]
}

apply_automatic_retention() {
  if [ ! -x "$PYTHON_BIN" ] || [ ! -f "$CLEANUP_SCRIPT" ]; then
    printf '%s\n' "retention unavailable"
    return 0
  fi
  if "$PYTHON_BIN" "$CLEANUP_SCRIPT" \
    --autosave-dir "$OUT_DIR" \
    --retention-days 0 \
    --keep-latest-snapshots "$KEEP_HISTORY_SNAPSHOTS" \
    --apply \
    --confirm 'SMAZAT STARE AUTOSAVE' >/dev/null 2>&1; then
    printf '%s\n' "ok"
  else
    printf '%s\n' "failed"
  fi
}

save_once() {
  local latest
  latest="$(latest_session_file || true)"

  if [ -z "$latest" ] || [ ! -f "$latest" ]; then
    printf '%s\n' "No Codex session file found." > "$OUT_DIR/latest_info.txt"
    return 0
  fi

  local stamp
  stamp="$(date '+%Y%m%d_%H%M%S')"

  cp "$latest" "$OUT_DIR/latest_session.jsonl"

  local latest_txt timestamped_txt
  latest_txt="$OUT_DIR/latest_session.txt"
  timestamped_txt="$OUT_DIR/session_${stamp}.txt"

  ruby -rjson - "$latest" "$latest_txt" <<'RUBY'
source, output = ARGV
File.open(output, "w") do |out|
  out.puts "Samantha/Codex autosave TXT"
  out.puts "Saved at: #{Time.now}"
  out.puts "Source: #{source}"
  out.puts
  out.puts "Poznamka: nouzovy textovy snapshot. Muze obsahovat citlive udaje. Necommitovat."
  out.puts "=" * 78
  out.puts

  File.foreach(source) do |line|
    begin
      item = JSON.parse(line)
    rescue JSON::ParserError
      next
    end

    timestamp = item["timestamp"] || ""
    type = item["type"]
    payload = item["payload"] || {}

    if type == "event_msg" && payload["type"] == "user_message"
      message = payload["message"].to_s.strip
      next if message.empty?
      out.puts "[#{timestamp}] USER:"
      out.puts message
      out.puts
    elsif type == "event_msg" && payload["type"] == "agent_message"
      phase = payload["phase"] || "assistant"
      message = payload["message"].to_s.strip
      next if message.empty?
      out.puts "[#{timestamp}] ASSISTANT #{phase}:"
      out.puts message
      out.puts
    end
  end
end
RUBY

  local history_note
  if historical_snapshot_due; then
    cp "$OUT_DIR/latest_session.jsonl" "$OUT_DIR/session_${stamp}.jsonl"
    cp "$latest_txt" "$timestamped_txt"
    history_note="$timestamped_txt"
  else
    history_note="bez nove kopie (hodinovy interval)"
  fi

  local retention_status
  retention_status="$(apply_automatic_retention)"

  {
    printf 'Saved at: %s\n' "$(date)"
    printf 'Source: %s\n' "$latest"
    printf 'Latest copy: %s\n' "$OUT_DIR/latest_session.jsonl"
    printf 'Historicky snapshot: %s\n' "$history_note"
    printf 'Historicky interval: %s sekund\n' "$HISTORY_INTERVAL_SECONDS"
    printf 'Automaticka retence: ponechat %s nejnovejsich casu (%s)\n' "$KEEP_HISTORY_SNAPSHOTS" "$retention_status"
    printf 'Latest TXT: %s\n' "$latest_txt"
    printf '\n'
    printf 'Poznamka: jde o nouzovy autosave, muze obsahovat citlive udaje. Necommitovat.\n'
  } > "$OUT_DIR/latest_info.txt"
}

if [ "${1:-}" = "--watch" ]; then
  if ! acquire_watcher_lock; then
    exit 0
  fi
  trap release_watcher_lock EXIT
  trap stop_watcher INT TERM HUP
  while true; do
    save_once
    sleep "$INTERVAL_SECONDS" &
    SLEEP_PID=$!
    wait "$SLEEP_PID" || true
    SLEEP_PID=""
  done
else
  save_once
fi
