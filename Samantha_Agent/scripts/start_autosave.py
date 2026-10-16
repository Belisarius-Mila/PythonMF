#!/usr/bin/env python3
"""Start one detached autosave worker without deleting existing snapshots."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import argparse
import signal
import time
import shlex

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.autosave_status import autosave_status


def worker_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["SAMANTHA_AUTOSAVE_AUTO_CLEANUP"] = "0"
    env["SAMANTHA_PROJECT_DIR"] = str(PROJECT_ROOT)
    env["SAMANTHA_AUTOSAVE_OUT_DIR"] = str(PROJECT_ROOT / "data/session_autosave")
    env["SAMANTHA_CODEX_SESSIONS_DIR"] = str(Path.home() / ".codex/sessions")
    return env


def run_service() -> int:
    """Keep the project Python as launchd parent and forward shutdown to its worker."""
    worker = subprocess.Popen(
        ["/bin/zsh", str(PROJECT_ROOT / "scripts/autosave_codex_session.sh"), "--watch"],
        cwd=PROJECT_ROOT, env=worker_environment(), stdin=subprocess.DEVNULL,
    )
    def stop(_signum, _frame):
        if worker.poll() is None:
            worker.terminate()
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        return worker.wait()
    finally:
        stop(None, None)
        worker.wait()
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def stop_owned_workers() -> None:
    pids = autosave_status().watcher_pids
    for pid in pids:
        command = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "command="],
                                 capture_output=True, text=True, check=False)
        expected = str(PROJECT_ROOT / "scripts/autosave_codex_session.sh")
        args = shlex.split(command.stdout)
        if len(args) < 3 or Path(args[0]).name != "zsh" or args[1:3] != [expected, "--watch"]:
            raise RuntimeError("Autosave worker ownership could not be verified")
    for pid in pids:
        os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 10
    def original_workers_running():
        return bool(set(pids).intersection(autosave_status().watcher_pids))
    while original_workers_running() and time.monotonic() < deadline:
        time.sleep(.1)
    if original_workers_running():
        raise RuntimeError("Owned autosave worker did not stop")


def start_autosave(*, restart: bool = False) -> dict:
    if restart:
        stop_owned_workers()
    status = autosave_status()
    if status.watcher_running:
        return {"ok": status.watcher_count == 1 and status.latest_age_minutes is not None
                and status.latest_age_minutes <= 20 and not status.last_error, "started": False,
                "watcher_count": status.watcher_count}
    logs = PROJECT_ROOT / "logs"
    logs.mkdir(exist_ok=True)
    with (logs / "autosave_worker.log").open("ab") as output:
        started_at = time.time()
        worker = subprocess.Popen(
            ["/bin/zsh", str(PROJECT_ROOT / "scripts/autosave_codex_session.sh"), "--watch"],
            cwd=PROJECT_ROOT, env=worker_environment(), stdin=subprocess.DEVNULL,
            stdout=output, stderr=output, start_new_session=True,
        )
    deadline = time.monotonic() + 20
    info = PROJECT_ROOT / "data/session_autosave/latest_info.txt"
    while time.monotonic() < deadline:
        if worker.poll() is not None:
            return {"ok": False, "started": False, "error": "autosave_worker_exited"}
        if info.exists() and info.stat().st_mtime >= started_at:
            current = autosave_status()
            return {"ok": current.watcher_count == 1 and not current.last_error, "started": True,
                    "pid": worker.pid, "automatic_cleanup": False}
        time.sleep(.1)
    return {"ok": False, "started": True, "pid": worker.pid, "error": "first_save_not_confirmed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--service", action="store_true", help="Foreground launchd worker parent")
    args = parser.parse_args()
    if args.service:
        raise SystemExit(run_service())
    result = start_autosave(restart=args.restart)
    print(json.dumps(result))
    raise SystemExit(0 if result["ok"] else 1)
