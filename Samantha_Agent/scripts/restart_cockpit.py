from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8770
SERVER_HEALTH_PATH = "/api/server/health"


def process_command(pid: int) -> str:
    completed = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        capture_output=True,
        text=True,
        timeout=3,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def command_is_cockpit_server(command: str) -> bool:
    script_path = str(PROJECT_DIR / "scripts" / "cockpit_server.py")
    return script_path in command or "scripts/cockpit_server.py" in command


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def port_is_busy(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def url_ok(host: str, port: int, *, timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}{SERVER_HEALTH_PATH}", timeout=timeout) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def wait_for_exit(pid: int, host: str, port: int, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_exists(pid):
            return True
        time.sleep(0.2)
    return not process_exists(pid)


def wait_for_launchd_restart(host: str, port: int, timeout: float = 12.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if url_ok(host, port):
            return True
        time.sleep(0.2)
    return False


def start_cockpit(host: str, port: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(PROJECT_DIR / ".venv" / "bin" / "python"),
            str(PROJECT_DIR / "scripts" / "open_cockpit.py"),
            "--host",
            host,
            "--port",
            str(port),
            "--no-open",
            "--no-fallback",
        ],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )


def restart_cockpit(pid: int, host: str, port: int, delay: float = 0.5) -> int:
    if pid <= 0:
        print("Neplatný PID.", file=sys.stderr)
        return 2
    if delay > 0:
        time.sleep(delay)
    command = process_command(pid)
    if not command_is_cockpit_server(command):
        print(f"PID {pid} nevypadá jako Samantha Cockpit server: {command}", file=sys.stderr)
        return 3
    print(f"Ukončuji ověřený Cockpit PID {pid}: {command}", flush=True)
    os.kill(pid, signal.SIGTERM)
    if not wait_for_exit(pid, host, port):
        print(f"Cockpit PID {pid} se neukončil v bezpečném limitu; nespouštím druhou instanci.", file=sys.stderr)
        return 4
    if wait_for_launchd_restart(host, port):
        print(f"Samantha Cockpit už znovu odpovídá na http://{host}:{port}; nespouštím druhou instanci.", flush=True)
        return 0
    completed = start_cockpit(host, port)
    if completed.stdout.strip():
        print(completed.stdout.strip(), flush=True)
    if completed.stderr.strip():
        print(completed.stderr.strip(), file=sys.stderr, flush=True)
    return completed.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bezpecne restartuje lokalni Samantha Cockpit.")
    parser.add_argument("--pid", type=int, required=True, help="PID overeneho cockpit_server.py procesu.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--delay", type=float, default=0.5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return restart_cockpit(pid=args.pid, host=args.host, port=args.port, delay=args.delay)


if __name__ == "__main__":
    raise SystemExit(main())
