"""Mac-only closure: synthetic archives, no launchctl/network or personal media."""
import hashlib
import http.client
import json
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from app import camino_film_workshop as workshop
from app import cockpit
from camino.film.closed_day import ClosedDayError
from tests.camino_viewer_fixture import ViewerFixture


class MacFilmTests(unittest.TestCase):
    def test_frontend_hides_stale_projects_and_requires_confirmation(self):
        from scripts.cockpit_quality_gate import node_binary
        result = subprocess.run([node_binary(), str(Path(__file__).with_name("camino_film_frontend.test.cjs"))],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir="/private/tmp")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        archive = self.root / "archive"
        archive.mkdir(mode=0o700)
        self.f = ViewerFixture(archive)
        self.f.upload(30, "photo", b"synthetic photo")
        self.f.upload(31, "video", b"synthetic video")
        self.f.upload(32, "audio", b"synthetic audio")
        self.f.upload(33, "audio", b"PRIVATE-AUDIO", private=True)
        self.store = workshop.MacFilmProjectStore(self.root / "projects",
            metadata_db=self.f.store.path, media_db=self.f.media.database_path,
            media_root=self.f.media.root, trip_id=self.f.trip.id)
        self.day = self.f.day.local_date

    def close(self):
        return self.store.close_mac_day(self.day, confirmed=True)

    def archive_hashes(self):
        return {str(p.relative_to(self.root / "archive")): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (self.root / "archive").rglob("*") if p.is_file()}

    def test_status_and_refused_confirmation_do_not_create_store_or_write_archive(self):
        before = self.archive_hashes()
        self.assertFalse(self.store.day_status(self.day)["exists"])
        for value in [False, "true", 1, None]:
            with self.assertRaises(ClosedDayError):
                self.store.close_mac_day(self.day, confirmed=value)
        self.assertFalse(self.store.root.exists())
        self.assertEqual(before, self.archive_hashes())

    def test_create_preserves_archive_and_records_mac_origin_with_whole_video(self):
        before = self.archive_hashes()
        result = self.close()
        self.assertTrue(result["valid"])
        self.assertEqual((result["source_count"], result["photo_count"], result["video_count"], result["audio_count"]), (3, 1, 1, 1))
        self.assertEqual(before, self.archive_hashes())
        folder = self.store.root / result["project_id"]
        manifest = json.loads((folder / "manifest.json").read_text())
        project = json.loads((folder / "project-r1.json").read_text())
        confirmation = json.loads((folder / "mac-confirmation.json").read_text())
        self.assertEqual(manifest["closure_origin"], workshop.ORIGIN)
        self.assertNotIn("phone_proof_sha256", manifest)
        self.assertNotIn("pending_media", confirmation)
        self.assertNotIn("pending_metadata", confirmation)
        self.assertEqual(project["shots"][1]["in_ms"], 0)
        self.assertEqual(project["shots"][1]["out_ms"], 1500)
        self.assertEqual(project["shots"][0]["out_ms"], 3000)
        self.assertNotIn("PRIVATE", json.dumps(result))
        self.assertNotIn(self.f.private.id, json.dumps(result))
        self.assertNotIn("excluded", result)

    def test_connections_cannot_write_existing_databases(self):
        with self.store._metadata_connection() as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("UPDATE meta SET cursor=999")
        connection = self.store.media._open()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM verified_assets")
        finally:
            connection.close()

    def test_repeat_and_private_text_use_same_immutable_project(self):
        first = self.close()
        folder = self.store.root / first["project_id"]
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        self.f.text(self.f.private, 25, "Private update outside the film selection")
        # This is still the same day but text does not alter the accepted Moment
        # revision/inventory; no other content silently enters the closed project.
        second = self.close()
        self.assertEqual(first["project_id"], second["project_id"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})

    def test_privacy_change_hides_all_old_counts_titles_and_shots(self):
        self.close()
        self.f.lock()
        result = self.store.day_status(self.day)
        self.assertTrue(result["exists"])
        self.assertFalse(result["valid"])
        self.assertNotIn("source_count", result)
        self.assertNotIn("shots", result)

    def test_missing_or_changed_original_blocks_create(self):
        path = self.f.media.objects / (self.f.upload(34, "photo", b"one more photo")["id"] + ".bin")
        path.write_bytes(b"same len wrong")
        with self.assertRaises(ClosedDayError):
            self.close()
        self.assertFalse(any(p.is_dir() for p in self.store.root.iterdir()))

    def test_incomplete_media_and_recovery_flags_block_create(self):
        self.f.upload(35, "video", b"pending", complete=False)
        with self.assertRaises(ClosedDayError):
            self.close()
        with self.f.store._connection() as db:
            db.execute("UPDATE meta SET exports_blocked=1")
        with self.assertRaises(ClosedDayError):
            self.close()

    def test_project_store_must_not_overlap_archive(self):
        with self.assertRaises(ClosedDayError):
            workshop.MacFilmProjectStore(self.f.media.root, metadata_db=self.f.store.path,
                media_db=self.f.media.database_path, media_root=self.f.media.root, trip_id=self.f.trip.id)

    def test_changed_confirmation_is_rejected(self):
        result = self.close()
        folder = self.store.root / result["project_id"]
        path = folder / "mac-confirmation.json"
        data = json.loads(path.read_text()); data["owner_confirmed_final"] = False
        path.write_text(json.dumps(data))
        with self.assertRaises(ClosedDayError):
            self.store.day_status(self.day)

    def test_status_never_reads_a_symlinked_foreign_project(self):
        self.store.root.mkdir(mode=0o700)
        foreign = self.root / "foreign"
        foreign.mkdir()
        (foreign / "manifest.json").write_text('{"PRIVATE": "outside project store"}')
        (self.store.root / "00000000-0000-0000-0000-000000000080").symlink_to(foreign, target_is_directory=True)
        with patch.object(self.store, "_read", wraps=self.store._read) as read:
            self.assertFalse(self.store.day_status(self.day)["exists"])
            read.assert_not_called()

    def test_http_confirmation_origin_and_summary_contract(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        with patch.object(workshop, "production_store", return_value=self.store), patch.object(workshop, "DAY", self.day):
            thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                def request(method, path, value=None, origin=None):
                    headers = {"Content-Type": "application/json"}
                    if origin: headers["Origin"] = origin
                    conn.request(method, path, body=json.dumps(value) if value is not None else None, headers=headers)
                    response = conn.getresponse()
                    return response.status, json.loads(response.read())
                self.assertEqual(request("GET", "/api/camino/film/day")[0], 200)
                code, result = request("POST", "/api/camino/film/close-mac-day", {"confirmed_final_mac_data": False})
                self.assertEqual(code, 409)
                self.assertFalse(self.store.root.exists())
                code, result = request("POST", "/api/camino/film/close-mac-day", {"confirmed_final_mac_data": True}, "https://foreign.example")
                self.assertEqual(code, 403)
                self.assertFalse(self.store.root.exists())
                # Access rejection closes the connection; HTTPConnection reconnects.
                code, result = request("POST", "/api/camino/film/close-mac-day", {"confirmed_final_mac_data": True}, f"http://127.0.0.1:{server.server_port}")
                self.assertEqual(code, 200)
                self.assertTrue(result["valid"])
                self.assertEqual(result["source_count"], 3)
                self.assertEqual(request("GET", "/api/camino/film/day?path=secret")[0], 400)
                pid = result["project_id"]
                code, chosen = request("GET", f"/api/camino/film/day?local_date={self.day}&project_id={pid}")
                self.assertEqual(code, 200); self.assertEqual(chosen["project_id"], pid)
                for query in ("local_date=2026-02-30", "local_date=", "project_id=../secret",
                              f"project_id={pid}&project_id={pid}"):
                    self.assertEqual(request("GET", "/api/camino/film/day?" + query)[0], 400)
                self.assertFalse(request("GET", f"/api/camino/film/day?local_date=2026-09-26&project_id={pid}")[1]["ok"])
                for value in (None, False, 26):
                    self.assertEqual(request("POST", "/api/camino/film/close-mac-day",
                        {"confirmed_final_mac_data": True, "local_date": value})[0], 400)
                code, result = request("POST", "/api/camino/film/close-mac-day",
                    {"confirmed_final_mac_data": True, "local_date": self.day})
                self.assertEqual(code, 200); self.assertEqual(result["project_id"], pid)
                conn.close()
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=3)
