from __future__ import annotations

import argparse
import hashlib
import hmac
import ipaddress
import json
import os
import re
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, replace
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import BinaryIO, Callable
from urllib.parse import unquote, urlsplit

from app.camino_receiver import ReceiverError, hash_file, validate_asset_id, validate_sha256


DEFAULT_CHUNK_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_BYTES = 512 * 1024 * 1024
DEFAULT_PORT = 8765
CREATE_PATTERN = re.compile(r"/v1/c02b/synthetic-assets/([^/]+)/sessions")
STATUS_PATTERN = re.compile(r"/v1/c02b/synthetic-assets/([^/]+)/status")
CHUNK_PATTERN = re.compile(r"/v1/c02b/synthetic-assets/([^/]+)/chunks/([0-9]+)")
FINALIZE_PATTERN = re.compile(r"/v1/c02b/synthetic-assets/([^/]+)/finalize")


@dataclass(frozen=True)
class ChunkManifest:
    schema: int
    asset_id: str
    byte_count: int
    sha256: str
    chunk_size: int
    chunk_count: int
    state: str = "uploading"


@dataclass(frozen=True)
class ChunkReceipt:
    schema: int
    asset_id: str
    chunk_index: int
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class VerifiedChunkedAsset:
    schema: int
    asset_id: str
    byte_count: int
    sha256: str
    chunk_count: int
    state: str = "verified"
    content_kind: str = "synthetic"


