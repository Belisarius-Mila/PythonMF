"""Shared system Git selection; repository state is never cached."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def resolve_git_executable() -> str:
    """Resolve Apple's selected Git once, avoiding its launcher on every call."""
    fallback = "/usr/bin/git"
    if sys.platform != "darwin":
        return fallback
    try:
        result = subprocess.run(
            ["/usr/bin/xcrun", "--find", "git"],
            capture_output=True, text=True, check=False, timeout=5,
        )
        candidate = Path(result.stdout.strip())
        if (
            result.returncode == 0
            and len(result.stdout.strip().splitlines()) == 1
            and candidate.is_absolute()
            and candidate.name == "git"
            and candidate.is_file()
            and os.access(candidate, os.X_OK)
        ):
            return str(candidate)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return fallback


# Toolchain selection is fixed for this process; restart after changing Xcode.
GIT_EXECUTABLE = resolve_git_executable()
