"""Test-owned ephemeral Unix RPC fixture. No Codex server, credentials or model.

Two modes distinguish raw NDJSON (CLI proxy) and WebSocket (Samantha transport).
This module is imported only by the isolated P1-C test suite.
"""

from __future__ import annotations

import json
import logging
import socket
import threading
from pathlib import Path


class SyntheticSocket:
    def __init__(self, directory: Path, *, websocket: bool = False, scenario: str = "complete"):
        self.directory = directory
        self.path = directory / "rpc.sock"
        self.websocket = websocket
        self.scenario = scenario
        self.calls = []
        self.approvals = []
        self.first_bytes = []
        self.connections = []
        self.workers = []
        self.errors = []
        self.lock = threading.Lock()
        self.stopping = threading.Event()
        self.started_turn = threading.Event()
        self.server = None
        self.preview = ""

    def __enter__(self):
        self.directory.chmod(0o700)
        (self.directory / "fixture-only").write_text("05/P1-C synthetic RPC\n")
        if self.websocket:
            from websockets.sync.server import unix_serve

            logger = logging.Logger("p1c-synthetic-websocket", level=logging.CRITICAL)
            self.server = unix_serve(self._websocket, path=str(self.path), open_timeout=0.5,
                                     close_timeout=0.5, logger=logger)
            target = self.server.serve_forever
        else:
            self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server.bind(str(self.path))
            self.server.listen(8)
            self.server.settimeout(0.1)
            target = self._accept
        self.path.chmod(0o600)
        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()
        return self

    def _accept(self):
        while not self.stopping.is_set():
            try:
                connection, _ = self.server.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            self.connections.append(connection)
            worker = threading.Thread(target=self._raw, args=(connection,), daemon=True)
            self.workers.append(worker)
            worker.start()

    def _raw(self, connection):
        try:
            with connection, connection.makefile("r", encoding="utf-8") as incoming:
                for line in incoming:
                    with self.lock:
                        self.first_bytes.append(line[:16])
                    message = json.loads(line)
                    def send(payload):
                        connection.sendall((json.dumps(payload) + "\n").encode())
                    if self._dispatch(message, send) is False:
                        return
        except (OSError, ValueError) as exc:
            if not self.stopping.is_set():
                self.errors.append(type(exc).__name__)

    def _websocket(self, connection):
        try:
            for message in connection:
                self._dispatch(json.loads(message), lambda payload: connection.send(json.dumps(payload)))
        except Exception as exc:
            if not self.stopping.is_set():
                self.errors.append(type(exc).__name__)

    def _dispatch(self, message, send):
        method = message.get("method")
        if not method:
            self.approvals.append(message)
            return True
        params = message.get("params") or {}
        with self.lock:
            self.calls.append((method, params))
        if "id" not in message:
            return True
        request_id = message["id"]
        if method == "initialize":
            result = {"userAgent": "codex/0.166.0", "serverInfo": {"name": "synthetic", "version": "0.166.0"},
                      "platformFamily": "unix", "platformOs": "macos"}
        elif method == "thread/resume":
            result = {"thread": self._thread(params["cwd"]), "cwd": params["cwd"],
                      "model": params["model"], "modelProvider": params["modelProvider"],
                      "approvalPolicy": "never", "approvalsReviewer": "user", "sandbox": {"type": "readOnly"}}
        elif method == "thread/read":
            result = {"thread": self._thread(str(self.directory))}
        elif method == "turn/start":
            self.started_turn.set()
            if self.scenario == "disconnect_before_ack":
                return False
            if self.scenario == "silent_before_ack":
                return True
            if self.scenario == "rpc_error":
                send({"id": request_id, "error": {"code": -32001, "message": "synthetic overload",
                      "data": {"codexErrorInfo": "server_overloaded", "retryAfterMs": 1}}})
                return True
            result = {"turn": {"id": "fixture-turn", "status": "inProgress", "items": [], "itemsView": "full"}}
        elif method == "fixture/approval":
            send({"id": "fixture-approval", "method": params["method"], "params": {}})
            result = {}
        else:
            send({"id": request_id, "error": {"code": -32601, "message": "synthetic unsupported"}})
            return True
        send({"id": request_id, "result": result})
        if method != "turn/start":
            return True
        send({"method": "turn/started", "params": {"threadId": "fixture-thread", "turn": result["turn"]}})
        if self.scenario == "disconnect_after_ack":
            return False
        if self.scenario == "silent_after_ack":
            return True
        items = [{"type": "userMessage", "id": "fixture-user", "content": [],
                  "clientId": params.get("clientUserMessageId")},
                 {"type": "agentMessage", "id": "fixture-final", "phase": "final_answer", "text": '{"ok":true}'},
                 {"type": "agentMessage", "id": "fixture-commentary", "phase": "commentary", "text": "Working"}]
        for item in items:
            send({"method": "item/completed", "params": {"threadId": "fixture-thread", "turnId": "fixture-turn",
                  "item": item, "completedAtMs": 1000}})
        send({"method": "fixture/futureEvent", "params": {"threadId": "fixture-thread", "value": {"retained": True}}})
        if self.scenario == "retry_hint":
            send({"method": "error", "params": {"threadId": "fixture-thread", "turnId": "fixture-turn",
                  "error": {"message": "synthetic reconnect", "codexErrorInfo": {"httpConnectionFailed": {"httpStatusCode": 503}},
                            "additionalDetails": "synthetic"}, "willRetry": True}})
            return False
        self.preview = "synthetic completed"
        send({"method": "turn/completed", "params": {"threadId": "fixture-thread",
              "turn": {"id": "fixture-turn", "status": "completed", "items": items, "itemsView": "full"}}})
        return True

    def _thread(self, cwd):
        return {"id": "fixture-thread", "cliVersion": "0.166.0", "createdAt": 1, "updatedAt": 1,
                "cwd": cwd, "ephemeral": False, "modelProvider": "openai", "preview": self.preview,
                "sessionId": "fixture-session", "source": "cli", "status": {"type": "idle"},
                "turns": [], "projectId": None}

    def __exit__(self, *_exc):
        self.stopping.set()
        if self.websocket:
            self.server.shutdown()
        else:
            for connection in self.connections:
                try:
                    connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            self.server.close()
        self.thread.join(timeout=2)
        for worker in self.workers:
            worker.join(timeout=2)
        # TemporaryDirectory owns cleanup, including the synthetic socket.
