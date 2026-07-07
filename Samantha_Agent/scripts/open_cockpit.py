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
FALLBACK_PORTS = range(DEFAULT_PORT + 1, DEFAULT_PORT + 10)


def url_ok(url: str, *, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def port_is_busy(host: str, port: int) -> bool:
    """Return True when this process cannot bind the local Cockpit port.

    A half-stuck Cockpit can hold the port while HTTP connects hang. In that
    state connect_ex is not reliable enough for deciding whether a new server
    can bind, so test the actual bind operation.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return True
        return False


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


def wait_until_ok(url: str, *, attempts: int = 40, delay: float = 0.2) -> bool:
    for _ in range(attempts):
        if url_ok(url):
            return True
        time.sleep(delay)
    return False


def open_or_start_fallback(host: str, *, no_open: bool) -> int:
    for port in FALLBACK_PORTS:
        url = f"http://{host}:{port}"
        log_file = PROJECT_DIR / "data" / "private" / "cockpit" / f"server_{port}.log"

        if url_ok(url):
            if not no_open:
                open_browser(url)
            print(f"Nouzový Samantha Cockpit už běží: {url}")
            return 0

        if port_is_busy(host, port):
            continue

        start_server(host, port, log_file)
        if wait_until_ok(url):
            if not no_open:
                open_browser(url)
            print(f"Nouzový Samantha Cockpit spuštěn: {url}")
            print(f"Standardní port {DEFAULT_PORT} je obsazený, ale neodpovídá; po restartu Macu se má vrátit normální adresa.")
            return 0

        print(f"Nouzový Cockpit se nepodařilo spustit na portu {port}. Log: {log_file}", file=sys.stderr)

    print("Nenašel jsem volný nouzový port pro Samantha Cockpit.", file=sys.stderr)
    return 1


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
        if args.port == DEFAULT_PORT and args.host in {"127.0.0.1", "localhost"}:
            print("Zkouším nouzový lokální port.", file=sys.stderr)
            return open_or_start_fallback(args.host, no_open=args.no_open)
        return 1

    start_server(args.host, args.port, log_file)
    if wait_until_ok(url):
        if not args.no_open:
            open_browser(url)
        print(f"Samantha Cockpit spuštěn: {url}")
        return 0

    print(f"Samantha Cockpit se nepodařilo spustit. Log: {log_file}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
