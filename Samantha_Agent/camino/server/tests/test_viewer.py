"""M1 HTTP/media integration in the isolated Camino server environment."""

import base64
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from camino.api import CaminoV1Contract
from camino.server.application import create_app
from camino.server.auth import RevocableTokenStore
from camino.server.viewer import CaminoViewer
from camino.server.viewer_media import ViewerMedia
from tests.camino_viewer_fixture import ViewerFixture, synthetic_media, uid


class ViewerHTTPTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_tmp = tempfile.TemporaryDirectory()
        cls.payloads = synthetic_media(Path(cls.media_tmp.name))

    @classmethod
    def tearDownClass(cls):
        cls.media_tmp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.f = ViewerFixture(self.root)
        self.owner_token = "synthetic-owner-credential-at-least-32"
        self.reader_token = "synthetic-reader-credential-at-least-32"
        self.owner = RevocableTokenStore(self.root / "owner.sqlite")
        self.reader = RevocableTokenStore(self.root / "reader.sqlite")
        self.owner.add(self.owner_token, label="synthetic owner")
        self.reader_id = self.reader.add(self.reader_token, label="synthetic Jana")
        self.viewer = CaminoViewer(self.f.store, self.f.media, ViewerMedia(self.root / "copies"), self.reader, self.f.trip.id)
        self.app = create_app(metadata_api=CaminoV1Contract(self.f.store, authenticate=self.owner.authenticate),
                              media_store=self.f.media, token_store=self.owner, viewer=self.viewer)
        self.auth = {"Authorization": "Basic " + base64.b64encode(("jana:" + self.reader_token).encode()).decode()}

    async def request(self, path, *, method="GET", headers=None):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="https://camino.test") as c:
            return await c.request(method, path, headers=self.auth if headers is None else headers)

    def upload_media(self):
        return {k: self.f.upload(30 + i, k, v) for i, (k, v) in enumerate(self.payloads.items())}

    async def test_auth_is_separate_revocable_and_no_content_writes(self):
        for path in ("/viewer/", "/viewer/days/2026-09-25", f"/viewer/media/{uid(30)}/preview.jpg"):
            self.assertEqual((await self.request(path, headers={})).status_code, 401)
            self.assertEqual((await self.request(path, headers={"Authorization": "Bearer " + self.owner_token})).status_code, 401)
        self.assertEqual((await self.request("/api/v1/state")).status_code, 401)
        wrong_basic = base64.b64encode(("jana:" + self.owner_token).encode()).decode()
        self.assertEqual((await self.request("/viewer/", headers={"Authorization": "Basic " + wrong_basic})).status_code, 401)
        self.assertEqual((await self.request("/viewer/", headers={"Authorization": "Basic !!!"})).status_code, 401)
        self.assertEqual((await self.request("/viewer/", method="POST")).status_code, 405)
        self.reader.revoke(self.reader_id)
        self.assertEqual((await self.request("/viewer/")).status_code, 401)

    async def test_html_escapes_text_and_does_not_leak_private_data(self):
        page = await self.request("/viewer/days/2026-09-25")
        self.assertEqual(page.status_code, 200)
        self.assertIn("&lt;script&gt;", page.text)
        self.assertNotIn("<script>", page.text)
        self.assertNotIn("TAJNA", page.text)
        self.assertNotIn(self.f.private.id, page.text)
        self.assertIn("no-store", page.headers["cache-control"])
        self.assertIn("frame-ancestors 'none'", page.headers["content-security-policy"])
        self.assertEqual((await self.request("/viewer/days/2020-01-01")).status_code, 404)

    async def test_real_derivatives_playable_ranges_metadata_and_originals_unchanged(self):
        assets = self.upload_media()
        self.assertEqual(self.viewer.build_pending(), {"ready": 3, "waiting": 0})
        self.assertEqual(self.viewer.build_pending(), {"ready": 3, "waiting": 0})
        page = await self.request("/viewer/days/2026-09-25")
        for tag in ("<img", "<audio", "<video"):
            self.assertIn(tag, page.text)
        for kind, asset in assets.items():
            original = self.f.media.verified_source(asset["id"])
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), asset["sha256"])
            for name, path in self.viewer.copies.ready(asset).items():
                url = f'/viewer/media/{asset["id"]}/{name}'
                response = await self.request(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, path.read_bytes())
                partial = await self.request(url, headers={**self.auth, "Range": "bytes=0-15"})
                self.assertEqual(partial.status_code, 206)
                self.assertEqual(partial.content, response.content[:16])
                self.assertEqual((await self.request(url, method="HEAD")).content, b"")
                probe = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], capture_output=True, check=True)
                info = json.loads(probe.stdout)
                self.assertTrue(info["streams"])
                tags = json.dumps([info.get("format", {}).get("tags", {}),
                                   *[s.get("tags", {}) for s in info["streams"]]]).lower()
                self.assertNotIn("private-exif", tags)
                self.assertNotIn("location", tags)
        self.assertFalse(any(self.viewer.copies.root.glob("pending-*")))

    async def test_lock_denies_old_html_media_head_and_range(self):
        asset = self.f.upload(30, "photo", self.payloads["photo"])
        self.viewer.build_pending()
        url = f'/viewer/media/{asset["id"]}/preview.jpg'
        self.assertEqual((await self.request(url)).status_code, 200)
        self.f.lock()
        self.assertEqual((await self.request("/viewer/days/2026-09-25")).status_code, 404)
        for method in ("GET", "HEAD"):
            self.assertEqual((await self.request(url, method=method, headers={**self.auth, "Range": "bytes=0-15"})).status_code, 404)
        self.assertTrue(self.viewer.copies.ready(asset))  # private copy retained, access revoked

    async def test_private_and_incomplete_media_never_generated_or_served(self):
        secret = self.f.upload(30, "photo", self.payloads["photo"], private=True)
        waiting = self.f.upload(31, "video", self.payloads["video"], complete=False)
        self.assertEqual(self.viewer.build_pending(), {"ready": 0, "waiting": 1})
        self.assertEqual(list(self.viewer.copies.root.iterdir()), [])
        for a, n in ((secret, "preview.jpg"), (waiting, "clip.mp4")):
            self.assertEqual((await self.request(f'/viewer/media/{a["id"]}/{n}')).status_code, 404)

    async def test_failed_conversion_and_tampered_cache_fail_closed(self):
        asset = self.f.upload(30, "photo", self.payloads["photo"])
        with patch("camino.server.viewer_media.subprocess.run", side_effect=OSError("synthetic failure")):
            self.assertEqual(self.viewer.build_pending()["waiting"], 1)
        self.assertIn("zatím není připravené", (await self.request("/viewer/days/2026-09-25")).text)
        self.viewer.build_pending()
        path = self.viewer.copies.ready(asset)["preview.jpg"]
        raw = path.read_bytes()
        path.write_bytes(b"!" + raw[1:])
        self.assertEqual((await self.request(f'/viewer/media/{asset["id"]}/preview.jpg')).status_code, 404)

    async def test_restore_and_symlink_do_not_reveal_media(self):
        asset = self.f.upload(30, "audio", self.payloads["audio"])
        self.viewer.build_pending()
        self.f.store.rotate_epoch_for_restore()
        self.assertEqual((await self.request(f'/viewer/media/{asset["id"]}/audio.m4a')).status_code, 404)
        self.assertNotIn("Dnes začíná", (await self.request("/viewer/")).text)
        link = self.root / "linked-copies"
        link.symlink_to(self.viewer.copies.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            ViewerMedia(link)


if __name__ == "__main__":
    unittest.main()
