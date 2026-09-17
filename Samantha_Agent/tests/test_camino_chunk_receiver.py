from __future__ import annotations

import hashlib
import http.client
import io
import json
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from app.camino_chunk_receiver import (
    DEFAULT_CHUNK_BYTES,
    ChunkedSyntheticAssetStore,
    ReceiverError,
    make_server,
)


TOKEN = "synthetic-c02b-token-with-32-characters"


@contextmanager
def running_receiver(store: ChunkedSyntheticAssetStore):
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
    connection = http.client.HTTPConnection(*address, timeout=10)
    try:
        connection.request(method, path, body=body, headers=values)
        response = connection.getresponse()
        return response.status, json.loads(response.read().decode("utf-8"))
    finally:
        connection.close()


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def create_headers() -> dict[str, str]:
    return {"Content-Type": "application/json", "X-Camino-Synthetic": "1"}


def chunk_headers(content: bytes, *, sha256: str | None = None) -> dict[str, str]:
    return {
        "Content-Length": str(len(content)),
        "Content-Type": "application/octet-stream",
        "X-Camino-Synthetic": "1",
        "X-Camino-Chunk-SHA256": sha256 or digest(content),
    }


class CaminoChunkReceiverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir="/private/tmp")
        self.root = Path(self.temporary.name) / "receiver"
        self.store = ChunkedSyntheticAssetStore(
            self.root,
            max_bytes=32 * 1024 * 1024,
            max_chunk_bytes=DEFAULT_CHUNK_BYTES,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def create_session(
        self,
        address: tuple[str, int],
        asset_id: str,
        content: bytes,
        chunk_size: int,
        *,
        full_sha256: str | None = None,
    ) -> tuple[int, dict[str, object]]:
        manifest = json.dumps(
            {
                "byte_count": len(content),
                "sha256": full_sha256 or digest(content),
                "chunk_size": chunk_size,
            }
        ).encode()
        return request(
            address,
            "POST",
            f"/v1/c02b/synthetic-assets/{asset_id}/sessions",
            body=manifest,
            headers=create_headers(),
        )

    def upload_chunk(
        self, address: tuple[str, int], asset_id: str, index: int, content: bytes
    ) -> tuple[int, dict[str, object]]:
        return request(
            address,
            "PUT",
            f"/v1/c02b/synthetic-assets/{asset_id}/chunks/{index}",
            body=content,
            headers=chunk_headers(content),
        )

    def test_health_requires_token_and_discloses_only_synthetic_scope(self) -> None:
        with running_receiver(self.store) as address:
            denied_status, denied = request(address, "GET", "/healthz", token=None)
            ok_status, body = request(address, "GET", "/healthz")

        self.assertEqual((denied_status, denied), (401, {"error": "unauthorized"}))
        self.assertEqual(ok_status, 200)
        self.assertEqual(body, {"scope": "c02b_synthetic_only", "status": "ok"})

    def test_default_eight_mib_chunks_resume_only_missing_and_finalize_once(self) -> None:
        content = b"A" * (DEFAULT_CHUNK_BYTES * 2) + b"camino-tail"
        chunks = [
            content[index : index + DEFAULT_CHUNK_BYTES]
            for index in range(0, len(content), DEFAULT_CHUNK_BYTES)
        ]
        asset_id = "large-resume"

        with running_receiver(self.store) as address:
            created_status, created = self.create_session(
                address, asset_id, content, DEFAULT_CHUNK_BYTES
            )
            first_status, _ = self.upload_chunk(address, asset_id, 0, chunks[0])
            tail_status, _ = self.upload_chunk(address, asset_id, 2, chunks[2])
            resumed_status, resumed = request(
                address, "GET", f"/v1/c02b/synthetic-assets/{asset_id}/status"
            )
            middle_status, _ = self.upload_chunk(address, asset_id, 1, chunks[1])
            final_status, final = request(
                address, "POST", f"/v1/c02b/synthetic-assets/{asset_id}/finalize"
            )
            retry_status, retry = request(
                address, "POST", f"/v1/c02b/synthetic-assets/{asset_id}/finalize"
            )

        self.assertEqual(created_status, 201)
        self.assertEqual(created["chunk_size"], DEFAULT_CHUNK_BYTES)
        self.assertEqual(
            (first_status, tail_status, resumed_status, middle_status),
            (201, 201, 200, 201),
        )
        self.assertEqual(resumed["accepted_chunks"], [0, 2])
        self.assertEqual(resumed["missing_chunks"], [1])
        self.assertEqual(final_status, 201)
        self.assertEqual(final["state"], "verified")
        self.assertEqual(final["sha256"], digest(content))
        self.assertTrue(final["created"])
        self.assertEqual(retry_status, 200)
        self.assertFalse(retry["created"])
        self.assertEqual((self.root / "objects" / f"{asset_id}.bin").read_bytes(), content)
        self.assertEqual(len(list((self.root / "objects").iterdir())), 1)
        self.assertEqual(len(list((self.root / "receipts").iterdir())), 1)

    def test_session_and_chunk_retries_are_idempotent_but_conflicts_fail_closed(self) -> None:
        content = b"abcdefgh"
        with running_receiver(self.store) as address:
            first_session, _ = self.create_session(address, "stable", content, 4)
            second_session, second = self.create_session(address, "stable", content, 4)
            first_chunk, _ = self.upload_chunk(address, "stable", 0, content[:4])
            second_chunk, retry = self.upload_chunk(address, "stable", 0, content[:4])
            conflict_chunk, conflict = request(
                address,
                "PUT",
                "/v1/c02b/synthetic-assets/stable/chunks/0",
                body=b"WXYZ",
                headers=chunk_headers(b"WXYZ"),
            )
            different_manifest, manifest_error = self.create_session(
                address, "stable", content + b"x", 4
            )

        self.assertEqual(
            (first_session, second_session, first_chunk, second_chunk),
            (201, 200, 201, 200),
        )
        self.assertFalse(second["created"])
        self.assertFalse(retry["chunk_created"])
        self.assertEqual(
            (conflict_chunk, conflict),
            (409, {"error": "chunk_identity_conflict"}),
        )
        self.assertEqual(
            (different_manifest, manifest_error),
            (409, {"error": "asset_identity_conflict"}),
        )

    def test_wrong_chunk_hash_and_missing_chunk_never_finalize(self) -> None:
        content = b"abcdefgh"
        with running_receiver(self.store) as address:
            self.create_session(address, "incomplete", content, 4)
            wrong_status, wrong = request(
                address,
                "PUT",
                "/v1/c02b/synthetic-assets/incomplete/chunks/0",
                body=content[:4],
                headers=chunk_headers(content[:4], sha256=digest(b"nope")),
            )
            self.upload_chunk(address, "incomplete", 0, content[:4])
            final_status, final = request(
                address, "POST", "/v1/c02b/synthetic-assets/incomplete/finalize"
            )

        self.assertEqual(
            (wrong_status, wrong), (422, {"error": "chunk_hash_mismatch"})
        )
        self.assertEqual(
            (final_status, final), (409, {"error": "missing_chunks"})
        )
        self.assertEqual(list((self.root / "objects").iterdir()), [])
        self.assertEqual(list((self.root / "receipts").iterdir()), [])

    def test_full_hash_mismatch_is_visible_and_not_promoted(self) -> None:
        content = b"abcdefgh"
        with running_receiver(self.store) as address:
            self.create_session(
                address,
                "bad-full-hash",
                content,
                4,
                full_sha256=digest(b"different"),
            )
            self.upload_chunk(address, "bad-full-hash", 0, content[:4])
            self.upload_chunk(address, "bad-full-hash", 1, content[4:])
            final_status, final = request(
                address, "POST", "/v1/c02b/synthetic-assets/bad-full-hash/finalize"
            )
            status_code, status = request(
                address, "GET", "/v1/c02b/synthetic-assets/bad-full-hash/status"
            )

        self.assertEqual(
            (final_status, final), (422, {"error": "asset_hash_mismatch"})
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(status["state"], "verification_failed")
        self.assertEqual(list((self.root / "objects").iterdir()), [])

    def test_status_says_verifying_after_bytes_reach_one_hundred_percent(self) -> None:
        entered = threading.Event()
        release = threading.Event()

        def before_verify(_asset_id: str) -> None:
            entered.set()
            release.wait(timeout=5)

        store = ChunkedSyntheticAssetStore(
            self.root,
            max_bytes=1024,
            max_chunk_bytes=1024,
            before_verify=before_verify,
        )
        content = b"verification-pending"
        result: list[object] = []
        store.create_session(
            asset_id="verify-state",
            byte_count=len(content),
            sha256=digest(content),
            chunk_size=len(content),
        )
        store.receive_chunk(
            asset_id="verify-state",
            chunk_index=0,
            expected_sha256=digest(content),
            content_length=len(content),
            stream=io.BytesIO(content),
        )
        thread = threading.Thread(
            target=lambda: result.append(store.finalize("verify-state"))
        )
        thread.start()
        self.assertTrue(entered.wait(timeout=5))
        pending = store.status("verify-state")
        release.set()
        thread.join(timeout=5)

        self.assertFalse(thread.is_alive())
        self.assertEqual(pending["accepted_chunks"], [0])
        self.assertEqual(pending["missing_chunks"], [])
        self.assertEqual(pending["state"], "verifying")
        self.assertEqual(result[0][0].state, "verified")

    def test_verified_status_recovers_a_lost_finalize_response(self) -> None:
        content = b"response-recovery"
        self.store.create_session(
            asset_id="lost-response",
            byte_count=len(content),
            sha256=digest(content),
            chunk_size=len(content),
        )
        self.store.receive_chunk(
            asset_id="lost-response",
            chunk_index=0,
            expected_sha256=digest(content),
            content_length=len(content),
            stream=io.BytesIO(content),
        )
        receipt, created = self.store.finalize("lost-response")
        recovered = self.store.status("lost-response")

        self.assertTrue(created)
        self.assertEqual(recovered["state"], "verified")
        self.assertEqual(recovered["receipt"]["sha256"], receipt.sha256)

    def test_public_bind_short_token_and_symlink_root_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "loopback"):
            make_server(
                store=self.store, bearer_token=TOKEN, host="0.0.0.0", port=0
            )
        with self.assertRaisesRegex(ValueError, "32"):
            make_server(store=self.store, bearer_token="short", port=0)
        unsafe = Path(self.temporary.name) / "unsafe"
        unsafe.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "unsafe"):
            ChunkedSyntheticAssetStore(unsafe)

    def test_invalid_index_length_and_absent_session_are_explicit(self) -> None:
        content = b"abcdefgh"
        self.store.create_session(
            asset_id="bounds",
            byte_count=len(content),
            sha256=digest(content),
            chunk_size=4,
        )
        cases = [
            (2, b"abcd", "invalid_chunk_index"),
            (0, b"abc", "invalid_chunk_length"),
        ]
        for index, chunk, code in cases:
            with self.subTest(code=code), self.assertRaises(ReceiverError) as raised:
                self.store.receive_chunk(
                    asset_id="bounds",
                    chunk_index=index,
                    expected_sha256=digest(chunk),
                    content_length=len(chunk),
                    stream=io.BytesIO(chunk),
                )
            self.assertEqual(raised.exception.code, code)
        with self.assertRaises(ReceiverError) as absent:
            self.store.status("absent")
        self.assertEqual(absent.exception.code, "upload_session_not_found")

    def test_controlled_read_delay_is_proportional_and_rejects_negative_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            ChunkedSyntheticAssetStore(self.root, read_delay_seconds_per_mib=-1)

        delayed = ChunkedSyntheticAssetStore(
            self.root,
            max_bytes=1024,
            max_chunk_bytes=1024,
            read_delay_seconds_per_mib=2,
        )
        content = b"x" * 1024
        delayed.create_session(
            asset_id="slow-read",
            byte_count=len(content),
            sha256=digest(content),
            chunk_size=len(content),
        )
        with mock.patch("app.camino_chunk_receiver.time.sleep") as sleeper:
            delayed.receive_chunk(
                asset_id="slow-read",
                chunk_index=0,
                expected_sha256=digest(content),
                content_length=len(content),
                stream=io.BytesIO(content),
            )

        sleeper.assert_called_once()
        self.assertAlmostEqual(sleeper.call_args.args[0], 2 / 1024)


if __name__ == "__main__":
    unittest.main()
