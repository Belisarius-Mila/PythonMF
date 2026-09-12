from __future__ import annotations

import json
import random
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app import article_archive as archive
from app.cockpit import library_image_prepare_action
from app.library_images import MAX_LIBRARY_PHOTO_BYTES, MAX_LIBRARY_PHOTO_INPUT_BYTES, MAX_LIBRARY_STORED_PHOTO_BYTES, MAX_LIBRARY_THUMB_BYTES, prepare_library_photo, prepare_library_recognition_photo
from scripts.cockpit_quality_gate import node_binary


def image_bytes(size=(80, 40), color="blue", *, format="JPEG", exif=None):
    output = BytesIO()
    Image.new("RGB", size, color).save(output, format=format, **({"exif": exif} if exif else {}))
    return output.getvalue()


class LibraryPhotoPreparationTests(unittest.TestCase):
    def test_camera_jpeg_with_auxiliary_mpo_frame_uses_main_image(self):
        buffer = BytesIO()
        Image.new("RGB", (240, 160), "blue").save(buffer, format="MPO", save_all=True,
                                                  append_images=[Image.new("RGB", (240, 160), "red")])
        with Image.open(BytesIO(prepare_library_photo(buffer.getvalue()))) as result:
            self.assertEqual(result.format, "JPEG")
            self.assertEqual(result.size, (240, 160))
            self.assertGreater(result.getpixel((0, 0))[2], 200)

    def test_recognition_keeps_larger_temporary_resolution_and_normalized_jpeg_is_stable(self):
        original = image_bytes(size=(2400, 1800))
        compact = prepare_library_photo(original)
        recognition = prepare_library_recognition_photo(original)
        with Image.open(BytesIO(compact)) as image:
            self.assertEqual(image.size, (1600, 1200))
        with Image.open(BytesIO(recognition)) as image:
            self.assertEqual(image.size, (2400, 1800))
        self.assertEqual(compact, prepare_library_photo(compact))
        self.assertEqual(recognition, library_image_prepare_action(original, purpose="recognition"))
        with self.assertRaisesRegex(ValueError, "účel"):
            library_image_prepare_action(original, purpose="unrecognized")

    def test_large_photo_is_actually_below_compact_budget(self):
        source = BytesIO()
        Image.frombytes("RGB", (2400, 1800), random.Random(42).randbytes(2400 * 1800 * 3)).save(source, format="PNG")
        original = source.getvalue()
        self.assertGreater(len(original), 7 * 1024 * 1024)
        prepared = library_image_prepare_action(original)
        self.assertLessEqual(len(prepared), MAX_LIBRARY_PHOTO_BYTES)
        with Image.open(BytesIO(prepared)) as result:
            self.assertEqual(result.format, "JPEG")
            self.assertLessEqual(max(result.size), 1600)
        self.assertEqual(original, source.getvalue())

    def test_orientation_and_private_metadata_are_normalized(self):
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = "synthetic private author"
        prepared = prepare_library_photo(image_bytes(exif=exif))
        with Image.open(BytesIO(prepared)) as result:
            self.assertEqual(result.size, (40, 80))
            self.assertFalse(result.getexif())

    def test_heic_and_transparency_are_supported_locally(self):
        from pillow_heif import register_heif_opener
        register_heif_opener()
        heic = image_bytes(format="HEIF")
        for original in (heic,):
            with Image.open(BytesIO(prepare_library_photo(original))) as result:
                self.assertEqual(result.size, (80, 40))
        png = BytesIO()
        Image.new("RGBA", (20, 20), (0, 0, 0, 0)).save(png, format="PNG")
        with Image.open(BytesIO(prepare_library_photo(png.getvalue()))) as result:
            self.assertEqual(result.getpixel((0, 0)), (255, 255, 255))

    def test_invalid_and_oversized_input_are_rejected(self):
        for raw in (b"", b"invalid image", b"x" * (MAX_LIBRARY_PHOTO_INPUT_BYTES + 1)):
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                prepare_library_photo(raw)
        with patch("PIL.Image.open") as opener:
            opener.return_value.__enter__.return_value.format = "JPEG"
            opener.return_value.__enter__.return_value.width = 8001
            opener.return_value.__enter__.return_value.height = 8001
            with self.assertRaisesRegex(ValueError, "64 milionů"):
                prepare_library_photo(b"header")


class LibraryPhotoAttachmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.item = archive.archive_text_entry(title="Synthetic trip", text="Synthetic test text", category="travel_places", archive_root=self.root)["item"]
        self.arguments = dict(article_id=self.item["id"], image_bytes=image_bytes(), filename="photo.jpg", role="supporting_image", request_id="a" * 32, archive_root=self.root, user_confirmed=True, confirmation_text=archive.ATTACHMENT_CONFIRMATION_PHRASE)

    def test_retry_returns_the_same_attachment_and_rejects_changed_payload(self):
        first = archive.attach_article_image(**self.arguments)
        second = archive.attach_article_image(**self.arguments)
        self.assertTrue(second["replayed"])
        self.assertEqual(first["attachment"]["id"], second["attachment"]["id"])
        self.assertEqual(second["item"]["attachment_count"], 1)
        before = {p: p.read_bytes() for p in self.root.rglob("*.jpg")}
        with self.assertRaisesRegex(ValueError, "jiný obsah"):
            archive.attach_article_image(**{**self.arguments, "image_bytes": image_bytes(color="red")})
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*.jpg")})

    def test_three_photos_store_only_main_and_thumbnail_under_one_mib(self):
        total = 0
        for index in range(3):
            archive.attach_article_image(**{**self.arguments, "request_id": f"{index:032x}",
                                             "image_bytes": image_bytes(size=(2400, 1800))})
        item = archive.find_article(self.item["id"], archive_root=self.root)
        for attachment in item.attachments:
            self.assertEqual(attachment.original_file, attachment.readable_file)
            files = {self.root / attachment.original_file, self.root / attachment.readable_file, self.root / attachment.thumb_file}
            self.assertEqual(len(files), 2)
            size = sum(p.stat().st_size for p in files)
            self.assertLessEqual(size, MAX_LIBRARY_STORED_PHOTO_BYTES)
            self.assertLessEqual((self.root / attachment.thumb_file).stat().st_size, MAX_LIBRARY_THUMB_BYTES)
            total += size
        self.assertLess(total, 1024 * 1024)

    def test_retry_repairs_interrupted_registry_write_without_duplicate(self):
        with patch("app.article_archive.update_registry", side_effect=OSError("synthetic disk failure")):
            with self.assertRaises(OSError):
                archive.attach_article_image(**self.arguments)
        result = archive.attach_article_image(**self.arguments)
        self.assertTrue(result["replayed"])
        self.assertEqual(archive.find_article(self.item["id"], archive_root=self.root).attachments[0].id, result["attachment"]["id"])
        self.assertEqual(len(list(self.root.rglob("*.jpg"))), 2)

    def test_concurrent_uploads_and_text_edit_preserve_both(self):
        def upload(index):
            return archive.attach_article_image(**{**self.arguments, "request_id": f"{index:032x}"})
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(upload, i) for i in range(6)]
            futures.append(pool.submit(archive.update_article, article_id=self.item["id"], title="Edited trip", text="Edited text", category="travel_places", archive_root=self.root))
            for future in futures:
                self.assertTrue(future.result()["ok"])
        item = archive.find_article(self.item["id"], archive_root=self.root)
        self.assertEqual(item.title, "Edited trip")
        self.assertEqual(len(item.attachments), 6)
        self.assertEqual(len({entry.id for entry in item.attachments}), 6)

    def test_bad_photo_does_not_leave_image_files(self):
        with self.assertRaises(Exception):
            archive.attach_article_image(**{**self.arguments, "image_bytes": b"broken"})
        self.assertFalse(list(self.root.rglob("*.jpg")))
        self.assertEqual(len(archive.find_article(self.item["id"], archive_root=self.root).attachments), 0)


class LibraryPhotoQueueTests(unittest.TestCase):
    def test_delayed_preparation_destination_binding_retry_and_cancellation(self):
        source = (Path(__file__).resolve().parents[1] / "app/frontend/cockpit/library_photos.js").read_text()
        script = source + r'''
const assert = require("node:assert/strict");
if (!globalThis.crypto) globalThis.crypto = require("node:crypto").webcrypto;
const tick = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  const pending = new Map(), attempts = [], completed = [];
  let fail = true;
  const queue = new LibraryPhotos.Queue({
    preparePhoto: file => new Promise(resolve => pending.set(file.name, resolve)),
    upload: async task => {
      attempts.push([task.id, task.target.id]);
      if (task.name === "first.jpg" && fail) { fail = false; throw new Error("lost response"); }
      return {ok: true};
    },
    attached: (_data, target) => completed.push(target.id),
  });
  const first = queue.add({name: "first.jpg"}, "text");
  const second = queue.add({name: "second.jpg"}, "text");
  const snapshot = queue.pending("text");
  const next = queue.add({name: "next.jpg"}, "text");
  queue.bind(snapshot, {id: "card-one", title: "First trip"});
  assert.equal(attempts.length, 0, "Saving text does not wait for photos");
  queue.bind([next], {id: "card-two"});
  queue.bind([first], {id: "wrong-card"});
  assert.equal(first.target.id, "card-one");
  const prepared = {blob: new Blob(["small"], {type: "image/jpeg"}), filename: "prepared.jpg"};
  pending.get("second.jpg")(prepared); pending.get("first.jpg")(prepared); pending.get("next.jpg")(prepared);
  await tick(); await queue.uploadTail;
  assert.equal(first.state, "error"); assert.equal(second.state, "attached"); assert.equal(next.state, "attached");
  queue.retry(first); queue.retry(first); await queue.uploadTail;
  assert.equal(first.state, "attached");
  assert.deepEqual(attempts.filter(row => row[0] === first.id), [[first.id, "card-one"], [first.id, "card-one"]]);
  assert.deepEqual(completed.sort(), ["card-one", "card-one", "card-two"]);
  const canceled = queue.add({name: "canceled.jpg"}, "url");
  queue.remove(canceled); pending.get("canceled.jpg")(prepared); await tick();
  assert.equal(canceled.state, "removed"); assert.equal(canceled.prepared, null);
  const boundCanceled = queue.add({name: "bound-canceled.jpg"}, "text");
  queue.bind([boundCanceled], {id: "card-three"});
  queue.remove(boundCanceled); pending.get("bound-canceled.jpg")(prepared); await tick();
  assert.equal(boundCanceled.state, "removed");
  assert.equal(attempts.some(row => row[1] === "card-three"), false);
  assert.equal(queue.unfinished(), false);
  for (const task of [...queue.tasks]) queue.remove(task);
  assert.equal(queue.tasks.length, 0);
  console.log("queue: delayed preparation, immutable destination, selective retry, cancellation OK");
})().catch(error => { console.error(error); process.exitCode = 1; });
'''
        result = subprocess.run([node_binary(), "-"], input=script, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
