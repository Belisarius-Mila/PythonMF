#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
SAMANTHA_DIR="${SCRIPT_DIR:h}"
PROJECT_ROOT="${SAMANTHA_DIR:h}"
ALWAYS_FILTER="$SCRIPT_DIR/backup_rsync_filter_always.rules"
SENSITIVE_FILTER="$SCRIPT_DIR/backup_rsync_filter_sensitive.rules"
RECOVERY_GUIDE="$SAMANTHA_DIR/RECOVERY_FROM_BACKUP.md"

MODE="dry-run"
PROFILE="${SAMANTHA_BACKUP_PROFILE:-safe}"
BACKUP_ROOT="${SAMANTHA_BACKUP_ROOT:-/Volumes/SamanthaSecureBackup/SamanthaBackups}"
STAMP="$(date '+%Y%m%d_%H%M%S')"
PYTHON_BIN="$SAMANTHA_DIR/.venv/bin/python"
VERBOSE=0

usage() {
  cat <<'USAGE'
Samantha backup helper

Default: dry-run only, no files are copied.

Usage:
  backup_samantha.command [--dry-run] [--execute] [--profile safe|recovery] [--target PATH] [--verbose]

Profiles:
  safe      Excludes .env, email local data, reminders, Tax, and session autosave.
  recovery  Includes local sensitive data for full restore. Use only with encrypted target.

Environment:
  SAMANTHA_BACKUP_ROOT=/Volumes/SamanthaSecureBackup/SamanthaBackups
  SAMANTHA_BACKUP_PROFILE=safe|recovery
  SAMANTHA_BACKUP_ALLOW_SENSITIVE_TARGET=1  # override encrypted-target guard
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      MODE="dry-run"
      ;;
    --execute)
      MODE="execute"
      ;;
    --profile)
      shift
      PROFILE="${1:-}"
      ;;
    --target)
      shift
      BACKUP_ROOT="${1:-}"
      ;;
    --verbose)
      VERBOSE=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'Neznamy argument: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [ "$PROFILE" != "safe" ] && [ "$PROFILE" != "recovery" ]; then
  printf 'Chyba: --profile musi byt safe nebo recovery.\n' >&2
  exit 2
fi

if [ ! -d "$PROJECT_ROOT" ] || [ ! -d "$SAMANTHA_DIR" ]; then
  printf 'Chyba: neumim najit projekt PythonMF/Samantha_Agent.\n' >&2
  printf 'PROJECT_ROOT=%s\nSAMANTHA_DIR=%s\n' "$PROJECT_ROOT" "$SAMANTHA_DIR" >&2
  exit 1
fi

if [ ! -f "$ALWAYS_FILTER" ] || [ ! -f "$SENSITIVE_FILTER" ] || [ ! -f "$RECOVERY_GUIDE" ]; then
  printf 'Chyba: chybi rsync filter pravidla nebo recovery navod.\n' >&2
  exit 1
fi

if [ "$MODE" = "dry-run" ] && [ ! -d "${BACKUP_ROOT:h}" ]; then
  if [ -d "/Volumes/Falta" ]; then
    BACKUP_ROOT="/Volumes/Falta"
  fi
fi

if [ "$MODE" = "execute" ] && [ ! -d "${BACKUP_ROOT:h}" ]; then
  printf 'Chyba: cilovy svazek/slozka neexistuje: %s\n' "${BACKUP_ROOT:h}" >&2
  printf 'Pripoj sifrovany kontejner nebo nastav --target PATH.\n' >&2
  exit 1
fi

