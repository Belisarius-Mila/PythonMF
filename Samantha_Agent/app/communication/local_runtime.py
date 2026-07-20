"""Private local process controller for Samantha's shared Codex app-server."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from app.codex_appserver import AppServerError, DEFAULT_CODEX_BIN, codex_environment
from app.file_persistence import FilePersistenceError, atomic_write_json


DEFAULT_RUNTIME_DIR = Path.home() / ".codex" / "samantha-communication"
DEFAULT_SOCKET_PATH = DEFAULT_RUNTIME_DIR / "app-server.sock"
APP_SERVER_OWNERSHIP_SCHEMA = 1


class LocalAppServerProcessController:
    """Start at most one local Unix-socket app-server and own only its process."""

    def __init__(
        self,
        *,
        socket_path: Path = DEFAULT_SOCKET_PATH,
        ownership_path: Path | None = None,
        codex_binary: str = DEFAULT_CODEX_BIN,
        startup_timeout: float = 30.0,
    ):
        self.socket_path = Path(socket_path).expanduser().resolve()
        self.ownership_path = Path(
            ownership_path or self.socket_path.with_suffix(".owner.json")
        ).expanduser().resolve()
        self.codex_binary = str(codex_binary)
        self.startup_timeout = float(startup_timeout)
        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.RLock()

    def _owned_process_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @staticmethod
    def _process_identity(pid: int) -> str:
        completed = subprocess.run(
            ["/bin/ps", "-p", str(pid), "-o", "lstart=", "-o", "command="],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if completed.returncode != 0:
            return ""
        return " ".join(completed.stdout.split())

    def _load_ownership(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.ownership_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(raw, dict) or set(raw) != {
            "schema_version",
            "pid",
            "process_identity",
            "socket_path",
        }:
            return {}
        try:
            pid = int(raw.get("pid") or 0)
        except (TypeError, ValueError):
            return {}
        identity = str(raw.get("process_identity") or "").strip()
        socket_path = str(raw.get("socket_path") or "")
        expected_command = f"app-server --listen unix://{self.socket_path}"
        if (
            raw.get("schema_version") != APP_SERVER_OWNERSHIP_SCHEMA
            or pid <= 0
            or socket_path != str(self.socket_path)
            or expected_command not in identity
        ):
            return {}
        return {
            "schema_version": APP_SERVER_OWNERSHIP_SCHEMA,
            "pid": pid,
            "process_identity": identity,
            "socket_path": socket_path,
        }

    def _persisted_owner_state(self) -> tuple[str, dict[str, Any]]:
        record = self._load_ownership()
        if not record:
            return "unknown", {}
        pid = int(record["pid"])
        current_identity = self._process_identity(pid)
        if not current_identity:
            return "stopped", record
        try:
            process_group = os.getpgid(pid)
        except OSError:
            return "unknown", record
        if current_identity == record["process_identity"] and process_group == pid:
            return "running", record
        return "foreign", record

    def _write_ownership(self, pid: int) -> None:
        identity = ""
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline and not identity:
            identity = self._process_identity(pid)
            if not identity:
                time.sleep(0.02)
        expected_command = f"app-server --listen unix://{self.socket_path}"
        if not identity or expected_command not in identity:
            return
        try:
            atomic_write_json(
                self.ownership_path,
                {
                    "schema_version": APP_SERVER_OWNERSHIP_SCHEMA,
                    "pid": int(pid),
                    "process_identity": identity,
                    "socket_path": str(self.socket_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        except (FilePersistenceError, OSError):
            return

    def _socket_listener_pids(self) -> list[int] | None:
        try:
            completed = subprocess.run(
                ["/usr/sbin/lsof", "-t", "--", str(self.socket_path)],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except OSError:
            return None
        if completed.returncode not in {0, 1}:
            return None
        listener_pids: list[int] = []
        for raw_pid in completed.stdout.splitlines():
            try:
                listener_pids.append(int(raw_pid.strip()))
            except ValueError:
                return None
        return listener_pids

    def _adopt_reachable_owner(self) -> bool:
        if self._load_ownership():
            return True
        listener_pids = self._socket_listener_pids()
        if listener_pids is None:
            return False
        expected_command = f"app-server --listen unix://{self.socket_path}"
        for listener_pid in listener_pids:
            try:
                process_group = os.getpgid(listener_pid)
            except OSError:
                continue
            identity = self._process_identity(process_group)
            if process_group <= 0 or expected_command not in identity:
                continue
            self._write_ownership(process_group)
            return bool(self._load_ownership())
        return False

    def _clear_ownership(self) -> None:
        try:
            self.ownership_path.unlink(missing_ok=True)
        except OSError:
            pass

    def _recover_persisted_owner(self) -> bool:
        state, record = self._persisted_owner_state()
        if state not in {"running", "stopped"}:
            return False
        if state == "stopped":
            listener_pids = self._socket_listener_pids()
            if listener_pids is None or listener_pids:
                return False
        if state == "running":
            pid = int(record["pid"])
            expected_identity = str(record["process_identity"])
            try:
                os.killpg(pid, signal.SIGTERM)
            except OSError:
                return False
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                current_identity = self._process_identity(pid)
                if not current_identity:
                    break
                if current_identity != expected_identity:
                    return False
                time.sleep(0.05)
            else:
                try:
                    os.killpg(pid, signal.SIGKILL)
                except OSError:
                    return False
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline and self._process_identity(pid):
                    time.sleep(0.05)
                if self._process_identity(pid):
                    return False
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                listener_pids = self._socket_listener_pids()
                if listener_pids is None:
                    return False
                if not listener_pids:
                    break
                time.sleep(0.05)
            else:
                return False
        try:
            self.socket_path.unlink(missing_ok=True)
        except OSError:
            return False
        self._clear_ownership()
        return True

    def _socket_reachable(self) -> bool:
        if not self.socket_path.exists():
            return False
        try:
            from websockets.sync.client import unix_connect

            connection = unix_connect(
                path=str(self.socket_path),
                uri="ws://localhost/rpc",
                open_timeout=0.5,
                close_timeout=0.5,
                compression=None,
            )
            connection.close()
            return True
        except (ImportError, OSError, TimeoutError):
            return False
        except Exception:
            return False

    def status(self) -> dict[str, Any]:
        with self._lock:
            running = self._owned_process_running()
            persisted_state, _record = self._persisted_owner_state()
            reachable = self._socket_reachable()
            return {
                "running": running or reachable,
                "reachable": reachable,
                "owned_by_cockpit": running or persisted_state == "running",
                "socket_exists": self.socket_path.exists(),
                "transport": "private_local_unix_socket",
            }

    def start(self, *, recover_unreachable_owned: bool = False) -> dict[str, Any]:
        with self._lock:
            current = self.status()
            if current["reachable"]:
                self._adopt_reachable_owner()
                return {**self.status(), "started": False}
            if current["socket_exists"]:
                recovered = bool(
                    recover_unreachable_owned and self._recover_persisted_owner()
                )
                if not recovered:
                    raise AppServerError(
                        "Lokální app-server socket existuje, ale neodpovídá. "
                        "Bez úplného důkazu vlastnictví ho automaticky neměním."
                    )
            if self._process is not None and self._process.poll() is not None:
                self._process = None

            self.socket_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            try:
                self.socket_path.parent.chmod(0o700)
                self._process = subprocess.Popen(
                    [
                        self.codex_binary,
                        "app-server",
                        "--listen",
                        f"unix://{self.socket_path}",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=codex_environment(),
                    start_new_session=True,
                )
                self._write_ownership(self._process.pid)
            except OSError as exc:
                self._process = None
                raise AppServerError(f"Lokální Codex app-server nelze spustit: {exc}") from exc

            deadline = time.monotonic() + self.startup_timeout
            while time.monotonic() < deadline:
                if self._process.poll() is not None:
                    code = self._process.returncode
                    self._process = None
                    raise AppServerError(f"Lokální Codex app-server skončil při startu (kód {code}).")
                if self._socket_reachable():
                    return {**self.status(), "started": True}
                time.sleep(0.05)

            self.close()
            raise AppServerError("Lokální Codex app-server se včas nepřihlásil na privátní socket.")

    def close(self) -> None:
        with self._lock:
            process = self._process
            self._process = None
            if process is None or process.poll() is not None:
                return
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            try:
                self.socket_path.unlink(missing_ok=True)
            except OSError:
                pass
            self._clear_ownership()
