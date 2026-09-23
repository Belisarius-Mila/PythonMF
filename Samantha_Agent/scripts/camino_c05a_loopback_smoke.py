#!/usr/bin/env python3
"""Run a one-shot C05a smoke test on loopback with synthetic data only."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_RECEIPT_ROOT = PROJECT_ROOT / "data" / "private" / "camino" / "c05a_loopback_smoke"
TEMP_ROOT = Path("/private/tmp")
CHUNK_SIZE = 256 * 1024
FIXTURE_BYTES = 1024 * 1024 + 123


def uid(number: int) -> str:
    return f"00000000-0000-0000-0000-{number:012x}"


def synthetic_media() -> bytes:
    """Return deterministic, non-personal bytes large enough for several chunks."""
    seed = bytes(range(256))
    repeats, remainder = divmod(FIXTURE_BYTES, len(seed))
    return seed * repeats + seed[:remainder]


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _private_directory(path: Path) -> None:
    if path.is_symlink():
        raise RuntimeError("private_directory_is_symlink")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise RuntimeError("private_directory_is_invalid")
    path.chmod(0o700)


def write_private_json(path: Path, value: dict[str, Any]) -> None:
    """Create one private receipt without overwriting or deleting evidence."""
    _private_directory(path.parent)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def public_summary(receipt: dict[str, Any]) -> str:
    checks = receipt.get("checks", {})
    passed = sum(value is True for value in checks.values())
    total = len(checks)
    if receipt.get("state") == "passed":
        return (
            "C05a loopback smoke PASS; "
            f"run_id={receipt['run_id']}; checks={passed}/{total}; "
            f"bytes={receipt['byte_count']}; chunks={receipt['chunk_count']}; "
            "Serve/Funnel/iPhone beze změny."
        )
    return (
        "C05a loopback smoke FAIL; "
        f"run_id={receipt['run_id']}; failure_type={receipt.get('failure_type', 'unknown')}; "
        "syntetické důkazy zůstaly zachované."
    )


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _request(
    port: int,
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: bytes | None = None,
    content_type: str | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    request_headers = {"Connection": "close"}
    if token is not None:
        request_headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        request_headers["Content-Length"] = str(len(body))
    if content_type is not None:
        request_headers["Content-Type"] = content_type
    request_headers.update(headers or {})
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        raw = response.read()
        decoded = json.loads(raw.decode("utf-8")) if raw else {}
        if not isinstance(decoded, dict):
            raise RuntimeError("response_is_not_an_object")
        return response.status, decoded
    finally:
        connection.close()


def _expect_status(
    port: int,
    expected: int,
    method: str,
    path: str,
    **kwargs: Any,
) -> dict[str, Any]:
    status, body = _request(port, method, path, **kwargs)
    if status != expected:
        code = body.get("error", {}).get("code") if isinstance(body.get("error"), dict) else "unknown"
        raise RuntimeError(f"unexpected_http_status_{status}_{code}")
    return body


def _start_server(run_dir: Path, port: int) -> tuple[subprocess.Popen[bytes], Any]:
    log_path = run_dir / "server.log"
    descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    log_handle = os.fdopen(descriptor, "ab", buffering=0)
    environment = os.environ.copy()
    environment.update({
        "CAMINO_C05A_METADATA_DB": str(run_dir / "metadata.sqlite"),
        "CAMINO_C05A_AUTH_DB": str(run_dir / "auth.sqlite"),
        "CAMINO_C05A_MEDIA_DB": str(run_dir / "media.sqlite"),
        "CAMINO_C05A_MEDIA_ROOT": str(run_dir / "media"),
    })
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "camino.server.main", "--host", "127.0.0.1", "--port", str(port)],
            cwd=PROJECT_ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except Exception:
        log_handle.close()
        raise
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            _stop_owned_process(process, log_handle)
            raise RuntimeError("server_exited_before_ready")
        try:
            status, body = _request(port, "GET", "/healthz")
            if status == 401 and body.get("error", {}).get("code") == "unauthorized":
                return process, log_handle
        except (ConnectionError, OSError, TimeoutError, json.JSONDecodeError):
            pass
        time.sleep(0.1)
    _stop_owned_process(process, log_handle)
    raise RuntimeError("server_readiness_timeout")


def _stop_owned_process(process: subprocess.Popen[bytes] | None, log_handle: Any | None) -> None:
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if log_handle is not None and not log_handle.closed:
        log_handle.close()


def _operation(epoch: str, sequence: int, kind: str, payload: dict[str, Any]) -> bytes:
    return json.dumps({
        "contract_version": 1,
        "epoch": epoch,
        "operation_id": uid(100 + sequence),
        "device_sequence": sequence,
        "device_id": uid(90),
        "kind": kind,
        "expected_revision": None,
        "payload": payload,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def execute() -> dict[str, Any]:
    # C05a dependencies are intentionally imported only in the dedicated environment.
    from camino.domain.codec import wire
    from camino.domain.model import (
        Asset, CaptureTime, JourneyDay, MomentKind, Privacy, TimeSource, Trip, create_moment,
    )
    from camino.server.auth import RevocableTokenStore

    if not TEMP_ROOT.is_dir():
        raise RuntimeError("private_tmp_is_unavailable")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    run_dir = Path(tempfile.mkdtemp(prefix=f"camino-c05a-smoke-{run_id}-", dir=TEMP_ROOT))
    run_dir.chmod(0o700)
    receipt_path = PRIVATE_RECEIPT_ROOT / f"{run_id}.json"
    started_at = _utc_now()
    checks: dict[str, bool] = {}
    token_store: Any | None = None
    token_ids: list[str] = []
    process: subprocess.Popen[bytes] | None = None
    log_handle: Any | None = None
    content = synthetic_media()
    asset_sha256 = digest(content)
    chunk_count = (len(content) + CHUNK_SIZE - 1) // CHUNK_SIZE
    base_receipt: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "started_at": started_at,
        "asset_id": uid(4),
        "byte_count": len(content),
        "sha256": asset_sha256,
        "chunk_count": chunk_count,
        "checks": checks,
        "serve_changed": False,
        "funnel_changed": False,
        "iphone_touched": False,
        "synthetic_only": True,
        "evidence_preserved": True,
    }
    try:
        token_store = RevocableTokenStore(run_dir / "auth.sqlite")
        first_token = secrets.token_urlsafe(48)
        first_token_id = token_store.add(first_token, label="synthetic C05a loopback smoke 1")
        token_ids.append(first_token_id)
        port = _free_loopback_port()
        process, log_handle = _start_server(run_dir, port)

        denied = _expect_status(port, 401, "GET", "/healthz")
        checks["unauthorized_is_401"] = denied.get("error", {}).get("code") == "unauthorized"
        health = _expect_status(port, 200, "GET", "/healthz", token=first_token)
        checks["authorized_health"] = health.get("scope") == "c05a_private_owner"
        state = _expect_status(port, 200, "GET", "/api/v1/state", token=first_token)
        epoch = state["epoch"]

        trip = Trip(uid(1), "Synthetic C05a smoke", "cs", True, True)
        day = JourneyDay(uid(2), trip.id, "2026-09-23")
        captured = CaptureTime(
            int(datetime(2026, 9, 23, 18, tzinfo=timezone.utc).timestamp() * 1000),
            "2026-09-23T20:00:00", 120, "Europe/Prague", TimeSource.DEVICE_CAPTURE,
        )
        moment = create_moment(
            id=uid(3), trip=trip, day=day, kind=MomentKind.VIDEO,
            captured=captured, new_moment_privacy=Privacy.DIARY,
        )
        asset = Asset(uid(4), moment.id, "video", "camera", len(content), asset_sha256, 9000)
        for sequence, kind, value in (
            (1, "create_trip", trip),
            (2, "create_day", day),
            (3, "create_moment", moment),
            (4, "create_asset", asset),
        ):
            accepted = _expect_status(
                port, 200, "POST", "/api/v1/operations", token=first_token,
                body=_operation(epoch, sequence, kind, wire(value)), content_type="application/json",
            )
            if accepted.get("cursor") != sequence or accepted.get("kind") != kind:
                raise RuntimeError("metadata_operation_not_accepted")
        checks["metadata_manifest_accepted"] = True

        session_body = json.dumps(
            {"contract_version": 1, "chunk_size": CHUNK_SIZE}, separators=(",", ":"),
        ).encode("utf-8")
        session = _expect_status(
            port, 201, "POST", f"/api/v1/assets/{asset.id}/upload-session",
            token=first_token, body=session_body, content_type="application/json",
        )
        checks["upload_session_created"] = session.get("chunk_count") == chunk_count

        first_chunk = content[:CHUNK_SIZE]
        chunk_headers = {"X-Camino-Chunk-SHA256": digest(first_chunk)}
        first = _expect_status(
            port, 201, "PUT", f"/api/v1/assets/{asset.id}/chunks/0", token=first_token,
            body=first_chunk, content_type="application/octet-stream", headers=chunk_headers,
        )
        retry = _expect_status(
            port, 200, "PUT", f"/api/v1/assets/{asset.id}/chunks/0", token=first_token,
            body=first_chunk, content_type="application/octet-stream", headers=chunk_headers,
        )
        checks["chunk_retry_idempotent"] = first.get("chunk_created") is True and retry.get("chunk_created") is False
        early = _expect_status(
            port, 409, "POST", f"/api/v1/assets/{asset.id}/finalize", token=first_token, body=b"",
        )
        checks["early_finalize_blocked"] = early.get("error", {}).get("code") == "missing_chunks"

        for index in range(1, chunk_count):
            chunk = content[index * CHUNK_SIZE:(index + 1) * CHUNK_SIZE]
            uploaded = _expect_status(
                port, 201, "PUT", f"/api/v1/assets/{asset.id}/chunks/{index}", token=first_token,
                body=chunk, content_type="application/octet-stream",
                headers={"X-Camino-Chunk-SHA256": digest(chunk)},
            )
            if uploaded.get("chunk_created") is not True:
                raise RuntimeError("chunk_was_not_created")
        status = _expect_status(
            port, 200, "GET", f"/api/v1/assets/{asset.id}/upload-status", token=first_token,
        )
        checks["all_chunks_stored"] = status.get("missing_chunks") == []

        finalized = _expect_status(
            port, 201, "POST", f"/api/v1/assets/{asset.id}/finalize", token=first_token, body=b"",
        )
        repeated = _expect_status(
            port, 200, "POST", f"/api/v1/assets/{asset.id}/finalize", token=first_token, body=b"",
        )
        stable_keys = ("asset_id", "byte_count", "sha256", "chunk_count", "state", "verified_at")
        checks["server_verified_asset"] = (
            finalized.get("created") is True
            and finalized.get("state") == "verified"
            and finalized.get("sha256") == asset_sha256
            and finalized.get("byte_count") == len(content)
        )
        checks["finalize_retry_idempotent"] = (
            repeated.get("created") is False
            and all(finalized.get(key) == repeated.get(key) for key in stable_keys)
        )

        second_token = secrets.token_urlsafe(48)
        second_token_id = token_store.add(second_token, label="synthetic C05a loopback smoke 2")
        token_ids.append(second_token_id)
        if not token_store.revoke(first_token_id):
            raise RuntimeError("first_token_revoke_failed")
        denied_after_revoke = _expect_status(port, 401, "GET", "/healthz", token=first_token)
        checks["first_token_revoked"] = denied_after_revoke.get("error", {}).get("code") == "unauthorized"

        _stop_owned_process(process, log_handle)
        process, log_handle = None, None
        restart_port = _free_loopback_port()
        process, log_handle = _start_server(run_dir, restart_port)
        restarted = _expect_status(
            restart_port, 200, "GET", f"/api/v1/assets/{asset.id}/upload-status", token=second_token,
        )
        checks["verified_receipt_survives_restart"] = (
            restarted.get("state") == "verified"
            and restarted.get("sha256") == asset_sha256
            and restarted.get("byte_count") == len(content)
        )
        if not token_store.revoke(second_token_id):
            raise RuntimeError("second_token_revoke_failed")
        denied_second = _expect_status(restart_port, 401, "GET", "/healthz", token=second_token)
        checks["second_token_revoked"] = denied_second.get("error", {}).get("code") == "unauthorized"

        if not checks or not all(checks.values()):
            raise RuntimeError("one_or_more_checks_failed")
        receipt = {
            **base_receipt,
            "state": "passed",
            "finished_at": _utc_now(),
            "tokens_revoked": token_store.active_count() == 0,
        }
        if not receipt["tokens_revoked"]:
            raise RuntimeError("active_token_remained")
        write_private_json(receipt_path, receipt)
        return receipt
    except Exception as error:
        if token_store is not None:
            for token_id in token_ids:
                try:
                    token_store.revoke(token_id)
                except Exception:
                    pass
        failure = {
            **base_receipt,
            "state": "failed",
            "finished_at": _utc_now(),
            "failure_type": type(error).__name__,
            "tokens_revoked": token_store is not None and token_store.active_count() == 0,
        }
        write_private_json(receipt_path, failure)
        raise
    finally:
        _stop_owned_process(process, log_handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("--execute is required; use the registered confirmed workflow")
    try:
        receipt = execute()
    except Exception as error:
        # Keep paths, tokens, and server detail in the private preserved evidence only.
        print(f"C05a loopback smoke FAIL; failure_type={type(error).__name__}", file=sys.stderr)
        return 1
    print(public_summary(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
