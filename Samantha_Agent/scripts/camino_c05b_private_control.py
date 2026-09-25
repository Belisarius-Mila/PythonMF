#!/usr/bin/env python3
"""Control one session-owned private C05a service for Camino C05b acceptance."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import signal
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from camino.domain.model import ContractError
from camino.domain.revision_store import RevisionStore
from camino.server.auth import RevocableTokenStore
from scripts import camino_c02b_t043_control as network


DEFAULT_STATE_ROOT = (
    Path.home() / "Library" / "Application Support" / "PythonMF" / "Camino" / "C05bAcceptance"
)
DEFAULT_TAILSCALE_CLI = Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale")
DEFAULT_PYTHON = Path("/private/tmp/camino-c05a-venv/bin/python")
DEFAULT_PBCOPY = Path("/usr/bin/pbcopy")
SERVER_MODULE = "camino.server.main"
ROUTE_PATH = "/camino-api"
LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8767
FINALIZE_DELAY_SECONDS = 5
STORAGE_FAULT_RESERVE_BYTES = 9_000_000_000_000_000_000


class ControlError(RuntimeError):
    """Expected fail-closed condition in the private C05b controller."""


@dataclass(frozen=True)
class ControlConfig:
    state_root: Path = DEFAULT_STATE_ROOT
    tailscale_cli: Path = DEFAULT_TAILSCALE_CLI
    python: Path = DEFAULT_PYTHON
    pbcopy: Path = DEFAULT_PBCOPY
    port: int = DEFAULT_PORT

    @property
    def current_path(self) -> Path:
        return self.state_root / "current.json"


Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def run_command(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv), cwd=str(PROJECT_ROOT), text=True, capture_output=True,
        timeout=30, check=False,
    )


def _private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise ControlError(f"unsafe private directory: {path.name}")
    os.chmod(path, 0o700)


def _write_private_text(path: Path, value: str) -> None:
    network._write_private_text(path, value, exclusive=True)


def _write_private_json(path: Path, value: Mapping[str, Any]) -> None:
    network._write_private_json(path, value)


def _load_state(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError) as error:
        raise ControlError("private Camino C05b state is unreadable") from error
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise ControlError("private Camino C05b state has an unsupported schema")
    return value


def _validate_state_paths(state: Mapping[str, Any], config: ControlConfig) -> None:
    root = config.state_root.resolve()
    for key in (
        "run_dir", "metadata_db", "auth_db", "media_db", "media_root",
        "server_log", "token_path", "serve_before_path",
    ):
        raw = state.get(key)
        if not isinstance(raw, str) or not raw:
            raise ControlError(f"private C05b state is missing {key}")
        candidate = Path(raw)
        if not candidate.is_absolute() or not candidate.resolve().is_relative_to(root):
            raise ControlError(f"private C05b state has an unsafe {key}")
    try:
        pid = int(state["server_pid"])
        port = int(state["port"])
    except (KeyError, TypeError, ValueError) as error:
        raise ControlError("private C05b state has invalid process metadata") from error
    if pid <= 1 or port != config.port or state.get("route_path") != ROUTE_PATH:
        raise ControlError("private C05b state does not match the registered scope")


def _checked_json(argv: Sequence[str], runner: Runner) -> dict[str, Any]:
    try:
        return network._checked_json(argv, runner)
    except network.ControlError as error:
        raise ControlError(str(error)) from error


def _checked(argv: Sequence[str], runner: Runner) -> None:
    try:
        network._checked(argv, runner)
    except network.ControlError as error:
        raise ControlError(str(error)) from error


def _tailnet_state(config: ControlConfig, runner: Runner) -> dict[str, Any]:
    return _checked_json([str(config.tailscale_cli), "status", "--json"], runner)


def _serve_state(
    config: ControlConfig, *, funnel: bool = False, runner: Runner,
) -> dict[str, Any]:
    mode = "funnel" if funnel else "serve"
    return _checked_json([str(config.tailscale_cli), mode, "status", "--json"], runner)


def _route_proxy(serve: Mapping[str, Any]) -> str | None:
    return network._route_proxy(serve, ROUTE_PATH)


def _funnel_enabled(value: Any) -> bool:
    return network._funnel_enabled(value)


def _process_command(pid: int) -> str:
    return network._process_command(pid)


def _owned_server_alive(state: Mapping[str, Any], config: ControlConfig) -> bool:
    try:
        pid = int(state["server_pid"])
    except (KeyError, TypeError, ValueError):
        return False
    command = _process_command(pid)
    return bool(
        command and f"-m {SERVER_MODULE}" in command
        and f"--host {LOOPBACK_HOST}" in command
        and f"--port {config.port}" in command
    )


def _terminate_owned_server(state: Mapping[str, Any], config: ControlConfig) -> None:
    if not _owned_server_alive(state, config):
        return
    pid = int(state["server_pid"])
    os.kill(pid, signal.SIGTERM)
    for _ in range(80):
        if not _owned_server_alive(state, config):
            return
        time.sleep(0.1)
    raise ControlError("owned C05a server did not stop after SIGTERM")


def _http_json(url: str, token: str, *, timeout: float = 8) -> tuple[int, dict[str, Any]]:
    try:
        return network._http_json(url, token, timeout=timeout)
    except network.ControlError as error:
        raise ControlError(str(error)) from error


def _wait_for_health(url: str, token: str, *, attempts: int = 80) -> None:
    last_error = "C05a server did not answer"
    for _ in range(attempts):
        try:
            status, body = _http_json(url, token, timeout=1)
            if status == 200 and body.get("scope") == "c05a_private_owner":
                return
            last_error = f"unexpected C05a health: {status}"
        except (ControlError, OSError, urllib.error.URLError) as error:
            last_error = str(error)
        time.sleep(0.1)
    raise ControlError(last_error)


def _copy_to_clipboard(value: str, config: ControlConfig) -> None:
    completed = subprocess.run(
        [str(config.pbcopy)], input=value, text=True, capture_output=True,
        timeout=5, check=False,
    )
    if completed.returncode != 0:
        raise ControlError("could not copy the private value to the clipboard")


def _new_run_directory(config: ControlConfig) -> Path:
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    path = config.state_root / f"run_{stamp}_{secrets.token_hex(3)}"
    path.mkdir(mode=0o700)
    return path


def _cockpit_root_healthy(dns_name: str) -> bool:
    request = urllib.request.Request(f"https://{dns_name}/api/server/health")
    with urllib.request.urlopen(
        request, timeout=8, context=network._system_tls_context(),
    ) as response:
        return response.status == 200


def _state_payload(
    *, run_dir: Path, server_pid: int, token_id: str, base_url: str,
    config: ControlConfig, started_at: str,
) -> dict[str, Any]:
    return {
        "schema": 1,
        "phase": "ready",
        "started_at": started_at,
        "run_dir": str(run_dir),
        "server_pid": server_pid,
        "metadata_db": str(run_dir / "metadata.sqlite"),
        "auth_db": str(run_dir / "auth.sqlite"),
        "media_db": str(run_dir / "media.sqlite"),
        "media_root": str(run_dir / "media"),
        "server_log": str(run_dir / "server.log"),
        "token_path": str(run_dir / "token.txt"),
        "token_id": token_id,
        "base_url": base_url,
        "route_path": ROUTE_PATH,
        "port": config.port,
        "storage_fault": False,
        "finalize_delay_seconds": FINALIZE_DELAY_SECONDS,
        "serve_before_path": str(run_dir / "serve-before.json"),
    }


def _server_environment(run_dir: Path, *, storage_fault: bool) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({
        "CAMINO_C05A_METADATA_DB": str(run_dir / "metadata.sqlite"),
        "CAMINO_VIEWER_ENABLED": "0",  # acceptance workflow never publishes a Viewer
        "CAMINO_C05A_AUTH_DB": str(run_dir / "auth.sqlite"),
        "CAMINO_C05A_MEDIA_DB": str(run_dir / "media.sqlite"),
        "CAMINO_C05A_MEDIA_ROOT": str(run_dir / "media"),
        "CAMINO_C05A_FINALIZE_DELAY_SECONDS": str(FINALIZE_DELAY_SECONDS),
        "CAMINO_C05A_RESERVE_BYTES": str(
            STORAGE_FAULT_RESERVE_BYTES if storage_fault else 512 * 1024 * 1024
        ),
    })
    return environment


def _spawn_server(
    run_dir: Path, token: str, config: ControlConfig, *, storage_fault: bool,
) -> subprocess.Popen[bytes]:
    log_path = run_dir / "server.log"
    log_descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(log_descriptor, 0o600)
    argv = [
        str(config.python), "-m", SERVER_MODULE,
        "--host", LOOPBACK_HOST, "--port", str(config.port),
    ]
    try:
        process = subprocess.Popen(
            argv, cwd=str(PROJECT_ROOT),
            env=_server_environment(run_dir, storage_fault=storage_fault),
            stdin=subprocess.DEVNULL, stdout=log_descriptor, stderr=subprocess.STDOUT,
            start_new_session=True, close_fds=True,
        )
    finally:
        os.close(log_descriptor)
    try:
        _wait_for_health(f"http://{LOOPBACK_HOST}:{config.port}/healthz", token)
    except Exception:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        raise
    return process


def start(config: ControlConfig = ControlConfig(), runner: Runner = run_command) -> str:
    for required in (config.tailscale_cli, config.python, config.pbcopy):
        if not required.exists():
            raise ControlError(f"required executable is missing: {required.name}")
    _private_directory(config.state_root)
    previous = _load_state(config.current_path)
    if previous is not None and previous.get("phase") in {"starting", "ready"}:
        raise ControlError("a private C05b service is already active; use status or stop")

    tailnet = _tailnet_state(config, runner)
    try:
        dns_name = network._dns_name(tailnet)
    except network.ControlError as error:
        raise ControlError(str(error)) from error
    serve_before = _serve_state(config, runner=runner)
    funnel_before = _serve_state(config, funnel=True, runner=runner)
    if _funnel_enabled(funnel_before):
        raise ControlError("Tailscale Funnel is active; C05b start is blocked")
    if ROUTE_PATH in network._handlers(serve_before):
        raise ControlError(f"Serve path {ROUTE_PATH} already exists")
    try:
        network._ensure_port_available(config.port)
    except network.ControlError as error:
        raise ControlError(str(error)) from error

    run_dir = _new_run_directory(config)
    media_root = run_dir / "media"
    _private_directory(media_root)
    token = secrets.token_urlsafe(48)
    token_path = run_dir / "token.txt"
    _write_private_text(token_path, token)
    auth_db = run_dir / "auth.sqlite"
    token_store = RevocableTokenStore(auth_db)
    token_id = token_store.add(token, label="C05b physical acceptance")
    _write_private_json(run_dir / "serve-before.json", serve_before)

    process: subprocess.Popen[bytes] | None = None
    route_added = False
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        process = _spawn_server(run_dir, token, config, storage_fault=False)
        _checked([
            str(config.tailscale_cli), "serve", "--yes", "--bg", "--https=443",
            f"--set-path={ROUTE_PATH}", f"http://{LOOPBACK_HOST}:{config.port}",
        ], runner)
        route_added = True
        serve_after = _serve_state(config, runner=runner)
        if _route_proxy(serve_after) != f"http://{LOOPBACK_HOST}:{config.port}":
            raise ControlError("Serve did not install the exact Camino C05b route")
        if _funnel_enabled(_serve_state(config, funnel=True, runner=runner)):
            raise ControlError("Funnel became active unexpectedly")

        base_url = f"https://{dns_name}{ROUTE_PATH}"
        remote_status, remote_body = _http_json(f"{base_url}/healthz", token)
        if remote_status != 200 or remote_body.get("scope") != "c05a_private_owner":
            raise ControlError("private HTTPS C05a health check failed")
        if not _cockpit_root_healthy(dns_name):
            raise ControlError("Cockpit root health changed during C05b setup")

        state = _state_payload(
            run_dir=run_dir, server_pid=process.pid, token_id=token_id,
            base_url=base_url, config=config, started_at=started_at,
        )
        _write_private_json(run_dir / "run.json", state)
        _write_private_json(config.current_path, state)
        _copy_to_clipboard(base_url, config)
        return (
            "READY: session-owned C05a service and private HTTPS route are active.\n"
            "The private server URL is now in the Mac clipboard.\n"
            "Funnel remains disabled and Cockpit root health is HTTP 200."
        )
    except Exception:
        if route_added:
            try:
                _checked([
                    str(config.tailscale_cli), "serve", "--yes", "--https=443",
                    f"--set-path={ROUTE_PATH}", "off",
                ], runner)
            except ControlError:
                pass
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        try:
            token_store.revoke(token_id)
        except Exception:
            pass
        raise


def set_storage_fault(
    enabled: bool, config: ControlConfig = ControlConfig(), runner: Runner = run_command,
) -> str:
    state = _load_state(config.current_path)
    if state is None or state.get("phase") != "ready":
        raise ControlError("no ready private C05b service exists")
    _validate_state_paths(state, config)
    if _route_proxy(_serve_state(config, runner=runner)) != f"http://{LOOPBACK_HOST}:{config.port}":
        raise ControlError("the exact private Camino route is not active")
    if _funnel_enabled(_serve_state(config, funnel=True, runner=runner)):
        raise ControlError("Funnel is active; storage mode change is blocked")
    token_path = Path(str(state["token_path"]))
    token = token_path.read_text(encoding="utf-8")
    run_dir = Path(str(state["run_dir"]))
    _terminate_owned_server(state, config)
    try:
        process = _spawn_server(run_dir, token, config, storage_fault=enabled)
    except Exception:
        process = _spawn_server(run_dir, token, config, storage_fault=False)
        recovered = dict(state)
        recovered["server_pid"] = process.pid
        recovered["storage_fault"] = False
        _write_private_json(run_dir / "run.json", recovered)
        _write_private_json(config.current_path, recovered)
        raise
    updated = dict(state)
    updated["server_pid"] = process.pid
    updated["storage_fault"] = enabled
    updated["storage_mode_changed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _write_private_json(run_dir / "run.json", updated)
    _write_private_json(config.current_path, updated)
    return (
        "STORAGE_FAULT_ON: new media writes will fail closed with insufficient_storage."
        if enabled else
        "STORAGE_FAULT_OFF: normal reserved-space policy is active again."
    )


def rotate_epoch(
    config: ControlConfig = ControlConfig(), runner: Runner = run_command,
) -> str:
    state = _load_state(config.current_path)
    if state is None or state.get("phase") != "ready":
        raise ControlError("no ready private C05b service exists")
    _validate_state_paths(state, config)
    if not _owned_server_alive(state, config):
        raise ControlError("the owned C05a server is not running")
    if _route_proxy(_serve_state(config, runner=runner)) != f"http://{LOOPBACK_HOST}:{config.port}":
        raise ControlError("the exact private Camino route is not active")
    if _funnel_enabled(_serve_state(config, funnel=True, runner=runner)):
        raise ControlError("Funnel is active; epoch rotation is blocked")
    result = RevisionStore(Path(str(state["metadata_db"]))).rotate_epoch_for_restore()
    if not result.get("reconciliation_required") or not result.get("exports_blocked"):
        raise ControlError("server did not enter the required fail-closed restore state")
    updated = dict(state)
    updated["epoch_rotated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _write_private_json(Path(str(state["run_dir"])) / "run.json", updated)
    _write_private_json(config.current_path, updated)
    return (
        "EPOCH_ROTATED: acceptance server requires inventory reconciliation and exports remain blocked."
    )


def copy_token(config: ControlConfig = ControlConfig(), runner: Runner = run_command) -> str:
    state = _load_state(config.current_path)
    if state is None or state.get("phase") != "ready":
        raise ControlError("no ready private C05b service exists")
    _validate_state_paths(state, config)
    if not _owned_server_alive(state, config):
        raise ControlError("the owned C05a server is not running")
    if _route_proxy(_serve_state(config, runner=runner)) != f"http://{LOOPBACK_HOST}:{config.port}":
        raise ControlError("the exact private Camino route is not active")
    if _funnel_enabled(_serve_state(config, funnel=True, runner=runner)):
        raise ControlError("Funnel is active; token copy is blocked")
    token_path = Path(str(state["token_path"]))
    if token_path.is_symlink() or not token_path.is_file() or token_path.stat().st_mode & 0o077:
        raise ControlError("the private token file is unavailable or permissive")
    token = token_path.read_text(encoding="utf-8")
    if len(token.encode("utf-8")) < 32:
        raise ControlError("the private token is invalid")
    _copy_to_clipboard(token, config)
    return "TOKEN_READY: the private token replaced the URL in the Mac clipboard."


def copy_url(config: ControlConfig = ControlConfig(), runner: Runner = run_command) -> str:
    state = _load_state(config.current_path)
    if state is None or state.get("phase") != "ready":
        raise ControlError("no ready private C05b service exists")
    _validate_state_paths(state, config)
    if not _owned_server_alive(state, config):
        raise ControlError("the owned C05a server is not running")
    if _route_proxy(_serve_state(config, runner=runner)) != f"http://{LOOPBACK_HOST}:{config.port}":
        raise ControlError("the exact private Camino route is not active")
    if _funnel_enabled(_serve_state(config, funnel=True, runner=runner)):
        raise ControlError("Funnel is active; URL copy is blocked")
    base_url = state.get("base_url")
    if (
        not isinstance(base_url, str)
        or not base_url.startswith("https://")
        or not base_url.endswith(ROUTE_PATH)
        or any(character.isspace() for character in base_url)
    ):
        raise ControlError("the private server URL is invalid")
    _copy_to_clipboard(base_url, config)
    return "URL_READY: the current private HTTPS address is in the Mac clipboard."


def _scalar(database: Path, query: str, parameters: tuple[Any, ...] = ()) -> int:
    if database.is_symlink() or not database.is_file():
        return -1
    uri = f"file:{database}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=2) as connection:
            value = connection.execute(query, parameters).fetchone()
        return int(value[0]) if value is not None else -1
    except (sqlite3.DatabaseError, OSError, TypeError, ValueError):
        return -1


def _evidence(state: Mapping[str, Any]) -> dict[str, int]:
    metadata = Path(str(state["metadata_db"]))
    media = Path(str(state["media_db"]))
    auth = Path(str(state["auth_db"]))
    return {
        "accepted_operations": _scalar(metadata, "SELECT COUNT(*) FROM accepted_operations"),
        "moments": _scalar(metadata, "SELECT COUNT(*) FROM moments"),
        "assets": _scalar(metadata, "SELECT COUNT(*) FROM assets"),
        "upload_sessions": _scalar(media, "SELECT COUNT(*) FROM upload_sessions"),
        "verified_assets": _scalar(media, "SELECT COUNT(*) FROM verified_assets"),
        "verified_bytes": _scalar(
            media,
            "SELECT COALESCE(SUM(byte_count),0) FROM upload_sessions WHERE state='verified'",
        ),
        "active_tokens": _scalar(auth, "SELECT COUNT(*) FROM owner_tokens WHERE revoked_at IS NULL"),
        "reconciliation_required": _scalar(
            metadata, "SELECT reconciliation_required FROM meta WHERE singleton=1"
        ),
        "exports_blocked": _scalar(
            metadata, "SELECT exports_blocked FROM meta WHERE singleton=1"
        ),
    }


def status(config: ControlConfig = ControlConfig(), runner: Runner = run_command) -> str:
    state = _load_state(config.current_path)
    if state is None:
        return "INACTIVE: no private C05b service has been prepared."
    _validate_state_paths(state, config)
    route_exact = (
        _route_proxy(_serve_state(config, runner=runner))
        == f"http://{LOOPBACK_HOST}:{config.port}"
    )
    funnel = _funnel_enabled(_serve_state(config, funnel=True, runner=runner))
    evidence = _evidence(state)
    return "\n".join([
        f"phase={state.get('phase', 'unknown')}",
        f"server_alive={str(_owned_server_alive(state, config)).lower()}",
        f"private_route_exact={str(route_exact).lower()}",
        f"funnel_enabled={str(funnel).lower()}",
        f"storage_fault={str(bool(state.get('storage_fault'))).lower()}",
        *(f"{key}={value}" for key, value in evidence.items()),
    ])


def stop(config: ControlConfig = ControlConfig(), runner: Runner = run_command) -> str:
    state = _load_state(config.current_path)
    if state is None:
        raise ControlError("no private C05b service exists")
    _validate_state_paths(state, config)
    serve_now = _serve_state(config, runner=runner)
    route = _route_proxy(serve_now)
    expected = f"http://{LOOPBACK_HOST}:{config.port}"
    if route not in (None, expected):
        raise ControlError("Camino route points elsewhere; refusing to remove it")
    if route == expected:
        _checked([
            str(config.tailscale_cli), "serve", "--yes", "--https=443",
            f"--set-path={ROUTE_PATH}", "off",
        ], runner)
    _terminate_owned_server(state, config)
    token_store = RevocableTokenStore(Path(str(state["auth_db"])))
    token_store.revoke(str(state.get("token_id", "")))
    serve_after = _serve_state(config, runner=runner)
    before_path = Path(str(state["serve_before_path"]))
    try:
        serve_before = json.loads(before_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
        raise ControlError("cannot compare the original Serve configuration") from error
    if not isinstance(serve_before, dict) or network._canonical(serve_after) != network._canonical(serve_before):
        raise ControlError("Serve configuration differs from the saved pre-test state")
    if _funnel_enabled(_serve_state(config, funnel=True, runner=runner)):
        raise ControlError("Funnel is active after C05b stop")
    completed = dict(state)
    completed["phase"] = "stopped"
    completed["stopped_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    _write_private_json(Path(str(state["run_dir"])) / "run.json", completed)
    _write_private_json(config.current_path, completed)
    evidence = _evidence(completed)
    return (
        "STOPPED: Camino C05b Serve path removed and owned C05a server stopped.\n"
        "Original Serve configuration restored exactly; Funnel remains disabled.\n"
        f"Evidence: operations={evidence['accepted_operations']}, "
        f"verified_assets={evidence['verified_assets']}, bytes={evidence['verified_bytes']}."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=(
        "start", "copy-url", "copy-token", "status", "storage-full-on", "storage-full-off",
        "rotate-epoch", "stop",
    ))
    args = parser.parse_args(argv)
    try:
        if args.action == "start":
            result = start()
        elif args.action == "copy-url":
            result = copy_url()
        elif args.action == "copy-token":
            result = copy_token()
        elif args.action == "status":
            result = status()
        elif args.action == "storage-full-on":
            result = set_storage_fault(True)
        elif args.action == "storage-full-off":
            result = set_storage_fault(False)
        elif args.action == "rotate-epoch":
            result = rotate_epoch()
        else:
            result = stop()
    except (
        ControlError, OSError, sqlite3.DatabaseError, subprocess.SubprocessError,
        urllib.error.URLError, ContractError,
    ) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
