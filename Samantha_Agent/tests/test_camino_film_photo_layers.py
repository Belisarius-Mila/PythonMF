"""Photo text/voice regressions: synthetic data only, including real media output."""
import copy
import hashlib
import http.client
import io
import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from PIL import Image
from app import cockpit
from app.camino_film_editor import FilmEditor, validate_draft, resolved_voices
from app.camino_film_layers import layout, reading_ms
from app.camino_film_narration import prepare_narration, narration_bytes, synthesize
from app.camino_film_render import render_edit, window
from app.camino_film_workshop import MacFilmProjectStore
from camino.film.project import FilmError, digest
from camino.film.media import probe, duration_ms, binary
from tests.camino_viewer_fixture import ViewerFixture, uid
from scripts.cockpit_quality_gate import node_binary

LONG_TEXT = ("Syntetický popis památky a okolní krajiny. " * 80)[:3022]


class PhotoLayerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(dir="/private/tmp"); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        archive = self.root / "archive"; archive.mkdir(mode=0o700)
        self.f = ViewerFixture(archive)
        image = Image.new("RGB", (320, 200), (70, 115, 80)); data = io.BytesIO(); image.save(data, "PNG")
        self.f.upload(30, "photo", data.getvalue())
        self.f.upload(31, "photo", data.getvalue())
        self.f.upload(32, "audio", b"synthetic audio")
        self.f.upload(33, "photo", data.getvalue(), private=True)
        self.store = MacFilmProjectStore(self.root / "projects", metadata_db=self.f.store.path,
            media_db=self.f.media.database_path, media_root=self.f.media.root, trip_id=self.f.trip.id)
        self.pid = self.store.close_mac_day(self.f.day.local_date, confirmed=True)["project_id"]
        self.editor = FilmEditor(self.store, day=self.f.day.local_date)

    def payload(self):
        view = self.editor.view()
        return {"project_id": self.pid, "expected_revision": view["revision"], "request_id": str(uuid4()),
                "draft": copy.deepcopy(view["draft"])}

    def save_text(self, text=LONG_TEXT, mode="none", duration=25000):
        p = self.payload(); row = p["draft"]["shots"][0]
        row["out_ms"] = duration
        row["photo_text"] = {"text": text, "mode": mode, "text_source": None, "narration": None}
        self.editor.save(p)
        return p

    def narration_payload(self):
        return {"project_id": self.pid, "revision": self.editor.view()["revision"],
                "asset_id": uid(30), "request_id": str(uuid4())}

    @staticmethod
    def fake_speech(text, directory):
        (directory / "speech.m4a").write_bytes(b"synthetic audio derivative")
        return 42000

    def prepare(self):
        request = self.narration_payload()
        with patch("app.camino_film_narration.synthesize", side_effect=self.fake_speech) as speech:
            result = prepare_narration(self.editor, request)
            self.assertEqual(speech.call_args.args[0], LONG_TEXT)
        return request, result

    def attach(self, result, *, included=False, duration=25000):
        p = self.payload(); row = p["draft"]["shots"][0]
        row["photo_text"]["narration"] = {**result["narration"], "included": included}
        row["photo_text"]["mode"] = "narration"; row["out_ms"] = duration
        self.editor.save(p)
        return p

    def test_long_text_25_second_photo_survives_reload_and_originals_are_unchanged(self):
        before = {p: digest(p) for p in self.f.media.objects.iterdir() if p.is_file()}
        p = self.save_text()
        restored = FilmEditor(self.store).view(self.pid)
        self.assertEqual(restored["draft"], p["draft"])
        self.assertEqual(len(restored["draft"]["shots"][0]["photo_text"]["text"]), 3022)
        self.assertEqual(before, {p: digest(p) for p in before})
        self.assertEqual(restored["draft"]["shots"][0]["out_ms"], 25000)

    def test_static_and_scroll_require_explicit_readable_layout_without_losing_text(self):
        self.save_text(mode="static")
        folder, manifest = self.editor.inputs(self.pid)
        draft = self.editor.view()["draft"]
        with self.assertRaisesRegex(FilmError, "Statický text"):
            validate_draft(draft, manifest, for_render=True)
        draft["shots"][0]["photo_text"]["mode"] = "scroll"
        with self.assertRaisesRegex(FilmError, "delší zobrazení"):
            validate_draft(draft, manifest, for_render=True)
        draft["shots"][0]["out_ms"] = reading_ms(LONG_TEXT)
        validate_draft(draft, manifest, for_render=True)
        _, lines, _ = layout(LONG_TEXT, (1280, 720))
        self.assertEqual("".join("".join(lines).split()), "".join(LONG_TEXT.split()))
        self.assertEqual(self.editor.view()["draft"]["shots"][0]["out_ms"], 25000)

    def test_narration_is_complete_idempotent_and_listening_does_not_include_it(self):
        self.save_text(); request, result = self.prepare()
        with patch("app.camino_film_narration.synthesize") as speech:
            self.assertEqual(prepare_narration(self.editor, request), result); speech.assert_not_called()
        self.assertEqual(narration_bytes(self.editor, self.pid, request["request_id"]), b"synthetic audio derivative")
        self.attach(result)
        self.assertEqual(narration_bytes(self.editor, self.pid, request["request_id"]), b"synthetic audio derivative")
        self.assertFalse(any(v.get("narration_id") for v in resolved_voices(self.editor.view()["draft"])))
        with self.assertRaisesRegex(FilmError, "přesahuje"):
            self.attach(result, included=True)
        self.attach(result, included=True, duration=42000)
        self.assertEqual(resolved_voices(self.editor.view()["draft"])[-1]["out_ms"], 42000)

    def test_changed_text_or_private_photo_blocks_old_audio(self):
        self.save_text(); request, result = self.prepare(); self.attach(result)
        p = self.payload(); p["draft"]["shots"][0]["photo_text"]["text"] += " Změna."
        with self.assertRaisesRegex(FilmError, "jiné verzi textu"):
            self.editor.save(p)
        self.f.lock()
        with self.assertRaises(FilmError): narration_bytes(self.editor, self.pid, request["request_id"])

    def test_symlink_and_corrupt_audio_are_never_served_or_used(self):
        self.save_text(); request, result = self.prepare(); self.attach(result)
        directory = self.store.root / self.pid / "narrations" / request["request_id"]
        (directory / "speech.m4a").write_bytes(b"damaged")
        with self.assertRaises(FilmError): narration_bytes(self.editor, self.pid, request["request_id"])
        # Keep original files: move the derivative and use a symlink only inside this synthetic fixture.
        (directory / "speech.m4a").rename(directory / "saved.m4a")
        (directory / "speech.m4a").symlink_to(directory / "saved.m4a")
        with self.assertRaises(FilmError): narration_bytes(self.editor, self.pid, request["request_id"])

    def test_privacy_or_text_change_during_generation_does_not_publish_receipt(self):
        self.save_text(); request = self.narration_payload()
        def changed(text, directory):
            result = self.fake_speech(text, directory); self.f.lock(); return result
        with patch("app.camino_film_narration.synthesize", side_effect=changed):
            with self.assertRaises(FilmError): prepare_narration(self.editor, request)
        self.assertFalse((self.store.root / self.pid / "narrations" / request["request_id"] / "receipt.json").exists())

    def test_photo_anchor_moves_voice_with_cards_and_reorder_and_checks_overlap(self):
        p = self.save_text(text="Krátký text.")
        p = self.payload(); photo, second = p["draft"]["shots"]
        voice = p["draft"]["voices"][0]
        voice.update(included=True, in_ms=0, out_ms=1000, photo_asset_id=photo["asset_id"])
        p["draft"]["shots"] = [second, photo]
        second["out_ms"] = 7000
        self.editor.save(p)
        draft = self.editor.view()["draft"]
        self.assertEqual(resolved_voices(draft)[0]["at_ms"], 7000)
        draft["shots"][0]["out_ms"] = 9000
        self.assertEqual(resolved_voices(draft)[0]["at_ms"], 9000)
        _, voices, _ = window(draft, 34000, {"start_ms": 9500, "end_ms": 11000})
        self.assertEqual((voices[0]["at_ms"], voices[0]["in_ms"]), (0, 500))
        draft["shots"][1]["included"] = False
        with self.assertRaisesRegex(FilmError, "vyřazená"): validate_draft(draft, self.editor.inputs(self.pid)[1])

    def test_foreign_narration_request_and_bad_layer_structure_are_rejected(self):
        self.save_text()
        request = self.narration_payload()
        for sid in (uid(33), str(uuid4())):
            with self.assertRaises(FilmError): prepare_narration(self.editor, {**request, "asset_id": sid})
        p = self.payload(); p["draft"]["shots"][0]["photo_text"]["text"] = "x" * 6001
        with self.assertRaises(FilmError): self.editor.save(p)
        p = self.payload(); p["draft"]["voices"][0]["photo_asset_id"] = uid(33)
        with self.assertRaises(FilmError): self.editor.save(p)

    def test_say_receives_full_text_on_stdin_without_secret_argv_or_truncation(self):
        directory = self.root / "mock-speech"; directory.mkdir()
        def run(args, **kwargs):
            self.assertNotIn(LONG_TEXT, args)
            self.assertEqual(kwargs["input"].decode(), LONG_TEXT)
            return subprocess.CompletedProcess(args, 0)
        def media(args, **kwargs):
            if args[-1].endswith("speech.m4a"): Path(args[-1]).write_bytes(b"mock m4a")
        with patch("app.camino_film_narration.subprocess.run", side_effect=run), \
             patch("app.camino_film_render.ffmpeg", side_effect=media), \
             patch("app.camino_film_narration.probe", return_value={"streams": [{"codec_type": "audio"}]}), \
             patch("app.camino_film_narration.duration_ms", return_value=150000):
            self.assertEqual(synthesize(LONG_TEXT, directory), 150000)

    def test_http_narration_origin_get_head_range_and_privacy(self):
        self.save_text(); request, result = self.prepare(); self.attach(result)
        server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(thread.join, 3); self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        def call(method, path, payload=None, headers=None):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            conn.request(method, path, body=json.dumps(payload) if payload else None,
                headers={"Content-Type": "application/json", **(headers or {})})
            response = conn.getresponse(); data = response.read(); status = response.status; hdr = dict(response.getheaders()); conn.close()
            return status, hdr, data
        url = result["url"]
        with patch.object(cockpit, "production_editor", return_value=self.editor), \
             patch("app.camino_film_editor.production_editor", return_value=self.editor):
            self.assertEqual(call("GET", url)[2], b"synthetic audio derivative")
            self.assertEqual(call("HEAD", url)[2], b"")
            status, headers, data = call("GET", url, headers={"Range": "bytes=0-3"})
            self.assertEqual((status, data), (206, b"synt")); self.assertIn("private", headers["Cache-Control"])
            self.assertEqual(headers["Content-Type"], "audio/mp4")
            self.assertEqual(call("GET", url, headers={"Range": "bytes=9999-"})[0], 416)
            self.assertEqual(call("GET", url + "?x=1")[0], 404)
            self.assertEqual(call("POST", "/api/camino/film/narration", request, {"Origin": "https://foreign.invalid"})[0], 403)
            self.assertEqual(call("POST", "/api/camino/film/narration?x=1", request)[0], 400)
            fresh = self.narration_payload()
            with patch("app.camino_film_narration.synthesize", side_effect=self.fake_speech):
                self.assertEqual(call("POST", "/api/camino/film/narration", fresh)[0], 200)
            self.f.lock()
            self.assertEqual(call("GET", url)[0], 404); self.assertEqual(call("HEAD", url)[0], 404)

    def test_photo_interactions_include_real_text_panel_and_async_races(self):
        with patch.dict("os.environ", {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}):
            result = subprocess.run([node_binary(), "tests/camino_film_photo_layers.test.cjs"],
                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "Local media tools required")
    def test_actual_static_and_scroll_exports_in_both_profiles_and_mid_photo_window(self):
        self.save_text(text="Syntetický text přes fotografii.", mode="static", duration=5000)
        folder, manifest = self.editor.inputs(self.pid)
        edit = self.editor.revision(folder, manifest)
        edit["draft"]["shots"][1]["included"] = False
        for mode, text in (("static", "Syntetický text přes fotografii."), ("scroll", LONG_TEXT)):
            shot = edit["draft"]["shots"][0]; shot["photo_text"].update(mode=mode, text=text)
            shot["out_ms"] = reading_ms(text)
            for profile in ("preview", "final"):
                out = self.root / (mode + profile); out.mkdir(mode=0o700)
                start = shot["out_ms"] // 2
                receipt = render_edit(edit, manifest, self.store.media.objects, out, profile,
                    {"start_ms": start, "end_ms": start + 1000}, progress=lambda n: None, revalidate=lambda: None)
                self.assertTrue(receipt["decoded_entire_file"])
                self.assertEqual(receipt["timeline_ms"], 1000)
                self.assertEqual(receipt["width"], 1280 if profile == "preview" else 1920)
                self.assertEqual(receipt["audio_ms"], 1000)

    @unittest.skipUnless(Path("/usr/bin/say").exists() and shutil.which("ffmpeg"), "Mac local voice required")
    def test_actual_long_local_narration_and_mixed_photo_export(self):
        self.save_text(); request = self.narration_payload()
        with patch.dict("os.environ", {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}):
            result = prepare_narration(self.editor, request)
        self.assertGreater(result["narration"]["duration_ms"], 25000)
        self.assertLessEqual(result["narration"]["duration_ms"], 300000)
        self.attach(result, included=True, duration=result["narration"]["duration_ms"])
        folder, manifest = self.editor.inputs(self.pid); edit = self.editor.revision(folder, manifest)
        paths = self.editor.verify_texts(manifest, edit["draft"], project_id=self.pid)
        audio = paths[request["request_id"]]
        self.assertEqual(duration_ms(probe(audio), "audio"), result["narration"]["duration_ms"])
        out = self.root / "spoken-preview"; out.mkdir(mode=0o700)
        receipt = render_edit(edit, manifest, self.store.media.objects, out, "preview", {"start_ms": 0, "end_ms": 1000},
            progress=lambda n: None, revalidate=lambda: None, narration_paths=paths)
        self.assertEqual(receipt["voices_selected"], 1); self.assertTrue(receipt["decoded_entire_file"])
        # Decode the mix to PCM: a non-silent signal proves the derived voice reached the exported film.
        pcm = subprocess.run([binary("ffmpeg"), "-v", "error", "-i", str(out / "film.mp4"),
            "-map", "0:a:0", "-f", "s16le", "-"], capture_output=True, check=True).stdout
        self.assertGreater(len(set(pcm)), 20)

    def trash(self, nid, deleted=True, **changes):
        from app.camino_film_narration import trash_narration
        payload = {"project_id": self.pid, "asset_id": uid(30), "narration_id": nid,
            "revision": self.editor.view()["revision"], "deleted": deleted, **changes}
        return trash_narration(self.editor, payload)

    def test_iphone_original_is_immutable_while_working_script_is_editable_and_legacy_is_preserved(self):
        p = self.payload(); source = self.editor.view()["texts"][0]
        p["draft"]["shots"][0]["photo_text"] = {"text": "Upravená verze pro přednes.",
            "original_text": source["text"], "text_source": source["reference"], "mode": "none", "narration": None}
        self.editor.save(p)
        p = self.payload(); p["draft"]["shots"][0]["photo_text"]["text"] = "Další ruční úprava."
        self.editor.save(p)
        self.assertEqual(self.editor.view()["draft"]["shots"][0]["photo_text"]["original_text"], source["text"])
        p = self.payload(); p["draft"]["shots"][0]["photo_text"]["original_text"] = "Pokus přepsat originál."
        with self.assertRaisesRegex(FilmError, "Původní text"): self.editor.save(p)
        # Older edits gain a read-only projection; their saved bytes remain unchanged.
        p = self.payload(); del p["draft"]["shots"][0]["photo_text"]["original_text"]
        number = self.editor.save(p)["revision"]
        path = self.store.root / self.pid / f"edit-r{number:06d}.json"; before = digest(path)
        self.assertEqual(self.editor.view()["draft"]["shots"][0]["photo_text"]["original_text"], source["text"])
        self.assertEqual(digest(path), before)

    def test_previous_takes_survive_edit_reload_trash_and_restore_without_media_deletion(self):
        self.save_text(); first_request, first = self.prepare(); self.attach(first)
        p = self.payload(); layer = p["draft"]["shots"][0]["photo_text"]
        layer.update(text="Druhá pracovní verze.", mode="none", narration=None); self.editor.save(p)
        second_request = self.narration_payload()
        with patch("app.camino_film_narration.synthesize", side_effect=self.fake_speech):
            second = prepare_narration(self.editor, second_request)
        takes = FilmEditor(self.store).view(self.pid)["narrations"]
        self.assertEqual({t["text"] for t in takes}, {LONG_TEXT, "Druhá pracovní verze."})
        media_before = {p: digest(p) for p in self.f.media.objects.iterdir() if p.is_file()}
        audio = self.store.root / self.pid / "narrations" / first_request["request_id"] / "speech.m4a"
        original_hash = digest(audio)
        self.trash(first_request["request_id"])
        with self.assertRaisesRegex(FilmError, "koši"): narration_bytes(self.editor, self.pid, first_request["request_id"])
        self.assertEqual(digest(audio), original_hash)
        self.assertEqual(self.editor.view()["draft"]["shots"][0]["photo_text"]["text"], "Druhá pracovní verze.")
        self.assertTrue(next(t for t in self.editor.view()["narrations"] if t["id"] == first_request["request_id"])["deleted"])
        self.trash(first_request["request_id"], False)
        self.assertEqual(narration_bytes(self.editor, self.pid, first_request["request_id"]), b"synthetic audio derivative")
        self.assertEqual(media_before, {p: digest(p) for p in media_before})

    def test_trash_rejects_current_attachment_foreign_photo_and_stale_revision(self):
        self.save_text(); request, result = self.prepare(); self.attach(result)
        with self.assertRaisesRegex(FilmError, "odpoj"): self.trash(request["request_id"])
        with self.assertRaisesRegex(FilmError, "jiné fotografii"): self.trash(request["request_id"], asset_id=uid(31))
        with self.assertRaisesRegex(FilmError, "Jiné okno"): self.trash(request["request_id"], revision=1)
        with self.assertRaises(FilmError): self.trash(request["request_id"], revision=True)
        p = self.payload(); p["draft"]["shots"][0]["photo_text"].update(narration=None, mode="none"); self.editor.save(p)
        self.trash(request["request_id"])
        with self.assertRaisesRegex(FilmError, "koši"):
            self.attach(result)

    def test_trash_preserves_already_rendered_film_and_its_frozen_derivative(self):
        self.save_text(); request, result = self.prepare(); self.attach(result, included=True, duration=42000)
        job = self.editor.enqueue({"project_id": self.pid, "revision": self.editor.view()["revision"],
            "request_id": str(uuid4()), "profile": "preview", "range": None}, background=False)
        def fake_render(edit, manifest, objects, out, *args, **kwargs):
            kwargs["revalidate"]()
            self.assertIn(request["request_id"], kwargs["narration_paths"])
            path = out / "film.mp4"; path.write_bytes(b"synthetic completed movie")
            return {"bytes": path.stat().st_size, "sha256": digest(path)}
        with patch("app.camino_film_render.render_edit", side_effect=fake_render): self.editor.run_queue(self.pid)
        original = self.editor.output(self.pid, job["job_id"]); before = digest(original)
        p = self.payload(); p["draft"]["shots"][0]["photo_text"].update(narration=None, mode="none"); self.editor.save(p)
        self.trash(request["request_id"])
        self.assertEqual(digest(self.editor.output(self.pid, job["job_id"])), before)
        self.assertEqual(original.read_bytes(), b"synthetic completed movie")

    @staticmethod
    def wav_bytes():
        import wave
        import math
        import struct
        data = io.BytesIO()
        with wave.open(data, "wb") as handle:
            handle.setnchannels(1); handle.setsampwidth(2); handle.setframerate(16000)
            handle.writeframes(b"".join(struct.pack("<h", round(8000 * math.sin(i * 440 * 2 * math.pi / 16000))) for i in range(16000)))
        return data.getvalue()

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "Local media tools required")
    def test_actual_wav_import_is_private_idempotent_and_can_be_used_without_text(self):
        from app.camino_film_narration import import_narration
        self.save_text(text="")
        payload = self.narration_payload(); body = self.wav_bytes()
        with patch.dict("os.environ", {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}):
            result = import_narration(self.editor, payload, body)
            self.assertEqual(import_narration(self.editor, payload, body), result)
        self.assertTrue(900 <= result["narration"]["duration_ms"] <= 1100)
        self.attach(result, included=True)
        view = self.editor.view(); self.assertIsNone(view["narrations"][0]["synthetic"])
        audio = narration_bytes(self.editor, self.pid, payload["request_id"])
        self.assertNotEqual(audio, body)
        self.assertFalse(view["narrations"][0]["deleted"])
        folder, manifest = self.editor.inputs(self.pid)
        validate_draft(view["draft"], manifest, for_render=True)
        with self.assertRaisesRegex(FilmError, "jinému"):
            import_narration(self.editor, {**payload, "revision": view["revision"]}, body + b"different")

    def test_import_rejects_playlists_and_unknown_bytes_without_creating_an_attempt(self):
        from app.camino_film_narration import import_narration
        self.save_text(); payload = self.narration_payload()
        for data in (b"", b"#EXTM3U\nfile:///private/secret.wav", b"not audio"):
            with self.assertRaises(FilmError): import_narration(self.editor, payload, data)
        self.assertFalse((self.store.root / self.pid / "narrations").exists())

    def test_history_rechecks_text_origin_and_photo_privacy(self):
        self.save_text(); request, result = self.prepare()
        self.assertEqual(len(self.editor.view()["narrations"]), 1)
        self.f.lock()
        with self.assertRaises(FilmError): self.editor.view()
        with self.assertRaises(FilmError): self.trash(request["request_id"])
        with self.assertRaises(FilmError): narration_bytes(self.editor, self.pid, request["request_id"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "Local media tools required")
    def test_http_audio_import_trash_restore_and_origin_checks(self):
        self.save_text()
        request = self.narration_payload()
        server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(thread.join, 3); self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        def call(path, data, headers):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=20)
            conn.request("POST", path, body=data, headers=headers)
            response = conn.getresponse(); value = response.read(); code = response.status; conn.close()
            return code, json.loads(value)
        headers = {"Content-Type": "application/octet-stream", "X-Camino-Project-Id": self.pid,
            "X-Camino-Asset-Id": uid(30), "X-Camino-Revision": str(request["revision"]), "X-Camino-Request-Id": request["request_id"]}
        with patch.object(cockpit, "production_editor", return_value=self.editor), patch("app.camino_film_editor.production_editor", return_value=self.editor):
            self.assertEqual(call("/api/camino/film/narration-import", b"test", {**headers, "Origin": "https://foreign.invalid"})[0], 403)
            self.assertEqual(call("/api/camino/film/narration-import?x=1", b"test", headers)[0], 409)
            self.assertEqual(call("/api/camino/film/narration-import", b"", {**headers, "Content-Length": str(64 * 1024**2 + 1)})[0], 409)
            code, result = call("/api/camino/film/narration-import", self.wav_bytes(), headers)
            self.assertEqual(code, 200)
            trash = {"project_id": self.pid, "asset_id": uid(30), "narration_id": result["narration"]["id"], "revision": request["revision"], "deleted": True}
            encoded = json.dumps(trash)
            self.assertEqual(call("/api/camino/film/narration-trash", encoded, {"Content-Type": "application/json", "Origin": "https://foreign.invalid"})[0], 403)
            code, result = call("/api/camino/film/narration-trash", encoded, {"Content-Type": "application/json"})
            self.assertEqual(code, 200); self.assertTrue(result["narrations"][0]["deleted"])
            trash["deleted"] = False
            code, result = call("/api/camino/film/narration-trash", json.dumps(trash), {"Content-Type": "application/json"})
            self.assertEqual(code, 200); self.assertFalse(result["narrations"][0]["deleted"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "Local media tools required")
    def test_actual_mp3_import_preserves_complete_audio_and_uses_service_tool_resolution(self):
        from app.camino_film_narration import import_narration
        self.save_text()
        encoded = subprocess.run([binary("ffmpeg"), "-v", "error", "-f", "wav", "-i", "pipe:0",
            "-map", "0:a:0", "-map_metadata", "-1", "-f", "mp3", "pipe:1"],
            input=self.wav_bytes(), capture_output=True, check=True, timeout=30).stdout
        with patch.dict("os.environ", {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}):
            result = import_narration(self.editor, self.narration_payload(), encoded)
        self.assertTrue(950 <= result["narration"]["duration_ms"] <= 1200)
        take = result["narrations"][0]
        self.assertEqual(take["label"], "Importovaná nahrávka MP3")
        self.assertEqual(take["text"], LONG_TEXT)

    def test_legacy_take_keeps_its_original_script_after_later_text_edits(self):
        self.save_text(text="Starší pracovní verze.")
        request = self.narration_payload()
        with patch("app.camino_film_narration.synthesize", side_effect=self.fake_speech):
            prepare_narration(self.editor, request)
        path = self.store.root / self.pid / "narrations" / request["request_id"] / "receipt.json"
        receipt = json.loads(path.read_text())
        for key in ("text", "created_at", "label"): receipt.pop(key, None)
        path.write_text(json.dumps(receipt))
        before = digest(path)
        p = self.payload(); p["draft"]["shots"][0]["photo_text"]["text"] = "Nová pracovní verze."
        self.editor.save(p)
        self.assertEqual(self.editor.view()["narrations"][0]["text"], "Starší pracovní verze.")
        self.assertEqual(digest(path), before)
