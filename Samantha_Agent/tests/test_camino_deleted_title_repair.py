"""Replay actual Swift repair envelopes through the unchanged private owner API."""

import json
import copy
import os
import platform
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from camino.api.v1 import CaminoV1Contract
from camino.domain.revision_store import RevisionStore

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == "Darwin" and shutil.which("xcrun"),
                     "actual Swift/CoreData repair fixture requires macOS")
class DeletedTitleWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix="camino-title-wire-")
        cls.addClassCleanup(cls.workspace.cleanup)
        fixture = os.environ.get("CAMINO_DELETED_TITLE_WIRE_FIXTURE")
        if not fixture:
            fixture = str(Path(cls.workspace.name) / "fixture.json")
            result = subprocess.run(["/usr/bin/xcrun", "swift", "test", "--package-path",
                str(ROOT / "camino/app"), "--filter",
                "testRenameDeleteThenContinueLiveTitleAndPrivacyEmitsRepairWireFixture"],
                env={**os.environ, "CAMINO_DELETED_TITLE_WIRE_FIXTURE": fixture},
                capture_output=True, text=True, timeout=180)
            if result.returncode:
                raise AssertionError("Swift deleted-title fixture failed; inspect its test output")
        cls.fixture = json.loads(Path(fixture).read_text())

    def setUp(self):
        self.store = RevisionStore(Path(self.workspace.name) / (self._testMethodName + ".sqlite"))
        store = self.store
        with store._open() as db:
            db.execute("UPDATE meta SET server_id=?,epoch=? WHERE singleton=1",
                       (self.fixture["server_id"], self.fixture["epoch"]))
        self.api = CaminoV1Contract(store, lambda token: token == "Bearer synthetic-owner")

    def send(self, packet, authorization="Bearer synthetic-owner"):
        raw = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
        return self.api.handle("POST", "/api/v1/operations", authorization=authorization,
                               body=raw, content_type="application/json"), raw

    def test_actual_rename_delete_repair_replays_without_weakening_rejection_or_losing_revisions(self):
        store, send = self.store, self.send

        rejected = {packet["device_sequence"]: packet for packet in self.fixture["rejected"]}
        originals = {}
        for packet in self.fixture["repaired"]:
            sequence = packet["device_sequence"]
            if sequence in rejected:
                before = store.state()
                denied, _ = send(rejected[sequence])
                self.assertEqual(denied.status, 422)
                self.assertEqual(denied.body["error"]["message"],
                                 "title target must be a photo or video of this Moment")
                self.assertEqual(store.state(), before)
                self.assertEqual(packet["operation_id"], rejected[sequence]["operation_id"])
                self.assertEqual(packet["expected_revision"], rejected[sequence]["expected_revision"])
            accepted, raw = send(packet)
            self.assertEqual(accepted.status, 200)
            self.assertEqual(accepted.body["cursor"], sequence)
            originals[sequence] = raw

        expected_cursor = len(self.fixture["repaired"])
        self.assertEqual(store.state()["cursor"], expected_cursor)
        self.assertFalse(store.state()["exports_blocked"])
        self.assertFalse(store.state()["reconciliation_required"])
        moment_id = self.fixture["rejected"][0]["payload"]["moment_id"]
        current = store.moment(moment_id)
        self.assertEqual(current["revision"], 5)
        self.assertTrue(current["hidden"])
        self.assertEqual([title["title"] for title in current["attachment_titles"]], ["Live"])
        with store._open() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM assets").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM conflict_candidates").fetchone()[0], 0)
            stored = dict(db.execute("SELECT device_sequence,request_body FROM accepted_operations"))
        self.assertEqual(stored, originals)
        before = store.state()
        for packet in self.fixture["repaired"]:
            self.assertEqual(send(packet)[0].status, 200)
        self.assertEqual(store.state(), before)
        reopened = RevisionStore(store.path)
        self.assertEqual(reopened.moment(moment_id), current)
        self.assertEqual(reopened.state()["cursor"], expected_cursor)

    def test_cancellation_refuses_forged_original_wrong_scope_live_targets_and_bad_titles(self):
        repaired = self.fixture["repaired"]
        first = min(packet["device_sequence"] for packet in self.fixture["rejected"])
        for packet in repaired[:first - 1]:
            self.assertEqual(self.send(packet)[0].status, 200)
        cancel = copy.deepcopy(repaired[first - 1])
        source = self.fixture["rejected"][0]
        variants = []
        for key, value in (("device_sequence", first + 1), ("expected_revision", 9),
                           ("epoch", "00000000-0000-4000-8000-000000000001"),
                           ("operation_id", "00000000-0000-4000-8000-000000000002")):
            original = copy.deepcopy(source)
            original[key] = value
            variants.append(json.dumps(original))
        original = copy.deepcopy(source)
        original["payload"]["moment_id"] = "00000000-0000-4000-8000-000000000003"
        variants.append(json.dumps(original))
        original = copy.deepcopy(source)
        original["payload"]["change"] = {"type": "hidden", "hidden": True}
        variants.append(json.dumps(original))
        live_id = next(packet["payload"]["id"] for packet in repaired if packet["kind"] == "create_asset")
        for key, value in (("target_id", live_id), ("kind", "audio_session"),
                           ("title", "invalid\nprivate title")):
            original = copy.deepcopy(source)
            original["payload"]["change"]["attachment"][key] = value
            variants.append(json.dumps(original))
        variants.extend(("not JSON", "x" * 8193,
                         '{"contract_version":1,"contract_version":1}',
                         '{"contract_version":NaN}'))
        before = self.store.state()
        for raw in variants:
            packet = copy.deepcopy(cancel)
            packet["payload"]["change"]["rejected_envelope"] = raw
            with self.subTest(proof_length=len(raw)):
                self.assertEqual(self.send(packet)[0].status, 422)
                self.assertEqual(self.store.state(), before)
        self.assertEqual(self.send(cancel, authorization="Bearer wrong")[0].status, 401)
        self.assertEqual(self.store.state(), before)
        self.assertEqual(self.send(cancel)[0].status, 200)

    def test_repair_never_rewrites_an_already_accepted_packet(self):
        packet = self.fixture["repaired"][0]
        accepted, raw = self.send(packet)
        self.assertEqual(accepted.status, 200)
        changed = copy.deepcopy(packet)
        changed["payload"]["name"] = "Different synthetic name"
        self.assertEqual(self.send(changed)[0].status, 409)
        with self.store._open() as db:
            persisted = db.execute("SELECT request_body FROM accepted_operations WHERE id=?",
                                   (packet["operation_id"],)).fetchone()[0]
        self.assertEqual(persisted, raw)


if __name__ == "__main__":
    unittest.main()
