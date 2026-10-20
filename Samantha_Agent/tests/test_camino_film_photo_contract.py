"""Independent acceptance contract for read-only, private film photo viewing."""
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
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


if __name__ == '__main__':
    unittest.main()
