#!/bin/zsh
set -eu

AGENT_DIR="$HOME/Library/LaunchAgents"
GUI_DOMAIN="gui/$(id -u)"
LABELS=(
  "com.miloslavfalta.samantha.cockpit"
  "com.miloslavfalta.samantha.scandocu"
)

for label in "${LABELS[@]}"; do
  plist_path="$AGENT_DIR/$label.plist"
  if [[ -f "$plist_path" ]]; then
    launchctl bootout "$GUI_DOMAIN" "$plist_path" >/dev/null 2>&1 || true
    rm "$plist_path"
    echo "Removed launchd service: $label"
  else
    echo "Launchd service not installed: $label"
  fi
done

echo ""
echo "Check:"
echo "  launchctl list | grep 'com.miloslavfalta.samantha' || true"