class ChunkedSyntheticAssetStore:
    """Persistent, create-only C02b chunk receiver for synthetic experiments."""

    def __init__(
        self,
        root: Path,
        *,
        max_bytes: int = DEFAULT_MAX_BYTES,
        max_chunk_bytes: int = DEFAULT_CHUNK_BYTES,
        before_verify: Callable[[str], None] | None = None,
        read_delay_seconds_per_mib: float = 0,
    ) -> None:
        if max_bytes <= 0 or max_chunk_bytes <= 0 or read_delay_seconds_per_mib < 0:
            raise ValueError("receiver limits must be positive")
        self.root = Path(root)
        self.max_bytes = max_bytes
        self.max_chunk_bytes = max_chunk_bytes
        self.before_verify = before_verify
        self.read_delay_seconds_per_mib = read_delay_seconds_per_mib
        self.sessions = self.root / "sessions"
        self.objects = self.root / "objects"
        self.receipts = self.root / "receipts"
        self.staging = self.root / ".staging"
        self._lock = threading.RLock()
        for directory in (self.root, self.sessions, self.objects, self.receipts, self.staging):
            self._prepare_directory(directory)

    def create_session(
        self,
        *,
        asset_id: str,
        byte_count: int,
        sha256: str,
        chunk_size: int = DEFAULT_CHUNK_BYTES,
    ) -> tuple[dict[str, object], bool]:
        asset_id = validate_asset_id(asset_id)
        sha256 = validate_sha256(sha256)
        if byte_count <= 0 or byte_count > self.max_bytes:
            raise ReceiverError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "invalid_asset_size")
        if chunk_size <= 0 or chunk_size > self.max_chunk_bytes:
            raise ReceiverError(HTTPStatus.BAD_REQUEST, "invalid_chunk_size")
        chunk_count = (byte_count + chunk_size - 1) // chunk_size
        manifest = ChunkManifest(
            schema=1,
            asset_id=asset_id,
            byte_count=byte_count,
            sha256=sha256,
            chunk_size=chunk_size,
            chunk_count=chunk_count,
        )
        with self._lock:
            session = self._session_directory(asset_id, create=True)
            path = session / "manifest.json"
            if path.exists():
                existing = self._load_manifest(asset_id)
                if self._identity(existing) != self._identity(manifest):
                    raise ReceiverError(HTTPStatus.CONFLICT, "asset_identity_conflict")
                return self.status(asset_id), False
            self._atomic_json(path, asdict(manifest))
            return self.status(asset_id), True

    def receive_chunk(
        self,
        *,
        asset_id: str,
        chunk_index: int,
        expected_sha256: str,
        content_length: int,
        stream: BinaryIO,
    ) -> tuple[dict[str, object], bool]:
        asset_id = validate_asset_id(asset_id)
        expected_sha256 = validate_sha256(expected_sha256)
        with self._lock:
            manifest = self._load_manifest(asset_id)
            if chunk_index < 0 or chunk_index >= manifest.chunk_count:
                raise ReceiverError(HTTPStatus.BAD_REQUEST, "invalid_chunk_index")
            expected_length = self._chunk_length(manifest, chunk_index)
            if content_length != expected_length:
                raise ReceiverError(HTTPStatus.BAD_REQUEST, "invalid_chunk_length")
            session = self._session_directory(asset_id)
            chunks = session / "chunks"
            destination = chunks / f"{chunk_index:08d}.part"
            receipt_path = chunks / f"{chunk_index:08d}.json"
            if destination.exists() or receipt_path.exists():
                receipt = self._verified_chunk(manifest, chunk_index)
                if receipt is None:
                    raise ReceiverError(HTTPStatus.CONFLICT, "chunk_identity_conflict")
                if receipt.sha256 != expected_sha256:
                    raise ReceiverError(HTTPStatus.CONFLICT, "chunk_identity_conflict")
                return self.status(asset_id), False

            temporary = self._read_staged(
                prefix=f".{asset_id}.{chunk_index}.",
                content_length=content_length,
                stream=stream,
            )
            try:
                actual_sha256 = hash_file(temporary)
                if not hmac.compare_digest(actual_sha256, expected_sha256):
                    raise ReceiverError(HTTPStatus.UNPROCESSABLE_ENTITY, "chunk_hash_mismatch")
                os.link(temporary, destination)
                self._fsync_directory(chunks)
                self._atomic_json(
                    receipt_path,
                    asdict(
                        ChunkReceipt(
                            schema=1,
                            asset_id=asset_id,
                            chunk_index=chunk_index,
                            byte_count=content_length,
                            sha256=actual_sha256,
                        )
                    ),
                )
            except FileExistsError as error:
                raise ReceiverError(HTTPStatus.CONFLICT, "chunk_identity_conflict") from error
            finally:
                temporary.unlink(missing_ok=True)
            return self.status(asset_id), True

    def status(self, asset_id: str) -> dict[str, object]:
        asset_id = validate_asset_id(asset_id)
        with self._lock:
            manifest = self._load_manifest(asset_id)
            accepted = [
                index
                for index in range(manifest.chunk_count)
                if self._verified_chunk(manifest, index) is not None
            ]
            missing = [index for index in range(manifest.chunk_count) if index not in accepted]
            body: dict[str, object] = {
                "asset_id": asset_id,
                "state": manifest.state,
                "byte_count": manifest.byte_count,
                "sha256": manifest.sha256,
                "chunk_size": manifest.chunk_size,
                "chunk_count": manifest.chunk_count,
                "accepted_chunks": accepted,
                "missing_chunks": missing,
            }
            receipt_path = self.receipts / f"{asset_id}.json"
            if manifest.state == "verified" and receipt_path.is_file() and not receipt_path.is_symlink():
                body["receipt"] = self._read_json(receipt_path)
            return body

    def finalize(self, asset_id: str) -> tuple[VerifiedChunkedAsset, bool]:
        asset_id = validate_asset_id(asset_id)
        with self._lock:
            manifest = self._load_manifest(asset_id)
            existing = self._existing_verified(manifest)
            if existing is not None:
                return existing, False
            status = self.status(asset_id)
            if status["missing_chunks"]:
                raise ReceiverError(HTTPStatus.CONFLICT, "missing_chunks")
            self._write_manifest(replace(manifest, state="verifying"))

        if self.before_verify is not None:
            self.before_verify(asset_id)

        with self._lock:
            manifest = self._load_manifest(asset_id)
            temporary = self._assemble(manifest)
            try:
                actual_size = temporary.stat().st_size
                actual_hash = hash_file(temporary)
                if actual_size != manifest.byte_count or not hmac.compare_digest(
                    actual_hash, manifest.sha256
                ):
                    self._write_manifest(replace(manifest, state="verification_failed"))
                    raise ReceiverError(HTTPStatus.UNPROCESSABLE_ENTITY, "asset_hash_mismatch")
                receipt = VerifiedChunkedAsset(
                    schema=1,
                    asset_id=asset_id,
                    byte_count=actual_size,
                    sha256=actual_hash,
                    chunk_count=manifest.chunk_count,
                )
                created = self._install_object(temporary, receipt)
                self._install_receipt(receipt)
                self._write_manifest(replace(manifest, state="verified"))
                return receipt, created
            finally:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _identity(manifest: ChunkManifest) -> tuple[object, ...]:
        return (
            manifest.asset_id,
            manifest.byte_count,
            manifest.sha256,
            manifest.chunk_size,
            manifest.chunk_count,
        )

    @staticmethod
    def _chunk_length(manifest: ChunkManifest, index: int) -> int:
        if index < manifest.chunk_count - 1:
            return manifest.chunk_size
        return manifest.byte_count - (manifest.chunk_size * index)

    def _session_directory(self, asset_id: str, *, create: bool = False) -> Path:
        path = self.sessions / asset_id
        if create and not path.exists():
            path.mkdir(mode=0o700)
            (path / "chunks").mkdir(mode=0o700)
            self._fsync_directory(self.sessions)
        self._prepare_directory(path)
        self._prepare_directory(path / "chunks")
        return path

    def _load_manifest(self, asset_id: str) -> ChunkManifest:
        path = self.sessions / asset_id / "manifest.json"
        if path.is_symlink() or not path.is_file():
            raise ReceiverError(HTTPStatus.NOT_FOUND, "upload_session_not_found")
        try:
            return ChunkManifest(**self._read_json(path))
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            raise ReceiverError(HTTPStatus.CONFLICT, "invalid_upload_session") from error

    def _write_manifest(self, manifest: ChunkManifest) -> None:
        self._atomic_json(self.sessions / manifest.asset_id / "manifest.json", asdict(manifest))

    def _verified_chunk(self, manifest: ChunkManifest, index: int) -> ChunkReceipt | None:
        chunks = self.sessions / manifest.asset_id / "chunks"
        data_path = chunks / f"{index:08d}.part"
        receipt_path = chunks / f"{index:08d}.json"
        if (
            data_path.is_symlink()
            or receipt_path.is_symlink()
            or not data_path.is_file()
            or not receipt_path.is_file()
        ):
            return None
        try:
            receipt = ChunkReceipt(**self._read_json(receipt_path))
        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
            return None
        expected_length = self._chunk_length(manifest, index)
        if (
            receipt.asset_id != manifest.asset_id
            or receipt.chunk_index != index
            or receipt.byte_count != expected_length
            or data_path.stat().st_size != expected_length
            or not hmac.compare_digest(hash_file(data_path), receipt.sha256)
        ):
            return None
        return receipt

    def _assemble(self, manifest: ChunkManifest) -> Path:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{manifest.asset_id}.", suffix=".assembled", dir=self.staging
        )
        path = Path(name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as output:
                descriptor = -1
                for index in range(manifest.chunk_count):
                    source = self.sessions / manifest.asset_id / "chunks" / f"{index:08d}.part"
                    with source.open("rb") as handle:
                        for block in iter(lambda: handle.read(1024 * 1024), b""):
                            output.write(block)
                output.flush()
                os.fsync(output.fileno())
            return path
        except Exception:
            path.unlink(missing_ok=True)
            raise
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def _existing_verified(self, manifest: ChunkManifest) -> VerifiedChunkedAsset | None:
        object_path = self.objects / f"{manifest.asset_id}.bin"
        receipt_path = self.receipts / f"{manifest.asset_id}.json"
        if not object_path.exists() and not receipt_path.exists():
            return None
        if (
            object_path.is_symlink()
            or receipt_path.is_symlink()
            or not object_path.is_file()
            or not receipt_path.is_file()
        ):
            raise ReceiverError(HTTPStatus.CONFLICT, "asset_identity_conflict")
        try:
            receipt = VerifiedChunkedAsset(**self._read_json(receipt_path))
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            raise ReceiverError(HTTPStatus.CONFLICT, "asset_identity_conflict") from error
        if (
            receipt.asset_id != manifest.asset_id
            or receipt.byte_count != manifest.byte_count
            or receipt.sha256 != manifest.sha256
            or receipt.chunk_count != manifest.chunk_count
            or object_path.stat().st_size != manifest.byte_count
            or not hmac.compare_digest(hash_file(object_path), manifest.sha256)
        ):
            raise ReceiverError(HTTPStatus.CONFLICT, "asset_identity_conflict")
        if manifest.state != "verified":
            self._write_manifest(replace(manifest, state="verified"))
        return receipt

    def _install_object(self, temporary: Path, receipt: VerifiedChunkedAsset) -> bool:
        destination = self.objects / f"{receipt.asset_id}.bin"
        if destination.exists() or destination.is_symlink():
            if (
                destination.is_symlink()
                or not destination.is_file()
                or destination.stat().st_size != receipt.byte_count
                or not hmac.compare_digest(hash_file(destination), receipt.sha256)
            ):
                raise ReceiverError(HTTPStatus.CONFLICT, "asset_identity_conflict")
            return False
        try:
            os.link(temporary, destination)
            self._fsync_directory(self.objects)
            return True
        except FileExistsError:
            return self._install_object(temporary, receipt)

    def _install_receipt(self, receipt: VerifiedChunkedAsset) -> None:
        path = self.receipts / f"{receipt.asset_id}.json"
        payload = self._json_bytes(asdict(receipt))
        if path.exists():
            if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
                raise ReceiverError(HTTPStatus.CONFLICT, "receipt_identity_conflict")
            return
        descriptor, name = tempfile.mkstemp(prefix=f".{receipt.asset_id}.", dir=self.staging)
        temporary = Path(name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, path)
            self._fsync_directory(self.receipts)
        except FileExistsError:
            if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
                raise ReceiverError(HTTPStatus.CONFLICT, "receipt_identity_conflict")
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            temporary.unlink(missing_ok=True)

    def _read_staged(self, *, prefix: str, content_length: int, stream: BinaryIO) -> Path:
        descriptor, name = tempfile.mkstemp(prefix=prefix, suffix=".chunk", dir=self.staging)
        path = Path(name)
        try:
            os.fchmod(descriptor, 0o600)
            remaining = content_length
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                while remaining:
                    block = stream.read(min(1024 * 1024, remaining))
                    if not block:
                        raise ReceiverError(HTTPStatus.BAD_REQUEST, "incomplete_chunk")
                    handle.write(block)
                    remaining -= len(block)
                    if self.read_delay_seconds_per_mib:
                        time.sleep(
                            self.read_delay_seconds_per_mib
                            * (len(block) / (1024 * 1024))
                        )
                handle.flush()
                os.fsync(handle.fileno())
            return path
        except Exception:
            path.unlink(missing_ok=True)
            raise
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def _atomic_json(self, path: Path, value: dict[str, object]) -> None:
        descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=self.staging)
        temporary = Path(name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(self._json_bytes(value))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            self._fsync_directory(path.parent)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _json_bytes(value: dict[str, object]) -> bytes:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"

    @staticmethod
    def _read_json(path: Path) -> dict[str, object]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    @staticmethod
    def _prepare_directory(directory: Path) -> None:
        if directory.exists():
            if directory.is_symlink() or not directory.is_dir():
                raise ValueError(f"unsafe receiver directory: {directory.name}")
            return
        directory.mkdir(mode=0o700)

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def make_handler(
    *, store: ChunkedSyntheticAssetStore, bearer_token: str
) -> type[BaseHTTPRequestHandler]:
    if len(bearer_token) < 32:
        raise ValueError("bearer token must have at least 32 characters")

    class Handler(BaseHTTPRequestHandler):
        server_version = "CaminoC02bReceiver/1"
        sys_version = ""

        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(30)

        def do_GET(self) -> None:  # noqa: N802
            if not self._authorized():
                self._respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            target = urlsplit(self.path)
            if target.query or target.fragment:
                self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            if target.path == "/healthz":
                self._respond(HTTPStatus.OK, {"status": "ok", "scope": "c02b_synthetic_only"})
                return
            match = STATUS_PATTERN.fullmatch(target.path)
            if match is None:
                self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            self._call(lambda: (HTTPStatus.OK, store.status(unquote(match.group(1)))))

        def do_POST(self) -> None:  # noqa: N802
            self.close_connection = True
            if not self._authorized():
                self._respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            target = urlsplit(self.path)
            if target.query or target.fragment:
                self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            create = CREATE_PATTERN.fullmatch(target.path)
            finalize = FINALIZE_PATTERN.fullmatch(target.path)
            if create is not None:
                if self.headers.get("X-Camino-Synthetic") != "1":
                    self._respond(HTTPStatus.BAD_REQUEST, {"error": "synthetic_marker_required"})
                    return
                try:
                    body = self._json_body()
                    status, created = store.create_session(
                        asset_id=unquote(create.group(1)),
                        byte_count=int(body.get("byte_count", 0)),
                        sha256=str(body.get("sha256", "")),
                        chunk_size=int(body.get("chunk_size", DEFAULT_CHUNK_BYTES)),
                    )
                    status["created"] = created
                    self._respond(HTTPStatus.CREATED if created else HTTPStatus.OK, status)
                except ReceiverError as error:
                    self._respond(error.status, {"error": error.code})
                except (TypeError, ValueError, json.JSONDecodeError):
                    self._respond(HTTPStatus.BAD_REQUEST, {"error": "invalid_manifest"})
                return
            if finalize is not None:
                try:
                    receipt, created = store.finalize(unquote(finalize.group(1)))
                    body = asdict(receipt)
                    body["created"] = created
                    self._respond(HTTPStatus.CREATED if created else HTTPStatus.OK, body)
                except ReceiverError as error:
                    self._respond(error.status, {"error": error.code})
                return
            self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def do_PUT(self) -> None:  # noqa: N802
            self.close_connection = True
            if not self._authorized():
                self._respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            target = urlsplit(self.path)
            match = CHUNK_PATTERN.fullmatch(target.path)
            if match is None or target.query or target.fragment:
                self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            if self.headers.get("X-Camino-Synthetic") != "1":
                self._respond(HTTPStatus.BAD_REQUEST, {"error": "synthetic_marker_required"})
                return
            lengths = self.headers.get_all("Content-Length", failobj=[])
            if (
                self.headers.get("Transfer-Encoding") is not None
                or len(lengths) != 1
                or not lengths[0].isdigit()
            ):
                self._respond(HTTPStatus.LENGTH_REQUIRED, {"error": "content_length_required"})
                return
            try:
                status, created = store.receive_chunk(
                    asset_id=unquote(match.group(1)),
                    chunk_index=int(match.group(2)),
                    expected_sha256=self.headers.get("X-Camino-Chunk-SHA256", ""),
                    content_length=int(lengths[0]),
                    stream=self.rfile,
                )
                status["chunk_created"] = created
                self._respond(HTTPStatus.CREATED if created else HTTPStatus.OK, status)
            except ReceiverError as error:
                self._respond(error.status, {"error": error.code})
            except (OSError, TimeoutError):
                self._respond(HTTPStatus.BAD_REQUEST, {"error": "incomplete_chunk"})

        def _json_body(self) -> dict[str, object]:
            lengths = self.headers.get_all("Content-Length", failobj=[])
            if (
                self.headers.get("Transfer-Encoding") is not None
                or len(lengths) != 1
                or not lengths[0].isdigit()
            ):
                raise ReceiverError(HTTPStatus.LENGTH_REQUIRED, "content_length_required")
            length = int(lengths[0])
            if length <= 0 or length > 4096:
                raise ReceiverError(HTTPStatus.BAD_REQUEST, "invalid_manifest")
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict):
                raise ValueError("JSON object required")
            return value

        def _call(self, operation: Callable[[], tuple[HTTPStatus, dict[str, object]]]) -> None:
            try:
                status, body = operation()
                self._respond(status, body)
            except ReceiverError as error:
                self._respond(error.status, {"error": error.code})

        def _authorized(self) -> bool:
            authorization = self.headers.get("Authorization", "")
            prefix = "Bearer "
            return authorization.startswith(prefix) and hmac.compare_digest(
                authorization[len(prefix) :], bearer_token
            )

        def _respond(self, status: HTTPStatus, body: dict[str, object]) -> None:
            payload = ChunkedSyntheticAssetStore._json_bytes(body)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format: str, *args: object) -> None:
            return

    return Handler


