#!/bin/zsh
set -eu

PROJECT_DIR="/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent"
PYTHON_BIN="${PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
HOST="${SAMANTHA_COCKPIT_LOCAL_HOST:-127.0.0.1}"
PORT="${SAMANTHA_COCKPIT_LOCAL_PORT:-8770}"
LABEL="com.miloslavfalta.samantha.cockpit"
AGENT_DIR="$HOME/Library/LaunchAgents"
GUI_DOMAIN="gui/$(id -u)"
LOG_DIR="$PROJECT_DIR/data/private/cockpit"
PLIST_PATH="$AGENT_DIR/$LABEL.plist"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

mkdir -p "$AGENT_DIR" "$LOG_DIR"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON_BIN</string>
    <string>$PROJECT_DIR/scripts/cockpit_launchd_runner.py</string>
    <string>--host</string>
    <string>$HOST</string>
    <string>--port</string>
    <string>$PORT</string>
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
  <string>$LOG_DIR/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/launchd.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout "$GUI_DOMAIN" "$PLIST_PATH" >/dev/null 2>&1 || true

existing_pids="$(pgrep -f "[c]ockpit_launchd_runner.py --host $HOST --port $PORT" || true)"
if [[ -n "$existing_pids" ]]; then
  echo "Stopping existing local Cockpit runner on $HOST:$PORT: $existing_pids"
  kill $existing_pids >/dev/null 2>&1 || true
  sleep 0.5
fi

launchctl bootstrap "$GUI_DOMAIN" "$PLIST_PATH"
launchctl enable "$GUI_DOMAIN/$LABEL"
launchctl kickstart -k "$GUI_DOMAIN/$LABEL"

echo "Installed launchd service: $LABEL"
echo "URL: http://$HOST:$PORT"
echo "Plist: $PLIST_PATH"
echo "Logs: $LOG_DIR"
