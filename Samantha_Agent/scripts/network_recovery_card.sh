#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CARD="${ROOT_DIR}/NETWORK_RECOVERY_CARD.txt"

if [[ -f "${CARD}" ]]; then
  cat "${CARD}"
else
  echo "Nenalezen soubor: ${CARD}" >&2
  exit 1
fi

