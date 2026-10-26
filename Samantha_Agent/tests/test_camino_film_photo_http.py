"""HTTP acceptance regressions for private, synthetic-only film photo viewing."""
import http.client
import io
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from PIL import Image
from app import cockpit
from app.camino_film_editor import FilmEditor
from app.camino_film_workshop import MacFilmProjectStore
from tests.camino_viewer_fixture import ViewerFixture, uid


class FilmPhotoHttpTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        archive = root / "archive"
        archive.mkdir()
        self.fixture = ViewerFixture(archive)
        image = Image.new("RGB", (3, 2), (40, 100, 180))
        buffer = io.BytesIO()
        image.save(buffer, "JPEG")
        self.original = buffer.getvalue()
        self.fixture.upload(30, "photo", self.original)
        self.fixture.upload(31, "photo", self.original, private=True)
        store = MacFilmProjectStore(root / "projects", metadata_db=self.fixture.store.path,
            media_db=self.fixture.media.database_path, media_root=self.fixture.media.root,
            trip_id=self.fixture.trip.id)
        self.project_id = store.close_mac_day(self.fixture.day.local_date, confirmed=True)["project_id"]
        self.editor = FilmEditor(store, day=self.fixture.day.local_date)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.thread.join, 3)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path):
        with patch.object(cockpit, "production_editor", return_value=self.editor):
            conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
            try:
                conn.request(method, path)
                response = conn.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            finally:
                conn.close()

    def test_get_and_head_deliver_only_png_with_private_no_store_headers(self):
        path = f"/api/camino/film/photo/{self.project_id}/{uid(30)}"
        status, headers, body = self.request("GET", path)
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "image/png")
        self.assertEqual(headers["Content-Disposition"], 'inline; filename="photo.png"')
        self.assertIn("no-store", headers["Cache-Control"])
        self.assertIn("private", headers["Cache-Control"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(int(headers["Content-Length"]), len(body))
        self.assertTrue(body.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertNotEqual(body, self.original)
        with Image.open(io.BytesIO(body)) as decoded:
            self.assertEqual(decoded.size, (3, 2))
            self.assertFalse(decoded.getexif())
        head_status, head_headers, head_body = self.request("HEAD", path)
        self.assertEqual(head_status, 200)
        self.assertEqual(head_headers["Content-Type"], "image/png")
        self.assertEqual(head_headers["Content-Length"], headers["Content-Length"])
        self.assertEqual(head_body, b"")
        self.assertFalse((self.editor.store.root / self.project_id / "jobs").exists())

    def test_query_bad_ids_private_sources_and_wrong_segments_are_generic_not_found(self):
        paths = [f"/api/camino/film/photo/{self.project_id}/{uid(30)}?x=1",
            f"/api/camino/film/photo/{self.project_id}/{uid(31)}",
            f"/api/camino/film/photo/{self.project_id}/{uid(32)}",
            f"/api/camino/film/photo/{self.project_id}/../../secret",
            f"/api/camino/film/photo/{uid(999)}/{uid(30)}",
            f"/api/camino/film/photo/{self.project_id}/{uid(30)}/extra"]
        for path in paths:
            with self.subTest(path=path):
                status, _, body = self.request("GET", path)
                self.assertEqual(status, 404)
                self.assertEqual(json.loads(body)["message"], "Fotografie není dostupná.")
                self.assertNotIn(str(self.editor.store.media.objects).encode(), body)

    def test_large_photo_is_available_over_get_and_head(self):
        buffer = io.BytesIO()
        with Image.new('RGB', (5000, 100), (40, 100, 180)) as image:
            image.save(buffer, 'JPEG')
        original = buffer.getvalue()
        self.fixture.upload(33, 'photo', original)
        pid = self.editor.store.close_mac_day(self.fixture.day.local_date, confirmed=True)['project_id']
        path = f'/api/camino/film/photo/{pid}/{uid(33)}'
        status, headers, body = self.request('GET', path)
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Type'], 'image/png')
        self.assertIn('no-store', headers['Cache-Control'])
        with Image.open(io.BytesIO(body)) as decoded:
            self.assertEqual(decoded.size, (4096, 82))
        status, head_headers, head_body = self.request('HEAD', path)
        self.assertEqual(status, 200)
        self.assertEqual(head_headers['Content-Length'], headers['Content-Length'])
        self.assertEqual(head_body, b'')
        self.assertEqual((self.fixture.media.objects / (uid(33) + '.bin')).read_bytes(), original)

    def test_privacy_revocation_blocks_subsequent_photo_requests(self):
        self.fixture.lock()
        status, _, body = self.request("GET", f"/api/camino/film/photo/{self.project_id}/{uid(30)}")
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body)["message"], "Fotografie není dostupná.")

    def test_small_image_routes_keep_no_store_and_current_privacy(self):
        for kind in ('thumbnail', 'image-preview'):
            path = f'/api/camino/film/{kind}/{self.project_id}/{uid(30)}'
            status, headers, body = self.request('GET', path)
            self.assertEqual(status, 200)
            self.assertIn('no-store', headers['Cache-Control'])
            self.assertIn('private', headers['Cache-Control'])
            self.assertEqual(headers['Content-Type'], 'image/png')
            with Image.open(io.BytesIO(body)) as image:
                self.assertFalse(image.getexif())
            self.assertEqual(self.request('HEAD', path)[0], 200)
            self.assertEqual(self.request('GET', path+'?width=9000')[0], 404)
        self.fixture.lock()
        for kind in ('thumbnail', 'image-preview'):
            self.assertEqual(self.request('GET', f'/api/camino/film/{kind}/{self.project_id}/{uid(30)}')[0], 404)
