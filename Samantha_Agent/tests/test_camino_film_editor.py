"""Synthetic tests of edit persistence, consent routes, private output and real rendering."""
import copy
import fcntl
from dataclasses import replace
import array
import http.client
import json
import math
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch, Mock
from uuid import uuid4

from app import cockpit
from app.camino_film_editor import FilmEditor, validate_draft
from app.camino_film_cleanup import DELETE_CONFIRMATION, deletion_plan, delete_export
from app.camino_film_workshop import MacFilmProjectStore
from app.file_persistence import atomic_write_json
from camino.film.media import ffmpeg, probe, binary, run, FONT
from camino.film.project import FilmError, digest
from tests.camino_viewer_fixture import ViewerFixture, uid
from camino.domain.codec import wire
from camino.domain.model import JourneyDay, Privacy


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir="/private/tmp"); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        archive = self.root / "archive"; archive.mkdir(mode=0o700)
        self.f = ViewerFixture(archive)
        self.f.upload(30, "photo", b"synthetic photo")
        self.f.upload(31, "video", b"synthetic video")
        self.f.upload(32, "audio", b"synthetic audio")
        self.f.upload(33, "audio", b"PRIVATE-CONTENT", private=True)
        self.store = MacFilmProjectStore(self.root / "projects", metadata_db=self.f.store.path,
            media_db=self.f.media.database_path, media_root=self.f.media.root, trip_id=self.f.trip.id)
        self.pid = self.store.close_mac_day(self.f.day.local_date, confirmed=True)["project_id"]
        self.editor = FilmEditor(self.store, day=self.f.day.local_date)

    def payload(self):
        v = self.editor.view()
        return {"project_id": self.pid, "expected_revision": v["revision"],
                "request_id": str(uuid4()), "draft": copy.deepcopy(v["draft"])}

    def second_day(self, *, close=True, private_only=False):
        self.f.day = JourneyDay(uid(50), self.f.trip.id, "2026-09-26")
        self.f.capture = replace(self.f.capture, local_wall="2026-09-26T10:00:00", utc_ms=self.f.capture.utc_ms + 86400000)
        self.f.send("create_day", wire(self.f.day))
        self.f.public = self.f.moment(51, Privacy.DIARY)
        self.f.private = self.f.moment(52, Privacy.OWNER_ONLY)
        self.f.upload(60, "photo", b"second synthetic photo", private=private_only)
        self.f.upload(61, "video", b"second synthetic video", private=private_only)
        return self.store.close_mac_day(self.f.day.local_date, confirmed=True)["project_id"] if close else None

    def test_two_days_keep_revisions_sources_worker_and_exports_separate(self):
        first = self.payload(); first["draft"]["shots"][0]["title"] = "First saved edit"
        self.editor.save(first)
        _, old_job = self.queue()
        with patch("app.camino_film_render.render_edit", side_effect=self.fake_render): self.editor.run_queue(self.pid)
        before = {p: digest(p) for p in (self.store.root / self.pid).rglob("*") if p.is_file()}
        second = self.second_day()
        view = self.editor.view(second)
        self.assertEqual((view["project_id"], view["local_date"], view["revision"]), (second, "2026-09-26", 1))
        draft = copy.deepcopy(view["draft"]); draft["shots"][0]["title"] = "Second saved edit"
        self.editor.save({"project_id": second, "expected_revision": 1, "request_id": str(uuid4()), "draft": draft})
        with self.assertRaises(FilmError):
            self.editor.save({"project_id": second, "expected_revision": 2, "request_id": str(uuid4()), "draft": first["draft"]})
        job = self.editor.enqueue({"project_id": second, "revision": 2, "request_id": str(uuid4()),
            "profile": "preview", "range": None}, background=False)
        with patch("app.camino_film_render.render_edit", side_effect=self.fake_render): self.editor.run_queue(second)
        self.assertEqual(self.editor.output(second, job["job_id"]).read_bytes(), b"synthetic mp4 bytes")
        with self.assertRaises(FilmError): self.editor.output(second, old_job["job_id"])
        self.assertEqual(before, {p: digest(p) for p in before})
        self.assertEqual(self.editor.view()["draft"]["shots"][0]["title"], "First saved edit")
        self.assertEqual(self.editor.view(second)["draft"]["shots"][0]["title"], "Second saved edit")
        catalog = self.editor.catalog()
        self.assertEqual([p["project_id"] for p in catalog["projects"]], [second, self.pid])
        self.assertEqual([(p["revision"], p["ready_exports"]) for p in catalog["projects"]], [(2, 1), (2, 1)])
        self.assertNotIn("First saved edit", json.dumps(catalog))

    def test_catalog_rechecks_privacy_without_hiding_the_other_day(self):
        second = self.second_day()
        self.f.lock()
        catalog = self.editor.catalog()
        self.assertEqual(catalog["days"], [{"local_date": "2026-09-25"}])
        self.assertEqual([p["project_id"] for p in catalog["projects"]], [self.pid])
        with self.assertRaises(FilmError): self.editor.view(second)
        self.assertEqual(self.editor.view()["project_id"], self.pid)

    def test_catalog_prefers_last_saved_edit_not_capture_day_or_export_time(self):
        second = self.second_day()
        first_edit = self.payload()
        first_edit['draft']['shots'][0]['title'] = 'Resumed older day'
        self.editor.save(first_edit)
        first_path = self.store.root / self.pid / 'edit-r000002.json'
        second_path = self.store.root / second / 'project-r1.json'
        os.utime(second_path, ns=(2_000_000_000, 2_000_000_000))
        os.utime(first_path, ns=(3_000_000_000, 3_000_000_000))
        before = {p: (digest(p), p.stat().st_mtime_ns) for p in self.store.root.rglob('*') if p.is_file()}
        catalog = self.editor.catalog()
        self.assertEqual([p['project_id'] for p in catalog['projects']], [self.pid, second])
        self.assertEqual(catalog['projects'][0]['last_edited_ms'], 3000)
        self.assertEqual(before, {p: (digest(p), p.stat().st_mtime_ns) for p in before})
        _, job = self.queue()
        with patch('app.camino_film_render.render_edit', side_effect=self.fake_render):
            self.editor.run_queue(self.pid)
        # Reading/rendering a film does not update the saved draft clock.
        self.assertEqual(self.editor.catalog()['projects'][0]['last_edited_ms'], 3000)

    def test_catalog_candidates_are_read_only_and_exclude_private_only_days(self):
        self.second_day(close=False, private_only=True)
        before = {p: digest(p) for p in self.root.rglob("*") if p.is_file()}
        catalog = self.editor.catalog()
        self.assertEqual(catalog["days"], [{"local_date": "2026-09-25"}])
        self.assertEqual(before, {p: digest(p) for p in before})
        empty = MacFilmProjectStore(self.root / "empty-projects", metadata_db=self.f.store.path,
            media_db=self.f.media.database_path, media_root=self.f.media.root, trip_id=self.f.trip.id)
        self.assertEqual(FilmEditor(empty).catalog()["projects"], [])
        self.assertFalse(empty.root.exists())

    def test_catalog_skips_unsafe_and_unconfirmed_projects(self):
        foreign = self.root / "foreign"; foreign.mkdir()
        (foreign / "manifest.json").write_text('{"PRIVATE": "foreign content"}')
        (self.store.root / uid(80)).symlink_to(foreign, target_is_directory=True)
        (self.store.root / uid(81)).mkdir()
        catalog = self.editor.catalog()
        self.assertEqual([p["project_id"] for p in catalog["projects"]], [self.pid])
        self.assertNotIn("PRIVATE", json.dumps(catalog))
        other_trip = MacFilmProjectStore(self.store.root, metadata_db=self.f.store.path,
            media_db=self.f.media.database_path, media_root=self.f.media.root, trip_id=uid(99))
        self.assertEqual(FilmEditor(other_trip).catalog(), {"ok": True, "days": [], "projects": []})

    def queue(self, **changes):
        payload = {"project_id": self.pid, "revision": self.editor.view()["revision"],
                   "request_id": str(uuid4()), "profile": "preview", "range": None, **changes}
        return payload, self.editor.enqueue(payload, background=False)

    @staticmethod
    def fake_render(edit, manifest, objects, output, profile, interval, **kwargs):
        kwargs["revalidate"]()
        path = output / "film.mp4"; path.write_bytes(b"synthetic mp4 bytes")
        return {"bytes": path.stat().st_size, "sha256": digest(path)}

    def ready_export(self):
        payload, job = self.queue()
        with patch("app.camino_film_render.render_edit", side_effect=self.fake_render): self.editor.run_queue(self.pid)
        selected = {"project_id": self.pid, "job_id": job["job_id"]}
        return payload, selected, self.store.root / self.pid / "jobs" / job["job_id"]

    def test_export_completion_time_is_exact_and_survives_reads_and_duplicate_request(self):
        instant = datetime(2026, 10, 28, 11, 34, 56, tzinfo=timezone.utc)
        with patch("app.camino_film_editor.datetime") as clock:
            clock.now.return_value = instant
            payload, selected, folder = self.ready_export()
        status = json.loads((folder / "status.json").read_text())
        self.assertEqual(status["completed_at"], "2026-10-28T11:34:56+00:00")
        original = {name: (folder / name).read_bytes() for name in ("request.json", "status.json")}
        for _ in range(2):
            job = self.editor.view()["jobs"][0]
            self.assertEqual(job["created_at"], status["completed_at"])
            self.assertFalse(job["created_at_estimated"])
            self.assertEqual(job["job_id"], selected["job_id"])
        self.editor.enqueue(payload, background=False)
        self.editor.run_queue(self.pid)
        self.assertEqual(original, {name: (folder / name).read_bytes() for name in original})

    def test_old_export_time_is_estimated_from_metadata_without_migration(self):
        _, _, folder = self.ready_export()
        path = folder / "status.json"
        status = json.loads(path.read_text()); status.pop("completed_at")
        atomic_write_json(path, status)
        stamp = datetime(2026, 7, 1, 8, 9, 10, tzinfo=timezone.utc).timestamp()
        os.utime(path, (stamp, stamp))
        before = path.read_bytes(), path.stat().st_mtime_ns
        for _ in range(2):
            job = self.editor.view()["jobs"][0]
            self.assertEqual(job["created_at"], "2026-07-01T08:09:10+00:00")
            self.assertTrue(job["created_at_estimated"])
        self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))

    def delete_payload(self, selected):
        plan = deletion_plan(self.editor, selected)
        return {**selected, "plan_token": plan["plan_token"], "confirmation": DELETE_CONFIRMATION}

    def test_permanent_delete_removes_every_attempt_but_keeps_sources_edits_and_other_day(self):
        queued, selected, folder = self.ready_export()
        abandoned = folder / ("attempt-" + uuid4().hex); abandoned.mkdir(mode=0o700)
        for n in range(8): (abandoned / f"segment-{n}.mkv").write_bytes(b"working bytes" * 100)
        (abandoned / "render.partial.mp4").write_bytes(b"partial")
        second = self.second_day()
        protected = [*(self.root / "archive").rglob("*"), *(self.store.root / second).rglob("*"),
                     *(self.store.root / self.pid).glob("*.json")]
        protected = {p: digest(p) for p in protected if p.is_file()}
        original = {p: digest(p) for p in folder.rglob("*") if p.is_file()}
        plan = deletion_plan(self.editor, selected)
        self.assertEqual(original, {p: digest(p) for p in original}, "preview never changes the variant")
        self.assertEqual(plan["file_count"], 10)
        self.assertNotIn("entries", plan)
        payload = {**selected, "plan_token": plan["plan_token"], "confirmation": DELETE_CONFIRMATION}
        result = delete_export(self.editor, payload)
        self.assertEqual(result["deleted_bytes"], plan["bytes"])
        self.assertEqual({p.name for p in folder.iterdir()}, {"request.json", "status.json", "status.json.lock"})
        self.assertEqual(protected, {p: digest(p) for p in protected})
        self.assertEqual(self.editor.view()["jobs"], [])
        self.assertEqual(next(p for p in self.editor.catalog()["projects"] if p["project_id"] == self.pid)["ready_exports"], 0)
        self.assertTrue(delete_export(self.editor, payload)["already_deleted"])
        with self.assertRaises(FilmError): self.editor.output(self.pid, selected["job_id"])
        with self.assertRaises(FilmError): self.editor.enqueue(queued, background=False)
        self.assertTrue(self.editor.enqueue({**queued, "request_id": str(uuid4())}, background=False)["queued"])

    def test_delete_refuses_confirmation_changes_paths_source_proxy_and_busy_worker(self):
        _, selected, folder = self.ready_export()
        payload = self.delete_payload(selected)
        for confirmation in (None, True, "ano", ""):
            with self.assertRaises(FilmError): delete_export(self.editor, {**payload, "confirmation": confirmation})
        with self.assertRaises(FilmError): deletion_plan(self.editor, {**selected, "job_id": "../archive"})
        extra = folder / ("attempt-" + uuid4().hex); extra.mkdir(mode=0o700)
        (extra / "new.mp4").write_bytes(b"new working bytes")
        with self.assertRaises(FilmError): delete_export(self.editor, payload)
        self.assertTrue((extra / "new.mp4").is_file())
        current = self.delete_payload(selected)
        lock = os.open(self.store.root / self.pid / ".render-worker", os.O_RDONLY)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(FilmError): deletion_plan(self.editor, selected)
            with self.assertRaises(FilmError): delete_export(self.editor, current)
        finally: os.close(lock)
        source = self.editor.source_preview(self.source_payload(), background=False)
        with patch("app.camino_film_render.render_edit", side_effect=self.fake_render): self.editor.run_queue(self.pid)
        with self.assertRaises(FilmError): deletion_plan(self.editor, {**selected, "job_id": source["job_id"]})

    def test_delete_refuses_links_and_never_traverses_into_originals(self):
        _, selected, folder = self.ready_export()
        attempt = next(folder.glob("attempt-*"))
        original = next(self.f.media.objects.iterdir()); before = digest(original)
        link = attempt / "foreign.bin"; link.symlink_to(original)
        with self.assertRaises((FilmError, OSError)): deletion_plan(self.editor, selected)
        self.assertEqual(digest(original), before)
        # Replace only the synthetic link created by this test.
        link.unlink(); os.link(original, link)
        with self.assertRaises(FilmError): deletion_plan(self.editor, selected)
        self.assertEqual(digest(original), before)

    def test_delete_accepts_renderer_internal_links_and_nested_work_files(self):
        _, selected, folder = self.ready_export()
        attempt = next(folder.glob("attempt-*"))
        os.link(attempt / "film.mp4", attempt / "render.partial.mp4")
        qa = attempt / "qa"; qa.mkdir(mode=0o700)
        (qa / "frame.png").write_bytes(b"synthetic frame")
        protected = digest(next(self.f.media.objects.iterdir()))
        payload = self.delete_payload(selected)
        self.assertEqual(deletion_plan(self.editor, selected)["file_count"], 3)
        self.assertTrue(delete_export(self.editor, payload)["deleted"])
        self.assertFalse(list(folder.glob("attempt-*")))
        self.assertEqual(self.editor.view()["jobs"], [])
        self.assertEqual(digest(next(self.f.media.objects.iterdir())), protected)

    def test_delete_refuses_any_link_outside_selected_variant_even_with_internal_pair(self):
        _, selected, folder = self.ready_export()
        attempt = next(folder.glob("attempt-*"))
        os.link(attempt / "film.mp4", attempt / "render.partial.mp4")
        foreign = self.root / "foreign.mp4"
        os.link(attempt / "film.mp4", foreign)
        before = digest(foreign)
        with self.assertRaises(FilmError): self.delete_payload(selected)
        self.assertEqual(digest(foreign), before)
        self.assertEqual((attempt / "film.mp4").stat().st_nlink, 3)
        self.assertEqual(self.editor.view()["jobs"][0]["state"], "ready")

    def test_interrupted_delete_resumes_after_one_internal_link_was_removed(self):
        _, selected, folder = self.ready_export()
        attempt = next(folder.glob("attempt-*"))
        os.link(attempt / "film.mp4", attempt / "render.partial.mp4")
        qa = attempt / "qa"; qa.mkdir(mode=0o700)
        (qa / "frame.png").write_bytes(b"frame")
        payload = self.delete_payload(selected)
        real_unlink = os.unlink; removed = []
        def interrupt(name, *, dir_fd=None):
            if dir_fd is not None:
                if removed: raise OSError("synthetic interruption")
                removed.append(name)
            return real_unlink(name, dir_fd=dir_fd)
        with patch("app.camino_film_cleanup.os.unlink", side_effect=interrupt):
            with self.assertRaises(OSError): delete_export(self.editor, payload)
        self.assertEqual(removed, ["film.mp4"])
        self.assertEqual((attempt / "render.partial.mp4").stat().st_nlink, 1)
        self.assertEqual(self.editor.view()["jobs"][0]["state"], "delete_pending")
        self.assertEqual(deletion_plan(self.editor, selected)["plan_token"], payload["plan_token"])
        self.assertTrue(delete_export(self.editor, payload)["deleted"])
        self.assertEqual(self.editor.view()["jobs"], [])

    def test_nested_work_directory_never_follows_external_symlinks(self):
        _, selected, folder = self.ready_export()
        attempt = next(folder.glob("attempt-*"))
        qa = attempt / "qa"; qa.mkdir(mode=0o700)
        (qa / "foreign").symlink_to(self.f.media.objects, target_is_directory=True)
        before = {p: digest(p) for p in self.f.media.objects.iterdir()}
        with self.assertRaises((FilmError, OSError)): self.delete_payload(selected)
        self.assertEqual(before, {p: digest(p) for p in before})

    def test_new_external_link_after_plan_blocks_unlink(self):
        _, selected, folder = self.ready_export()
        attempt = next(folder.glob("attempt-*"))
        os.link(attempt / "film.mp4", attempt / "render.partial.mp4")
        payload = self.delete_payload(selected)
        foreign = self.root / "foreign.mp4"
        def add_external_link(*args, **kwargs):
            result = atomic_write_json(*args, **kwargs)
            os.link(attempt / "film.mp4", foreign)
            return result
        with patch("app.camino_film_cleanup.atomic_write_json", side_effect=add_external_link):
            with self.assertRaises(FilmError): delete_export(self.editor, payload)
        self.assertEqual((attempt / "film.mp4").read_bytes(), b"synthetic mp4 bytes")
        self.assertTrue((attempt / "render.partial.mp4").is_file())
        self.assertTrue(foreign.is_file())

    def test_interrupted_delete_can_finish_without_restoring_or_delivering_bytes(self):
        _, selected, folder = self.ready_export()
        attempt = next(folder.glob("attempt-*")); (attempt / "segment.mkv").write_bytes(b"working")
        payload = self.delete_payload(selected)
        real_unlink = os.unlink; deleted = []
        def interrupt(name, *, dir_fd=None):
            if dir_fd is not None:
                if deleted: raise OSError("synthetic interruption")
                deleted.append(name)
            return real_unlink(name, dir_fd=dir_fd)
        with patch("app.camino_film_cleanup.os.unlink", side_effect=interrupt):
            with self.assertRaises(OSError): delete_export(self.editor, payload)
        self.assertEqual(self.editor.view()["jobs"][0]["state"], "delete_pending")
        with self.assertRaises(FilmError): self.editor.output(self.pid, selected["job_id"])
        remaining = deletion_plan(self.editor, selected)
        self.assertEqual(remaining["plan_token"], payload["plan_token"])
        self.assertEqual(remaining["file_count"], 1)
        self.assertTrue(delete_export(self.editor, payload)["deleted"])
        self.assertFalse(list(folder.glob("attempt-*")))
        self.assertEqual(self.editor.view()["jobs"], [])

    def test_queued_or_foreign_project_delete_does_not_remove_a_variant(self):
        _, selected, folder = self.ready_export()
        second = self.second_day()
        with self.assertRaises(FilmError): deletion_plan(self.editor, {**selected, "project_id": second})
        _, queued = self.queue()
        with self.assertRaises(FilmError): deletion_plan(self.editor, {**selected, "job_id": queued["job_id"]})
        self.assertTrue(list(folder.glob("attempt-*")))

    def test_delete_selects_one_partial_export_even_with_identical_revision_and_range(self):
        interval = {"start_ms": 0, "end_ms": 1000}
        _, first = self.queue(range=interval); _, second = self.queue(range=interval)
        with patch("app.camino_film_render.render_edit", side_effect=self.fake_render): self.editor.run_queue(self.pid)
        before = self.editor.output(self.pid, second["job_id"]); expected = digest(before)
        selected = {"project_id": self.pid, "job_id": first["job_id"]}
        self.assertEqual(deletion_plan(self.editor, selected)["range"], interval)
        delete_export(self.editor, self.delete_payload(selected))
        self.assertEqual(digest(self.editor.output(self.pid, second["job_id"])), expected)
        self.assertEqual([j["job_id"] for j in self.editor.view()["jobs"]], [second["job_id"]])

    def test_concurrent_deletes_are_idempotent_and_never_restore_the_variant(self):
        _, selected, folder = self.ready_export()
        payload = self.delete_payload(selected); barrier = threading.Barrier(2); results = []; errors = []
        def remove():
            barrier.wait(timeout=3)
            try: results.append(delete_export(self.editor, payload))
            except Exception as error: errors.append(type(error).__name__)
        threads = [threading.Thread(target=remove) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=5); self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertCountEqual([r["already_deleted"] for r in results], [False, True])
        self.assertFalse(list(folder.glob("attempt-*")))

    def test_oversized_recovery_record_is_refused_before_any_file_is_removed(self):
        _, selected, folder = self.ready_export()
        before = {p: digest(p) for p in folder.rglob("*") if p.is_file()}
        inventory = [{"path": f"attempt-{'a' * 32}/segment-{n:06d}.mkv", "kind": "file",
                      "device": 1, "inode": n + 1, "bytes": 100, "mtime_ns": 1} for n in range(6000)]
        with patch("app.camino_film_cleanup._inventory", return_value=inventory):
            with self.assertRaises(FilmError): deletion_plan(self.editor, selected)
        self.assertEqual(before, {p: digest(p) for p in before})
        self.assertEqual(self.editor.view()["jobs"][0]["state"], "ready")

    def test_http_delete_is_origin_guarded_exact_confirmed_and_revokes_get_head_range(self):
        _, selected, folder = self.ready_export()
        server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        with patch("app.camino_film_editor.production_editor", return_value=self.editor), patch.object(cockpit, "production_editor", return_value=self.editor):
            thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                def request(method, path, value=None, headers=None):
                    conn.request(method, path, body=None if value is None else json.dumps(value),
                        headers={"Content-Type": "application/json", **(headers or {})})
                    response = conn.getresponse(); return response.status, response.read()
                base = "/api/camino/film/"
                self.assertEqual(request("POST", base + "delete-plan", selected, {"Origin": "https://foreign.example"})[0], 403)
                self.assertEqual(request("POST", base + "delete-plan?file=secret", selected)[0], 400)
                code, body = request("POST", base + "delete-plan", selected)
                self.assertEqual(code, 200); plan = json.loads(body)
                payload = {**selected, "plan_token": plan["plan_token"], "confirmation": DELETE_CONFIRMATION}
                self.assertEqual(request("POST", base + "delete", {**payload, "confirmation": "ano"})[0], 409)
                self.assertEqual(request("POST", base + "delete", payload, {"Origin": "https://foreign.example"})[0], 403)
                self.assertTrue(list(folder.glob("attempt-*")))
                self.assertEqual(request("POST", base + "delete", payload)[0], 200)
                self.assertEqual(request("POST", base + "delete", payload)[0], 200)
                url = base + "output/" + self.pid + "/" + selected["job_id"]
                for method, headers in (("GET", {}), ("HEAD", {}), ("GET", {"Range": "bytes=0-3"})):
                    self.assertEqual(request(method, url, headers=headers)[0], 404)
                self.assertFalse(list(folder.glob("attempt-*")))
                conn.close()
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=3)

    def test_read_only_view_keeps_base_and_archive_unchanged(self):
        before = {p: digest(p) for p in (self.root / "archive").rglob("*") if p.is_file()}
        folder = self.store.root / self.pid
        original = (folder / "project-r1.json").read_bytes()
        v = self.editor.view()
        self.assertEqual(v["revision"], 1)
        self.assertEqual(v["duration_ms"], 4500)
        self.assertFalse(v["draft"]["voices"][0]["included"])
        self.assertNotIn("PRIVATE", json.dumps(v))
        self.assertFalse(list(folder.glob("edit-r*.json")))
        self.assertEqual(original, (folder / "project-r1.json").read_bytes())
        self.assertEqual(before, {p: digest(p) for p in before})

    def test_immutable_revision_and_lost_reply_idempotence(self):
        p = self.payload(); p["draft"]["shots"][0]["title"] = "Ručně změněný titulek"
        self.assertEqual(self.editor.save(p)["revision"], 2)
        self.assertEqual(self.editor.save(p)["revision"], 2)
        p2 = self.payload(); p2["draft"]["shots"].reverse()
        self.editor.save(p2)
        folder, manifest = self.editor.inputs()
        self.assertEqual(self.editor.revision(folder, manifest, 2)["draft"]["shots"][0]["title"], "Ručně změněný titulek")
        self.assertEqual(self.editor.view()["revision"], 3)
        with self.assertRaises(FilmError):
            p["draft"]["shots"][0]["title"] = "Conflict"; self.editor.save(p)

    def test_optimistic_conflict_does_not_overwrite_edits(self):
        first, second = self.payload(), self.payload()
        first["draft"]["shots"][0]["out_ms"] = 6000
        self.editor.save(first)
        with self.assertRaises(FilmError): self.editor.save(second)
        self.assertEqual(self.editor.view()["draft"]["shots"][0]["out_ms"], 6000)

    def test_concurrent_saves_commit_exactly_one_revision(self):
        barrier = threading.Barrier(2); outcomes = []
        payloads = [self.payload(), self.payload()]
        def save(p):
            barrier.wait(timeout=3)
            try: self.editor.save(p); outcomes.append("saved")
            except FilmError: outcomes.append("conflict")
        threads = [threading.Thread(target=save, args=(p,)) for p in payloads]
        for t in threads: t.start()
        for t in threads: t.join(timeout=5); self.assertFalse(t.is_alive())
        self.assertCountEqual(outcomes, ["saved", "conflict"])
        self.assertEqual(self.editor.view()["revision"], 2)

    def test_invalid_trim_private_source_and_nonfinite_gain_are_rejected(self):
        for mutate in (
            lambda d: d["shots"][1].update(out_ms=1501),
            lambda d: d["shots"][0].update(in_ms=1),
            lambda d: d["shots"][0].update(asset_id=self.f.private.id),
            lambda d: d["shots"][0].update(gain=float("nan")),
            lambda d: d["shots"][0].update(included="true"),
            lambda d: d["shots"].clear(),
        ):
            p = self.payload(); mutate(p["draft"])
            with self.assertRaises(FilmError): self.editor.save(p)
        self.assertEqual(self.editor.view()["revision"], 1)

    def test_whole_voice_requires_explicit_placement_and_sufficient_picture(self):
        p = self.payload(); p["draft"]["voices"][0].update(included=True, at_ms=4000)
        with self.assertRaisesRegex(FilmError, "přesahuje"): self.editor.save(p)
        p["draft"]["shots"][0]["out_ms"] = 6000
        self.editor.save(p)
        voice = self.editor.view()["draft"]["voices"][0]
        self.assertEqual((voice["in_ms"], voice["out_ms"]), (0, 1500))

    def test_queue_idempotence_and_range_validation(self):
        p, _ = self.queue(range={"end_ms": 3000, "start_ms": 1000})
        self.editor.enqueue(p, background=False)
        self.assertEqual(len(self.editor.view()["jobs"]), 1)
        for changes in ({"profile": "final"}, {"range": {"start_ms": 0, "end_ms": 4501}}, {"revision": True}):
            bad = {**p, **changes}
            with self.assertRaises(FilmError): self.editor.enqueue(bad, background=False)

    def test_worker_interruption_restarts_in_new_attempt_and_preserves_partial(self):
        p, r = self.queue()
        directory = self.store.root / self.pid / "jobs" / r["job_id"]
        abandoned = directory / ("attempt-" + uuid4().hex); abandoned.mkdir(mode=0o700)
        partial = abandoned / "render.partial.mp4"; partial.write_bytes(b"incomplete")
        atomic_write_json(directory / "status.json", {"state": "rendering", "progress": 30})
        self.assertEqual(self.editor.view()["jobs"][0]["state"], "interrupted")
        with patch("app.camino_film_render.render_edit", side_effect=self.fake_render):
            self.editor.run_queue(self.pid)
        self.assertEqual(partial.read_bytes(), b"incomplete")
        self.assertEqual(self.editor.output(self.pid, r["job_id"]).read_bytes(), b"synthetic mp4 bytes")

    def test_failed_output_never_becomes_deliverable_and_privacy_revokes_ready_output(self):
        _, first = self.queue()
        with patch("app.camino_film_render.render_edit", side_effect=FilmError("unsafe")):
            self.editor.run_queue(self.pid)
        with self.assertRaises(FilmError): self.editor.output(self.pid, first["job_id"])
        _, second = self.queue()
        with patch("app.camino_film_render.render_edit", side_effect=self.fake_render):
            self.editor.run_queue(self.pid)
        self.assertTrue(self.editor.output(self.pid, second["job_id"]).is_file())
        self.f.lock()
        with self.assertRaises(FilmError): self.editor.view()
        with self.assertRaises(FilmError): self.editor.output(self.pid, second["job_id"])

    def test_privacy_change_during_render_stops_publication(self):
        _, job = self.queue()
        def change_privacy(edit, manifest, objects, output, profile, interval, **kwargs):
            (output / "render.partial.mp4").write_bytes(b"partial")
            self.f.lock(); kwargs["revalidate"]()
            self.fail("privacy change must interrupt the renderer")
        with patch("app.camino_film_render.render_edit", side_effect=change_privacy): self.editor.run_queue(self.pid)
        folder = self.store.root / self.pid / "jobs" / job["job_id"]
        self.assertEqual(json.loads((folder / "status.json").read_text())["state"], "failed")
        self.assertFalse(list(folder.glob("*/film.mp4")))

    def test_revision_tampering_during_render_stops_publication(self):
        self.editor.save(self.payload()); _, job = self.queue()
        def tamper(edit, manifest, objects, output, profile, interval, **kwargs):
            path = self.store.root / self.pid / "edit-r000002.json"
            record = json.loads(path.read_text()); record["draft"]["shots"][0]["title"] = "Tampered"
            path.write_text(json.dumps(record)); kwargs["revalidate"]()
            self.fail("changed revision must not publish")
        with patch("app.camino_film_render.render_edit", side_effect=tamper): self.editor.run_queue(self.pid)
        self.assertEqual(self.editor.view()["jobs"][0]["state"], "failed")

    def test_concurrent_workers_serialize_the_queue(self):
        self.queue(); self.queue(); entered = threading.Event(); release = threading.Event()
        active = [0, 0]
        def render(*args, **kwargs):
            active[0] += 1; active[1] = max(active)
            entered.set(); release.wait(timeout=3)
            result = self.fake_render(*args, **kwargs); active[0] -= 1
            return result
        with patch("app.camino_film_render.render_edit", side_effect=render):
            first = threading.Thread(target=self.editor.run_queue, args=(self.pid,)); first.start()
            self.assertTrue(entered.wait(timeout=3))
            second = threading.Thread(target=self.editor.run_queue, args=(self.pid,)); second.start()
            release.set(); first.join(timeout=5); second.join(timeout=5)
            self.assertFalse(first.is_alive() or second.is_alive())
        self.assertEqual(active[1], 1)
        self.assertEqual([j["state"] for j in self.editor.view()["jobs"]], ["ready", "ready"])

    def test_view_and_unknown_output_do_not_create_paths(self):
        folder = self.store.root / self.pid
        with self.assertRaises(FilmError): self.editor.output(self.pid, str(uuid4()))
        self.assertFalse((folder / "jobs").exists())
        self.assertFalse((folder / ".render-worker").exists())

    def source_payload(self):
        sid = next(s["asset_id"] for s in self.editor.view()["sources"] if s["kind"] == "video")
        return {"project_id": self.pid, "asset_id": sid, "request_id": str(uuid4())}

    def test_source_preview_is_whole_cached_and_does_not_change_saved_edits(self):
        p = self.payload(); p["draft"]["shots"][1].update(in_ms=500, out_ms=1000, included=False)
        self.editor.save(p)
        before = self.editor.view()["draft"]
        source = self.source_payload(); first = self.editor.source_preview(source, background=False)
        self.assertEqual(self.editor.source_preview(source, background=False)["job_id"], first["job_id"])
        def render(edit, manifest, *args, **kwargs):
            shots = [s for s in edit["draft"]["shots"] if s["included"]]
            self.assertEqual(len(shots), 1)
            self.assertEqual((shots[0]["in_ms"], shots[0]["out_ms"], shots[0]["title"], shots[0]["gain"]), (0, 1500, "", 1))
            self.assertFalse(any(v["included"] for v in edit["draft"]["voices"]))
            return self.fake_render(edit, manifest, *args, **kwargs)
        with patch("app.camino_film_render.render_edit", side_effect=render): self.editor.run_queue(self.pid)
        again = self.editor.source_preview({**source, "request_id": str(uuid4())}, background=False)
        self.assertEqual(again["job_id"], first["job_id"])
        self.assertEqual(self.editor.view()["revision"], 2)
        self.assertEqual(self.editor.view()["draft"], before)
        job = self.editor.view()["jobs"][0]
        self.assertEqual(job["source_asset_id"], source["asset_id"])
        target = self.editor.output(self.pid, job["job_id"])
        self.assertFalse(target.is_relative_to(self.f.media.objects))
        target.write_bytes(b"corrupt")
        replacement = self.editor.source_preview({**source, "request_id": str(uuid4())}, background=False)
        self.assertNotEqual(replacement["job_id"], first["job_id"])

    def test_source_preview_rejects_foreign_private_nonvideo_and_conflicting_request(self):
        source = self.source_payload()
        for sid in (str(uuid4()), self.f.private.id, self.editor.view()["sources"][0]["asset_id"]):
            with self.assertRaises(FilmError): self.editor.source_preview({**source, "asset_id": sid}, background=False)
        self.editor.source_preview(source, background=False)
        with self.assertRaises(FilmError):
            self.editor.enqueue({"project_id": self.pid, "revision": 1, "request_id": source["request_id"],
                "profile": "preview", "range": None}, background=False)

    def test_source_preview_privacy_change_blocks_publication_and_delivery(self):
        job = self.editor.source_preview(self.source_payload(), background=False)
        def change(*args, **kwargs):
            result = self.fake_render(*args, **kwargs); self.f.lock(); return result
        with patch("app.camino_film_render.render_edit", side_effect=change): self.editor.run_queue(self.pid)
        state = json.loads((self.store.root / self.pid / "jobs" / job["job_id"] / "status.json").read_text())
        self.assertEqual(state["state"], "failed")
        with self.assertRaises(FilmError): self.editor.output(self.pid, job["job_id"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "Local media tools required")
    def test_worker_finds_media_tools_with_service_path_without_changing_parent(self):
        service_path = "/usr/bin:/bin:/usr/sbin:/sbin"
        with patch.dict(os.environ, {"PATH": service_path}), patch("app.camino_film_editor.subprocess.Popen") as launch:
            self.editor.start_worker(self.pid)
            child = launch.call_args.kwargs["env"]
            self.assertEqual(os.environ["PATH"], service_path)
            self.assertEqual(child["PATH"].split(os.pathsep)[:4], service_path.split(os.pathsep))
            for name in ("ffmpeg", "ffprobe"):
                self.assertTrue(shutil.which(name, path=child["PATH"]), f"{name} unavailable in the film worker")
            self.assertTrue(Path(launch.call_args.args[0][0]).is_absolute())

    def test_http_save_origin_and_streaming_range_contract(self):
        _, job = self.queue()
        with patch("app.camino_film_render.render_edit", side_effect=self.fake_render): self.editor.run_queue(self.pid)
        server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        with patch("app.camino_film_editor.production_editor", return_value=self.editor), patch("app.camino_film_workshop.production_store", return_value=self.store), patch.object(cockpit, "production_editor", return_value=self.editor), patch.object(self.editor, "start_worker"):
            thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                def request(method, path, payload=None, headers=None):
                    conn.request(method, path, body=json.dumps(payload) if payload else None,
                        headers={"Content-Type": "application/json", **(headers or {})})
                    r = conn.getresponse(); return r.status, dict(r.getheaders()), r.read()
                code, _, body = request("GET", "/api/camino/film/editor")
                self.assertEqual(code, 200); self.assertNotIn(b"PRIVATE", body)
                original_public = self.f.public
                self.second_day(close=False)
                self.f.public = original_public
                confirmation = {"local_date": self.f.day.local_date, "confirmed_final_mac_data": True}
                self.assertEqual(request("POST", "/api/camino/film/close-mac-day", confirmation, {"Origin": "https://foreign.example"})[0], 403)
                self.assertEqual(self.store.project_ids(), [self.pid])
                code, _, body = request("POST", "/api/camino/film/close-mac-day", confirmation)
                self.assertEqual(code, 200); second = json.loads(body)["project_id"]
                self.assertEqual(json.loads(body)["local_date"], "2026-09-26")
                code, _, body = request("GET", f"/api/camino/film/editor?project_id={second}")
                self.assertEqual(code, 200); self.assertEqual(json.loads(body)["project_id"], second)
                code, _, body = request("GET", "/api/camino/film/catalog")
                self.assertEqual(code, 200); self.assertEqual(len(json.loads(body)["projects"]), 2)
                for suffix in ("?project_id=", "?local_date=2026-09-26", "?project_id=../../secret",
                               f"?project_id={self.pid}&project_id={second}"):
                    self.assertEqual(request("GET", "/api/camino/film/editor" + suffix)[0], 400)
                self.assertEqual(request("GET", "/api/camino/film/catalog?path=secret")[0], 400)
                self.assertEqual(request("POST", "/api/camino/film/save", self.payload(), {"Origin": "https://foreign.example"})[0], 403)
                self.assertEqual(request("POST", "/api/camino/film/save", self.payload())[0], 200)
                self.assertEqual(request("POST", "/api/camino/film/render", {"project_id": self.pid, "revision": 2, "request_id": str(uuid4()), "profile": "preview", "range": None})[0], 200)
                source = self.source_payload()
                self.assertEqual(request("POST", "/api/camino/film/source", source, {"Origin": "https://foreign.example"})[0], 403)
                self.assertEqual(request("POST", "/api/camino/film/source?file=secret", source)[0], 400)
                code, _, body = request("POST", "/api/camino/film/source", source)
                self.assertEqual(code, 200)
                source_id = json.loads(body)["job_id"]
                with patch("app.camino_film_render.render_edit", side_effect=self.fake_render): self.editor.run_queue(self.pid)
                source_url = f'/api/camino/film/output/{self.pid}/{source_id}'
                self.assertEqual(request("GET", source_url, headers={"Range": "bytes=0-3"})[2], b"synt")
                self.assertEqual(request("HEAD", source_url)[0], 200)
                url = f'/api/camino/film/output/{self.pid}/{job["job_id"]}'
                code, headers, body = request("GET", url, headers={"Range": "bytes=0-3"})
                self.assertEqual((code, body), (206, b"synt")); self.assertEqual(headers["Content-Type"], "video/mp4")
                self.assertIn("no-store", headers["Cache-Control"])
                self.assertEqual(request("HEAD", url)[2], b"")
                self.assertEqual(request("GET", url, headers={"Range": "bytes=9999-"})[0], 416)
                self.assertEqual(request("GET", url + "?file=secret")[0], 404)
                self.f.lock(); self.assertEqual(request("GET", url)[0], 404)
                self.assertEqual(request("HEAD", source_url)[0], 404)
                self.assertEqual(request("GET", source_url, headers={"Range": "bytes=0-3"})[0], 404)
                conn.close()
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=3)

    def test_frontend_autosave_privacy_and_stale_export_behavior(self):
        from scripts.cockpit_quality_gate import node_binary
        r = subprocess.run([node_binary(), str(Path(__file__).with_name("camino_film_editor.test.cjs"))],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_cli_history_failure_does_not_poison_a_new_successful_render(self):
        from scripts import camino_film_editor as cli
        editor = Mock(); queued = []
        def enqueue(payload, **kwargs):
            queued.append({"job_id": payload["request_id"], "state": "ready", "profile": payload["profile"]})
            return {"job_id": payload["request_id"]}
        editor.enqueue.side_effect = enqueue
        editor.view.side_effect = lambda: {"ok": True, "project_id": self.pid,
            "local_date": self.f.day.local_date, "revision": 1, "duration_ms": 4500,
            "jobs": [{"job_id": "old", "state": "failed", "profile": "preview"}, *queued]}
        with patch.object(cli, "production_editor", return_value=editor), patch("sys.argv", ["editor", "render", "--execute"]), patch("builtins.print"):
            self.assertEqual(cli.main(), 0)
        self.assertEqual(len(queued), 2)
        editor.view.side_effect = lambda: {"ok": True, "project_id": self.pid,
            "local_date": self.f.day.local_date, "revision": 1, "duration_ms": 4500,
            "jobs": queued[:1]}
        queued.clear()
        with patch.object(cli, "production_editor", return_value=editor), patch("sys.argv", ["editor", "render", "--execute"]), patch("builtins.print"):
            self.assertEqual(cli.main(), 1, "a missing requested output must fail")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe") and FONT.is_file(), "Local FFmpeg and Czech font required")
class RenderTests(unittest.TestCase):
    def test_large_photo_full_frame_survives_both_output_profiles(self):
        import io
        from PIL import Image, ImageDraw, ImageCms
        with tempfile.TemporaryDirectory(dir="/private/tmp") as tmp:
            root = Path(tmp); archive = root / 'archive'; archive.mkdir(mode=0o700)
            f = ViewerFixture(archive)
            with Image.new('RGB', (5918, 3860), 'lime') as photo:
                draw = ImageDraw.Draw(photo)
                draw.rectangle((0, 0, 400, 3859), fill='red')
                draw.rectangle((5518, 0, 5917, 3859), fill='blue')
                buffer = io.BytesIO()
                photo.save(buffer, 'JPEG', icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
            original = buffer.getvalue()
            f.upload(30, 'photo', original)
            store = MacFilmProjectStore(root / 'projects', metadata_db=f.store.path,
                media_db=f.media.database_path, media_root=f.media.root, trip_id=f.trip.id)
            pid = store.close_mac_day(f.day.local_date, confirmed=True)['project_id']
            e = FilmEditor(store, day=f.day.local_date)
            view = e.view()
            view['draft']['shots'][0].update(in_ms=0, out_ms=1000, title='')
            e.save({'project_id': pid, 'expected_revision': 1, 'request_id': str(uuid4()), 'draft': view['draft']})
            for profile, dimensions, photo_size in [('preview', (1280, 720), (1104, 720)),
                                                     ('final', (1920, 1080), (1656, 1080))]:
                request = {'project_id': pid, 'revision': 2, 'request_id': str(uuid4()), 'profile': profile, 'range': None}
                e.enqueue(request, background=False); e.run_queue(pid)
                output = e.output(pid, request['request_id'])
                data = probe(output)
                video = next(s for s in data['streams'] if s['codec_type'] == 'video')
                self.assertEqual((video['width'], video['height']), dimensions)
                self.assertEqual(int(video['nb_frames']), 30)
                receipt = json.loads((output.parent / 'receipt.json').read_text())
                self.assertTrue(receipt['decoded_entire_file'])
                with Image.open(output.parent / 'photo-0000.png') as working:
                    self.assertEqual(working.size, photo_size)
                    self.assertFalse(working.getexif())
                frame = root / (profile + '.png')
                ffmpeg(['-ss', '0.5', '-i', str(output), '-frames:v', '1', '-update', '1', str(frame)])
                left = (dimensions[0] - photo_size[0]) // 2
                with Image.open(frame) as decoded:
                    self.assertLess(max(decoded.getpixel((left // 2, dimensions[1] // 2))[:3]), 15)
                    self.assertGreater(decoded.getpixel((left + 20, dimensions[1] // 2))[0], 200)
                    self.assertGreater(decoded.getpixel((dimensions[0] - left - 20, dimensions[1] // 2))[2], 200)
            self.assertEqual((f.media.objects / (uid(30) + '.bin')).read_bytes(), original)

    def test_video_dimension_and_hdr_guards_are_not_relaxed_for_large_photos(self):
        from app.camino_film_render import render_edit
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); archive = root / 'archive'; archive.mkdir(mode=0o700)
            f = ViewerFixture(archive)
            f.upload(31, 'video', b'synthetic-video-for-preflight')
            store = MacFilmProjectStore(root / 'projects', metadata_db=f.store.path,
                media_db=f.media.database_path, media_root=f.media.root, trip_id=f.trip.id)
            pid = store.close_mac_day(f.day.local_date, confirmed=True)['project_id']
            e = FilmEditor(store, day=f.day.local_date)
            folder, manifest = e.inputs(pid); edit = e.revision(folder, manifest)
            for track in [{'codec_type': 'video', 'width': 4098, 'height': 100},
                          {'codec_type': 'video', 'width': 1920, 'height': 1080, 'color_transfer': 'smpte2084'}]:
                with self.subTest(track=track), patch('app.camino_film_render.probe', return_value={'streams': [track]}):
                    with self.assertRaisesRegex(FilmError, 'SDR'):
                        render_edit(edit, manifest, f.media.objects, root, 'preview', None,
                                    progress=lambda _: None, revalidate=lambda: None)

    def test_full_source_preview_and_saved_trim_show_the_same_selected_frames(self):
        from PIL import Image
        with tempfile.TemporaryDirectory(dir="/private/tmp") as tmp:
            root = Path(tmp); archive = root / "archive"; archive.mkdir(mode=0o700)
            f = ViewerFixture(archive); video = root / "source.mp4"
            ffmpeg(["-f", "lavfi", "-i", "color=red:s=60x90:r=30:d=0.5",
                "-f", "lavfi", "-i", "color=lime:s=60x90:r=30:d=0.5",
                "-f", "lavfi", "-i", "color=blue:s=60x90:r=30:d=0.5",
                "-f", "lavfi", "-i", "sine=frequency=880:duration=1.5",
                "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-map", "3:a",
                "-metadata", "location=PRIVATE-LOCATION", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(video)])
            f.upload(31, "video", video.read_bytes())
            store = MacFilmProjectStore(root / "projects", metadata_db=f.store.path, media_db=f.media.database_path,
                media_root=f.media.root, trip_id=f.trip.id)
            pid = store.close_mac_day(f.day.local_date, confirmed=True)["project_id"]
            e = FilmEditor(store, day=f.day.local_date); v = e.view(); sid = v["sources"][0]["asset_id"]
            original = f.media.objects / (sid + ".bin"); before = digest(original)
            source = e.source_preview({"project_id": pid, "asset_id": sid, "request_id": str(uuid4())}, background=False)
            e.run_queue(pid); full = e.output(pid, source["job_id"])
            data = probe(full)
            self.assertNotIn("PRIVATE-LOCATION", json.dumps(data))
            self.assertEqual(next(s for s in data["streams"] if s["codec_type"] == "video")["nb_frames"], "45")
            v["draft"]["shots"][0].update(in_ms=500, out_ms=1000, title="")
            e.save({"project_id": pid, "expected_revision": 1, "request_id": str(uuid4()), "draft": v["draft"]})
            render_id = str(uuid4())
            e.enqueue({"project_id": pid, "revision": 2, "request_id": render_id, "profile": "preview", "range": None}, background=False)
            e.run_queue(pid); trimmed = e.output(pid, render_id)
            receipt = json.loads((trimmed.parent / "receipt.json").read_text())
            self.assertEqual(receipt["timeline_ms"], 500)
            for index, (path, seconds, channel) in enumerate(((full, .2, 0), (full, .7, 1), (full, 1.3, 2), (trimmed, .2, 1))):
                frame = root / f"frame-{index}.png"
                ffmpeg(["-ss", str(seconds), "-i", str(path), "-frames:v", "1", "-update", "1", str(frame)])
                with Image.open(frame) as image:
                    self.assertGreater(image.getpixel((640, 200))[channel], 200)
                    self.assertLess(max(image.getpixel((320, 200))[:3]), 15)
            self.assertEqual(e.source_preview({"project_id": pid, "asset_id": sid, "request_id": str(uuid4())}, background=False)["job_id"], source["job_id"])
            self.assertEqual(digest(original), before)
            # Exercise cleanup over the actual renderer's hardlinked MP4 pair,
            # rather than a simplified fake renderer with only one output name.
            self.assertTrue(os.path.samefile(trimmed, trimmed.parent / "render.partial.mp4"))
            selected = {"project_id": pid, "job_id": render_id}
            plan = deletion_plan(e, selected)
            delete_export(e, {**selected, "plan_token": plan["plan_token"], "confirmation": DELETE_CONFIRMATION})
            self.assertFalse(trimmed.exists())
            self.assertFalse(trimmed.parent.exists())
            self.assertEqual([j["job_id"] for j in e.view()["jobs"]], [source["job_id"]])
            self.assertTrue(e.output(pid, source["job_id"]).is_file())
            self.assertEqual(digest(original), before)

    def test_mpo_main_photo_preserves_full_duration_and_exif_orientation(self):
        from PIL import Image, ImageCms
        with tempfile.TemporaryDirectory(dir="/private/tmp") as tmp:
            root = Path(tmp); archive = root / "archive"; archive.mkdir(mode=0o700)
            f = ViewerFixture(archive)
            main = Image.new("RGB", (90, 60), "blue"); auxiliary = Image.new("RGB", (45, 30), "red")
            exif = Image.Exif(); exif[274] = 6; exif[315] = "PRIVATE-EXIF"
            original = root / "photo.mpo"
            main.save(original, "MPO", save_all=True, append_images=[auxiliary], exif=exif,
                      icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
            before = digest(original)
            with Image.open(original) as image: self.assertEqual(image.n_frames, 2)
            f.upload(30, "photo", original.read_bytes())
            store = MacFilmProjectStore(root / "projects", metadata_db=f.store.path, media_db=f.media.database_path,
                media_root=f.media.root, trip_id=f.trip.id)
            pid = store.close_mac_day(f.day.local_date, confirmed=True)["project_id"]
            e = FilmEditor(store, day=f.day.local_date)
            request = {"project_id": pid, "revision": 1, "request_id": str(uuid4()), "profile": "preview", "range": None}
            e.enqueue(request, background=False); e.run_queue(pid)
            self.assertEqual(e.view()["jobs"][0]["state"], "ready")
            target = e.output(pid, request["request_id"]); data = probe(target)
            video = next(s for s in data["streams"] if s["codec_type"] == "video")
            self.assertEqual(int(video["nb_frames"]), 90)
            with Image.open(target.parent / "photo-0000.png") as image:
                self.assertEqual(image.size, (60, 90)); self.assertNotIn("exif", image.info)
            frame = root / "last.png"
            ffmpeg(["-ss", "2.9", "-i", str(target), "-frames:v", "1", "-update", "1", str(frame)])
            with Image.open(frame) as image:
                self.assertGreater(image.getpixel((640, 200))[2], 200)
                self.assertLess(max(image.getpixel((320, 200))[:3]), 15)
            self.assertEqual(digest(original), before)

    def test_many_fractional_frame_joins_keep_audio_timestamps_monotonic(self):
        from PIL import Image
        with tempfile.TemporaryDirectory(dir="/private/tmp") as tmp:
            root = Path(tmp); archive = root / "archive"; archive.mkdir(mode=0o700)
            f = ViewerFixture(archive)
            photo = root / "photo.jpg"; Image.new("RGB", (60, 90), "blue").save(photo)
            for tag in range(30, 50): f.upload(tag, "photo", photo.read_bytes())
            store = MacFilmProjectStore(root / "projects", metadata_db=f.store.path, media_db=f.media.database_path,
                media_root=f.media.root, trip_id=f.trip.id)
            pid = store.close_mac_day(f.day.local_date, confirmed=True)["project_id"]
            e = FilmEditor(store, day=f.day.local_date); v = e.view()
            for i, shot in enumerate(v["draft"]["shots"]): shot["out_ms"] = 230 + i * 5
            e.save({"project_id": pid, "expected_revision": 1, "request_id": str(uuid4()), "draft": v["draft"]})
            request = {"project_id": pid, "revision": 2, "request_id": str(uuid4()), "profile": "preview", "range": None}
            e.enqueue(request, background=False); e.run_queue(pid)
            self.assertEqual(e.view()["jobs"][0]["state"], "ready")
            target = e.output(pid, request["request_id"])
            receipt = json.loads((target.parent / "receipt.json").read_text())
            self.assertLess(abs(receipt["video_ms"] - receipt["audio_ms"]), 100)
            self.assertTrue(receipt["decoded_entire_file"])

    def test_real_preview_and_final_share_timeline_and_manual_voice(self):
        from PIL import Image
        with tempfile.TemporaryDirectory(dir="/private/tmp") as tmp:
            root = Path(tmp); archive = root / "archive"; archive.mkdir(mode=0o700)
            f = ViewerFixture(archive)
            photo = root / "photo.jpg"; Image.new("RGB", (60, 90), "blue").save(photo)
            raw = root / "video-raw.mp4"; video = root / "video.mp4"
            ffmpeg(["-f", "lavfi", "-i", "color=red:s=90x60:r=30:d=1.5", "-f", "lavfi", "-i", "sine=frequency=880:duration=1.5",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(raw)])
            ffmpeg(["-display_rotation:v:0", "90", "-i", str(raw), "-c", "copy", str(video)])
            voice = root / "voice.wav"
            ffmpeg(["-f", "lavfi", "-i", "sine=frequency=660:duration=1.5", str(voice)])
            f.upload(30, "photo", photo.read_bytes()); f.upload(31, "video", video.read_bytes()); f.upload(32, "audio", voice.read_bytes())
            store = MacFilmProjectStore(root / "projects", metadata_db=f.store.path, media_db=f.media.database_path,
                media_root=f.media.root, trip_id=f.trip.id)
            pid = store.close_mac_day(f.day.local_date, confirmed=True)["project_id"]
            e = FilmEditor(store, day=f.day.local_date); v = e.view()
            draft = copy.deepcopy(v["draft"])
            draft["voices"][0].update(included=True, at_ms=2000)
            e.save({"project_id": pid, "expected_revision": 1, "request_id": str(uuid4()), "draft": draft})
            for profile in ("preview", "final"):
                e.enqueue({"project_id": pid, "revision": 2, "request_id": str(uuid4()), "profile": profile, "range": None}, background=False)
            e.run_queue(pid)
            jobs = e.view()["jobs"]
            self.assertEqual([j["state"] for j in jobs], ["ready", "ready"])
            for job, dimensions in zip(jobs, [(1280, 720), (1920, 1080)]):
                target = e.output(pid, job["job_id"]); info = probe(target)
                track = next(s for s in info["streams"] if s["codec_type"] == "video")
                self.assertEqual((track["width"], track["height"]), dimensions)
                receipt = json.loads((target.parent / "receipt.json").read_text())
                self.assertEqual((receipt["revision"], receipt["timeline_ms"], receipt["voices_selected"]), (2, 4500, 1))
                self.assertTrue(receipt["decoded_entire_file"])
                frame = root / (job["profile"] + ".png")
                ffmpeg(["-ss", "3.8", "-i", str(target), "-frames:v", "1", "-update", "1", str(frame)])
                with Image.open(frame) as image:
                    self.assertGreater(image.getpixel((dimensions[0] // 2, 200))[0], 200)
                    self.assertLess(max(image.getpixel((dimensions[0] // 4, 200))[:3]), 15)
                pcm = run([binary("ffmpeg"), "-v", "error", "-ss", "3.1", "-i", str(target),
                           "-t", "0.2", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"]).stdout
                samples = array.array("f"); samples.frombytes(pcm)
                def amplitude(hz):
                    return abs(sum(v * complex(math.cos(2*math.pi*hz*i/48000), math.sin(2*math.pi*hz*i/48000)) for i, v in enumerate(samples)))
                self.assertGreater(amplitude(660), 3 * amplitude(880), "voice must remain clear while video sound is ducked")
            partial = {"project_id": pid, "revision": 2, "request_id": str(uuid4()), "profile": "preview", "range": {"start_ms": 2500, "end_ms": 3500}}
            e.enqueue(partial, background=False); e.run_queue(pid)
            target = e.output(pid, partial["request_id"])
            self.assertEqual(json.loads((target.parent / "receipt.json").read_text())["timeline_ms"], 1000)
