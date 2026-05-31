#!/bin/zsh
set -eu

PROJECT_DIR="/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent"

cd "${PROJECT_DIR}"
exec "${PROJECT_DIR}/.venv/bin/python" "${PROJECT_DIR}/scripts/open_cockpit.py" "$@"
