#!/usr/bin/env python3
"""Isolated, fail-closed reliability probe for the Codex app-server protocol.

This script deliberately does not interact with Cockpit, VoiceBridge inboxes,
terminal TTYs, or the watcher.  It creates one ephemeral, read-only Codex
thread and validates delivery using protocol events tied to explicit thread,
turn, and client-message identifiers.
"""

from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class ProbeError(RuntimeError):
    """Raised when protocol evidence is missing, inconsistent, or malformed."""


@dataclass(frozen=True)
class DeliveryEvidence:
    sequence: int
    client_message_id: str
    thread_id: str
    turn_id: str
    user_item_confirmed: bool
    turn_status: str
    exact_reply_confirmed: bool
    duplicate_user_items: int
    duration_ms: int

    @property
    def passed(self) -> bool:
        return (
            self.user_item_confirmed
            and self.turn_status == "completed"
            and self.exact_reply_confirmed
            and self.duplicate_user_items == 0
        )


class StdioAppServer:
    def __init__(self, *, codex_binary: str = "codex", timeout: float = 120.0):
        self.timeout = timeout
        self._next_request_id = 1
        self._messages: queue.Queue[dict[str, Any] | BaseException] = queue.Queue()
        self._deferred: list[dict[str, Any]] = []
        self._process = subprocess.Popen(
            [codex_binary, "app-server", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        if self._process.stdin is None or self._process.stdout is None:
            raise ProbeError("Codex app-server did not expose stdio pipes")
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    def _read_stdout(self) -> None:
        assert self._process.stdout is not None
        try:
            for raw_line in self._process.stdout:
                line = raw_line.strip()
                if line:
                    self._messages.put(json.loads(line))
        except BaseException as exc:  # Propagate reader/protocol failures.
            self._messages.put(exc)

    def _send(self, message: dict[str, Any]) -> None:
        if self._process.poll() is not None:
            raise ProbeError(f"Codex app-server exited with {self._process.returncode}")
        assert self._process.stdin is not None
        self._process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self._process.stdin.flush()

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
            description=f"response to {method}",
        )
        if "error" in response:
            raise ProbeError(f"{method} failed: {response['error']}")
        result = response.get("result")
        if not isinstance(result, dict):
            raise ProbeError(f"{method} returned no object result")
        return result

    def receive(self, predicate: Any, *, description: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.timeout
        while True:
            for index, message in enumerate(self._deferred):
                if predicate(message):
                    return self._deferred.pop(index)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProbeError(f"Timed out waiting for {description}")
            try:
                incoming = self._messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise ProbeError(f"Timed out waiting for {description}") from exc
            if isinstance(incoming, BaseException):
                raise ProbeError(f"Invalid app-server output: {incoming}") from incoming
            if predicate(incoming):
                return incoming
            self._deferred.append(incoming)

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)

    def __enter__(self) -> "StdioAppServer":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def _item_from_notification(message: dict[str, Any]) -> dict[str, Any] | None:
    params = message.get("params")
    if not isinstance(params, dict):
        return None
    item = params.get("item")
    return item if isinstance(item, dict) else None


def _initialize_server(server: StdioAppServer) -> None:
    server.request(
        "initialize",
        {
            "clientInfo": {
                "name": "samantha-voicebridge-reliability-probe",
                "title": "Samantha VoiceBridge Reliability Probe",
                "version": "0.1.0",
            },
            "capabilities": None,
        },
    )
    server.notify("initialized")


def run_probe(
    *, count: int,
    timeout: float,
    codex_binary: str,
    workdir: Path,
    restart_after: int | None = None,
) -> list[DeliveryEvidence]:
    if count < 1:
        raise ProbeError("Count must be at least 1")
    if restart_after is not None and not 1 <= restart_after < count:
        raise ProbeError("restart-after must be at least 1 and lower than count")

    evidence: list[DeliveryEvidence] = []
    server = StdioAppServer(codex_binary=codex_binary, timeout=timeout)
    try:
        _initialize_server(server)
        thread_result = server.request(
            "thread/start",
            {
                "cwd": str(workdir.resolve()),
                "ephemeral": restart_after is None,
                "sandbox": "read-only",
                "approvalPolicy": "never",
                "developerInstructions": (
                    "Reliability probe only. Never call tools, access files, or perform actions. "
                    "Reply with exactly the text requested by each user message."
                ),
            },
        )
        thread = thread_result.get("thread")
        if not isinstance(thread, dict) or not isinstance(thread.get("id"), str):
            raise ProbeError("thread/start returned no thread id")
        thread_id = thread["id"]

        for sequence in range(1, count + 1):
            if restart_after is not None and sequence == restart_after + 1:
                server.close()
                server = StdioAppServer(codex_binary=codex_binary, timeout=timeout)
                _initialize_server(server)
                resume_result = server.request(
                    "thread/resume",
                    {
                        "threadId": thread_id,
                        "cwd": str(workdir.resolve()),
                        "sandbox": "read-only",
                        "approvalPolicy": "never",
                        "developerInstructions": (
                            "Reliability probe only. Never call tools, access files, or perform "
                            "actions. Reply with exactly the text requested by each user message."
                        ),
                    },
                )
                resumed_thread = resume_result.get("thread")
                if not isinstance(resumed_thread, dict) or resumed_thread.get("id") != thread_id:
                    raise ProbeError("thread/resume returned a different thread id")

            nonce = uuid.uuid4().hex
            client_message_id = f"vb-lab-{nonce}"
            expected_reply = f"VB_ACK_{sequence:03d}_{nonce}"
            started = time.monotonic()
            turn_result = server.request(
                "turn/start",
                {
                    "threadId": thread_id,
                    "clientUserMessageId": client_message_id,
                    "input": [
                        {
                            "type": "text",
                            "text": f"Odpověz přesně tímto jediným řádkem: {expected_reply}",
                        }
                    ],
                    "effort": "low",
                    "sandboxPolicy": {"type": "readOnly"},
                    "approvalPolicy": "never",
                },
            )
            turn = turn_result.get("turn")
            if not isinstance(turn, dict) or not isinstance(turn.get("id"), str):
                raise ProbeError("turn/start returned no turn id")
            turn_id = turn["id"]

            user_item_count = 0
            exact_reply_confirmed = False
            turn_status = ""
            while turn_status == "":
                message = server.receive(
                    lambda candidate: (
                        isinstance(candidate.get("params"), dict)
                        and candidate["params"].get("threadId") == thread_id
                        and (
                            candidate["params"].get("turnId") == turn_id
                            or (
                                isinstance(candidate["params"].get("turn"), dict)
                                and candidate["params"]["turn"].get("id") == turn_id
                            )
                        )
                    ),
                    description=f"event for turn {turn_id}",
                )
                method = message.get("method")
                item = _item_from_notification(message)
                if method == "item/completed" and item:
                    if item.get("type") == "userMessage" and item.get("clientId") == client_message_id:
                        user_item_count += 1
                    if item.get("type") == "agentMessage" and item.get("text") == expected_reply:
                        exact_reply_confirmed = True
                if method == "turn/completed":
                    completed_turn = message["params"].get("turn", {})
                    turn_status = str(completed_turn.get("status", ""))

            evidence.append(
                DeliveryEvidence(
                    sequence=sequence,
                    client_message_id=client_message_id,
                    thread_id=thread_id,
                    turn_id=turn_id,
                    user_item_confirmed=user_item_count >= 1,
                    turn_status=turn_status,
                    exact_reply_confirmed=exact_reply_confirmed,
                    duplicate_user_items=max(0, user_item_count - 1),
                    duration_ms=round((time.monotonic() - started) * 1000),
                )
            )
            if not evidence[-1].passed:
                break
    finally:
        server.close()
    return evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--codex-binary", default="codex")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print aggregate evidence without per-turn protocol identifiers.",
    )
    parser.add_argument(
        "--restart-after",
        type=int,
        help=(
            "Persist the isolated lab thread, restart app-server after this many turns, "
            "then resume by thread id. Must be lower than --count."
        ),
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path(tempfile.gettempdir()),
        help="Read-only lab cwd; defaults to the system temporary directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        results = run_probe(
            count=args.count,
            timeout=args.timeout,
            codex_binary=args.codex_binary,
            workdir=args.workdir,
            restart_after=args.restart_after,
        )
    except (OSError, ProbeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    passed = len(results) == args.count and all(item.passed for item in results)
    output = {
        "passed": passed,
        "requested": args.count,
        "completed": len(results),
        "failures": sum(not item.passed for item in results),
    }
    if results:
        durations = [item.duration_ms for item in results]
        output["duration_ms"] = {
            "minimum": min(durations),
            "maximum": max(durations),
            "average": round(sum(durations) / len(durations)),
        }
    if not args.summary_only:
        output["results"] = [asdict(item) | {"passed": item.passed} for item in results]
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
