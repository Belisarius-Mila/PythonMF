"""Private local process controller for Samantha's shared Codex app-server."""

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from app.codex_appserver import AppServerError, DEFAULT_CODEX_BIN, codex_environment


DEFAULT_RUNTIME_DIR = Path.home() / ".codex" / "samantha-communication"
DEFAULT_SOCKET_PATH = DEFAULT_RUNTIME_DIR / "app-server.sock"


class LocalAppServerProcessController:
    """Start at most one local Unix-socket app-server and own only its process."""

    def __init__(
        self,
        *,
        socket_path: Path = DEFAULT_SOCKET_PATH,
        codex_binary: str = DEFAULT_CODEX_BIN,
        startup_timeout: float = 12.0,
    ):
        self.socket_path = Path(socket_path).expanduser().resolve()
        self.codex_binary = str(codex_binary)
        self.startup_timeout = float(startup_timeout)
        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.RLock()

    def _owned_process_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

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
            reachable = self._socket_reachable()
            return {
                "running": running or reachable,
                "reachable": reachable,
                "owned_by_cockpit": running,
                "socket_exists": self.socket_path.exists(),
                "transport": "private_local_unix_socket",
            }

    def start(self) -> dict[str, Any]:
        with self._lock:
            current = self.status()
            if current["reachable"]:
                return {**current, "started": False}
            if current["socket_exists"]:
                raise AppServerError(
                    "Lokální app-server socket existuje, ale neodpovídá. "
                    "Kvůli ochraně cizího procesu ho automaticky nemažu."
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
