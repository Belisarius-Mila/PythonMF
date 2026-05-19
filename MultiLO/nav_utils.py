"""Navigation helpers for MultiLO.

Current architecture keeps one active Python process and swaps screens by
replacing the running script with another one via os.execl().
"""

from __future__ import annotations

import os
from pathlib import Path
import sys


def replace_process(script_path: str | Path, *args: str) -> None:
    path = Path(script_path).resolve()
    os.chdir(str(path.parent))
    os.execl(sys.executable, sys.executable, str(path), *args)
