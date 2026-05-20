#!/bin/zsh
set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
LABEL="${SAMANTHA_DAILY_3AM_LABEL:-com.miloslavfalta.samantha.daily-3am}"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$PROJECT_DIR/logs"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

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
    <string>$PROJECT_DIR/scripts/daily_3am.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$PROJECT_DIR</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>3</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/daily_3am.launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/daily_3am.launchd.err.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
PLIST

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load "$PLIST_PATH"

if pmset repeat wakeorpoweron MTWRFSU 02:55:00; then
  WAKE_STATUS="Wake schedule set: pmset repeat wakeorpoweron MTWRFSU 02:55:00"
else
  WAKE_STATUS="Wake schedule was not set. Run manually if needed: sudo pmset repeat wakeorpoweron MTWRFSU 02:55:00"
fi

echo "Installed launchd job: $LABEL"
echo "Plist: $PLIST_PATH"
echo "$WAKE_STATUS"
echo "Check with: launchctl list | grep $LABEL"
