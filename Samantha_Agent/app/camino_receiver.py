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
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import BinaryIO
from urllib.parse import unquote, urlsplit


DEFAULT_MAX_BYTES = 64 * 1024 * 1024
DEFAULT_PORT = 8764
ASSET_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
UPLOAD_PATH_PATTERN = re.compile(r"/v1/c02a/synthetic-assets/([^/]+)")


class ReceiverError(Exception):
    def __init__(self, status: HTTPStatus, code: str) -> None:
        super().__init__(code)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class VerifiedSyntheticAsset:
    schema: int
    asset_id: str
    byte_count: int
    sha256: str
    state: str = "verified"
    content_kind: str = "synthetic"


@dataclass(frozen=True)
class ReceiveResult:
    receipt: VerifiedSyntheticAsset
    created: bool


class SyntheticAssetStore:
    """Create-only C02a storage for non-sensitive synthetic transfer tests."""

    def __init__(self, root: Path, *, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.root = Path(root)
        self.max_bytes = max_bytes
        self.objects = self.root / "objects"
        self.receipts = self.root / "receipts"
        self.staging = self.root / ".staging"
        self._lock = threading.Lock()
        for directory in (self.root, self.objects, self.receipts, self.staging):
            self._prepare_directory(directory)

    def receive(
        self,
        *,
        asset_id: str,
        expected_sha256: str,
        content_length: int,
        stream: BinaryIO,
    ) -> ReceiveResult:
        asset_id = validate_asset_id(asset_id)
        expected_sha256 = validate_sha256(expected_sha256)
        if content_length < 0:
            raise ReceiverError(HTTPStatus.BAD_REQUEST, "invalid_content_length")
        if content_length > self.max_bytes:
            raise ReceiverError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "synthetic_file_too_large")

        with self._lock:
            temporary = self._read_staged(
                asset_id=asset_id,
                content_length=content_length,
                stream=stream,
            )
            try:
                actual_sha256 = hash_file(temporary)
                actual_size = temporary.stat().st_size
                if actual_size != content_length:
                    raise ReceiverError(HTTPStatus.BAD_REQUEST, "incomplete_upload")
                if not hmac.compare_digest(actual_sha256, expected_sha256):
                    raise ReceiverError(HTTPStatus.UNPROCESSABLE_ENTITY, "hash_mismatch")

                receipt = VerifiedSyntheticAsset(
                    schema=1,
                    asset_id=asset_id,
                    byte_count=actual_size,
                    sha256=actual_sha256,
                )
                created = self._install_object(temporary, receipt)
                self._install_receipt(receipt)
                return ReceiveResult(receipt=receipt, created=created)
            finally:
                temporary.unlink(missing_ok=True)

    def _read_staged(self, *, asset_id: str, content_length: int, stream: BinaryIO) -> Path:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{asset_id}.", suffix=".upload", dir=self.staging
        )
        path = Path(name)
        try:
            os.fchmod(descriptor, 0o600)
            remaining = content_length
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                while remaining:
                    chunk = stream.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ReceiverError(HTTPStatus.BAD_REQUEST, "incomplete_upload")
                    handle.write(chunk)
                    remaining -= len(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            return path
        except Exception:
            path.unlink(missing_ok=True)
            raise
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def _install_object(self, temporary: Path, receipt: VerifiedSyntheticAsset) -> bool:
        destination = self.objects / f"{receipt.asset_id}.bin"
        if destination.exists():
            self._verify_existing_object(destination, receipt)
            return False
        try:
            os.link(temporary, destination)
            self._fsync_directory(self.objects)
            return True
        except FileExistsError:
            self._verify_existing_object(destination, receipt)
            return False

    def _verify_existing_object(
        self, destination: Path, receipt: VerifiedSyntheticAsset
    ) -> None:
        if destination.is_symlink() or not destination.is_file():
            raise ReceiverError(HTTPStatus.CONFLICT, "asset_identity_conflict")
        if destination.stat().st_size != receipt.byte_count:
            raise ReceiverError(HTTPStatus.CONFLICT, "asset_identity_conflict")
        if not hmac.compare_digest(hash_file(destination), receipt.sha256):
            raise ReceiverError(HTTPStatus.CONFLICT, "asset_identity_conflict")

    def _install_receipt(self, receipt: VerifiedSyntheticAsset) -> None:
        destination = self.receipts / f"{receipt.asset_id}.json"
        payload = json.dumps(
            asdict(receipt), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8") + b"\n"
        if destination.exists():
            if (
                destination.is_symlink()
                or not destination.is_file()
                or destination.read_bytes() != payload
            ):
                raise ReceiverError(HTTPStatus.CONFLICT, "receipt_identity_conflict")
            return

        descriptor, name = tempfile.mkstemp(
            prefix=f".{receipt.asset_id}.", suffix=".receipt", dir=self.staging
        )
        temporary = Path(name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, destination)
                self._fsync_directory(self.receipts)
            except FileExistsError:
                if (
                    destination.is_symlink()
                    or not destination.is_file()
                    or destination.read_bytes() != payload
                ):
                    raise ReceiverError(HTTPStatus.CONFLICT, "receipt_identity_conflict")
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            temporary.unlink(missing_ok=True)

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


def validate_asset_id(value: str) -> str:
    if not ASSET_ID_PATTERN.fullmatch(value):
        raise ReceiverError(HTTPStatus.BAD_REQUEST, "invalid_asset_id")
    return value


def validate_sha256(value: str) -> str:
    normalized = value.strip().lower()
    if not SHA256_PATTERN.fullmatch(normalized):
        raise ReceiverError(HTTPStatus.BAD_REQUEST, "invalid_sha256")
    return normalized


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_handler(
    *, store: SyntheticAssetStore, bearer_token: str
) -> type[BaseHTTPRequestHandler]:
    if len(bearer_token) < 32:
        raise ValueError("bearer token must have at least 32 characters")

    class Handler(BaseHTTPRequestHandler):
        server_version = "CaminoC02aReceiver/1"
        sys_version = ""

        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(30)

        def do_GET(self) -> None:  # noqa: N802
            if not self._authorized():
                self._respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            target = urlsplit(self.path)
            if target.path != "/healthz" or target.query or target.fragment:
                self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            self._respond(
                HTTPStatus.OK,
                {"status": "ok", "scope": "c02a_synthetic_only"},
            )

        def do_PUT(self) -> None:  # noqa: N802
            self.close_connection = True
            if not self._authorized():
                self._respond(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            target = urlsplit(self.path)
            match = UPLOAD_PATH_PATTERN.fullmatch(target.path)
            if match is None or target.query or target.fragment:
                self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            if self.headers.get("X-Camino-Synthetic") != "1":
                self._respond(HTTPStatus.BAD_REQUEST, {"error": "synthetic_marker_required"})
                return
            if self.headers.get("Transfer-Encoding") is not None:
                self._respond(HTTPStatus.BAD_REQUEST, {"error": "transfer_encoding_not_supported"})
                return
            lengths = self.headers.get_all("Content-Length", failobj=[])
            if len(lengths) != 1 or not lengths[0].isdigit():
                self._respond(HTTPStatus.LENGTH_REQUIRED, {"error": "content_length_required"})
                return
            try:
                result = store.receive(
                    asset_id=unquote(match.group(1)),
                    expected_sha256=self.headers.get("X-Camino-Expected-SHA256", ""),
                    content_length=int(lengths[0]),
                    stream=self.rfile,
                )
            except ReceiverError as error:
                self._respond(error.status, {"error": error.code})
                return
            except (OSError, TimeoutError):
                self._respond(HTTPStatus.BAD_REQUEST, {"error": "incomplete_upload"})
                return

            body = asdict(result.receipt)
            body["created"] = result.created
            self._respond(HTTPStatus.CREATED if result.created else HTTPStatus.OK, body)

        def _authorized(self) -> bool:
            authorization = self.headers.get("Authorization", "")
            prefix = "Bearer "
            if not authorization.startswith(prefix):
                return False
            supplied = authorization[len(prefix) :]
            return hmac.compare_digest(supplied, bearer_token)

        def _respond(self, status: HTTPStatus, body: dict[str, object]) -> None:
            payload = json.dumps(
                body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8") + b"\n"
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format: str, *args: object) -> None:
            # Asset identifiers, paths and authorization never enter shared logs.
            return

    return Handler


def make_server(
    *,
    store: SyntheticAssetStore,
    bearer_token: str,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
) -> ThreadingHTTPServer:
    try:
        if not ipaddress.ip_address(host).is_loopback:
            raise ValueError("C02a receiver must bind to a loopback address")
    except ValueError as error:
        if "loopback" in str(error):
            raise
        raise ValueError("C02a receiver host must be a loopback IP address") from error
    server = ThreadingHTTPServer((host, port), make_handler(store=store, bearer_token=bearer_token))
    server.daemon_threads = True
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Camino C02a synthetic receiver")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    args = parser.parse_args(argv)

    root = args.root or (Path(os.environ["CAMINO_C02A_ROOT"]) if "CAMINO_C02A_ROOT" in os.environ else None)
    token = os.environ.get("CAMINO_C02A_TOKEN", "")
    if root is None:
        parser.error("--root or CAMINO_C02A_ROOT is required")
    if len(token) < 32:
        parser.error("CAMINO_C02A_TOKEN with at least 32 characters is required")

    store = SyntheticAssetStore(root, max_bytes=args.max_bytes)
    server = make_server(store=store, bearer_token=token, host=args.host, port=args.port)
    print(f"Camino C02a receiver listens on {args.host}:{server.server_port}; HTTPS is required upstream.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
