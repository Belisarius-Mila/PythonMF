"""Independent acceptance contract for read-only, private film photo viewing."""
import hashlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageCms
from app.camino_film_editor import FilmEditor
from app.camino_film_workshop import MacFilmProjectStore
from tests.camino_viewer_fixture import ViewerFixture, uid


class FilmPhotoContractTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        archive = self.root / 'archive'
        archive.mkdir()
        self.fixture = ViewerFixture(archive)
        image = Image.new('RGB', (3, 2), (40, 100, 180))
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = 'PRIVATE-SYNTHETIC-TAG'
        buffer = io.BytesIO()
        image.save(buffer, 'JPEG', exif=exif)
        self.original = buffer.getvalue()
        self.fixture.upload(30, 'photo', self.original)
        self.fixture.upload(31, 'photo', self.original, private=True)
        self.fixture.upload(32, 'video', b'synthetic video')
        self.store = MacFilmProjectStore(self.root / 'projects', metadata_db=self.fixture.store.path,
            media_db=self.fixture.media.database_path, media_root=self.fixture.media.root,
            trip_id=self.fixture.trip.id)
        self.pid = self.store.close_mac_day(self.fixture.day.local_date, confirmed=True)['project_id']
        self.editor = FilmEditor(self.store, day=self.fixture.day.local_date)

    def method(self):
        method = getattr(self.editor, 'photo_bytes', None)
        self.assertTrue(callable(method), 'FilmEditor.photo_bytes(project_id, asset_id) is required')
        return method

    def test_photo_is_oriented_metadata_free_and_creates_no_render_or_copy(self):
        method = self.method()
        folder = self.store.root / self.pid
        before = {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in folder.rglob('*') if p.is_file()}
        data = method(self.pid, uid(30))
        self.assertIsInstance(data, bytes)
        self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
        with Image.open(io.BytesIO(data)) as image:
            self.assertEqual(image.size, (2, 3))
            self.assertFalse(image.getexif())
        self.assertNotIn(b'PRIVATE-SYNTHETIC-TAG', data)
        self.assertEqual((self.fixture.media.objects / (uid(30) + '.bin')).read_bytes(), self.original)
        after = {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in folder.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((folder / 'jobs').exists())

    def test_large_sdr_photo_fits_preview_preserving_original_and_metadata_privacy(self):
        exif = Image.Exif(); exif[270] = 'PRIVATE-LARGE-PHOTO'
        buffer = io.BytesIO()
        with Image.new('RGB', (5918, 3860), (40, 100, 180)) as image:
            image.save(buffer, 'JPEG', exif=exif,
                icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
        original = buffer.getvalue()
        self.fixture.upload(33, 'photo', original)
        pid = self.store.close_mac_day(self.fixture.day.local_date, confirmed=True)['project_id']
        data = self.method()(pid, uid(33))
        with Image.open(io.BytesIO(data)) as decoded:
            self.assertEqual(decoded.size, (4096, 2672))
            self.assertFalse(decoded.getexif())
            self.assertNotIn('icc_profile', decoded.info)
        self.assertNotIn(b'PRIVATE-LARGE-PHOTO', data)
        self.assertEqual((self.fixture.media.objects / (uid(33) + '.bin')).read_bytes(), original)
        self.assertFalse((self.store.root / pid / 'jobs').exists())

    def test_decoding_keeps_byte_pixel_and_edge_limits(self):
        for setting, limit in [('MAX_PHOTO_BYTES', len(self.original) - 1),
                               ('MAX_PHOTO_PIXELS', 5), ('MAX_PHOTO_EDGE', 2)]:
            with self.subTest(setting=setting), patch('app.camino_film_photo.' + setting, limit):
                with self.assertRaises(ValueError):
                    self.method()(self.pid, uid(30))
        self.assertEqual((self.fixture.media.objects / (uid(30) + '.bin')).read_bytes(), self.original)

    def test_foreign_private_nonphoto_and_malformed_ids_are_rejected(self):
        method = self.method()
        for project_id, asset_id in [(self.pid, uid(31)), (self.pid, uid(32)), (self.pid, uid(999)),
                                     (uid(999), uid(30)), (self.pid, '../../secret'), ('../secret', uid(30))]:
            with self.subTest(project_id=project_id, asset_id=asset_id):
                with self.assertRaises((ValueError, OSError)):
                    method(project_id, asset_id)

    def test_privacy_change_revokes_delivery(self):
        method = self.method()
        self.fixture.lock()
        with self.assertRaises((ValueError, OSError)):
            method(self.pid, uid(30))

    def test_warm_digest_cache_does_not_cache_permission_or_unrelated_file_integrity(self):
        self.editor.photo_bytes(self.pid, uid(30), image_kind="thumbnail")
        video = self.fixture.media.objects / (uid(32) + '.bin')
        before = video.stat()
        video.write_bytes(b'synthetic videX')
        os.utime(video, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaises((ValueError, OSError)):
            self.editor.photo_bytes(self.pid, uid(30), image_kind="thumbnail")

    def test_strict_validation_still_reads_bytes_after_a_warm_ui_validation(self):
        _, manifest = self.editor.inputs(self.pid, cached_files=True)
        with patch.object(hashlib, 'file_digest', wraps=hashlib.file_digest) as hashing:
            self.editor.inputs(self.pid)
            self.assertEqual(hashing.call_count, len(manifest['sources']))

    def test_warm_thumbnail_is_revoked_before_decoding_after_privacy_change(self):
        self.editor.photo_bytes(self.pid, uid(30), image_kind="thumbnail")
        self.fixture.lock()
        with patch.object(Image, 'open', side_effect=AssertionError('private bytes must not decode')):
            for kind in ("thumbnail", "image-preview", "photo"):
                with self.subTest(kind=kind), self.assertRaises((ValueError, OSError)):
                    self.editor.photo_bytes(self.pid, uid(30), image_kind=kind)

    def test_small_preview_sizes_strip_metadata_without_changing_the_original(self):
        buffer = io.BytesIO()
        with Image.new('RGB', (2000, 1000), (40, 100, 180)) as image:
            image.save(buffer, 'JPEG')
        original = buffer.getvalue()
        self.fixture.upload(33, 'photo', original)
        pid = self.store.close_mac_day(self.fixture.day.local_date, confirmed=True)['project_id']
        for kind, size in [('thumbnail', (256, 128)), ('image-preview', (1600, 800))]:
            data = self.editor.photo_bytes(pid, uid(33), image_kind=kind)
            with Image.open(io.BytesIO(data)) as image:
                self.assertEqual(image.size, size)
                self.assertFalse(image.getexif())
        self.assertEqual((self.fixture.media.objects / (uid(33) + '.bin')).read_bytes(), original)

    def test_privacy_change_during_decode_is_rechecked_before_delivery(self):
        method = self.method()
        original_open = Image.open
        def open_and_revoke(*args, **kwargs):
            image = original_open(*args, **kwargs)
            self.fixture.lock()
            return image
        with patch.object(Image, 'open', side_effect=open_and_revoke):
            with self.assertRaises((ValueError, OSError)):
                method(self.pid, uid(30))


class FilmDigestCacheTests(unittest.TestCase):
    def setUp(self):
        from camino.film import digest_cache
        self.cache = digest_cache
        with digest_cache._LOCK:
            digest_cache._CACHE.clear()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'source.bin'
        self.path.write_bytes(b'unchanged bytes')
        self.expected = hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_hits_expire_without_sliding_the_byte_check_deadline(self):
        with patch.object(hashlib, 'file_digest', wraps=hashlib.file_digest) as hashing, patch.object(self.cache, '_clock', return_value=100) as clock:
            self.assertEqual(self.cache.verified_digest(self.path, self.expected), self.expected)
            clock.return_value = 110
            self.assertEqual(self.cache.verified_digest(self.path, self.expected), self.expected)
            self.assertEqual(hashing.call_count, 1)
            clock.return_value = 131
            self.assertEqual(self.cache.verified_digest(self.path, self.expected), self.expected)
            self.assertEqual(hashing.call_count, 2)

    def test_same_size_mutation_with_restored_mtime_is_rehashed(self):
        self.cache.verified_digest(self.path, self.expected)
        before = self.path.stat()
        self.path.write_bytes(b'CHANGED!! bytes')
        self.assertEqual(self.path.stat().st_size, before.st_size)
        os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertNotEqual(self.cache.verified_digest(self.path, self.expected), self.expected)

    def test_cached_path_cannot_follow_a_replacement_symlink(self):
        self.cache.verified_digest(self.path, self.expected)
        target = self.path.with_name('elsewhere.bin')
        target.write_bytes(b'unchanged bytes')
        self.path.unlink(); self.path.symlink_to(target)
        with self.assertRaises(OSError):
            self.cache.verified_digest(self.path, self.expected)

    def test_changes_during_hashing_are_not_cached(self):
        original = hashlib.file_digest
        def changed(stream, *args, **kwargs):
            result = original(stream, *args, **kwargs)
            self.path.write_bytes(b'CHANGED!! bytes')
            return result
        with patch.object(hashlib, 'file_digest', side_effect=changed), self.assertRaises(OSError):
            self.cache.verified_digest(self.path, self.expected)
        self.assertFalse(self.cache._CACHE)

    def test_memory_is_bounded(self):
        with patch.object(self.cache, '_LIMIT', 2):
            for index in range(3):
                path = self.path.with_name(f'{index}.bin'); path.write_bytes(b'unchanged bytes')
                self.cache.verified_digest(path, self.expected)
            self.assertEqual(len(self.cache._CACHE), 2)


if __name__ == '__main__':
    unittest.main()
