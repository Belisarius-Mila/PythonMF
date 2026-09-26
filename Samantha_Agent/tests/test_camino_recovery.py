"""Synthetic identical-copy recovery; no personal archive or live service."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from camino.domain.revision_store import StoreConflict
from camino.domain.model import ContractError
from camino.server.recovery import complete_recovery
from tests.camino_viewer_fixture import ViewerFixture, uid


def proof_for(store):
    state = store.state()
    with store._connection() as db:
        return {"contract_version": 1, **{k: state[k] for k in ("server_id", "epoch", "cursor")},
                "device_id": state["writer_device_id"],
                "operations": [{"id": r["id"], "sequence": r["device_sequence"], "sha256": r["request_sha256"]}
                    for r in db.execute("SELECT * FROM accepted_operations ORDER BY device_sequence")],
                "moments": [{"id": r["id"], "revision": r["revision"], "privacy": json.loads(r["body"])["privacy"]}
                    for r in db.execute("SELECT * FROM moments")],
                "assets": [{k: json.loads(r["body"])[k] for k in ("id", "byte_count", "sha256")}
                    for r in db.execute("SELECT * FROM assets")]}


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.f = ViewerFixture(self.root)
        self.asset = self.f.upload(30, "video", b"synthetic-original")
        self.f.store.rotate_epoch_for_restore()
        self.proof = proof_for(self.f.store)

    def complete(self, proof=None):
        raw = json.dumps(self.proof if proof is None else proof, sort_keys=True).encode()
        return complete_recovery(self.f.store, self.f.media, raw)

    def assertBlocked(self):
        self.assertTrue(self.f.store.state()["exports_blocked"])
        self.assertTrue(self.f.store.state()["reconciliation_required"])

    def test_complete_retry_preserves_history_originals_identity_and_grants(self):
        before = proof_for(self.f.store)
        path = self.f.media._object_path(self.asset["id"])
        original = path.read_bytes()
        receipt = self.complete()
        self.assertFalse(receipt["exports_blocked"])
        self.assertEqual(receipt, self.complete(), "lost response is safely repeatable")
        self.assertEqual(proof_for(self.f.store), before)
        self.assertEqual(path.read_bytes(), original)
        with self.f.store._connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM viewer_permissions").fetchone()[0], 0)
        self.assertEqual(receipt["request_sha256"], hashlib.sha256(json.dumps(self.proof, sort_keys=True).encode()).hexdigest())

    def test_identity_epoch_writer_cursor_and_operation_differences_block(self):
        for key, value in (("server_id", uid(999)), ("epoch", uid(998)), ("device_id", uid(997)), ("cursor", 1)):
            with self.subTest(key=key), self.assertRaises(StoreConflict):
                self.complete({**self.proof, key: value})
            self.assertBlocked()
        for field, value in (("sha256", "b" * 64), ("sequence", True), ("id", uid(996))):
            proof = copy.deepcopy(self.proof)
            proof["operations"][0][field] = value
            with self.assertRaises(StoreConflict):
                self.complete(proof)
            self.assertBlocked()

    def test_missing_extra_duplicate_and_privacy_differences_block(self):
        for key in ("operations", "moments", "assets"):
            for entries in (self.proof[key][:-1], self.proof[key] + self.proof[key][:1]):
                with self.subTest(key=key), self.assertRaises(StoreConflict):
                    self.complete({**self.proof, key: entries})
                self.assertBlocked()
        proof = copy.deepcopy(self.proof)
        proof["moments"][0]["privacy"] = "owner_only"
        with self.assertRaises(StoreConflict):
            self.complete(proof)
        self.assertBlocked()

    def test_bad_actual_bytes_or_missing_receipt_cannot_unlock(self):
        path = self.f.media._object_path(self.asset["id"])
        path.write_bytes(b"synthetic-corrupt!")
        with self.assertRaises(StoreConflict):
            self.complete()
        self.assertBlocked()

    def test_unverified_media_blocks(self):
        with self.f.media._open() as db:
            db.execute("DELETE FROM verified_assets")  # Only this disposable synthetic fixture.
            db.commit()
        with self.assertRaises(StoreConflict):
            self.complete()
        self.assertBlocked()

    def test_conflict_cannot_be_cleared_by_matching_inventory(self):
        with self.f.store._connection() as db:
            db.execute("INSERT INTO conflict_candidates VALUES (?,?,?,?,?,?)",
                       (uid(999), "a" * 64, b"{}", "identity_conflict", "synthetic", None))
        with self.assertRaises(StoreConflict):
            self.complete()
        self.assertBlocked()

    def test_stale_proof_after_new_restore_stays_blocked(self):
        self.complete()
        self.f.store.rotate_epoch_for_restore()
        with self.assertRaises(StoreConflict):
            self.complete()
        self.assertBlocked()

    def test_invalid_and_oversize_proof_do_not_write(self):
        for raw in (b"{}", b'{"contract_version":1,"contract_version":1}', b"x" * 1_048_577):
            with self.assertRaises(ContractError):
                complete_recovery(self.f.store, self.f.media, raw)
            self.assertBlocked()

    def test_unrelated_export_block_is_not_a_restore(self):
        with self.f.store._connection() as db:
            db.execute("UPDATE meta SET reconciliation_required=0")
        with self.assertRaises(StoreConflict):
            self.complete()
        self.assertTrue(self.f.store.state()["exports_blocked"])


if __name__ == "__main__":
    unittest.main()
