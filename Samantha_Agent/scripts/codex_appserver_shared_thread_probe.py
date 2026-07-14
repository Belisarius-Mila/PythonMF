#!/usr/bin/env python3
"""Isolated proof that two clients can use one Codex app-server thread."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.codex_appserver import (
    AppServerError,
    CodexAppServerClient,
    UnixSocketAppServerTransport,
    codex_environment,
)


PROBE_INSTRUCTIONS = (
    "Jsi izolovaný read-only Adam pro test sdíleného app-server vlákna. "
    "Nevyvolávej nástroje a neměň žádná data. Dodrž přesně požadovaný formát odpovědi."
)


class SharedThreadProbeError(RuntimeError):
    """Raised when the isolated server or shared-thread evidence is incomplete."""


def unix_server_command(*, codex_binary: str, socket_path: Path) -> list[str]:
    target = Path(socket_path).expanduser()
    if not target.is_absolute():
        raise SharedThreadProbeError("Cesta k testovacímu socketu musí být absolutní.")
    return [codex_binary, "app-server", "--listen", f"unix://{target}"]


class IsolatedUnixAppServer:
    """Own one temporary app-server process and remove only its own socket."""

    def __init__(
        self,
        *,
        socket_path: Path,
        codex_binary: str = "codex",
        startup_timeout: float = 15.0,
        process_factory: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
    ):
        self.socket_path = Path(socket_path).expanduser()
        self.codex_binary = codex_binary
        self.startup_timeout = startup_timeout
        self._process_factory = process_factory
        self._process: subprocess.Popen[str] | None = None

    @property
    def process_id(self) -> int:
        return int(self._process.pid) if self._process is not None else 0

    def start(self) -> None:
        if self._process is not None:
            raise SharedThreadProbeError("Testovací app-server už byl spuštěn.")
        if self.socket_path.exists():
            raise SharedThreadProbeError("Testovací socket už existuje; nic nepřepisuji.")
        self._process = self._process_factory(
            unix_server_command(codex_binary=self.codex_binary, socket_path=self.socket_path),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=codex_environment(),
        )
        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                detail = (self._process.stderr.read() if self._process.stderr else "").strip()
                raise SharedThreadProbeError(
                    f"Testovací app-server skončil při startu: {detail or self._process.returncode}"
                )
            if self.socket_path.exists():
                return
            time.sleep(0.05)
        raise SharedThreadProbeError("Testovací app-server nevytvořil Unix socket včas.")

    def close(self) -> None:
        process = self._process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        self._process = None
        try:
            if self.socket_path.is_socket():
                self.socket_path.unlink()
        except OSError:
            pass

    def __enter__(self) -> "IsolatedUnixAppServer":
        self.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


@dataclass(frozen=True)
class SharedThreadEvidence:
    server_process_id: int
    first_connection_id: str
    second_connection_id: str
    thread_id: str
    resumed_thread_id: str
    first_turn_id: str
    second_turn_id: str
    first_reply_exact: bool
    context_reply_exact: bool
    first_delivery_confirmed: bool
    second_delivery_confirmed: bool
    archived_after_probe: bool

    @property
    def passed(self) -> bool:
        return (
            self.server_process_id > 0
            and bool(self.first_connection_id)
            and bool(self.second_connection_id)
            and self.first_connection_id != self.second_connection_id
            and bool(self.thread_id)
            and self.resumed_thread_id == self.thread_id
            and bool(self.first_turn_id)
            and bool(self.second_turn_id)
            and self.first_reply_exact
            and self.context_reply_exact
            and self.first_delivery_confirmed
            and self.second_delivery_confirmed
            and self.archived_after_probe
        )


def run_probe(*, timeout: float, codex_binary: str) -> SharedThreadEvidence:
    with tempfile.TemporaryDirectory(prefix="samantha-shared-thread-") as temp_dir:
        root = Path(temp_dir)
        socket_path = root / "app-server.sock"
        workdir = root / "workspace"
        workdir.mkdir()
        nonce = uuid.uuid4().hex[:16].upper()
        remembered_code = f"SAME_THREAD_{nonce}"
        ready_code = f"READY_{nonce}"
        def transport_factory(**kwargs: Any) -> UnixSocketAppServerTransport:
            return UnixSocketAppServerTransport(socket_path=socket_path, **kwargs)

        with IsolatedUnixAppServer(socket_path=socket_path, codex_binary=codex_binary) as server:
            first = CodexAppServerClient(
                codex_binary=codex_binary,
                timeout=timeout,
                transport_factory=transport_factory,
            )
            second: CodexAppServerClient | None = None
            thread_id = ""
            archived = False
            try:
                thread_id = first.start_thread(
                    cwd=workdir,
                    ephemeral=False,
                    developer_instructions=PROBE_INSTRUCTIONS,
                    sandbox="read-only",
                    approval_policy="never",
                )
                first_receipt = first.send_text(
                    thread_id=thread_id,
                    client_message_id=f"shared-probe-first-{nonce.lower()}",
                    text=(
                        f"Zapamatuj si kontrolní kód {remembered_code}. "
                        f"Nyní odpověz přesně jediným řádkem: {ready_code}"
                    ),
                )

                second = CodexAppServerClient(
                    codex_binary=codex_binary,
                    timeout=timeout,
                    transport_factory=transport_factory,
                )
                resumed_thread_id = second.resume_thread(
                    thread_id,
                    cwd=workdir,
                    developer_instructions=PROBE_INSTRUCTIONS,
                    sandbox="read-only",
                    approval_policy="never",
                )
                second_receipt = second.send_text(
                    thread_id=resumed_thread_id,
                    client_message_id=f"shared-probe-second-{nonce.lower()}",
                    text="Odpověz přesně jediným řádkem kontrolním kódem z předchozí zprávy.",
                )
                second.archive_thread(thread_id)
                archived = True
                return SharedThreadEvidence(
                    server_process_id=server.process_id,
                    first_connection_id=first.connection_id,
                    second_connection_id=second.connection_id,
                    thread_id=thread_id,
                    resumed_thread_id=resumed_thread_id,
                    first_turn_id=first_receipt.turn_id,
                    second_turn_id=second_receipt.turn_id,
                    first_reply_exact=first_receipt.answer == ready_code,
                    context_reply_exact=second_receipt.answer == remembered_code,
                    first_delivery_confirmed=first_receipt.delivered,
                    second_delivery_confirmed=second_receipt.delivered,
                    archived_after_probe=archived,
                )
            finally:
                if thread_id and not archived:
                    for archive_client in (second, first):
                        if archive_client is None:
                            continue
                        try:
                            archive_client.archive_thread(thread_id)
                            break
                        except AppServerError:
                            continue
                if second is not None:
                    second.close()
                first.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--codex-binary", default="codex")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        evidence = run_probe(timeout=args.timeout, codex_binary=args.codex_binary)
    except (OSError, AppServerError, SharedThreadProbeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    payload: dict[str, Any] = asdict(evidence) | {"passed": evidence.passed}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if evidence.passed else 1


if __name__ == "__main__":
    sys.exit(main())
