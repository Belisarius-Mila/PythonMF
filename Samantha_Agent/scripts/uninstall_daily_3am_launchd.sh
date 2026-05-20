#!/bin/zsh
set -eu

LABEL="${SAMANTHA_DAILY_3AM_LABEL:-com.miloslavfalta.samantha.daily-3am}"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ -f "$PLIST_PATH" ]]; then
  launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
  rm "$PLIST_PATH"
  echo "Removed launchd job: $LABEL"
else
  echo "Launchd job not installed: $LABEL"
fi

echo "Current pmset repeat schedule:"
pmset -g sched || true
echo ""
echo "If the only repeat schedule was for Samantha daily 3 AM, remove it manually with:"
echo "pmset repeat cancel"
