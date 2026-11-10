from __future__ import annotations

import base64
import io
import json
import os
import tempfile
import threading
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from PIL import Image, PngImagePlugin

from app.interior_atelier import AtelierConflict, AtelierError, InteriorAtelier, MAX_IMAGE_BYTES


def image_bytes(size=(600, 400), metadata=False):
    image = Image.new("RGB", size, "beige")
    output = io.BytesIO()
    info = PngImagePlugin.PngInfo()
    if metadata:
        info.add_text("PRIVATE_LOCATION", "synthetic-secret")
    image.save(output, format="PNG", pnginfo=info)
    return output.getvalue()


class InteriorAtelierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "atelier"
        self.store = InteriorAtelier(self.root)

    def command(self, action, **payload):
        return self.store.execute({"action": action, "request_id": uuid.uuid4().hex, **payload})

    def project(self):
        result = self.command("create_project", title="Synthetic project", room_title="Synthetic room")
        return result["project_id"], result["room_id"]

    def source(self, project, room, raw=None, **extra):
        return self.command("add_source", project_id=project, room_id=room, title="test.png", kind="photo",
                            data=base64.b64encode(raw or image_bytes()).decode(), **extra)["asset_id"]

    def draft(self, project, room, base="base"):
        return self.store.state(project, room, base)["draft"]

    def save(self, project, room, values, revision=0, base="base"):
        return self.command("save_draft", project_id=project, room_id=room, base_id=base,
                            expected_revision=revision, draft=values)

    def test_read_and_constructor_do_not_create_private_storage(self):
        self.assertEqual(self.store.state()["projects"], [])
        self.assertFalse(self.root.exists())

    def test_explicit_project_creation_and_restart_preserve_room(self):
        project, room = self.project()
        state = InteriorAtelier(self.root).state(project, room)
        self.assertEqual(state["room"]["title"], "Synthetic room")
        self.assertEqual(state["draft"]["revision"], 0)
        self.assertEqual(os.stat(self.root).st_mode & 0o777, 0o700)
        self.assertEqual(os.stat(self.store.path).st_mode & 0o777, 0o600)

    def test_request_identity_is_durable_and_rejects_changed_payload(self):
        payload = {"action": "create_project", "request_id": uuid.uuid4().hex,
                   "title": "One", "room_title": "Room"}
        first = self.store.execute(payload)
        second = InteriorAtelier(self.root).execute(payload)
        self.assertTrue(second["replayed"])
        self.assertEqual(first["project_id"], second["project_id"])
        before = self.store.path.read_bytes()
        with self.assertRaises(AtelierConflict):
            self.store.execute({**payload, "title": "Different"})
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_same_image_upload_is_deduplicated_without_overwriting_original(self):
        project, room = self.project()
        asset = self.source(project, room)
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (self.root / "objects").iterdir()}
        duplicate = self.source(project, room)
        self.assertEqual(asset, duplicate)
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (self.root / "objects").iterdir()})

    def test_original_bytes_preserved_and_derivatives_strip_metadata(self):
        project, room = self.project()
        raw = image_bytes((1800, 900), metadata=True)
        asset = self.source(project, room, raw)
        self.assertEqual(self.store.asset(project, room, asset, "original"), (raw, "image/png"))
        for view, limit in (("thumbnail", 256), ("preview", 1400)):
            content, mime = self.store.asset(project, room, asset, view)
            with Image.open(io.BytesIO(content)) as image:
                self.assertLessEqual(max(image.size), limit)
                self.assertNotIn("PRIVATE_LOCATION", image.info)
                self.assertEqual(image.width, 2 * image.height)
            self.assertEqual(mime, "image/png")

    def test_image_payload_is_validated_instead_of_trusting_filename(self):
        project, room = self.project()
        before = self.store.state(project, room)
        for data in ("not-base64!", base64.b64encode(b"<svg onload='evil()'/>").decode(),
                     base64.b64encode(b"not an image").decode()):
            with self.subTest(data=data), self.assertRaises(AtelierError):
                self.command("add_source", project_id=project, room_id=room, title="picture.png",
                             kind="photo", data=data)
        self.assertEqual(self.store.state(project, room), before)

    def test_animated_images_and_over_limit_images_are_rejected(self):
        project, room = self.project()
        output = io.BytesIO()
        Image.new("RGB", (10, 10), "red").save(output, format="WEBP", save_all=True,
            append_images=[Image.new("RGB", (10, 10), "blue")], duration=100, loop=0)
        with self.assertRaises(AtelierError):
            self.source(project, room, output.getvalue())
        with self.assertRaises(AtelierError):
            self.command("add_source", project_id=project, room_id=room, title="large.png",
                         kind="photo", data="A" * (((MAX_IMAGE_BYTES + 2) // 3 * 4) + 1))
        with patch("app.interior_atelier.MAX_IMAGE_PIXELS", 100):
            with self.assertRaises(AtelierError):
                self.source(project, room)

    def test_iphone_jpeg_mpo_preserves_original_and_uses_only_oriented_main_photo(self):
        project, room = self.project()
        output = io.BytesIO()
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = "PRIVATE_SYNTHETIC_AUTHOR"
        Image.new("RGB", (240, 160), "blue").save(output, format="MPO", save_all=True,
            append_images=[Image.new("RGB", (240, 160), "red")], exif=exif)
        raw = output.getvalue()
        asset = self.source(project, room, raw)
        self.assertEqual(self.store.asset(project, room, asset, "original"), (raw, "image/jpeg"))
        source = self.store.state(project, room)["room"]["sources"][asset]
        self.assertEqual((source["width"], source["height"]), (160, 240))
        for view in ("preview", "thumbnail"):
            content, mime = self.store.asset(project, room, asset, view)
            self.assertEqual(mime, "image/png")
            with Image.open(io.BytesIO(content)) as image:
                self.assertEqual(image.size, (160, 240))
                self.assertEqual(getattr(image, "n_frames", 1), 1)
                self.assertGreater(image.getpixel((80, 120))[2], 200)
                self.assertLess(image.getpixel((80, 120))[0], 20)
                self.assertFalse(image.getexif())
                self.assertNotIn("exif", image.info)
            self.assertNotIn(b"PRIVATE_SYNTHETIC_AUTHOR", content)

    def test_mpo_still_obeys_pixel_limit_without_publishing_partial_source(self):
        project, room = self.project()
        output = io.BytesIO()
        Image.new("RGB", (100, 100), "blue").save(output, format="MPO", save_all=True,
            append_images=[Image.new("RGB", (100, 100), "red")])
        before = self.store.state(project, room)
        with patch("app.interior_atelier.MAX_IMAGE_PIXELS", 100), self.assertRaisesRegex(AtelierError, "rozlišení"):
            self.source(project, room, output.getvalue())
        self.assertEqual(self.store.state(project, room), before)

    def test_other_room_cannot_read_or_reference_an_asset(self):
        project, room = self.project()
        asset = self.source(project, room)
        other = self.command("create_room", project_id=project, title="Second")["room_id"]
        with self.assertRaises(AtelierError):
            self.store.asset(project, other, asset)
        draft = {k: v for k, v in self.draft(project, other).items() if k != "revision"}
        draft.update(source_ids=[asset], image_source_id=asset)
        with self.assertRaises(AtelierError):
            self.save(project, other, draft)

    def test_second_project_does_not_inherit_sources_or_drafts(self):
        project, room = self.project()
        self.source(project, room)
        project2, room2 = self.project()
        second = self.store.state(project2, room2)
        self.assertEqual(second["room"]["sources"], {})
        self.assertEqual(second["draft"]["source_ids"], [])

    def test_save_and_restart_preserve_selected_sources_and_normalized_drawing(self):
        project, room = self.project()
        asset = self.source(project, room)
        draft = self.draft(project, room)
        draft.pop("revision")
        draft.update(title="First", source_ids=[asset], image_source_id=asset,
                     prompt="Only lower the bookcase", annotations=[[[0.1, 0.2], [0.8, 0.9]]])
        self.assertEqual(self.save(project, room, draft)["revision"], 1)
        reopened = InteriorAtelier(self.root).state(project, room)["draft"]
        self.assertEqual(reopened, {**draft, "revision": 1})

    def test_stale_revision_does_not_overwrite_newer_draft(self):
        project, room = self.project()
        draft = self.draft(project, room)
        draft.pop("revision")
        self.save(project, room, {**draft, "prompt": "New"})
        with self.assertRaises(AtelierConflict):
            self.save(project, room, {**draft, "prompt": "Stale"})
        self.assertEqual(self.draft(project, room)["prompt"], "New")

    def test_concurrent_writers_have_one_winner(self):
        project, room = self.project()
        draft = self.draft(project, room)
        draft.pop("revision")
        barrier = threading.Barrier(2)
        outcomes = []
        def writer(text):
            barrier.wait()
            try:
                self.save(project, room, {**draft, "prompt": text})
                outcomes.append("saved")
            except AtelierConflict:
                outcomes.append("conflict")
        threads = [threading.Thread(target=writer, args=(text,)) for text in ("One", "Two")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertCountEqual(outcomes, ["saved", "conflict"])

    def test_derived_variant_preserves_parent_and_pins_its_source_set(self):
        project, room = self.project()
        asset = self.source(project, room)
        draft = self.draft(project, room)
        draft.pop("revision")
        draft.update(title="First", source_ids=[asset], image_source_id=asset, prompt="Original")
        self.save(project, room, draft)
        parent = self.command("create_variant", project_id=project, room_id=room, base_id="base",
                              expected_revision=1)["variant_id"]
        original = copy_json(self.store.state(project, room)["room"]["variants"][parent])
        edited = self.draft(project, room, parent)
        edited.pop("revision")
        edited.update(title="Second", prompt="Only change color")
        self.save(project, room, edited, base=parent)
        child = self.command("create_variant", project_id=project, room_id=room, base_id=parent,
                             expected_revision=1)["variant_id"]
        variants = self.store.state(project, room)["room"]["variants"]
        self.assertEqual(variants[parent], original)
        self.assertEqual(variants[child]["parent_id"], parent)
        self.assertEqual(variants[child]["source_ids"], [asset])
        self.assertEqual(variants[child]["kind"], "human_proposal")

    def test_notes_stay_bound_to_their_existing_variant(self):
        project, room = self.project()
        self.command("add_note", project_id=project, room_id=room, base_id="base", text="Original note")
        with self.assertRaises(AtelierError):
            self.command("add_note", project_id=project, room_id=room, base_id="f"*32, text="Wrong scope")
        notes = InteriorAtelier(self.root).state(project, room)["room"]["notes"]
        self.assertEqual([(n["base_id"], n["text"]) for n in notes], [("base", "Original note")])

    def test_outside_and_nonfinite_annotation_coordinates_are_rejected(self):
        project, room = self.project()
        asset = self.source(project, room)
        draft = self.draft(project, room)
        draft.pop("revision")
        draft.update(source_ids=[asset], image_source_id=asset)
        for coordinates in ([[0, 0], [2, 1]], [[True, 0], [1, 1]], [[float("nan"), 0], [1, 1]]):
            with self.subTest(coordinates=coordinates), self.assertRaises(AtelierError):
                self.save(project, room, {**draft, "annotations": [coordinates]})
        self.assertEqual(self.draft(project, room)["revision"], 0)

    def test_symlink_root_and_blob_are_not_followed(self):
        outside = Path(self.temp.name).resolve() / "outside"
        outside.mkdir()
        link = Path(self.temp.name).resolve() / "link"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(AtelierError):
            InteriorAtelier(link).state()
        project, room = self.project()
        asset = self.source(project, room)
        stored = self.store.state(project, room)["room"]["sources"][asset]["files"]["preview"]
        target = self.root / "objects" / stored["name"]
        # Synthetic fixture is intentionally replaced with an outside link.
        target.unlink()
        secret = outside / "secret"
        secret.write_text("synthetic-secret")
        target.symlink_to(secret)
        with self.assertRaises(AtelierError):
            self.store.asset(project, room, asset)

    def test_changed_blob_is_rejected_by_content_hash(self):
        project, room = self.project()
        asset = self.source(project, room)
        stored = self.store.state(project, room)["room"]["sources"][asset]["files"]["thumbnail"]
        (self.root / "objects" / stored["name"]).write_bytes(b"changed")
        with self.assertRaises(AtelierError):
            self.store.asset(project, room, asset, "thumbnail")

    def test_interrupted_metadata_save_never_exposes_incomplete_source(self):
        project, room = self.project()
        before = self.store.path.read_bytes()
        with patch("app.work_repository._write_repository_document_under_lock", side_effect=OSError("synthetic")):
            with self.assertRaises(OSError):
                self.source(project, room)
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertEqual(self.store.state(project, room)["room"]["sources"], {})
        asset = self.source(project, room)
        self.assertTrue(self.store.asset(project, room, asset)[0])

    def test_unknown_operations_and_path_identity_inputs_are_rejected(self):
        with self.assertRaises(AtelierError):
            self.command(["bad"])
        with self.assertRaises(AtelierError):
            self.store.state("../outside", "a"*32)
        with self.assertRaises(AtelierError):
            self.command("create_project", title="One", room_title="Room", path="../outside")
        self.assertFalse(self.root.exists())


def copy_json(value):
    return json.loads(json.dumps(value))


class InteriorSourceDeletionTests(unittest.TestCase):
    setUp = InteriorAtelierTests.setUp
    command = InteriorAtelierTests.command
    project = InteriorAtelierTests.project
    source = InteriorAtelierTests.source
    draft = InteriorAtelierTests.draft
    save = InteriorAtelierTests.save

    def deletion(self, project, room, asset):
        from app.interior_cleanup import DELETE_CONFIRMATION
        plan = self.store.deletion_preview(project, room, asset)
        return {"action": "delete_source", "request_id": uuid.uuid4().hex, "project_id": project,
                "room_id": room, "asset_id": asset, "plan_token": plan["plan_token"],
                "confirmation": DELETE_CONFIRMATION}, plan

    def test_preview_is_readonly_and_does_not_materialize_an_unknown_store(self):
        with self.assertRaises(AtelierError):
            self.store.deletion_preview("a" * 32, "b" * 32, "c" * 32)
        self.assertFalse(self.root.exists())
        p, r = self.project(); a = self.source(p, r)
        before = {str(f.relative_to(self.root)): (f.read_bytes(), f.stat().st_mtime_ns)
                  for f in self.root.rglob("*") if f.is_file()}
        _, plan = self.deletion(p, r, a)
        self.assertEqual(plan["file_count"], 3)
        self.assertGreater(plan["bytes"], 0)
        self.assertNotIn("files", plan)
        self.assertEqual(before, {str(f.relative_to(self.root)): (f.read_bytes(), f.stat().st_mtime_ns)
                                  for f in self.root.rglob("*") if f.is_file()})

    def test_permanent_delete_removes_image_bytes_but_retains_text_and_notes(self):
        p, r = self.project(); a = self.source(p, r)
        draft = self.draft(p, r); draft.pop("revision")
        draft.update(title="Retained text", prompt="Keep this text", source_ids=[a], image_source_id=a,
                     annotations=[[[0, 0], [1, 1]]])
        self.save(p, r, draft)
        variant = self.command("create_variant", project_id=p, room_id=r, base_id="base", expected_revision=1)["variant_id"]
        self.command("add_note", project_id=p, room_id=r, base_id=variant, text="Retained note")
        payload, plan = self.deletion(p, r, a)
        self.assertEqual((plan["variant_count"], plan["draft_count"]), (1, 1))
        outcome = self.store.execute(payload)
        self.assertEqual(outcome["deleted_bytes"], plan["bytes"])
        self.assertEqual(list((self.root / "objects").iterdir()), [])
        current = self.store.state(p, r)
        self.assertEqual(current["room"]["sources"], {})
        self.assertEqual(current["draft"]["prompt"], "Keep this text")
        self.assertEqual(current["draft"]["revision"], 2)
        self.assertEqual(current["draft"]["annotations"], [])
        self.assertEqual(current["room"]["variants"][variant]["image_source_id"], "")
        self.assertEqual(current["room"]["notes"][0]["text"], "Retained note")
        with self.assertRaises(AtelierError): self.store.asset(p, r, a)
        self.assertTrue(InteriorAtelier(self.root).execute(payload)["already_deleted"])

    def test_confirmation_and_stale_manifest_never_delete_bytes(self):
        p, r = self.project(); a = self.source(p, r)
        payload, _ = self.deletion(p, r, a)
        for replacement in ("", "ano", True):
            with self.assertRaises(AtelierError): self.store.execute({**payload, "confirmation": replacement})
        self.command("add_note", project_id=p, room_id=r, base_id="base", text="Concurrent note")
        with self.assertRaises(AtelierConflict): self.store.execute(payload)
        self.assertTrue(self.store.asset(p, r, a)[0])
        self.assertNotIn("source_deletions", self.store._read())

    def test_shared_objects_remain_until_last_source_is_deleted(self):
        p, r = self.project(); a = self.source(p, r)
        other = self.command("create_room", project_id=p, title="Other")["room_id"]
        b = self.source(p, other)
        payload, plan = self.deletion(p, r, a)
        self.assertEqual((plan["bytes"], plan["shared_file_count"]), (0, 3))
        self.store.execute(payload)
        self.assertEqual(self.store.asset(p, other, b, "original")[0], image_bytes())
        self.store.execute(self.deletion(p, other, b)[0])
        self.assertEqual(list((self.root / "objects").iterdir()), [])

    def test_other_room_and_path_input_cannot_redirect_deletion(self):
        p, r = self.project(); a = self.source(p, r)
        other = self.command("create_room", project_id=p, title="Other")["room_id"]
        with self.assertRaises(AtelierError): self.store.deletion_preview(p, other, a)
        payload, _ = self.deletion(p, r, a)
        with self.assertRaises(AtelierError): self.store.execute({**payload, "path": "../outside"})
        with self.assertRaises(AtelierError): self.store.execute({**payload, "room_id": "../outside"})
        self.assertTrue(self.store.asset(p, r, a)[0])

    def test_symlink_and_hardlink_are_rejected_without_touching_external_bytes(self):
        p, r = self.project(); a = self.source(p, r)
        original = self.root / "objects" / self.store.state(p, r)["room"]["sources"][a]["files"]["original"]["name"]
        external = Path(self.temp.name) / "outside.png"
        original.rename(external); original.symlink_to(external)
        with self.assertRaises(AtelierError): self.store.deletion_preview(p, r, a)
        original.unlink(); os.link(external, original)
        with self.assertRaises(AtelierError): self.store.deletion_preview(p, r, a)
        self.assertEqual(external.read_bytes(), image_bytes())

    def test_partial_unlink_is_durable_and_same_request_finishes_only_remaining_files(self):
        p, r = self.project(); a = self.source(p, r)
        payload, plan = self.deletion(p, r, a)
        unlink = os.unlink; calls = []
        def fail_second(name, **kwargs):
            if "dir_fd" in kwargs:
                calls.append(name)
                if len(calls) == 2: raise OSError("synthetic disk failure")
            return unlink(name, **kwargs)
        with patch("app.interior_cleanup.os.unlink", side_effect=fail_second), self.assertRaises(OSError):
            self.store.execute(payload)
        self.assertEqual(len(list((self.root / "objects").iterdir())), 2)
        self.assertEqual(self.store.state(p, r)["pending_deletions"][0]["request_id"], payload["request_id"])
        with self.assertRaises(AtelierError): self.store.asset(p, r, a)
        with self.assertRaises(AtelierConflict): self.store.execute({**payload, "asset_id": "a" * 32})
        resumed = InteriorAtelier(self.root).execute(payload)
        self.assertEqual(resumed["deleted_bytes"], plan["bytes"])
        self.assertEqual(resumed["deleted_files"], 3)
        self.assertEqual(self.store.state(p, r)["pending_deletions"], [])

    def test_failed_final_metadata_commit_does_not_lose_deletion_intent(self):
        from app import work_repository
        p, r = self.project(); a = self.source(p, r)
        payload, plan = self.deletion(p, r, a)
        writer = work_repository._write_repository_document_under_lock
        calls = []
        def fail_second(*args):
            calls.append(1)
            if len(calls) == 2: raise OSError("synthetic final commit failure")
            return writer(*args)
        with patch("app.work_repository._write_repository_document_under_lock", side_effect=fail_second), self.assertRaises(OSError):
            self.store.execute(payload)
        self.assertEqual(list((self.root / "objects").iterdir()), [])
        self.assertEqual(self.store.state(p, r)["pending_deletions"][0]["status"], "pending")
        self.assertEqual(self.store.execute(payload)["deleted_bytes"], plan["bytes"])

    def test_modified_bytes_between_preview_and_confirm_are_preserved(self):
        p, r = self.project(); a = self.source(p, r)
        payload, _ = self.deletion(p, r, a)
        original = self.root / "objects" / self.store.state(p, r)["room"]["sources"][a]["files"]["original"]["name"]
        original.write_bytes(b"changed")
        with self.assertRaises(AtelierConflict): self.store.execute(payload)
        self.assertEqual(len(list((self.root / "objects").iterdir())), 3)

    def test_unfinished_ai_blocks_removal_but_completed_ai_copies_are_purged(self):
        from app.work_repository import RepositoryMutation
        p, r = self.project(); a = self.source(p, r)
        job_id = "b" * 32
        def add_job(status):
            def update(data):
                room = self.store._room(data, p, r)[1]
                room["ai_requests"] = {job_id: {"status": status, "context": {"draft": {"source_ids": [a]}}, "variant_ids": []}}
                return RepositoryMutation(data)
            self.store.repository.transact(update)
        for status in ("queued", "running", "delivery_unknown", "result_ready"):
            add_job(status)
            with self.assertRaises(AtelierConflict): self.store.deletion_preview(p, r, a)
        add_job("completed")
        home = self.root / "ai_inputs" / job_id; home.mkdir(parents=True)
        for name in ("input_1.png", "result.json", "result.json.lock"): (home / name).write_bytes(b"synthetic copy")
        payload, plan = self.deletion(p, r, a)
        self.assertEqual(plan["file_count"], 6)
        self.store.execute(payload)
        self.assertFalse(home.exists())
        self.assertTrue(self.store._read()["projects"][p]["rooms"][r]["ai_requests"][job_id]["source_cleanup"])

    def test_unknown_ai_cache_files_are_not_deleted(self):
        from app.work_repository import RepositoryMutation
        p, r = self.project(); a = self.source(p, r)
        job_id = "b" * 32
        def update(data):
            self.store._room(data, p, r)[1]["ai_requests"] = {job_id: {"status": "completed", "context": {"draft": {"source_ids": [a]}}}}
            return RepositoryMutation(data)
        self.store.repository.transact(update)
        home = self.root / "ai_inputs" / job_id; home.mkdir(parents=True)
        (home / "unexpected.txt").write_text("preserve")
        with self.assertRaises(AtelierError): self.store.deletion_preview(p, r, a)
        self.assertEqual((home / "unexpected.txt").read_text(), "preserve")
