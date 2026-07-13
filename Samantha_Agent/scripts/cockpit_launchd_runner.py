from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PYTHON_BIN = PROJECT_DIR / ".venv" / "bin" / "python"
SERVER_HEALTH_PATH = "/api/server/health"


def url_ok(host: str, port: int, *, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}{SERVER_HEALTH_PATH}", timeout=timeout) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        try:
            with urllib.request.urlopen(f"http://{host}:{port}/", timeout=timeout) as response:
                return 200 <= response.status < 300
        except (OSError, urllib.error.URLError):
            return False


def port_is_busy(host: str, port: int) -> bool:
    """Return True when a new local server cannot bind this port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Cockpit server uses address reuse. Match it here so a closed listener
        # in TIME_WAIT is not mistaken for a live process holding the port.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return True
        return False


def start_cockpit(host: str, port: int) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            str(PYTHON_BIN),
            str(PROJECT_DIR / "scripts" / "cockpit_server.py"),
            "--host",
            host,
            "--port",
            str(port),
        ],
        cwd=str(PROJECT_DIR),
        text=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Long-running launchd supervisor for Samantha Cockpit.")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--check-interval", type=float, default=10.0)
    parser.add_argument("--startup-grace", type=float, default=60.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    process: subprocess.Popen[str] | None = None
    startup_deadline = time.monotonic() + args.startup_grace

    while True:
        if url_ok(args.host, args.port):
            print(f"Samantha Cockpit odpovida na http://{args.host}:{args.port}", flush=True)
            if process and process.poll() is not None:
                process = None
            time.sleep(args.check_interval)
            continue

        if process and process.poll() is None:
            print("Cockpit proces bezi, cekam na HTTP odpoved.", flush=True)
            time.sleep(args.check_interval)
            continue

        process = None
        if port_is_busy(args.host, args.port):
            print(f"Port {args.host}:{args.port} je obsazeny, ale Cockpit neodpovida; cekam.", file=sys.stderr, flush=True)
            time.sleep(args.check_interval)
            continue

        if time.monotonic() < startup_deadline:
            print(f"Startuji Samantha Cockpit na http://{args.host}:{args.port}", flush=True)
        else:
            print(f"Znovu startuji Samantha Cockpit na http://{args.host}:{args.port}", flush=True)
        process = start_cockpit(args.host, args.port)
        time.sleep(args.check_interval)


if __name__ == "__main__":
    raise SystemExit(main())
