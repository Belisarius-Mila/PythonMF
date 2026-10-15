"""Actual Swift build-18 orphan layout recovery through the private owner API."""

import copy
import json
import os
import platform
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from camino.api.v1 import CaminoV1Contract
from camino.domain.revision_store import RevisionStore

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == "Darwin" and shutil.which("xcrun"),
                     "actual Swift/CoreData fixture requires macOS")
class DeletedAudioLayoutWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix="camino-audio-wire-")
        cls.addClassCleanup(cls.workspace.cleanup)
        fixture = os.environ.get("CAMINO_DELETED_AUDIO_WIRE_FIXTURE")
        if not fixture:
            fixture = str(Path(cls.workspace.name) / "fixture.json")
            result = subprocess.run(["/usr/bin/xcrun", "swift", "test", "--package-path",
                str(ROOT / "camino/app"), "--filter",
                "testLegacyDeletedAudioRepairThenPhotoAndPrivacyEmitsActualSwiftWireFixture"],
                env={**os.environ, "CAMINO_DELETED_AUDIO_WIRE_FIXTURE": fixture},
                capture_output=True, text=True, timeout=180)
            if result.returncode:
                raise AssertionError("Swift deleted-audio wire fixture failed")
        cls.fixture = json.loads(Path(fixture).read_text())

    def setUp(self):
        self.store = RevisionStore(Path(self.workspace.name) / (self._testMethodName + ".sqlite"))
        with self.store._open() as db:
            db.execute("UPDATE meta SET server_id=?,epoch=? WHERE singleton=1",
                       (self.fixture["server_id"], self.fixture["epoch"]))
        self.api = CaminoV1Contract(self.store, lambda value: value == "Bearer synthetic-owner")
        self.original = copy.deepcopy(self.fixture["rejected"])
        self.cancel = next(copy.deepcopy(p) for p in self.fixture["repaired"]
                           if p["device_sequence"] == self.original["device_sequence"])
        for packet in self.fixture["repaired"]:
            if packet["device_sequence"] < self.original["device_sequence"]:
                self.assertEqual(self.send(packet).status, 200)

    def send(self, packet, *, raw=None, auth="Bearer synthetic-owner"):
        return self.api.handle("POST", "/api/v1/operations", authorization=auth,
            body=raw if raw is not None else json.dumps(packet, sort_keys=True, separators=(",", ":")).encode(),
            content_type="application/json")

    def snapshot(self):
        with self.store._open() as db:
            return {name: sorted(repr(tuple(row)) for row in db.execute('SELECT * FROM "' + name + '"'))
                    for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    def inject_asset(self, *, media_kind="audio", moment_id=None, identifier=None):
        part = self.original["payload"]["parts"][0]["asset_id"]
        photo = next(p["payload"] for p in self.fixture["repaired"] if p["kind"] == "create_asset")
        body = {**photo, "id": identifier or part, "media_kind": media_kind,
                "moment_id": moment_id or self.original["payload"]["moment_id"],
                "origin": "recording" if media_kind == "audio" else "camera",
                "duration_ms": 1000 if media_kind == "audio" else None}
        with self.store._open() as db:
            if not db.execute("SELECT 1 FROM moments WHERE id=?", (body["moment_id"],)).fetchone():
                row = db.execute("SELECT trip_id,revision,body FROM moments LIMIT 1").fetchone()
                moment = {**json.loads(row["body"]), "id": body["moment_id"]}
                db.execute("INSERT INTO moments VALUES (?,?,?,?)", (
                    body["moment_id"], row["trip_id"], row["revision"], json.dumps(moment)))
            db.execute("INSERT INTO assets VALUES (?,?,?)", (body["id"], body["moment_id"], json.dumps(body)))
        return body

    def test_actual_swift_cancellation_then_photo_and_privacy_retries_and_reopens(self):
        before = self.snapshot()
        refused = self.send(self.original)
        self.assertEqual(refused.status, 404)
        self.assertEqual(refused.body["error"]["code"], "not_found")
        self.assertEqual(self.snapshot(), before)
        accepted = self.send(self.cancel)
        self.assertEqual(accepted.status, 200)
        self.assertIsNone(accepted.body["revision"])
        after_cancel = self.snapshot()
        for table in before.keys() - {"meta", "accepted_operations"}:
            self.assertEqual(before[table], after_cancel[table], table)
        with self.store._open() as db:
            raw = db.execute("SELECT request_body FROM accepted_operations WHERE device_sequence=?",
                             (self.original["device_sequence"],)).fetchone()[0]
            self.assertEqual(json.loads(raw)["payload"]["rejected_envelope"],
                             self.cancel["payload"]["rejected_envelope"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM audio_layouts").fetchone()[0], 0)
        for packet in self.fixture["repaired"]:
            self.assertEqual(self.send(packet).status, 200)
        final = self.snapshot()
        self.store = RevisionStore(self.store.path)
        self.api = CaminoV1Contract(self.store, lambda value: value == "Bearer synthetic-owner")
        for packet in self.fixture["repaired"]:
            self.assertEqual(self.send(packet).status, 200)
        self.assertEqual(self.snapshot(), final)
        self.assertFalse(self.store.state()["exports_blocked"])
        self.assertFalse(self.store.state()["reconciliation_required"])

    def test_feature_and_authentication(self):
        self.assertIn("deleted_audio_layout_repair_v1", self.store.state()["features"])
        before = self.snapshot()
        self.assertEqual(self.send(self.cancel, auth="").status, 401)
        self.assertEqual(self.snapshot(), before)

    def test_embedded_envelope_must_belong_to_the_exact_operation(self):
        for field, value in [("contract_version", True), ("epoch", str(uuid4())),
                             ("operation_id", str(uuid4())), ("device_id", str(uuid4())),
                             ("device_sequence", self.original["device_sequence"] + 1),
                             ("kind", "update_metadata"), ("expected_revision", 1)]:
            with self.subTest(field=field):
                packet = copy.deepcopy(self.cancel)
                original = copy.deepcopy(self.original); original[field] = value
                packet["payload"]["rejected_envelope"] = json.dumps(original)
                before = self.snapshot()
                self.assertEqual(self.send(packet).status, 422)
                self.assertEqual(self.snapshot(), before)

    def test_embedded_json_bounds_duplicate_fields_and_nonfinite_numbers(self):
        raw = self.cancel["payload"]["rejected_envelope"]
        for bad in ["x" * 524289, "{", raw.replace('{', '{"kind":"create_audio_layout",', 1),
                    raw.replace('{', '{"unexpected":NaN,', 1)]:
            packet = copy.deepcopy(self.cancel); packet["payload"]["rejected_envelope"] = bad
            before = self.snapshot()
            self.assertEqual(self.send(packet).status, 422)
            self.assertEqual(self.snapshot(), before)

    def test_clip_and_moment_binding_and_invalid_layout_are_rejected(self):
        for field in ("clip_id", "moment_id"):
            packet = copy.deepcopy(self.cancel); packet["payload"][field] = str(uuid4())
            before = self.snapshot()
            self.assertEqual(self.send(packet).status, 422)
            self.assertEqual(self.snapshot(), before)
        packet = copy.deepcopy(self.cancel)
        original = copy.deepcopy(self.original); original["payload"]["parts"] = []
        packet["payload"]["rejected_envelope"] = json.dumps(original)
        self.assertEqual(self.send(packet).status, 422)

    def test_declared_sources_are_preserved_and_a_missing_source_is_required(self):
        self.inject_asset()
        before = self.snapshot()
        self.assertEqual(self.send(self.cancel).status, 422)
        self.assertEqual(self.snapshot(), before)
        # One declared part followed by one missing part is a valid legacy
        # partial declaration. Cancellation must retain the declared part too.
        original = copy.deepcopy(self.original)
        original["payload"]["parts"].append({"asset_id": str(uuid4()), "index": 1,
                                               "discontinuity_before": False})
        packet = copy.deepcopy(self.cancel)
        packet["payload"]["rejected_envelope"] = json.dumps(original)
        self.assertEqual(self.send(original).status, 404)
        self.assertEqual(self.send(packet).status, 200)
        after = self.snapshot()
        for table in before.keys() - {"meta", "accepted_operations"}:
            self.assertEqual(after[table], before[table], table)

    def test_missing_first_source_cannot_hide_a_later_photo_or_foreign_audio(self):
        for kind in ("photo", "audio"):
            extra = self.inject_asset(media_kind=kind,
                moment_id=str(uuid4()) if kind == "audio" else None, identifier=str(uuid4()))
            original = copy.deepcopy(self.original)
            original["payload"]["parts"].append({"asset_id": extra["id"], "index": 1,
                                                   "discontinuity_before": False})
            packet = copy.deepcopy(self.cancel)
            packet["payload"]["rejected_envelope"] = json.dumps(original)
            before = self.snapshot()
            self.assertEqual(self.send(packet).status, 422)
            self.assertEqual(self.snapshot(), before)

    def test_existing_layout_cannot_be_cancelled(self):
        original = self.original["payload"]
        with self.store._open() as db:
            db.execute("INSERT INTO audio_layouts VALUES (?,?,?)", (
                original["clip_id"], original["moment_id"], json.dumps(original)))
        before = self.snapshot()
        self.assertEqual(self.send(self.cancel).status, 422)
        self.assertEqual(self.snapshot(), before)

    def test_missing_source_cannot_hide_a_session_branch(self):
        root = copy.deepcopy(self.original["payload"])
        sibling = {**root, "clip_id": str(uuid4()), "previous_clip_id": root["clip_id"],
                   "parts": [{"asset_id": str(uuid4()), "index": 0, "discontinuity_before": False}]}
        with self.store._open() as db:
            for layout in (root, sibling):
                db.execute("INSERT INTO audio_layouts VALUES (?,?,?)", (
                    layout["clip_id"], layout["moment_id"], json.dumps(layout)))
        original = copy.deepcopy(self.original)
        original["payload"]["clip_id"] = str(uuid4())
        original["payload"]["previous_clip_id"] = root["clip_id"]
        original["payload"]["parts"][0]["asset_id"] = str(uuid4())
        packet = copy.deepcopy(self.cancel)
        packet["payload"]["clip_id"] = original["payload"]["clip_id"]
        packet["payload"]["rejected_envelope"] = json.dumps(original)
        before = self.snapshot()
        self.assertEqual(self.send(packet).status, 422)
        self.assertEqual(self.snapshot(), before)

    def test_transaction_failure_rolls_back_and_exact_retry_can_succeed(self):
        with self.store._open() as db:
            db.execute("CREATE TRIGGER fail_audio_cancel BEFORE INSERT ON accepted_operations "
                       "WHEN NEW.kind='create_audio_layout' BEGIN SELECT RAISE(ABORT,'synthetic'); END")
        before = self.snapshot()
        self.assertEqual(self.send(self.cancel).status, 503)
        self.assertEqual(self.snapshot(), before)
        with self.store._open() as db:
            db.execute("DROP TRIGGER fail_audio_cancel")
        self.assertEqual(self.send(self.cancel).status, 200)

    def test_already_accepted_original_is_never_rewritten(self):
        self.inject_asset()
        self.assertEqual(self.send(self.original).status, 200)
        with self.store._open() as db:
            old = tuple(db.execute("SELECT * FROM accepted_operations WHERE device_sequence=?",
                                   (self.original["device_sequence"],)).fetchone())
        self.assertEqual(self.send(self.cancel).status, 409)
        with self.store._open() as db:
            self.assertEqual(tuple(db.execute("SELECT * FROM accepted_operations WHERE device_sequence=?",
                                              (self.original["device_sequence"],)).fetchone()), old)
