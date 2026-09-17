#!/usr/bin/env python3
"""Bounded private-network control for the physical Camino C02b T043 test."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import signal
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_ROOT = PROJECT_ROOT / "data" / "private" / "camino" / "c02b_t043"
DEFAULT_TAILSCALE_CLI = Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale")
DEFAULT_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
DEFAULT_RECEIVER = PROJECT_ROOT / "app" / "camino_chunk_receiver.py"
RECEIVER_MODULE = "app.camino_chunk_receiver"
DEFAULT_PBCOPY = Path("/usr/bin/pbcopy")
SYSTEM_CA_BUNDLE = Path("/etc/ssl/cert.pem")
ROUTE_PATH = "/camino-c02b"
LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class ControlError(RuntimeError):
    """Expected fail-closed condition in the physical-test controller."""


@dataclass(frozen=True)
class ControlConfig:
    state_root: Path = DEFAULT_STATE_ROOT
    tailscale_cli: Path = DEFAULT_TAILSCALE_CLI
    python: Path = DEFAULT_PYTHON
    receiver: Path = DEFAULT_RECEIVER
    pbcopy: Path = DEFAULT_PBCOPY
    port: int = DEFAULT_PORT

    @property
    def current_path(self) -> Path:
        return self.state_root / "current.json"


Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def run_command(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def _checked_json(argv: Sequence[str], runner: Runner = run_command) -> dict[str, Any]:
    completed = runner(argv)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        raise ControlError(detail[-1] if detail else f"command failed: {Path(argv[0]).name}")
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ControlError(f"invalid JSON from {Path(argv[0]).name}") from error
    if not isinstance(value, dict):
        raise ControlError("expected a JSON object")
    return value


def _checked(argv: Sequence[str], runner: Runner = run_command) -> None:
    completed = runner(argv)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        raise ControlError(detail[-1] if detail else f"command failed: {Path(argv[0]).name}")


def _private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise ControlError(f"unsafe private directory: {path.name}")
    os.chmod(path, 0o700)


def _write_private_text(path: Path, value: str, *, exclusive: bool = False) -> None:
    flags = os.O_WRONLY | os.O_CREAT
    flags |= os.O_EXCL if exclusive else os.O_TRUNC
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _write_private_json(path: Path, value: Mapping[str, Any]) -> None:
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(
                json.dumps(dict(value), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _load_state(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError) as error:
        raise ControlError("private T043 state is unreadable") from error
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise ControlError("private T043 state has an unsupported schema")
    return value


def _validate_state_paths(state: Mapping[str, Any], config: ControlConfig) -> None:
    root = config.state_root.resolve()
    for key in ("run_dir", "receiver_root", "receiver_log", "token_path", "serve_before_path"):
        raw = state.get(key)
        if not isinstance(raw, str) or not raw:
            raise ControlError(f"private T043 state is missing {key}")
        candidate = Path(raw)
        if not candidate.is_absolute() or not candidate.resolve().is_relative_to(root):
            raise ControlError(f"private T043 state has an unsafe {key}")
    try:
        pid = int(state["receiver_pid"])
        port = int(state["port"])
    except (KeyError, TypeError, ValueError) as error:
        raise ControlError("private T043 state has invalid process metadata") from error
    if pid <= 1 or port != config.port or state.get("route_path") != ROUTE_PATH:
        raise ControlError("private T043 state does not match the registered test scope")


def _tailnet_state(config: ControlConfig, runner: Runner = run_command) -> dict[str, Any]:
    return _checked_json([str(config.tailscale_cli), "status", "--json"], runner)


def _serve_state(
    config: ControlConfig,
    *,
    funnel: bool = False,
    runner: Runner = run_command,
) -> dict[str, Any]:
    mode = "funnel" if funnel else "serve"
    return _checked_json([str(config.tailscale_cli), mode, "status", "--json"], runner)


def _funnel_enabled(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() == "allowfunnel" and bool(child):
                return True
            if _funnel_enabled(child):
                return True
    elif isinstance(value, list):
        return any(_funnel_enabled(child) for child in value)
    return False


def _handlers(serve: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    web = serve.get("Web", {})
    if not isinstance(web, dict):
        return result
    for endpoint in web.values():
        if not isinstance(endpoint, dict):
            continue
        handlers = endpoint.get("Handlers", {})
        if isinstance(handlers, dict):
            result.update(handlers)
    return result


def _route_proxy(serve: Mapping[str, Any], route_path: str = ROUTE_PATH) -> str | None:
    value = _handlers(serve).get(route_path)
    if not isinstance(value, dict):
        return None
    proxy = value.get("Proxy")
    return proxy if isinstance(proxy, str) else None


def _dns_name(status: Mapping[str, Any]) -> str:
    if status.get("BackendState") != "Running":
        raise ControlError("Tailscale backend is not running")
    own = status.get("Self")
    if not isinstance(own, dict) or own.get("Online") is not True:
        raise ControlError("this Tailscale device is not online")
    dns_name = own.get("DNSName")
    if not isinstance(dns_name, str) or not dns_name.strip("."):
        raise ControlError("Tailscale DNS name is unavailable")
    return dns_name.rstrip(".")


def _ensure_port_available(port: int) -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind((LOOPBACK_HOST, port))
    except OSError as error:
        raise ControlError(f"loopback port {port} is already in use") from error
    finally:
        probe.close()


def _system_tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    if SYSTEM_CA_BUNDLE.is_file():
        context.load_verify_locations(cafile=str(SYSTEM_CA_BUNDLE))
    return context


def _http_json(url: str, token: str, *, timeout: float = 8) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Cache-Control": "no-store"},
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=_system_tls_context() if url.lower().startswith("https://") else None,
        ) as response:
            payload = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        payload = error.read()
        status = error.code
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ControlError("receiver returned invalid JSON") from error
    if not isinstance(value, dict):
        raise ControlError("receiver returned a non-object response")
    return status, value


def _wait_for_health(url: str, token: str, *, attempts: int = 40) -> None:
    last_error = "receiver did not answer"
    for _ in range(attempts):
        try:
            status, body = _http_json(url, token, timeout=1)
            if status == 200 and body.get("scope") == "c02b_synthetic_only":
                return
            last_error = f"unexpected receiver health: {status}"
        except (ControlError, OSError, urllib.error.URLError) as error:
            last_error = str(error)
        time.sleep(0.1)
    raise ControlError(last_error)


def _copy_to_clipboard(value: str, config: ControlConfig) -> None:
    completed = subprocess.run(
        [str(config.pbcopy)],
        input=value,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    if completed.returncode != 0:
        raise ControlError("could not copy the private value to the clipboard")


def _process_command(pid: int) -> str:
    completed = subprocess.run(
        ["/bin/ps", "-p", str(pid), "-o", "command="],
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _owned_receiver_alive(state: Mapping[str, Any], config: ControlConfig) -> bool:
    try:
        pid = int(state["receiver_pid"])
        receiver_root = str(Path(str(state["receiver_root"])))
    except (KeyError, TypeError, ValueError):
        return False
    command = _process_command(pid)
    return bool(
        command
        and f"-m {RECEIVER_MODULE}" in command
        and receiver_root in command
        and f"--port {config.port}" in command
    )


def _terminate_owned_receiver(state: Mapping[str, Any], config: ControlConfig) -> None:
    if not _owned_receiver_alive(state, config):
        return
    pid = int(state["receiver_pid"])
    os.kill(pid, signal.SIGTERM)
    for _ in range(50):
        if not _owned_receiver_alive(state, config):
            return
        time.sleep(0.1)
    raise ControlError("owned receiver did not stop after SIGTERM")


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"))


def _new_run_directory(config: ControlConfig) -> Path:
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    path = config.state_root / f"run_{stamp}_{secrets.token_hex(3)}"
    path.mkdir(mode=0o700)
    return path


def start(config: ControlConfig = ControlConfig(), runner: Runner = run_command) -> str:
    for required in (config.tailscale_cli, config.python, config.receiver, config.pbcopy):
        if not required.exists():
            raise ControlError(f"required executable or file is missing: {required.name}")
    _private_directory(config.state_root)
    previous = _load_state(config.current_path)
    if previous is not None and previous.get("phase") in {"starting", "ready"}:
        raise ControlError("a T043 run is already active; use status or stop")

    status = _tailnet_state(config, runner)
    dns_name = _dns_name(status)
    serve_before = _serve_state(config, runner=runner)
    funnel_before = _serve_state(config, funnel=True, runner=runner)
    if _funnel_enabled(funnel_before):
        raise ControlError("Tailscale Funnel is active; T043 start is blocked")
    if ROUTE_PATH in _handlers(serve_before):
        raise ControlError(f"Serve path {ROUTE_PATH} already exists")
    _ensure_port_available(config.port)

    run_dir = _new_run_directory(config)
    receiver_root = run_dir / "receiver"
    _private_directory(receiver_root)
    token_path = run_dir / "token.txt"
    token = secrets.token_urlsafe(48)
    _write_private_text(token_path, token, exclusive=True)
    _write_private_json(run_dir / "serve-before.json", serve_before)
    log_path = run_dir / "receiver.log"
    log_descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(log_descriptor, 0o600)
    receiver_argv = [
        str(config.python),
        "-m",
        RECEIVER_MODULE,
        "--host",
        LOOPBACK_HOST,
        "--port",
        str(config.port),
        "--root",
        str(receiver_root),
        "--read-delay-ms-per-mib",
        "1000",
        "--verify-delay-seconds",
        "5",
    ]
    environment = os.environ.copy()
    environment["CAMINO_C02B_TOKEN"] = token
    process: subprocess.Popen[bytes] | None = None
    route_added = False
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        process = subprocess.Popen(
            receiver_argv,
            cwd=str(PROJECT_ROOT),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log_descriptor,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
        os.close(log_descriptor)
        log_descriptor = -1
        _wait_for_health(f"http://{LOOPBACK_HOST}:{config.port}/healthz", token)
        serve_add = [
            str(config.tailscale_cli),
            "serve",
            "--yes",
            "--bg",
            "--https=443",
            f"--set-path={ROUTE_PATH}",
            f"http://{LOOPBACK_HOST}:{config.port}",
        ]
        _checked(serve_add, runner)
        route_added = True
        serve_after = _serve_state(config, runner=runner)
        expected_proxy = f"http://{LOOPBACK_HOST}:{config.port}"
        if _route_proxy(serve_after) != expected_proxy:
            raise ControlError("Serve did not install the exact Camino route")
        if _funnel_enabled(_serve_state(config, funnel=True, runner=runner)):
            raise ControlError("Funnel became active unexpectedly")

        base_url = f"https://{dns_name}{ROUTE_PATH}"
        remote_status, remote_body = _http_json(f"{base_url}/healthz", token)
        if remote_status != 200 or remote_body.get("scope") != "c02b_synthetic_only":
            raise ControlError("private HTTPS health check failed")
        cockpit_request = urllib.request.Request(f"https://{dns_name}/api/server/health")
        with urllib.request.urlopen(
            cockpit_request,
            timeout=8,
            context=_system_tls_context(),
        ) as response:
            if response.status != 200:
                raise ControlError("Cockpit root health changed during T043 setup")

        state: dict[str, Any] = {
            "schema": 1,
            "phase": "ready",
            "started_at": started_at,
            "run_dir": str(run_dir),
            "receiver_pid": process.pid,
            "receiver_root": str(receiver_root),
            "receiver_log": str(log_path),
            "token_path": str(token_path),
            "base_url": base_url,
            "route_path": ROUTE_PATH,
            "port": config.port,
            "serve_before_path": str(run_dir / "serve-before.json"),
        }
        _write_private_json(run_dir / "run.json", state)
        _write_private_json(config.current_path, state)
        _copy_to_clipboard(base_url, config)
        return (
            "READY: private HTTPS route and loopback receiver are active.\n"
            "The private server URL is now in the Mac clipboard.\n"
            "Funnel remains disabled and Cockpit health is HTTP 200."
        )
    except Exception:
        if route_added:
            try:
                _checked(
                    [
                        str(config.tailscale_cli),
                        "serve",
                        "--yes",
                        "--https=443",
                        f"--set-path={ROUTE_PATH}",
                        "off",
                    ],
                    runner,
                )
            except ControlError:
                pass
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        raise
    finally:
        if log_descriptor >= 0:
            os.close(log_descriptor)


def copy_token(config: ControlConfig = ControlConfig(), runner: Runner = run_command) -> str:
    state = _load_state(config.current_path)
    if state is None or state.get("phase") != "ready":
        raise ControlError("no ready T043 run exists")
    _validate_state_paths(state, config)
    if not _owned_receiver_alive(state, config):
        raise ControlError("the owned receiver is not running")
    serve = _serve_state(config, runner=runner)
    if _route_proxy(serve) != f"http://{LOOPBACK_HOST}:{config.port}":
        raise ControlError("the exact private Camino route is not active")
    if _funnel_enabled(_serve_state(config, funnel=True, runner=runner)):
        raise ControlError("Funnel is active; token copy is blocked")
    token_path = Path(str(state.get("token_path", "")))
    if token_path.is_symlink() or not token_path.is_file():
        raise ControlError("the private token file is unavailable")
    token = token_path.read_text(encoding="utf-8")
    if len(token) < 32:
        raise ControlError("the private token is invalid")
    _copy_to_clipboard(token, config)
    return "TOKEN_READY: the ephemeral bearer token replaced the URL in the Mac clipboard."


def _evidence(state: Mapping[str, Any]) -> dict[str, Any]:
    receiver_root = Path(str(state.get("receiver_root", "")))
    objects = receiver_root / "objects"
    receipts = receiver_root / "receipts"
    object_paths = sorted(
        path for path in objects.glob("*.bin") if path.is_file() and not path.is_symlink()
    )
    receipt_paths = sorted(
        path for path in receipts.glob("*.json") if path.is_file() and not path.is_symlink()
    )
    result: dict[str, Any] = {
        "object_count": len(object_paths),
        "receipt_count": len(receipt_paths),
        "verified_match": False,
        "byte_count": 0,
    }
    if len(object_paths) != 1 or len(receipt_paths) != 1:
        return result
    try:
        receipt = json.loads(receipt_paths[0].read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return result
    if not isinstance(receipt, dict):
        return result
    digest = hashlib.sha256()
    with object_paths[0].open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    byte_count = object_paths[0].stat().st_size
    result["byte_count"] = byte_count
    result["verified_match"] = bool(
        receipt.get("state") == "verified"
        and receipt.get("byte_count") == byte_count
        and receipt.get("sha256") == digest.hexdigest()
    )
    return result


def status(config: ControlConfig = ControlConfig(), runner: Runner = run_command) -> str:
    state = _load_state(config.current_path)
    if state is None:
        return "INACTIVE: no C02b T043 run has been prepared."
    _validate_state_paths(state, config)
    serve = _serve_state(config, runner=runner)
    funnel = _serve_state(config, funnel=True, runner=runner)
    evidence = _evidence(state)
    route_exact = _route_proxy(serve) == f"http://{LOOPBACK_HOST}:{config.port}"
    receiver_alive = _owned_receiver_alive(state, config)
    return "\n".join(
        [
            f"phase={state.get('phase', 'unknown')}",
            f"receiver_alive={str(receiver_alive).lower()}",
            f"private_route_exact={str(route_exact).lower()}",
            f"funnel_enabled={str(_funnel_enabled(funnel)).lower()}",
            f"object_count={evidence['object_count']}",
            f"receipt_count={evidence['receipt_count']}",
            f"verified_match={str(evidence['verified_match']).lower()}",
            f"verified_byte_count={evidence['byte_count']}",
        ]
    )


def stop(config: ControlConfig = ControlConfig(), runner: Runner = run_command) -> str:
    state = _load_state(config.current_path)
    if state is None:
        raise ControlError("no C02b T043 run exists")
    _validate_state_paths(state, config)
    serve_now = _serve_state(config, runner=runner)
    route = _route_proxy(serve_now)
    expected = f"http://{LOOPBACK_HOST}:{config.port}"
    if route not in (None, expected):
        raise ControlError("Camino route points elsewhere; refusing to remove it")
    if route == expected:
        _checked(
            [
                str(config.tailscale_cli),
                "serve",
                "--yes",
                "--https=443",
                f"--set-path={ROUTE_PATH}",
                "off",
            ],
            runner,
        )
    _terminate_owned_receiver(state, config)
    serve_after = _serve_state(config, runner=runner)
    before_path = Path(str(state.get("serve_before_path", "")))
    try:
        serve_before = json.loads(before_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
        raise ControlError("cannot compare the original Serve configuration") from error
    if not isinstance(serve_before, dict) or _canonical(serve_after) != _canonical(serve_before):
        raise ControlError("Serve configuration differs from the saved pre-test state")
    if _funnel_enabled(_serve_state(config, funnel=True, runner=runner)):
        raise ControlError("Funnel is active after T043 stop")
    completed = dict(state)
    completed["phase"] = "stopped"
    completed["stopped_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _write_private_json(Path(str(state["run_dir"])) / "run.json", completed)
    _write_private_json(config.current_path, completed)
    evidence = _evidence(completed)
    return (
        "STOPPED: Camino Serve path removed and the owned receiver stopped.\n"
        "Original Serve configuration restored exactly; Funnel remains disabled.\n"
        f"Evidence: objects={evidence['object_count']}, receipts={evidence['receipt_count']}, "
        f"verified_match={str(evidence['verified_match']).lower()}, bytes={evidence['byte_count']}."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "copy-token", "status", "stop"))
    args = parser.parse_args(argv)
    try:
        if args.action == "start":
            result = start()
        elif args.action == "copy-token":
            result = copy_token()
        elif args.action == "status":
            result = status()
        else:
            result = stop()
    except (ControlError, OSError, subprocess.SubprocessError, urllib.error.URLError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
