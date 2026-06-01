#!/bin/zsh
set -eu

PROJECT_DIR="/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent"
AGENT_DIR="${PROJECT_DIR}/data/private/cockpit/hotkey"
SOURCE="${PROJECT_DIR}/scripts/samantha_cockpit_hotkey.swift"
BINARY="${AGENT_DIR}/SamanthaCockpitHotkey"
PLIST="${HOME}/Library/LaunchAgents/com.miloslavfalta.samantha.cockpit-hotkey.plist"
LOG_DIR="${PROJECT_DIR}/data/private/cockpit"

mkdir -p "${AGENT_DIR}" "${LOG_DIR}" "${HOME}/Library/LaunchAgents"

/usr/bin/swiftc "${SOURCE}" -o "${BINARY}"

/usr/bin/plutil -create xml1 "${PLIST}"
/usr/bin/plutil -replace Label -string "com.miloslavfalta.samantha.cockpit-hotkey" "${PLIST}"
/usr/bin/plutil -replace ProgramArguments -json "[\"${BINARY}\"]" "${PLIST}"
/usr/bin/plutil -replace RunAtLoad -bool YES "${PLIST}"
/usr/bin/plutil -replace KeepAlive -bool YES "${PLIST}"
/usr/bin/plutil -replace StandardOutPath -string "${LOG_DIR}/hotkey.out.log" "${PLIST}"
/usr/bin/plutil -replace StandardErrorPath -string "${LOG_DIR}/hotkey.err.log" "${PLIST}"

/bin/launchctl bootout "gui/$(id -u)" "${PLIST}" 2>/dev/null || true
/bin/launchctl bootstrap "gui/$(id -u)" "${PLIST}"
/bin/launchctl kickstart -k "gui/$(id -u)/com.miloslavfalta.samantha.cockpit-hotkey"

echo "Samantha Cockpit hotkey agent installed: Ctrl+Option+Cmd+C"
