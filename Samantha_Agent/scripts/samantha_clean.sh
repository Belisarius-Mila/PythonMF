#!/bin/zsh
set -eu

PROJECT_DIR="$HOME/Desktop/PythonMF/Samantha_Agent"

export SAMANTHA_DISABLE_VPN=1
exec "$PROJECT_DIR/scripts/samantha_codex.sh"
