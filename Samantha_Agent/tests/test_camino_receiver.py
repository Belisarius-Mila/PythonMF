from __future__ import annotations

import hashlib
import http.client
import io
import json
import stat
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path

from app.camino_receiver import (
    ReceiverError,
    SyntheticAssetStore,
    make_server,
)


TOKEN = "synthetic-c02a-token-with-32-characters"


@contextmanager
def running_receiver(store: SyntheticAssetStore):
    server = make_server(store=store, bearer_token=TOKEN, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(
    address: tuple[str, int],
    method: str,
    path: str,
    *,
    body: bytes = b"",
    token: str | None = TOKEN,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, object]]:
    values = dict(headers or {})
    if token is not None:
        values["Authorization"] = f"Bearer {token}"
    connection = http.client.HTTPConnection(*address, timeout=5)
    try:
        connection.request(method, path, body=body, headers=values)
        response = connection.getresponse()
        return response.status, json.loads(response.read().decode("utf-8"))
    finally:
        connection.close()


def upload_headers(content: bytes, *, sha256: str | None = None) -> dict[str, str]:
    return {
        "Content-Length": str(len(content)),
        "Content-Type": "application/octet-stream",
        "X-Camino-Synthetic": "1",
        "X-Camino-Expected-SHA256": sha256 or hashlib.sha256(content).hexdigest(),
    }


class CaminoReceiverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir="/private/tmp")
        self.root = Path(self.temporary.name) / "receiver"
        self.store = SyntheticAssetStore(self.root, max_bytes=1024)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_health_requires_token_and_discloses_only_prototype_scope(self) -> None:
        with running_receiver(self.store) as address:
            unauthorized, denied = request(address, "GET", "/healthz", token=None)
            authorized, body = request(address, "GET", "/healthz")

        self.assertEqual(unauthorized, 401)
        self.assertEqual(denied, {"error": "unauthorized"})
        self.assertEqual(authorized, 200)
        self.assertEqual(body, {"scope": "c02a_synthetic_only", "status": "ok"})

    def test_valid_upload_is_server_hashed_and_create_only(self) -> None:
        content = b"camino-c02a-synthetic-payload\n" * 7
        expected = hashlib.sha256(content).hexdigest()

        with running_receiver(self.store) as address:
            status, body = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/test-asset-01",
                body=content,
                headers=upload_headers(content),
            )

        self.assertEqual(status, 201)
        self.assertEqual(body["state"], "verified")
        self.assertEqual(body["content_kind"], "synthetic")
        self.assertEqual(body["byte_count"], len(content))
        self.assertEqual(body["sha256"], expected)
        self.assertTrue(body["created"])
        stored = self.root / "objects" / "test-asset-01.bin"
        self.assertEqual(stored.read_bytes(), content)
        self.assertEqual(stat.S_IMODE(stored.stat().st_mode), 0o600)
        receipt = json.loads(
            (self.root / "receipts" / "test-asset-01.json").read_text(encoding="utf-8")
        )
        self.assertEqual(receipt["sha256"], expected)
        self.assertEqual(receipt["asset_id"], "test-asset-01")

    def test_identical_retry_returns_one_asset_without_rewrite(self) -> None:
        content = b"repeatable synthetic content"
        headers = upload_headers(content)

        with running_receiver(self.store) as address:
            first_status, first = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/retry-asset",
                body=content,
                headers=headers,
            )
            object_path = self.root / "objects" / "retry-asset.bin"
            first_inode = object_path.stat().st_ino
            second_status, second = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/retry-asset",
                body=content,
                headers=headers,
            )

        self.assertEqual(first_status, 201)
        self.assertTrue(first["created"])
        self.assertEqual(second_status, 200)
        self.assertFalse(second["created"])
        self.assertEqual(object_path.stat().st_ino, first_inode)
        self.assertEqual(len(list((self.root / "objects").iterdir())), 1)
        self.assertEqual(len(list((self.root / "receipts").iterdir())), 1)

    def test_wrong_hash_is_not_promoted_or_verified(self) -> None:
        content = b"synthetic hash mismatch"
        wrong_hash = hashlib.sha256(b"different").hexdigest()

        with running_receiver(self.store) as address:
            status, body = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/bad-hash",
                body=content,
                headers=upload_headers(content, sha256=wrong_hash),
            )

        self.assertEqual(status, 422)
        self.assertEqual(body, {"error": "hash_mismatch"})
        self.assertEqual(list((self.root / "objects").iterdir()), [])
        self.assertEqual(list((self.root / "receipts").iterdir()), [])
        self.assertEqual(list((self.root / ".staging").iterdir()), [])

    def test_same_identity_with_different_bytes_is_conflict_without_overwrite(self) -> None:
        original = b"first synthetic payload"
        replacement = b"different synthetic payload"

        with running_receiver(self.store) as address:
            first_status, _ = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/stable-id",
                body=original,
                headers=upload_headers(original),
            )
            conflict_status, conflict = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/stable-id",
                body=replacement,
                headers=upload_headers(replacement),
            )

        self.assertEqual(first_status, 201)
        self.assertEqual(conflict_status, 409)
        self.assertEqual(conflict, {"error": "asset_identity_conflict"})
        self.assertEqual((self.root / "objects" / "stable-id.bin").read_bytes(), original)

    def test_receiver_rejects_non_synthetic_and_oversized_bodies(self) -> None:
        content = b"x" * 1025
        missing_marker = upload_headers(b"small")
        missing_marker.pop("X-Camino-Synthetic")

        with running_receiver(self.store) as address:
            marker_status, marker_body = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/no-marker",
                body=b"small",
                headers=missing_marker,
            )
            large_status, large_body = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/too-large",
                body=content,
                headers=upload_headers(content),
            )

        self.assertEqual(marker_status, 400)
        self.assertEqual(marker_body, {"error": "synthetic_marker_required"})
        self.assertEqual(large_status, 413)
        self.assertEqual(large_body, {"error": "synthetic_file_too_large"})
        self.assertEqual(list((self.root / "objects").iterdir()), [])

    def test_path_traversal_and_invalid_hash_are_rejected(self) -> None:
        content = b"synthetic"

        with running_receiver(self.store) as address:
            path_status, path_body = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/%2e%2e%2fescape",
                body=content,
                headers=upload_headers(content),
            )
            hash_status, hash_body = request(
                address,
                "PUT",
                "/v1/c02a/synthetic-assets/valid-id",
                body=content,
                headers=upload_headers(content, sha256="not-a-hash"),
            )

        self.assertEqual(path_status, 400)
        self.assertEqual(path_body, {"error": "invalid_asset_id"})
        self.assertEqual(hash_status, 400)
        self.assertEqual(hash_body, {"error": "invalid_sha256"})
        self.assertFalse((self.root.parent / "escape").exists())

    def test_incomplete_stream_never_creates_object(self) -> None:
        content = b"short"
        with self.assertRaises(ReceiverError) as raised:
            self.store.receive(
                asset_id="incomplete",
                expected_sha256=hashlib.sha256(content).hexdigest(),
                content_length=len(content) + 1,
                stream=io.BytesIO(content),
            )

        self.assertEqual(raised.exception.code, "incomplete_upload")
        self.assertEqual(list((self.root / "objects").iterdir()), [])
        self.assertEqual(list((self.root / ".staging").iterdir()), [])

    def test_store_refuses_symlinked_internal_directory(self) -> None:
        other_root = Path(self.temporary.name) / "other"
        other_root.mkdir()
        unsafe_root = Path(self.temporary.name) / "unsafe"
        unsafe_root.mkdir()
        (unsafe_root / "objects").symlink_to(other_root, target_is_directory=True)

        with self.assertRaisesRegex(ValueError, "unsafe receiver directory"):
            SyntheticAssetStore(unsafe_root)

    def test_server_refuses_public_bind_and_short_token(self) -> None:
        with self.assertRaisesRegex(ValueError, "loopback"):
            make_server(store=self.store, bearer_token=TOKEN, host="0.0.0.0", port=0)
        with self.assertRaisesRegex(ValueError, "32 characters"):
            make_server(store=self.store, bearer_token="short", port=0)


if __name__ == "__main__":
    unittest.main()
