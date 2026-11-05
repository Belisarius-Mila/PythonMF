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
