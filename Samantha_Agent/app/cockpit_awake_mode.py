from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import threading
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.file_persistence import FilePersistenceError, atomic_write_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_PATH = (
    PROJECT_ROOT / "data" / "private" / "cockpit" / "awake_mode.json"
)
CAFFEINATE_PATH = Path("/usr/bin/caffeinate")
ALLOWED_HOURS = (1, 2, 4)
STATE_SCHEMA = 1


class CockpitAwakeModeError(RuntimeError):
    """Raised when the bounded awake-mode operation cannot be verified."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _launch_caffeinate(argv: Sequence[str]) -> int:
    process = subprocess.Popen(
        list(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )
    return int(process.pid)


def _process_command(pid: int) -> str:
    completed = subprocess.run(
        ["/bin/ps", "-p", str(pid), "-o", "command="],
        capture_output=True,
        text=True,
        timeout=3,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _terminate_process(pid: int) -> None:
    os.kill(pid, signal.SIGTERM)


class CockpitAwakeMode:
    """Manage one time-limited, explicitly owned macOS caffeinate process."""

    def __init__(
        self,
        *,
        state_path: Path = DEFAULT_STATE_PATH,
        caffeinate_path: Path = CAFFEINATE_PATH,
        now: Callable[[], datetime] = _utc_now,
        launcher: Callable[[Sequence[str]], int] = _launch_caffeinate,
        process_command: Callable[[int], str] = _process_command,
        terminator: Callable[[int], None] = _terminate_process,
        executable_available: Callable[[Path], bool] | None = None,
    ) -> None:
        self.state_path = Path(state_path)
        self.caffeinate_path = Path(caffeinate_path)
        self._now = now
        self._launcher = launcher
        self._process_command = process_command
        self._terminator = terminator
        self._executable_available = executable_available or (
            lambda path: path.is_file() and os.access(path, os.X_OK)
        )
        self._lock = threading.RLock()

    def status(self) -> dict[str, Any]:
        with self._lock:
            state = self._load_state()
            return self._status_from_state(state)

    def start(self, hours: int) -> dict[str, Any]:
        if hours not in ALLOWED_HOURS:
            raise CockpitAwakeModeError("Povolená délka je pouze 1, 2 nebo 4 hodiny.")
        with self._lock:
            current = self._status_from_state(self._load_state())
            if current.get("active"):
                raise CockpitAwakeModeError(
                    "Režim už běží. Nejprve ho ukonči, potom můžeš zvolit novou délku."
                )
            if not self._executable_available(self.caffeinate_path):
                raise CockpitAwakeModeError("Systémový příkaz caffeinate není dostupný.")

            duration_seconds = hours * 60 * 60
            argv = (
                str(self.caffeinate_path),
                "-i",
                "-t",
                str(duration_seconds),
            )
            try:
                pid = int(self._launcher(argv))
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                raise CockpitAwakeModeError(
                    "Časově omezený režim se nepodařilo spustit."
                ) from exc
            if pid <= 0:
                raise CockpitAwakeModeError("Systémový proces vrátil neplatnou identitu.")

            started_at = self._normalized_now()
            expires_at = started_at.timestamp() + duration_seconds
            state = {
                "schema": STATE_SCHEMA,
                "active": True,
                "pid": pid,
                "duration_seconds": duration_seconds,
                "started_at": started_at.isoformat(),
                "expires_at": datetime.fromtimestamp(
                    expires_at, tz=timezone.utc
                ).isoformat(),
            }
            try:
                self._write_state(state)
            except CockpitAwakeModeError:
                try:
                    self._terminator(pid)
                except (OSError, ProcessLookupError):
                    pass
                raise
            return self._public_status(
                active=True,
                status="active",
                message=(
                    f"Vzdálený Cockpit zůstane vzhůru {hours} "
                    f"{self._hour_label(hours)}."
                ),
                duration_seconds=duration_seconds,
                remaining_seconds=duration_seconds,
                started_at=state["started_at"],
                expires_at=state["expires_at"],
            )

    def stop(self) -> dict[str, Any]:
        with self._lock:
            state = self._load_state()
            current = self._status_from_state(state)
            if not current.get("active"):
                return self._public_status(
                    active=False,
                    status="inactive",
                    message="Časově omezený režim už není aktivní.",
                )

            pid = self._state_pid(state)
            if pid is None or not self._is_owned_process(pid, state):
                raise CockpitAwakeModeError(
                    "Proces nelze bezpečně ověřit, proto jsem ho neukončil."
                )
            try:
                self._terminator(pid)
            except ProcessLookupError:
                pass
            except OSError as exc:
                raise CockpitAwakeModeError(
                    "Ověřený proces se nepodařilo bezpečně ukončit."
                ) from exc

            stopped_at = self._normalized_now().isoformat()
            self._write_state(
                {
                    "schema": STATE_SCHEMA,
                    "active": False,
                    "stopped_at": stopped_at,
                }
            )
            return self._public_status(
                active=False,
                status="stopped",
                message="Časově omezený režim byl ukončen.",
            )

    def _status_from_state(self, state: dict[str, Any] | None) -> dict[str, Any]:
        if not state or not state.get("active"):
            return self._public_status(
                active=False,
                status="inactive",
                message="Časově omezený režim není aktivní.",
            )
        if state.get("schema") != STATE_SCHEMA:
            return self._public_status(
                active=False,
                status="unknown",
                ok=False,
                message="Uložený stav režimu má neznámou verzi.",
            )

        duration_seconds = self._positive_int(state.get("duration_seconds"))
        pid = self._state_pid(state)
        expires_at = self._parse_datetime(state.get("expires_at"))
        if duration_seconds is None or pid is None or expires_at is None:
            return self._public_status(
                active=False,
                status="unknown",
                ok=False,
                message="Uložený stav režimu je neúplný; nic jsem neukončil.",
            )

        remaining_seconds = max(
            0,
            int((expires_at - self._normalized_now()).total_seconds() + 0.999),
        )
        if remaining_seconds <= 0:
            return self._public_status(
                active=False,
                status="expired",
                message="Časově omezený režim už vypršel.",
                expires_at=expires_at.isoformat(),
            )
        if not self._is_owned_process(pid, state):
            return self._public_status(
                active=False,
                status="not_running",
                message="Časově omezený režim už neběží.",
                expires_at=expires_at.isoformat(),
            )
        return self._public_status(
            active=True,
            status="active",
            message="Mac zůstává vzhůru pro vzdálený Cockpit.",
            duration_seconds=duration_seconds,
            remaining_seconds=remaining_seconds,
            started_at=str(state.get("started_at") or ""),
            expires_at=expires_at.isoformat(),
        )

    def _is_owned_process(self, pid: int, state: dict[str, Any]) -> bool:
        duration_seconds = self._positive_int(state.get("duration_seconds"))
        if duration_seconds is None:
            return False
        try:
            command = self._process_command(pid)
        except (OSError, ValueError, subprocess.SubprocessError):
            return False
        if not command:
            return False
        try:
            argv = shlex.split(command)
        except ValueError:
            return False
        return (
            len(argv) == 4
            and Path(argv[0]) == self.caffeinate_path
            and argv[1:] == ["-i", "-t", str(duration_seconds)]
        )

    def _load_state(self) -> dict[str, Any] | None:
        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as exc:
            raise CockpitAwakeModeError("Stav režimu nelze bezpečně načíst.") from exc
        if not isinstance(payload, dict):
            raise CockpitAwakeModeError("Stav režimu nemá očekávaný formát.")
        return payload

    def _write_state(self, payload: dict[str, Any]) -> None:
        try:
            atomic_write_json(
                self.state_path,
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            os.chmod(self.state_path, 0o600)
        except (OSError, FilePersistenceError) as exc:
            raise CockpitAwakeModeError("Stav režimu nelze bezpečně uložit.") from exc

    def _normalized_now(self) -> datetime:
        value = self._now()
        if value.tzinfo is None:
            raise CockpitAwakeModeError("Čas režimu musí obsahovat časové pásmo.")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        try:
            parsed = datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _positive_int(value: Any) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @classmethod
    def _state_pid(cls, state: dict[str, Any] | None) -> int | None:
        if not state:
            return None
        return cls._positive_int(state.get("pid"))

    @staticmethod
    def _hour_label(hours: int) -> str:
        return "hodinu" if hours == 1 else "hodiny"

    @staticmethod
    def _public_status(
        *,
        active: bool,
        status: str,
        message: str,
        ok: bool = True,
        duration_seconds: int = 0,
        remaining_seconds: int = 0,
        started_at: str = "",
        expires_at: str = "",
    ) -> dict[str, Any]:
        return {
            "ok": ok,
            "active": active,
            "status": status,
            "message": message,
            "duration_seconds": duration_seconds,
            "remaining_seconds": remaining_seconds,
            "started_at": started_at,
            "expires_at": expires_at,
            "allowed_hours": list(ALLOWED_HOURS),
            "lid_warning": "Režim funguje pouze s otevřeným víkem MacBooku.",
        }


COCKPIT_AWAKE_MODE = CockpitAwakeMode()


def cockpit_awake_mode_status_action(
    *, manager: CockpitAwakeMode = COCKPIT_AWAKE_MODE
) -> dict[str, Any]:
    try:
        return manager.status()
    except CockpitAwakeModeError as exc:
        return CockpitAwakeMode._public_status(
            active=False,
            status="unknown",
            ok=False,
            message=str(exc),
        )


def cockpit_awake_mode_action(
    payload: dict[str, Any],
    *,
    manager: CockpitAwakeMode = COCKPIT_AWAKE_MODE,
) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip().casefold()
    try:
        if action == "start":
            try:
                hours = int(payload.get("hours"))
            except (TypeError, ValueError) as exc:
                raise CockpitAwakeModeError(
                    "Povolená délka je pouze 1, 2 nebo 4 hodiny."
                ) from exc
            return manager.start(hours)
        if action == "stop":
            return manager.stop()
        raise CockpitAwakeModeError("Neznámá akce časově omezeného režimu.")
    except CockpitAwakeModeError as exc:
        return CockpitAwakeMode._public_status(
            active=False,
            status="awake_mode_failed",
            ok=False,
            message=str(exc),
        )
