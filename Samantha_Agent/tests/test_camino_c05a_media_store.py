"""C05a media durability, idempotence, storage pressure, and recovery tests."""

from __future__ import annotations

import hashlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from camino.domain.model import ContractError
from camino.domain.revision_store import StoreNotFound
from camino.server.auth import RevocableTokenStore
from camino.server.media_store import MediaStore, MediaStoreError


def uid(number: int) -> str:
    return f"00000000-0000-0000-0000-{number:012x}"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class CaminoC05aMediaStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir="/private/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.asset_id = uid(1)
        self.moment_id = uid(2)
        self.content = b"synthetic-c05a-media-payload"
        self.manifest = {
            "id": self.asset_id,
            "moment_id": self.moment_id,
            "media_kind": "audio",
            "origin": "recording",
            "byte_count": len(self.content),
            "sha256": digest(self.content),
            "duration_ms": 1200,
        }
        self.free = 10 * 1024 * 1024 * 1024

    def store(self, *, fault=None, manifest=None) -> MediaStore:
        selected = self.manifest if manifest is None else manifest

        def lookup(asset_id: str):
            if asset_id != selected["id"]:
                raise StoreNotFound("missing")
            return dict(selected)

        return MediaStore(
            self.root / "media.sqlite",
            self.root / "media",
            asset_lookup=lookup,
            max_asset_bytes=1024 * 1024,
            max_chunk_bytes=8,
            reserve_bytes=64,
            free_bytes=lambda _path: self.free,
            fault_injector=fault,
        )

    def upload_all(self, store: MediaStore, *, chunk_size: int = 8) -> None:
        status, created = store.create_session(self.asset_id, chunk_size=chunk_size)
        self.assertTrue(created)
        self.assertEqual(status["missing_chunks"], list(range(status["chunk_count"])))
        for index in range(status["chunk_count"]):
            chunk = self.content[index * chunk_size:(index + 1) * chunk_size]
            result, chunk_created = store.receive_chunk(
                self.asset_id,
                index,
                content_length=len(chunk),
                expected_sha256=digest(chunk),
                stream=io.BytesIO(chunk),
            )
            self.assertTrue(chunk_created)
            self.assertIn(index, result["accepted_chunks"])

    def test_chunks_finalize_and_lost_response_retry_are_idempotent(self) -> None:
        store = self.store()
        self.upload_all(store)
        receipt, created = store.finalize(self.asset_id)
        repeated, repeated_created = store.finalize(self.asset_id)
        self.assertTrue(created)
        self.assertFalse(repeated_created)
        self.assertEqual(repeated, receipt)
        self.assertEqual(receipt["sha256"], digest(self.content))
        self.assertEqual(store.status(self.asset_id)["state"], "verified")
        self.assertEqual(len(list((self.root / "media" / "objects").glob("*.bin"))), 1)
        reopened = self.store()
        self.assertEqual(reopened.status(self.asset_id)["receipt"], receipt)

    def test_manifest_chunk_and_hash_conflicts_fail_closed(self) -> None:
        store = self.store()
        store.create_session(self.asset_id, chunk_size=8)
        with self.assertRaises(MediaStoreError) as changed_session:
            store.create_session(self.asset_id, chunk_size=4)
        self.assertEqual(changed_session.exception.code, "asset_identity_conflict")
        first = self.content[:8]
        with self.assertRaises(MediaStoreError) as bad_chunk:
            store.receive_chunk(
                self.asset_id, 0, content_length=8,
                expected_sha256=digest(b"different"), stream=io.BytesIO(first),
            )
        self.assertEqual(bad_chunk.exception.code, "chunk_hash_mismatch")
        with self.assertRaises(MediaStoreError) as changed_chunk:
            store.reserve_chunk(
                self.asset_id, 0, content_length=8, expected_sha256=digest(first),
            )
        self.assertEqual(changed_chunk.exception.code, "chunk_identity_conflict")
        with self.assertRaises(MediaStoreError) as missing:
            store.finalize(self.asset_id)
        self.assertEqual(missing.exception.code, "missing_chunks")
        self.assertGreaterEqual(len(list((self.root / "media" / "quarantine").iterdir())), 1)

    def test_full_hash_mismatch_never_becomes_verified(self) -> None:
        wrong_manifest = dict(self.manifest, sha256=digest(b"different complete payload"))
        store = self.store(manifest=wrong_manifest)
        self.upload_all(store)
        with self.assertRaises(MediaStoreError) as mismatch:
            store.finalize(self.asset_id)
        self.assertEqual(mismatch.exception.code, "asset_hash_mismatch")
        status = store.status(self.asset_id)
        self.assertEqual(status["state"], "verification_failed")
        self.assertNotIn("receipt", status)
        self.assertFalse((self.root / "media" / "objects" / f"{self.asset_id}.bin").exists())

    def test_low_space_blocks_new_bytes_and_preserves_completed_asset(self) -> None:
        store = self.store()
        store.create_session(self.asset_id, chunk_size=8)
        self.free = 70
        with self.assertRaises(MediaStoreError) as blocked:
            store.reserve_chunk(
                self.asset_id, 0, content_length=8, expected_sha256=digest(self.content[:8]),
            )
        self.assertEqual(blocked.exception.status, 507)
        self.assertEqual(blocked.exception.code, "insufficient_storage")
        self.free = 10 * 1024 * 1024
        for index in range(4):
            chunk = self.content[index * 8:(index + 1) * 8]
            if not chunk:
                break
            store.receive_chunk(
                self.asset_id, index, content_length=len(chunk),
                expected_sha256=digest(chunk), stream=io.BytesIO(chunk),
            )
        receipt, _ = store.finalize(self.asset_id)
        object_path = self.root / "media" / "objects" / f"{self.asset_id}.bin"
        before = object_path.read_bytes()
        self.free = 0
        repeated, created = store.finalize(self.asset_id)
        self.assertFalse(created)
        self.assertEqual(repeated, receipt)
        self.assertEqual(object_path.read_bytes(), before)

    def test_mid_write_storage_error_preserves_partial_bytes_without_receipt(self) -> None:
        class FailingStream:
            def __init__(self):
                self.calls = 0

            def read(self, _size: int) -> bytes:
                self.calls += 1
                if self.calls == 1:
                    return self_content[:3]
                raise OSError("synthetic full filesystem")

        self_content = self.content
        store = self.store()
        store.create_session(self.asset_id, chunk_size=8)
        with self.assertRaisesRegex(OSError, "synthetic full filesystem"):
            store.receive_chunk(
                self.asset_id, 0, content_length=8,
                expected_sha256=digest(self.content[:8]), stream=FailingStream(),
            )
        self.assertEqual(store.status(self.asset_id)["accepted_chunks"], [])
        preserved = list((self.root / "media" / "quarantine").iterdir())
        self.assertEqual(len(preserved), 1)
        self.assertEqual(preserved[0].read_bytes(), self.content[:3])

    def test_tampered_stored_chunk_blocks_finalization_after_restart(self) -> None:
        store = self.store()
        store.create_session(self.asset_id, chunk_size=8)
        first = self.content[:8]
        store.receive_chunk(
            self.asset_id, 0, content_length=8,
            expected_sha256=digest(first), stream=io.BytesIO(first),
        )
        chunk_path = self.root / "media" / "sessions" / self.asset_id / "chunks" / "00000000.part"
        chunk_path.write_bytes(b"tampered")
        reopened = self.store()
        self.assertEqual(reopened.recovery_report["blocked"], 1)
        self.assertEqual(reopened.status(self.asset_id)["state"], "recovery_required")
        with self.assertRaises(MediaStoreError) as finalization:
            reopened.finalize(self.asset_id)
        self.assertEqual(finalization.exception.code, "missing_chunks")

    def test_live_object_tamper_revokes_verified_status(self) -> None:
        store = self.store()
        self.upload_all(store)
        store.finalize(self.asset_id)
        object_path = self.root / "media" / "objects" / f"{self.asset_id}.bin"
        object_path.write_bytes(b"tampered after verification")
        status = store.status(self.asset_id)
        self.assertEqual(status["state"], "recovery_required")
        self.assertEqual(status["failure_code"], "verified_asset_incomplete")
        self.assertNotIn("receipt", status)

    def test_recovery_closes_chunk_and_finalization_journal_gaps(self) -> None:
        phases = {"after_chunk_install"}

        def fault(phase: str, _asset_id: str, _index: int | None) -> None:
            if phase in phases:
                phases.remove(phase)
                raise RuntimeError(f"synthetic crash at {phase}")

        crashing = self.store(fault=fault)
        status, _ = crashing.create_session(self.asset_id, chunk_size=8)
        first = self.content[:8]
        with self.assertRaisesRegex(RuntimeError, "after_chunk_install"):
            crashing.receive_chunk(
                self.asset_id, 0, content_length=8,
                expected_sha256=digest(first), stream=io.BytesIO(first),
            )
        recovered = self.store()
        self.assertEqual(recovered.recovery_report["chunks_recovered"], 1)
        self.assertEqual(recovered.status(self.asset_id)["accepted_chunks"], [0])
        for index in range(1, status["chunk_count"]):
            chunk = self.content[index * 8:(index + 1) * 8]
            recovered.receive_chunk(
                self.asset_id, index, content_length=len(chunk),
                expected_sha256=digest(chunk), stream=io.BytesIO(chunk),
            )

        final_phases = {"after_object_install"}

        def final_fault(phase: str, _asset_id: str, _index: int | None) -> None:
            if phase in final_phases:
                final_phases.remove(phase)
                raise RuntimeError(f"synthetic crash at {phase}")

        interrupted = self.store(fault=final_fault)
        with self.assertRaisesRegex(RuntimeError, "after_object_install"):
            interrupted.finalize(self.asset_id)
        final = self.store()
        self.assertEqual(final.recovery_report["assets_recovered"], 1)
        self.assertEqual(final.status(self.asset_id)["state"], "verified")
        self.assertEqual(final.finalize(self.asset_id)[1], False)

    def test_orphan_chunk_is_quarantined_not_deleted(self) -> None:
        store = self.store()
        store.create_session(self.asset_id, chunk_size=8)
        orphan = self.root / "media" / "sessions" / self.asset_id / "chunks" / "00000000.part"
        orphan.write_bytes(b"preserve me")
        os.chmod(orphan, 0o600)
        reopened = self.store()
        self.assertEqual(reopened.recovery_report["files_quarantined"], 1)
        self.assertFalse(orphan.exists())
        preserved = list((self.root / "media" / "quarantine").iterdir())
        self.assertEqual(len(preserved), 1)
        self.assertEqual(preserved[0].read_bytes(), b"preserve me")

    def test_missing_manifest_and_private_path_guards(self) -> None:
        store = self.store()
        with self.assertRaises(MediaStoreError) as missing:
            store.create_session(uid(99), chunk_size=8)
        self.assertEqual(missing.exception.code, "asset_manifest_not_found")
        with self.assertRaises(ContractError):
            MediaStore(
                Path(__file__).resolve().parents[1] / "forbidden.sqlite",
                self.root / "other-media",
                asset_lookup=lambda _value: dict(self.manifest),
            )

    def test_owner_tokens_are_hashed_and_revocable(self) -> None:
        token_store = RevocableTokenStore(self.root / "auth.sqlite")
        token = "synthetic-owner-token-that-is-long-enough"
        token_id = token_store.add(token, label="synthetic iPhone")
        self.assertTrue(token_store.authenticate(f"Bearer {token}"))
        self.assertFalse(token_store.authenticate("Bearer wrong"))
        self.assertTrue(token_store.revoke(token_id))
        self.assertFalse(token_store.authenticate(f"Bearer {token}"))
        self.assertNotIn(token, (self.root / "auth.sqlite").read_bytes().decode("latin1"))


if __name__ == "__main__":
    unittest.main()
