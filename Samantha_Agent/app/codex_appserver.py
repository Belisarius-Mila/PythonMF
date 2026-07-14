"""Fail-closed Codex app-server client shared by LAB and reliability tests."""

from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


LAB_DEVELOPER_INSTRUCTIONS = (
    "Jsi izolovaný read-only Adam App-server LAB. Odpovídej česky, stručně a věcně. "
    "Nikdy nevolej nástroje, nečti soubory, neměň data a neprováděj žádné akce. "
    "Jde pouze o test spolehlivého textového chatu a návaznosti konverzace."
)
CODEX_PATH_PREFIXES = (
    "/usr/local/bin",
    "/opt/homebrew/bin",
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class AppServerError(RuntimeError):
    """Base error for an app-server contract or transport failure."""


class AppServerTimeout(AppServerError):
    """Raised when required protocol evidence does not arrive in time."""


class AppServerContractError(AppServerError):
    """Raised when the server response violates the expected protocol contract."""


def codex_environment(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    existing = [part for part in str(env.get("PATH") or "").split(os.pathsep) if part]
    ordered: list[str] = []
    for part in (*CODEX_PATH_PREFIXES, *existing):
        if part not in ordered:
            ordered.append(part)
    env["PATH"] = os.pathsep.join(ordered)
    env.setdefault("LANG", "cs_CZ.UTF-8")
    env.setdefault("LC_ALL", "cs_CZ.UTF-8")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


@dataclass(frozen=True)
class CodexVersion:
    raw: str
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "CodexVersion":
        raw = str(value or "").strip()
        match = re.fullmatch(r"codex-cli\s+(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", raw)
        if not match:
            raise AppServerContractError("Codex vrátil neznámý formát verze.")
        return cls(raw=raw, major=int(match.group(1)), minor=int(match.group(2)), patch=int(match.group(3)))


@dataclass(frozen=True)
class TurnReceipt:
    client_message_id: str
    thread_id: str
    turn_id: str
    requested_at: str
    accepted_at: str
    started_at: str
    completed_at: str
    status: str
    answer: str
    turn_started_confirmed: bool
    user_item_count: int
    duration_ms: int

    @property
    def delivered(self) -> bool:
        return (
            self.status == "completed"
            and self.turn_started_confirmed
            and self.user_item_count == 1
            and bool(self.answer.strip())
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self) | {"delivered": self.delivered}


def read_codex_version(
    codex_binary: str = "codex",
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> CodexVersion:
    try:
        completed = runner(
            [codex_binary, "--version"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
            env=codex_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AppServerError(f"Codex verzi nelze zjistit: {exc}") from exc
    if completed.returncode != 0:
        raise AppServerError("Codex verzi nelze zjistit.")
    return CodexVersion.parse(completed.stdout)


class StdioAppServerTransport:
    """One JSON-lines stdio connection to ``codex app-server``."""

    def __init__(self, *, codex_binary: str = "codex", timeout: float = 120.0):
        self.timeout = timeout
        self._next_request_id = 1
        self._messages: queue.Queue[dict[str, Any] | BaseException] = queue.Queue()
        self._deferred: list[dict[str, Any]] = []
        try:
            self._process = subprocess.Popen(
                [codex_binary, "app-server", "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                bufsize=1,
                env=codex_environment(),
            )
        except OSError as exc:
            raise AppServerError(f"Codex app-server nelze spustit: {exc}") from exc
        if self._process.stdin is None or self._process.stdout is None:
            self.close()
            raise AppServerError("Codex app-server neposkytl stdio transport.")
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    @property
    def running(self) -> bool:
        return self._process.poll() is None

    @property
    def process_id(self) -> int:
        return int(self._process.pid)

    def _read_stdout(self) -> None:
        assert self._process.stdout is not None
        try:
            for raw_line in self._process.stdout:
                line = raw_line.strip()
                if line:
                    parsed = json.loads(line)
                    if not isinstance(parsed, dict):
                        raise AppServerContractError("App-server vrátil neobjektovou JSON zprávu.")
                    self._messages.put(parsed)
        except BaseException as exc:
            self._messages.put(exc)

    def _send(self, message: dict[str, Any]) -> None:
        if not self.running:
            raise AppServerError(f"Codex app-server skončil s kódem {self._process.returncode}.")
        assert self._process.stdin is not None
        try:
            self._process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise AppServerError(f"Zápis do app-serveru selhal: {exc}") from exc

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        message: dict[str, Any] = {"method": method}
        if params is not None:
            message["params"] = params
        self._send(message)

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self._next_request_id
        self._next_request_id += 1
        self._send({"id": request_id, "method": method, "params": params})
        response = self.receive(
            lambda message: message.get("id") == request_id,
            description=f"odpověď na {method}",
        )
        if "error" in response:
            raise AppServerContractError(f"App-server odmítl {method}.")
        result = response.get("result")
        if not isinstance(result, dict):
            raise AppServerContractError(f"App-server neposkytl objektový výsledek pro {method}.")
        return result

    def receive(
        self,
        predicate: Callable[[dict[str, Any]], bool],
        *,
        description: str,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + self.timeout
        while True:
            for index, message in enumerate(self._deferred):
                if predicate(message):
                    return self._deferred.pop(index)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AppServerTimeout(f"Vypršel čas při čekání na {description}.")
            try:
                incoming = self._messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise AppServerTimeout(f"Vypršel čas při čekání na {description}.") from exc
            if isinstance(incoming, BaseException):
                raise AppServerContractError("App-server vrátil neplatný výstup.") from incoming
            if predicate(incoming):
                return incoming
            self._deferred.append(incoming)

    def close(self) -> None:
        process = getattr(self, "_process", None)
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


class UnixSocketAppServerTransport(StdioAppServerTransport):
    """Direct WebSocket client connection over a local Unix domain socket."""

    def __init__(
        self,
        *,
        socket_path: Path,
        codex_binary: str = "codex",
        timeout: float = 120.0,
    ):
        del codex_binary  # The external app-server process owns its executable.
        target = Path(socket_path).expanduser()
        if not target.is_absolute():
            raise AppServerContractError("Cesta k app-server socketu musí být absolutní.")
        try:
            from websockets.sync.client import unix_connect
            from websockets.exceptions import WebSocketException
        except ImportError as exc:
            raise AppServerError("Pro Unix app-server transport chybí knihovna websockets.") from exc

        self.socket_path = target
        self.timeout = timeout
        self._next_request_id = 1
        self._messages: queue.Queue[dict[str, Any] | BaseException] = queue.Queue()
        self._deferred: list[dict[str, Any]] = []
        self._send_lock = threading.Lock()
        self._closed = False
        try:
            self._connection = unix_connect(
                path=str(target),
                uri="ws://localhost/rpc",
                open_timeout=timeout,
                close_timeout=5,
                compression=None,
            )
        except (OSError, TimeoutError, WebSocketException) as exc:
            raise AppServerError(f"K Unix app-server socketu se nelze připojit: {exc}") from exc
        self._reader = threading.Thread(target=self._read_websocket, daemon=True)
        self._reader.start()

    @property
    def running(self) -> bool:
        return not self._closed

    @property
    def process_id(self) -> int:
        return 0

    def _read_websocket(self) -> None:
        try:
            for raw_message in self._connection:
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode("utf-8")
                parsed = json.loads(raw_message)
                if not isinstance(parsed, dict):
                    raise AppServerContractError("App-server vrátil neobjektovou JSON zprávu.")
                self._messages.put(parsed)
        except BaseException as exc:
            if not self._closed:
                self._messages.put(exc)
        finally:
            self._closed = True

    def _send(self, message: dict[str, Any]) -> None:
        if not self.running:
            raise AppServerError("Unix app-server spojení je uzavřené.")
        try:
            with self._send_lock:
                self._connection.send(json.dumps(message, ensure_ascii=False))
        except Exception as exc:
            raise AppServerError(f"Zápis do Unix app-serveru selhal: {exc}") from exc

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._connection.close()
        except OSError:
            pass


class CodexAppServerClient:
    """Typed minimal client for start/resume/turn operations."""

    def __init__(
        self,
        *,
        codex_binary: str = "codex",
        timeout: float = 120.0,
        transport_factory: Callable[..., StdioAppServerTransport] = StdioAppServerTransport,
    ):
        self.codex_binary = codex_binary
        self.connection_id = uuid.uuid4().hex
        self.version = read_codex_version(codex_binary)
        self.transport = transport_factory(codex_binary=codex_binary, timeout=timeout)
        self.process_id = self.transport.process_id
        try:
            self.transport.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "samantha-appserver-core",
                        "title": "Samantha App-server Core",
                        "version": "0.1.0",
                    },
                    "capabilities": None,
                },
            )
            self.transport.notify("initialized")
        except Exception:
            self.close()
            raise

    @property
    def running(self) -> bool:
        return self.transport.running

    def start_thread(
        self,
        *,
        cwd: Path,
        ephemeral: bool = False,
        developer_instructions: str = LAB_DEVELOPER_INSTRUCTIONS,
        sandbox: str = "read-only",
        approval_policy: str = "never",
        model: str | None = None,
    ) -> str:
        params: dict[str, Any] = {
            "cwd": str(cwd.resolve()),
            "ephemeral": ephemeral,
            "sandbox": sandbox,
            "approvalPolicy": approval_policy,
            "developerInstructions": developer_instructions,
        }
        if model:
            params["model"] = model
        result = self.transport.request("thread/start", params)
        return self._thread_id(result, operation="thread/start")

    def resume_thread(
        self,
        thread_id: str,
        *,
        cwd: Path,
        developer_instructions: str = LAB_DEVELOPER_INSTRUCTIONS,
        sandbox: str = "read-only",
        approval_policy: str = "never",
        model: str | None = None,
    ) -> str:
        expected = str(thread_id or "").strip()
        if not expected:
            raise AppServerContractError("Chybí threadId pro obnovení.")
        params: dict[str, Any] = {
            "threadId": expected,
            "cwd": str(cwd.resolve()),
            "sandbox": sandbox,
            "approvalPolicy": approval_policy,
            "developerInstructions": developer_instructions,
        }
        if model:
            params["model"] = model
        result = self.transport.request("thread/resume", params)
        resumed = self._thread_id(result, operation="thread/resume")
        if resumed != expected:
            raise AppServerContractError("App-server obnovil jiné vlákno.")
        return resumed

    def archive_thread(self, thread_id: str) -> None:
        target = str(thread_id or "").strip()
        if not target:
            raise AppServerContractError("Chybí threadId pro archivaci.")
        self.transport.request("thread/archive", {"threadId": target})

    @staticmethod
    def _thread_id(result: dict[str, Any], *, operation: str) -> str:
        thread = result.get("thread")
        thread_id = thread.get("id") if isinstance(thread, dict) else None
        if not isinstance(thread_id, str) or not thread_id:
            raise AppServerContractError(f"{operation} nevrátil threadId.")
        return thread_id

    def send_text(
        self,
        *,
        thread_id: str,
        text: str,
        client_message_id: str | None = None,
        effort: str = "low",
        sandbox_policy: dict[str, Any] | None = None,
        approval_policy: str = "never",
        model: str | None = None,
    ) -> TurnReceipt:
        clean_text = str(text or "").strip()
        if not clean_text:
            raise AppServerContractError("Nelze odeslat prázdnou zprávu.")
        message_id = str(client_message_id or f"appserver-lab-{uuid.uuid4().hex}").strip()
        requested_at = utc_now()
        started_monotonic = time.monotonic()
        params: dict[str, Any] = {
            "threadId": thread_id,
            "clientUserMessageId": message_id,
            "input": [{"type": "text", "text": clean_text}],
            "effort": effort,
            "sandboxPolicy": dict(sandbox_policy or {"type": "readOnly"}),
            "approvalPolicy": approval_policy,
        }
        if model:
            params["model"] = model
        result = self.transport.request("turn/start", params)
        accepted_at = utc_now()
        turn = result.get("turn")
        turn_id = turn.get("id") if isinstance(turn, dict) else None
        if not isinstance(turn_id, str) or not turn_id:
            raise AppServerContractError("turn/start nevrátil turnId.")

        turn_started_confirmed = False
        started_at = ""
        user_items: list[dict[str, Any]] = []
        agent_messages: list[str] = []
        status = ""
        while not status:
            event = self.transport.receive(
                lambda candidate: self._belongs_to_turn(candidate, thread_id=thread_id, turn_id=turn_id),
                description=f"událost turnu {turn_id}",
            )
            method = event.get("method")
            params = event.get("params")
            if not isinstance(params, dict):
                raise AppServerContractError("Turn událost nemá objektové params.")
            if method == "turn/started":
                turn_started_confirmed = True
                started_at = utc_now()
            item = params.get("item")
            if method == "item/completed" and isinstance(item, dict):
                if item.get("type") == "userMessage" and item.get("clientId") == message_id:
                    user_items.append(item)
                if item.get("type") == "agentMessage" and isinstance(item.get("text"), str):
                    agent_messages.append(item["text"])
            if method == "turn/completed":
                completed_turn = params.get("turn")
                if not isinstance(completed_turn, dict):
                    raise AppServerContractError("turn/completed neobsahuje turn.")
                status = str(completed_turn.get("status") or "")
                completed_items = completed_turn.get("items")
                if isinstance(completed_items, list) and completed_items:
                    authoritative_users = [
                        item
                        for item in completed_items
                        if isinstance(item, dict)
                        and item.get("type") == "userMessage"
                        and item.get("clientId") == message_id
                    ]
                    authoritative_answers = [
                        str(item.get("text"))
                        for item in completed_items
                        if isinstance(item, dict)
                        and item.get("type") == "agentMessage"
                        and str(item.get("text") or "").strip()
                    ]
                    user_items = authoritative_users
                    if authoritative_answers:
                        agent_messages = authoritative_answers

        receipt = TurnReceipt(
            client_message_id=message_id,
            thread_id=thread_id,
            turn_id=turn_id,
            requested_at=requested_at,
            accepted_at=accepted_at,
            started_at=started_at,
            completed_at=utc_now(),
            status=status,
            answer=agent_messages[-1].strip() if agent_messages else "",
            turn_started_confirmed=turn_started_confirmed,
            user_item_count=len(user_items),
            duration_ms=round((time.monotonic() - started_monotonic) * 1000),
        )
        if not receipt.delivered:
            raise AppServerContractError("Turn nebyl jednoznačně potvrzen jako doručený a dokončený.")
        return receipt

    def read_effective_config(self, *, cwd: Path) -> dict[str, Any]:
        result = self.transport.request(
            "config/read",
            {"cwd": str(cwd.resolve()), "includeLayers": False},
        )
        config = result.get("config")
        if not isinstance(config, dict):
            raise AppServerContractError("config/read nevrátil efektivní konfiguraci.")
        return config

    def list_models(self, *, include_hidden: bool = True) -> list[dict[str, Any]]:
        models: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"includeHidden": include_hidden, "limit": 100}
            if cursor:
                params["cursor"] = cursor
            result = self.transport.request("model/list", params)
            page = result.get("data")
            if not isinstance(page, list):
                raise AppServerContractError("model/list nevrátil seznam modelů.")
            models.extend(item for item in page if isinstance(item, dict))
            raw_cursor = result.get("nextCursor")
            cursor = str(raw_cursor) if raw_cursor else None
            if not cursor:
                return models

    @staticmethod
    def _belongs_to_turn(message: dict[str, Any], *, thread_id: str, turn_id: str) -> bool:
        params = message.get("params")
        if not isinstance(params, dict) or params.get("threadId") != thread_id:
            return False
        if params.get("turnId") == turn_id:
            return True
        turn = params.get("turn")
        return isinstance(turn, dict) and turn.get("id") == turn_id

    def close(self) -> None:
        transport = getattr(self, "transport", None)
        if transport is not None:
            transport.close()

    def __enter__(self) -> "CodexAppServerClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
