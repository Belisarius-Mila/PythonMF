#!/bin/zsh
set -eu

PROJECT_DIR="$HOME/Desktop/PythonMF/Samantha_Agent"
OUT_DIR="$PROJECT_DIR/data/session_autosave"
INTERVAL_SECONDS="${SAMANTHA_AUTOSAVE_SECONDS:-600}"

mkdir -p "$OUT_DIR"

latest_session_file() {
  find "$HOME/.codex/sessions" -type f -name 'rollout-*.jsonl' -print0 2>/dev/null \
    | xargs -0 ls -t 2>/dev/null \
    | head -n 1
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
  cp "$latest" "$OUT_DIR/session_${stamp}.jsonl"

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

  cp "$latest_txt" "$timestamped_txt"

  {
    printf 'Saved at: %s\n' "$(date)"
    printf 'Source: %s\n' "$latest"
    printf 'Latest copy: %s\n' "$OUT_DIR/latest_session.jsonl"
    printf 'Timestamped copy: %s\n' "$OUT_DIR/session_${stamp}.jsonl"
    printf 'Latest TXT: %s\n' "$latest_txt"
    printf 'Timestamped TXT: %s\n' "$timestamped_txt"
    printf '\n'
    printf 'Poznamka: jde o nouzovy autosave, muze obsahovat citlive udaje. Necommitovat.\n'
  } > "$OUT_DIR/latest_info.txt"
}

if [ "${1:-}" = "--watch" ]; then
  while true; do
    save_once
    sleep "$INTERVAL_SECONDS"
  done
else
  save_once
fi