def make_server(
    *,
    store: ChunkedSyntheticAssetStore,
    bearer_token: str,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
) -> ThreadingHTTPServer:
    try:
        if not ipaddress.ip_address(host).is_loopback:
            raise ValueError("C02b receiver must bind to a loopback address")
    except ValueError as error:
        if "loopback" in str(error):
            raise
        raise ValueError("C02b receiver host must be a loopback IP address") from error
    server = ThreadingHTTPServer((host, port), make_handler(store=store, bearer_token=bearer_token))
    server.daemon_threads = True
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Camino C02b chunk receiver")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--read-delay-ms-per-mib", type=float, default=0)
    parser.add_argument("--verify-delay-seconds", type=float, default=0)
    args = parser.parse_args(argv)
    root = args.root or (
        Path(os.environ["CAMINO_C02B_ROOT"])
        if "CAMINO_C02B_ROOT" in os.environ
        else None
    )
    token = os.environ.get("CAMINO_C02B_TOKEN", "")
    if root is None:
        parser.error("--root or CAMINO_C02B_ROOT is required")
    if len(token) < 32:
        parser.error("CAMINO_C02B_TOKEN with at least 32 characters is required")
    if not 0 <= args.read_delay_ms_per_mib <= 5_000:
        parser.error("--read-delay-ms-per-mib must be between 0 and 5000")
    if not 0 <= args.verify_delay_seconds <= 300:
        parser.error("--verify-delay-seconds must be between 0 and 300")
    store = ChunkedSyntheticAssetStore(
        root,
        max_bytes=args.max_bytes,
        read_delay_seconds_per_mib=args.read_delay_ms_per_mib / 1_000,
        before_verify=(
            (lambda _asset_id: time.sleep(args.verify_delay_seconds))
            if args.verify_delay_seconds
            else None
        ),
    )
    server = make_server(store=store, bearer_token=token, host=args.host, port=args.port)
    print(
        f"Camino C02b receiver listens on {args.host}:{server.server_port}; "
        "HTTPS is required upstream."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
