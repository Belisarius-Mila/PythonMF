#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


SAMANTHA_DIR = Path(__file__).resolve().parents[1]
if str(SAMANTHA_DIR) not in sys.path:
    sys.path.insert(0, str(SAMANTHA_DIR))

from app.backup.incremental import main


if __name__ == "__main__":
    raise SystemExit(main())
