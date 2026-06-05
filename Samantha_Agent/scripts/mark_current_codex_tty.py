from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MARKER_PATH = PROJECT_ROOT / "data/private/voice_inbox/current_codex_tty.json"


def current_parent_tty() -> str:
    parent_pid = os.getppid()
    output = subprocess.check_output(["ps", "-o", "tty=", "-p", str(parent_pid)], text=True).strip()
    return output.removeprefix("/dev/").strip()


def main() -> int:
    tty = current_parent_tty()
    if not tty or tty == "??":
        raise SystemExit("Nepodařilo se určit TTY aktuální Codex relace.")
    MARKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKER_PATH.write_text(
        json.dumps(
            {
                "tty": tty,
                "marked_at": datetime.now(timezone.utc).isoformat(),
                "parent_pid": os.getppid(),
                "note": "Private runtime marker for Adam Voice Mode terminal bridge.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Marked current Codex TTY: {tty}")
    print(f"Marker: {MARKER_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