if [ "$MODE" = "execute" ] && [ "$PROFILE" = "recovery" ]; then
  case "$BACKUP_ROOT" in
    /Volumes/SamanthaSecureBackup/*)
      ;;
    *)
      if [ "${SAMANTHA_BACKUP_ALLOW_SENSITIVE_TARGET:-}" != "1" ]; then
        cat >&2 <<'WARNING'
Chyba: recovery profil muze kopirovat .env, lokalni email archive, reminders a Tax.
Pro ostrou recovery zalohu pouzij sifrovany kontejner pripojeny jako:
  /Volumes/SamanthaSecureBackup

Nebo nastav SAMANTHA_BACKUP_ALLOW_SENSITIVE_TARGET=1, pokud vedome pouzivas jiny
sifrovany cil.
WARNING
        exit 1
      fi
      ;;
  esac
fi

SNAPSHOT_DIR="$BACKUP_ROOT/snapshots/$STAMP"
DEST="$SNAPSHOT_DIR/PythonMF"
CODEX_DEST="$SNAPSHOT_DIR/codex_home"
if [ "$MODE" = "dry-run" ]; then
  DEST="$BACKUP_ROOT/SamanthaBackupDryRunPreview"
  CODEX_DEST="$BACKUP_ROOT/SamanthaCodexDryRunPreview"
fi
PREVIOUS_SNAPSHOT=""
if [ -d "$BACKUP_ROOT/snapshots" ]; then
  PREVIOUS_SNAPSHOT="$(find "$BACKUP_ROOT/snapshots" -maxdepth 1 -mindepth 1 -type d -print 2>/dev/null | sort | tail -n 1 || true)"
fi

BASE_RSYNC_ARGS=(
  -a
  --human-readable
  --stats
  --exclude-from="$ALWAYS_FILTER"
)

if [ "$VERBOSE" -eq 1 ]; then
  BASE_RSYNC_ARGS+=(--itemize-changes)
fi

if [ "$PROFILE" = "safe" ]; then
  BASE_RSYNC_ARGS+=(--exclude-from="$SENSITIVE_FILTER")
fi

PROJECT_RSYNC_ARGS=("${BASE_RSYNC_ARGS[@]}")
CODEX_RSYNC_ARGS=("${BASE_RSYNC_ARGS[@]}")

if [ "$MODE" != "dry-run" ] && [ -n "$PREVIOUS_SNAPSHOT" ] && [ -d "$PREVIOUS_SNAPSHOT/PythonMF" ]; then
  PROJECT_RSYNC_ARGS+=(--link-dest="$PREVIOUS_SNAPSHOT/PythonMF")
fi

if [ "$MODE" != "dry-run" ] && [ -n "$PREVIOUS_SNAPSHOT" ] && [ -d "$PREVIOUS_SNAPSHOT/codex_home" ]; then
  CODEX_RSYNC_ARGS+=(--link-dest="$PREVIOUS_SNAPSHOT/codex_home")
fi

if [ "$MODE" = "dry-run" ]; then
  PROJECT_RSYNC_ARGS+=(--dry-run)
  CODEX_RSYNC_ARGS+=(--dry-run)
else
  mkdir -p "$SNAPSHOT_DIR" "$CODEX_DEST"
fi

printf 'Samantha backup\n'
printf 'Mode: %s\n' "$MODE"
printf 'Profile: %s\n' "$PROFILE"
printf 'Source: %s\n' "$PROJECT_ROOT"
printf 'Target: %s\n' "$DEST"
if [ -n "$PREVIOUS_SNAPSHOT" ]; then
  printf 'Previous snapshot: %s\n' "$PREVIOUS_SNAPSHOT"
fi
printf '\n'

rsync "${PROJECT_RSYNC_ARGS[@]}" "$PROJECT_ROOT/" "$DEST/"

CODEX_HOME="$HOME/.codex"
if [ -d "$CODEX_HOME" ]; then
  printf '\nCodex home backup preview\n'
  printf 'Source: %s\n' "$CODEX_HOME"
  printf 'Target: %s\n' "$CODEX_DEST"
  printf 'Note: auth.json is never backed up by this script.\n\n'

  if [ -f "$CODEX_HOME/config.toml" ]; then
    rsync "${CODEX_RSYNC_ARGS[@]}" "$CODEX_HOME/config.toml" "$CODEX_DEST/"
  fi

  if [ "$PROFILE" = "recovery" ]; then
    if [ -f "$CODEX_HOME/history.jsonl" ]; then
      rsync "${CODEX_RSYNC_ARGS[@]}" "$CODEX_HOME/history.jsonl" "$CODEX_DEST/"
    fi
    if [ -d "$CODEX_HOME/sessions" ]; then
      rsync "${CODEX_RSYNC_ARGS[@]}" "$CODEX_HOME/sessions/" "$CODEX_DEST/sessions/"
    fi
  else
    printf 'Safe profil: history.jsonl a sessions/ jsou vynechane jako citlivy konverzacni kontext.\n'
  fi
else
  printf '\nCodex home backup preview\n'
  printf 'Nenalezena slozka: %s\n' "$CODEX_HOME"
fi

if [ "$MODE" = "dry-run" ]; then
  cat <<'DONE'

Dry-run hotov. Nic nebylo zkopirovano.
Az po kontrole spust s --execute a vhodnym --profile.
DONE
  exit 0
fi

MANIFEST="$SNAPSHOT_DIR/backup_manifest.txt"
SNAPSHOT_RECOVERY_GUIDE="$SNAPSHOT_DIR/READ_ME_FIRST_RECOVERY.md"
cp -p "$RECOVERY_GUIDE" "$SNAPSHOT_RECOVERY_GUIDE"
{
  printf 'Created at: %s\n' "$(date)"
  printf 'Mode: %s\n' "$MODE"
  printf 'Profile: %s\n' "$PROFILE"
  printf 'Source: %s\n' "$PROJECT_ROOT"
  printf 'Target: %s\n' "$DEST"
  printf 'Codex target: %s\n' "$CODEX_DEST"
  printf 'Recovery guide: %s\n' "$SNAPSHOT_RECOVERY_GUIDE"
  printf 'Previous snapshot: %s\n' "${PREVIOUS_SNAPSHOT:-none}"
  printf '\nAlways filter:\n'
  cat "$ALWAYS_FILTER"
  if [ "$PROFILE" = "safe" ]; then
    printf '\nSensitive filter:\n'
    cat "$SENSITIVE_FILTER"
  fi
} > "$MANIFEST"

if [ -x "$PYTHON_BIN" ]; then
  (cd "$SAMANTHA_DIR" && PYTHONPATH="$SAMANTHA_DIR" SAMANTHA_BACKUP_RECORDED_TARGET="$DEST" "$PYTHON_BIN" -c \
    "import os; from app.backup.activity_state import record_backup_completed; record_backup_completed(target=os.environ['SAMANTHA_BACKUP_RECORDED_TARGET'], mode='$PROFILE')")
else
  (cd "$SAMANTHA_DIR" && PYTHONPATH="$SAMANTHA_DIR" SAMANTHA_BACKUP_RECORDED_TARGET="$DEST" python3 -c \
    "import os; from app.backup.activity_state import record_backup_completed; record_backup_completed(target=os.environ['SAMANTHA_BACKUP_RECORDED_TARGET'], mode='$PROFILE')")
fi

BACKUP_STATE="$SAMANTHA_DIR/data/backup/activity_state.json"
if [ -f "$BACKUP_STATE" ]; then
  mkdir -p "$DEST/Samantha_Agent/data/backup"
  cp -p "$BACKUP_STATE" "$DEST/Samantha_Agent/data/backup/activity_state.json"
fi

printf '\nOstra zaloha hotova.\n'
printf 'Manifest: %s\n' "$MANIFEST"
printf 'Ted muzes bezpecne odpojit sifrovany kontejner a externi disk.\n'
