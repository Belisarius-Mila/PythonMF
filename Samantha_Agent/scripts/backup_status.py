#!/usr/bin/env python3
"""Print the current Samantha/PythonMF backup reminder status."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.backup.activity_state import format_backup_activity_reminder


def main() -> None:
    print(format_backup_activity_reminder())


if __name__ == "__main__":
    main()
