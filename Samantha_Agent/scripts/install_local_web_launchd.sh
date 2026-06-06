#!/bin/zsh
set -eu

PROJECT_DIR="/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent"
PYTHON_BIN="${PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
AGENT_DIR="$HOME/Library/LaunchAgents"
GUI_DOMAIN="gui/$(id -u)"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

mkdir -p "$AGENT_DIR"

install_service() {
  local label="$1"
  local port="$2"
  local script_name="$3"
  local log_dir="$4"
  local plist_path="$AGENT_DIR/$label.plist"

  mkdir -p "$log_dir"

  cat > "$plist_path" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON_BIN</string>
    <string>$PROJECT_DIR/scripts/$script_name</string>
    <string>--host</string>
    <string>127.0.0.1</string>
    <string>--port</string>
    <string>$port</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$PROJECT_DIR</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PYTHONUNBUFFERED</key>
    <string>1</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$log_dir/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$log_dir/launchd.err.log</string>
</dict>
</plist>
PLIST

  launchctl bootout "$GUI_DOMAIN" "$plist_path" >/dev/null 2>&1 || true

  local existing_pid
  existing_pid="$(lsof -tiTCP:"$port" -sTCP:LISTEN || true)"
  if [[ -n "$existing_pid" ]]; then
    echo "Stopping existing listener on port $port: $existing_pid"
    kill $existing_pid >/dev/null 2>&1 || true
    sleep 0.5
  fi

  launchctl bootstrap "$GUI_DOMAIN" "$plist_path"
  launchctl enable "$GUI_DOMAIN/$label"
  launchctl kickstart -k "$GUI_DOMAIN/$label"

  echo "Installed launchd service: $label"
  echo "Port: $port"
  echo "Plist: $plist_path"
}

install_service \
  "com.miloslavfalta.samantha.cockpit" \
  "8770" \
  "cockpit_launchd_runner.py" \
  "$PROJECT_DIR/data/private/cockpit"

install_service \
  "com.miloslavfalta.samantha.scandocu" \
  "8766" \
  "scandocu_server.py" \
  "$PROJECT_DIR/data/private/documents/scandocu"

echo ""
echo "Check:"
echo "  launchctl list | grep 'com.miloslavfalta.samantha'"
echo "  open http://127.0.0.1:8770"
