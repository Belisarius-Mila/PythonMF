"""Actual Swift queues for two projects through the isolated owner API and media store."""

import copy
import hashlib
import io
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from camino.api.v1 import CaminoV1Contract
from camino.domain.model import ContractError, ProjectDetails
from camino.domain.revision_store import RevisionStore
from camino.server.media_store import MediaStore


class ProjectDetailsTests(unittest.TestCase):
    def test_optional_real_calendar_dates_and_explicit_lifecycle(self):
        for profile in [ProjectDetails(), ProjectDetails(end_date="2027-07-01"),
                        ProjectDetails("2028-02-29", "2028-02-29", "archived")]:
            self.assertIn(profile.status, ("active", "archived"))
        for args in [("2027-02-29",), ("2027-7-01",), ("2027-07-14", "2027-07-01"),
                     (False,), (None, None, "deleted"), (None, None, True)]:
            with self.subTest(args=args), self.assertRaises(ContractError):
                ProjectDetails(*args)


@unittest.skipUnless(platform.system() == "Darwin" and shutil.which("xcrun"), "actual Swift/CoreData requires macOS")
class ProjectWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix="camino-project-wire-")
        cls.addClassCleanup(cls.workspace.cleanup)
        fixture = os.environ.get("CAMINO_PROJECT_WIRE_FIXTURE")
        if not fixture:
            fixture = str(Path(cls.workspace.name) / "fixture.json")
            root = Path(__file__).resolve().parents[1]
            result = subprocess.run(["/usr/bin/xcrun", "swift", "test", "--package-path", str(root / "camino/app"),
                "--filter", "testTwoProjectsKeepFrozenTransfersAndEmitActualWireFixture"],
                env={**os.environ, "CAMINO_PROJECT_WIRE_FIXTURE": fixture}, capture_output=True, text=True, timeout=180)
            if result.returncode:
                raise AssertionError("Swift two-project fixture failed")
        cls.fixture = json.loads(Path(fixture).read_text())

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="camino-project-api-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.store = RevisionStore(self.root / "metadata.sqlite")
        with self.store._connection() as db:
            db.execute("UPDATE meta SET server_id=?,epoch=? WHERE singleton=1",
                       (self.fixture["server_id"], self.fixture["epoch"]))
        self.api = CaminoV1Contract(self.store, authenticate=lambda value: value == "Bearer synthetic-owner")
        self.initial = self.fixture["initial"]
        self.continued = self.fixture["continued"]
        for packet in self.initial:
            self.assertEqual(self.send(packet).status, 200)

    def send(self, packet):
        return self.api.handle("POST", "/api/v1/operations", authorization="Bearer synthetic-owner",
            content_type="application/json", body=json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())

    def finish_metadata(self):
        for packet in self.continued:
            result = self.send(packet)
            self.assertEqual(result.status, 200, result.body)

    def test_catalog_reopen_exact_retry_and_original_archive_preserved(self):
        with sqlite3.connect(self.store.path) as db:
            original = db.execute("SELECT body FROM trips WHERE id=?", (self.fixture["a_id"],)).fetchone()[0]
            moments = db.execute("SELECT * FROM moments ORDER BY id").fetchall()
        self.finish_metadata()
        reopened = RevisionStore(self.store.path)
        projects = {p["id"]: p for p in reopened.projects()}
        self.assertEqual(len(projects), 2)
        a, b = (projects[self.fixture[k]] for k in ("a_id", "b_id"))
        self.assertEqual((a["name"], a["status"], a["start_date"], a["end_date"]),
                         ("First holiday", "archived", "2027-07-01", "2027-07-14"))
        self.assertEqual(b["status"], "active")
        self.assertFalse(a["viewer_enabled"] or b["viewer_enabled"])
        for packet in self.initial + self.continued:
            self.assertEqual(self.send(packet).status, 200)
        with sqlite3.connect(self.store.path) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 3)
            self.assertEqual(db.execute("SELECT body FROM trips WHERE id=?", (a["id"],)).fetchone()[0], original)
            for row in moments:
                self.assertEqual(db.execute("SELECT * FROM moments WHERE id=?", (row[0],)).fetchone(), row)
        self.assertEqual(reopened.projects(), self.store.projects())
        catalog = self.api.handle("GET", "/api/v1/projects", authorization="Bearer synthetic-owner")
        self.assertEqual(catalog.status, 200)
        self.assertEqual(catalog.body["projects"], self.store.projects())
        detail = self.api.handle("GET", "/api/v1/projects/" + a["id"], authorization="Bearer synthetic-owner")
        self.assertEqual(detail.body["project"], a)
        for authorization in (None, "Bearer reader"):
            self.assertEqual(self.api.handle("GET", "/api/v1/projects", authorization=authorization).status, 401)
        self.assertEqual(self.api.handle("GET", "/api/v1/projects/" + str(uuid4()), authorization="Bearer synthetic-owner").status, 404)

    def test_partial_a_upload_finishes_after_project_switch_and_restart(self):
        def media():
            return MediaStore(self.root / "media.sqlite", self.root / "originals", asset_lookup=self.store.asset,
                              reserve_bytes=0, max_chunk_bytes=8)
        a, b = self.fixture["a_asset"], self.fixture["b_asset"]
        content = b"synthetic-A"
        store = media()
        store.create_session(a, chunk_size=8)
        store.receive_chunk(a, 0, content_length=8, expected_sha256=hashlib.sha256(content[:8]).hexdigest(), stream=io.BytesIO(content[:8]))
        self.finish_metadata()
        store = media()
        store.receive_chunk(a, 1, content_length=3, expected_sha256=hashlib.sha256(content[8:]).hexdigest(), stream=io.BytesIO(content[8:]))
        store.finalize(a)
        store.create_session(b, chunk_size=8)
        for index, chunk in enumerate((b"syntheti", b"c-B")):
            store.receive_chunk(b, index, content_length=len(chunk), expected_sha256=hashlib.sha256(chunk).hexdigest(), stream=io.BytesIO(chunk))
        store.finalize(b)
        self.assertEqual(self.store.asset(a)["moment_id"], self.fixture["a_moment"])
        self.assertEqual(self.store.asset(b)["moment_id"], self.fixture["b_moment"])
        self.assertEqual((self.root / "originals/objects" / (a + ".bin")).read_bytes(), b"synthetic-A")
        self.assertEqual((self.root / "originals/objects" / (b + ".bin")).read_bytes(), b"synthetic-B")
        self.assertEqual(store.status(a)["state"], "verified")

    def test_cross_project_day_link_is_rejected_and_viewer_grants_stay_separate(self):
        self.finish_metadata()
        packet = copy.deepcopy(next(p for p in self.continued if p["kind"] == "create_moment"))
        packet.update(operation_id=str(uuid4()), device_sequence=self.store.state()["cursor"] + 1)
        packet["payload"].update(id=str(uuid4()), trip_id=self.fixture["a_id"])
        self.assertEqual(self.send(packet).status, 422)
        self.store.set_viewer_permission(self.fixture["a_id"], enabled=True)
        self.assertEqual([m["id"] for m in self.store.viewer_snapshot(self.fixture["a_id"])["moments"]], [self.fixture["a_moment"]])
        self.assertEqual(self.store.viewer_snapshot(self.fixture["b_id"])["moments"], [])
        self.store.set_viewer_permission(self.fixture["b_id"], enabled=True)
        self.assertEqual([m["id"] for m in self.store.viewer_snapshot(self.fixture["b_id"])["moments"]], [self.fixture["b_moment"]])

    def test_project_revision_conflict_and_old_day_identity_remain_safe(self):
        self.finish_metadata()
        packet = copy.deepcopy(next(p for p in self.continued if p["kind"] == "set_project_details"))
        packet.update(operation_id=str(uuid4()), device_sequence=self.store.state()["cursor"] + 1)
        before = self.store.projects()
        self.assertEqual(self.send(packet).status, 409)
        self.assertEqual(self.store.projects(), before)
        packet = copy.deepcopy(next(p for p in self.initial if p["kind"] == "create_day"))
        packet.update(operation_id=str(uuid4()), device_sequence=self.store.state()["cursor"] + 1)
        packet["payload"]["id"] = str(uuid4())
        self.assertEqual(self.send(packet).status, 409)
        self.assertEqual(self.store.projects(), before)
