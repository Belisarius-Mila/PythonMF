#!/bin/zsh
set -eu

PROJECT_DIR="/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent"
PYTHON_BIN="${PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

echo "Tailscale Cockpit uz nepouziva druhy Python server."
echo "Zapinam bezpecny TCP proxy do lokalni instance s automatickym rollbackem."
exec "$PYTHON_BIN" "$PROJECT_DIR/scripts/migrate_cockpit_single_instance.py" --apply
