#!/usr/bin/env python3
"""Compatibility entry point for the read-only Codex session report."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.codex_session_report import main


if __name__ == "__main__":
    raise SystemExit(main())
