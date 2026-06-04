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
DEFAULT_PORT = 8770


def url_ok(url: str, *, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def port_is_busy(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def open_browser(url: str) -> None:
    subprocess.run(["/usr/bin/open", url], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_server(host: str, port: int, log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_file.open("a", encoding="utf-8")
    subprocess.Popen(
        [
            str(PROJECT_DIR / ".venv" / "bin" / "python"),
            str(PROJECT_DIR / "scripts" / "cockpit_server.py"),
            "--host",
            host,
            "--port",
            str(port),
        ],
        cwd=str(PROJECT_DIR),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spusti nebo otevri lokalni Samantha Cockpit.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-open", action="store_true", help="Jen spustit server, neotevirat prohlizec.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    url = f"http://{args.host}:{args.port}"
    log_file = PROJECT_DIR / "data" / "private" / "cockpit" / "server.log"

    if url_ok(url):
        if not args.no_open:
            open_browser(url)
        print(f"Samantha Cockpit už běží: {url}")
        return 0

    if port_is_busy(args.host, args.port):
        print(f"Port {args.port} je obsazený, ale hlavní stránka Cockpitu neodpovídá na {url}.", file=sys.stderr)
        print("Neukončuji existující proces automaticky.", file=sys.stderr)
        return 1

    start_server(args.host, args.port, log_file)
    for _ in range(40):
        if url_ok(url):
            if not args.no_open:
                open_browser(url)
            print(f"Samantha Cockpit spuštěn: {url}")
            return 0
        time.sleep(0.2)

    print(f"Samantha Cockpit se nepodařilo spustit. Log: {log_file}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
