#!/bin/zsh
set -eu

PROJECT_DIR="/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent"
PORT="8766"
URL="http://127.0.0.1:${PORT}"
LOG_DIR="${PROJECT_DIR}/data/private/documents/scandocu"
LOG_FILE="${LOG_DIR}/server.log"

mkdir -p "${LOG_DIR}"
cd "${PROJECT_DIR}"

if /usr/bin/curl -fsS "${URL}/api/list" >/dev/null 2>&1; then
  open "${URL}" >/dev/null 2>&1 || true
  echo "ScanDocu už běží: ${URL}"
  exit 0
fi

existing_pid="$(lsof -tiTCP:${PORT} -sTCP:LISTEN || true)"
if [[ -n "${existing_pid}" ]]; then
  kill ${existing_pid} >/dev/null 2>&1 || true
  sleep 0.5
fi

if ! /usr/bin/curl -fsS "${URL}/api/list" >/dev/null 2>&1; then
  nohup "${PROJECT_DIR}/.venv/bin/python" "${PROJECT_DIR}/scripts/scandocu_server.py" --port "${PORT}" >> "${LOG_FILE}" 2>&1 &
  sleep 2
fi

open "${URL}" >/dev/null 2>&1 || true
echo "ScanDocu spuštěno: ${URL}"
