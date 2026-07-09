from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PORT = 8770
FALLBACK_PORTS = range(DEFAULT_PORT + 1, DEFAULT_PORT + 10)
READY_PATHS = ("/", "/api/status", "/api/recovery/status", "/api/web-apps")
CODE_STAMP_PATHS = (
    PROJECT_DIR / "app" / "cockpit.py",
    PROJECT_DIR / "scripts" / "cockpit_server.py",
)


def cockpit_code_stamp(paths: tuple[Path, ...] = CODE_STAMP_PATHS) -> str:
    digest = hashlib.sha256()
    for path in paths:
        try:
            stat = path.stat()
        except OSError:
            digest.update(f"{path}:missing\n".encode("utf-8"))
            continue
        digest.update(f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}\n".encode("utf-8"))
    return digest.hexdigest()[:16]


def url_ok(url: str, *, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def endpoint_ok(host: str, port: int, path: str, *, timeout: float = 4.0) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}{path}", timeout=timeout) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def server_ready(host: str, port: int) -> bool:
    return all(endpoint_ok(host, port, path) for path in READY_PATHS)


def status_payload(host: str, port: int, *, timeout: float = 1.5) -> dict[str, object] | None:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/api/status", timeout=timeout) as response:
            if not 200 <= response.status < 300:
                return None
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError, urllib.error.URLError):
        return None
    return payload if isinstance(payload, dict) else None


def server_code_stamp(payload: dict[str, object] | None) -> str:
    if not payload:
        return ""
    server = payload.get("server")
    if not isinstance(server, dict):
        return ""
    code_stamp = server.get("code_stamp")
    return code_stamp if isinstance(code_stamp, str) else ""


def server_is_current(payload: dict[str, object] | None, expected_stamp: str | None = None) -> bool:
    return bool(server_code_stamp(payload) and server_code_stamp(payload) == (expected_stamp or cockpit_code_stamp()))


def process_command(pid: int) -> str:
    try:
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def command_is_cockpit_server(command: str) -> bool:
    script_path = str(PROJECT_DIR / "scripts" / "cockpit_server.py")
    return script_path in command or "scripts/cockpit_server.py" in command


def listening_pids(host: str, port: int) -> list[int]:
    target = f"-iTCP@{host}:{port}" if host not in {"0.0.0.0", "::"} else f"-iTCP:{port}"
    try:
        completed = subprocess.run(
            ["lsof", "-nP", target, "-sTCP:LISTEN", "-t"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    pids: list[int] = []
    for line in completed.stdout.splitlines():
        try:
            pids.append(int(line.strip()))
        except ValueError:
            continue
    return pids


def listening_cockpit_pid(host: str, port: int) -> int | None:
    for pid in listening_pids(host, port):
        if command_is_cockpit_server(process_command(pid)):
            return pid
    return None


def restart_cockpit_pid(pid: int, host: str, port: int) -> bool:
    try:
        completed = subprocess.run(
            [
                str(PROJECT_DIR / ".venv" / "bin" / "python"),
                str(PROJECT_DIR / "scripts" / "restart_cockpit.py"),
                "--pid",
                str(pid),
                "--host",
                host,
                "--port",
                str(port),
                "--delay",
                "0",
            ],
            cwd=str(PROJECT_DIR),
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Cockpit restart se nepodařilo spustit: {exc}", file=sys.stderr)
        return False
    if completed.returncode == 0:
        return True
    print("Cockpit restart worker skončil chybou; ještě krátce čekám, jestli server nezvedl launchd.", file=sys.stderr)
    return wait_until_current(host, port, attempts=60, delay=0.5)


def wait_until_current(host: str, port: int, *, attempts: int = 40, delay: float = 0.2) -> bool:
    expected_stamp = cockpit_code_stamp()
    for _ in range(attempts):
        if server_is_current(status_payload(host, port), expected_stamp):
            return True
        time.sleep(delay)
    return False


def ensure_current_server(host: str, port: int) -> bool:
    expected_stamp = cockpit_code_stamp()
    payload = status_payload(host, port)
    if server_is_current(payload, expected_stamp):
        return True

    current_stamp = server_code_stamp(payload)
    if current_stamp:
        print(f"Cockpit na portu {port} běží se starším kódem; restartuji ho před otevřením.", flush=True)
    else:
        print(f"Cockpit na portu {port} nehlásí otisk kódu; restartuji ho před otevřením.", flush=True)

    pid = listening_cockpit_pid(host, port)
    if pid is None:
        print(f"Port {port} odpovídá, ale nenašel jsem ověřený cockpit_server.py proces; neotvírám neověřený server.", file=sys.stderr)
        return False
    if not restart_cockpit_pid(pid, host, port):
        return False
    return wait_until_current(host, port)


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


def fresh_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("cockpit_launch", str(int(time.time()))))
    return urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))


def open_browser(url: str) -> None:
    subprocess.run(["/usr/bin/open", fresh_url(url)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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


def wait_until_ready(host: str, port: int, *, attempts: int = 30, delay: float = 0.5) -> bool:
    stable_hits = 0
    for _ in range(attempts):
        if server_ready(host, port):
            stable_hits += 1
            if stable_hits >= 2:
                return True
        else:
            stable_hits = 0
        time.sleep(delay)
    return False


def open_or_start_fallback(host: str, *, no_open: bool) -> int:
    for port in FALLBACK_PORTS:
        url = f"http://{host}:{port}"
        log_file = PROJECT_DIR / "data" / "private" / "cockpit" / f"server_{port}.log"

        if url_ok(url):
            if not ensure_current_server(host, port):
                return 1
            if not wait_until_ready(host, port):
                print(f"Nouzový Cockpit na portu {port} odpovídá neúplně; neotvírám nestabilní stránku.", file=sys.stderr)
                return 1
            if not no_open:
                open_browser(url)
            print(f"Nouzový Samantha Cockpit už běží: {url}")
            return 0

        if port_is_busy(host, port):
            continue

        start_server(host, port, log_file)
        if wait_until_ready(host, port):
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
    parser.add_argument("--no-fallback", action="store_true", help="Pri obsazenem cilovem portu neskakat na nouzovy port.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    url = f"http://{args.host}:{args.port}"
    log_file = PROJECT_DIR / "data" / "private" / "cockpit" / "server.log"

    if url_ok(url):
        if not ensure_current_server(args.host, args.port):
            return 1
        if not wait_until_ready(args.host, args.port):
            print(f"Samantha Cockpit na {url} odpovídá neúplně; neotvírám nestabilní stránku.", file=sys.stderr)
            return 1
        if not args.no_open:
            open_browser(url)
        print(f"Samantha Cockpit už běží: {url}")
        return 0

    if port_is_busy(args.host, args.port):
        print(f"Port {args.port} je obsazený, ale hlavní stránka Cockpitu neodpovídá na {url}.", file=sys.stderr)
        print("Neukončuji existující proces automaticky.", file=sys.stderr)
        if not args.no_fallback and args.port == DEFAULT_PORT and args.host in {"127.0.0.1", "localhost"}:
            print("Zkouším nouzový lokální port.", file=sys.stderr)
            return open_or_start_fallback(args.host, no_open=args.no_open)
        return 1

    start_server(args.host, args.port, log_file)
    if wait_until_ready(args.host, args.port):
        if not args.no_open:
            open_browser(url)
        print(f"Samantha Cockpit spuštěn: {url}")
        return 0

    print(f"Samantha Cockpit se nepodařilo spustit. Log: {log_file}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
