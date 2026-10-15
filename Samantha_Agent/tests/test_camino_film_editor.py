"""Synthetic tests of edit persistence, consent routes, private output and real rendering."""
import copy
import array
import http.client
import json
import math
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch, Mock
from uuid import uuid4

from app import cockpit
from app.camino_film_editor import FilmEditor, validate_draft
from app.camino_film_workshop import MacFilmProjectStore
from app.file_persistence import atomic_write_json
from camino.film.media import ffmpeg, probe, binary, run, FONT
from camino.film.project import FilmError, digest
from tests.camino_viewer_fixture import ViewerFixture


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

    def queue(self, **changes):
        payload = {"project_id": self.pid, "revision": self.editor.view()["revision"],
                   "request_id": str(uuid4()), "profile": "preview", "range": None, **changes}
        return payload, self.editor.enqueue(payload, background=False)

    @staticmethod
    def fake_render(edit, manifest, objects, output, profile, interval, **kwargs):
        kwargs["revalidate"]()
        path = output / "film.mp4"; path.write_bytes(b"synthetic mp4 bytes")
        return {"bytes": path.stat().st_size, "sha256": digest(path)}

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

    def test_http_save_origin_and_streaming_range_contract(self):
        _, job = self.queue()
        with patch("app.camino_film_render.render_edit", side_effect=self.fake_render): self.editor.run_queue(self.pid)
        server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        with patch("app.camino_film_editor.production_editor", return_value=self.editor), patch.object(cockpit, "production_editor", return_value=self.editor), patch.object(self.editor, "start_worker"):
            thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                def request(method, path, payload=None, headers=None):
                    conn.request(method, path, body=json.dumps(payload) if payload else None,
                        headers={"Content-Type": "application/json", **(headers or {})})
                    r = conn.getresponse(); return r.status, dict(r.getheaders()), r.read()
                code, _, body = request("GET", "/api/camino/film/editor")
                self.assertEqual(code, 200); self.assertNotIn(b"PRIVATE", body)
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
