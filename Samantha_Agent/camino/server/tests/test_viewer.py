"""M1 HTTP/media integration in the isolated Camino server environment."""

import base64
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from html.parser import HTMLParser
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import httpx

from camino.api import CaminoV1Contract
from camino.domain.model import LocationFix, Privacy
from camino.server.application import create_app
from camino.server.auth import RevocableTokenStore
from camino.server.viewer import CaminoViewer
from camino.server.viewer_media import ViewerMedia
from tests.camino_viewer_fixture import ViewerFixture, synthetic_media, uid
from tests.test_camino_audio_layout import layout


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

    async def test_route_endpoints_reader_auth_headers_and_live_revoke(self):
        paths = ['/viewer/map', '/viewer/map-data', '/viewer/map-assets/map.js',
                 '/viewer/map-assets/map.css', '/viewer/map-assets/leaflet.js', '/viewer/map-assets/leaflet.css']
        for path in paths:
            for headers in ({}, {"Authorization": "Bearer " + self.owner_token}):
                self.assertEqual((await self.request(path, headers=headers)).status_code, 401)
            response = await self.request(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn('no-store', response.headers['cache-control'])
        self.assertEqual((await self.request('/viewer/map-assets/LICENSE.txt')).status_code, 404)
        page = await self.request('/viewer/map')
        self.assertEqual(page.headers['referrer-policy'], 'origin')
        self.assertIn('https://tile.openstreetmap.org', page.headers['content-security-policy'])
        diary = await self.request('/viewer/')
        self.assertEqual(diary.headers['referrer-policy'], 'no-referrer')
        self.assertNotIn('tile.openstreetmap', diary.headers['content-security-policy'])
        m = self.f.moment(70, Privacy.DIARY, location=LocationFix(0, 0, self.f.capture.utc_ms, 8))
        self.assertEqual(len((await self.request('/viewer/map-data')).json()['points']), 1)
        self.f.send('update_metadata', {'moment_id': m.id, 'change': {'type': 'hidden', 'hidden': True}}, expected=1)
        self.assertEqual((await self.request('/viewer/map-data')).json(), {'points': []})
        self.reader.revoke(self.reader_id)
        for path in paths:
            self.assertEqual((await self.request(path)).status_code, 401)

    async def test_route_proxy_prefix_and_diary_anchor(self):
        self.f.moment(70, Privacy.DIARY, location=LocationFix(0, 0, self.f.capture.utc_ms, 8))
        transport = httpx.ASGITransport(app=self.app, root_path='/camino-api')
        async with httpx.AsyncClient(transport=transport, base_url='https://camino.test', headers=self.auth) as client:
            page = await client.get('/viewer/map')
            self.assertIn('data-map-url="/camino-api/viewer/map-data"', page.text)
            point = (await client.get('/viewer/map-data')).json()['points'][0]
            self.assertEqual(point['href'], f'/camino-api/viewer/days/2026-09-25#moment-{uid(70)}')
            diary = await client.get('/viewer/days/2026-09-25')
            self.assertIn(f'id="moment-{uid(70)}"', diary.text)

    async def test_title_api_retry_html_escaping_and_reader_cannot_edit(self):
        title = 'Káva <script>alert("x")</script> 🥾'
        body = {"contract_version": 1, "epoch": self.f.store.state()["epoch"],
                "operation_id": uid(850), "device_id": uid(90),
                "device_sequence": self.f.sequence + 1, "kind": "update_metadata",
                "expected_revision": 1, "payload": {"moment_id": self.f.public.id,
                "change": {"type": "title", "title": title}}}
        raw = json.dumps(body, sort_keys=True).encode()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="https://camino.test") as client:
            forbidden = await client.post("/api/v1/operations", content=raw, headers=self.auth)
            self.assertEqual(forbidden.status_code, 401)
            headers = {"Authorization": f"Bearer {self.owner_token}", "Content-Type": "application/json"}
            for _ in range(2):
                response = await client.post("/api/v1/operations", content=raw, headers=headers)
                self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.f.store.moment(self.f.public.id)["revision"], 2)
        self.f.sequence += 1
        html = (await self.request("/viewer/days/2026-09-25")).text
        self.assertIn('Káva &lt;script&gt;', html)
        self.assertNotIn('<script>alert("x")</script>', html)
        self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
            "type": "privacy", "new_privacy": "owner_only", "user_action": "lock"}}, expected=2)
        self.assertNotIn("Káva", (await self.request("/viewer/")).text)

    async def test_attachment_api_retry_collapsed_cards_names_counts_and_chronology(self):
        from dataclasses import replace
        from camino.domain.codec import wire
        self.f.upload(30, "photo", self.payloads["photo"])
        for n in (31, 32):
            self.f.upload(n, "audio", self.payloads["audio"])
        self.f.send("create_audio_layout", layout(50, [31, 32]))
        title = 'Most <script>bad()</script> "🥾"'
        for revision, (kind, target, name) in enumerate([
            ("asset", 30, title), ("audio_session", 50, "Celý komentář")
        ], 1):
            body = {"contract_version": 1, "epoch": self.f.store.state()["epoch"],
                    "operation_id": uid(850 + revision), "device_id": uid(90),
                    "device_sequence": self.f.sequence + 1, "kind": "update_metadata",
                    "expected_revision": revision, "payload": {"moment_id": self.f.public.id,
                    "change": {"type": "attachment_title", "attachment": {
                        "kind": kind, "target_id": uid(target), "title": name}}}}
            raw = json.dumps(body, sort_keys=True).encode()
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="https://camino.test") as client:
                self.assertEqual((await client.post("/api/v1/operations", content=raw, headers=self.auth)).status_code, 401)
                for _ in range(2):
                    response = await client.post("/api/v1/operations", content=raw, headers={
                        "Authorization": f"Bearer {self.owner_token}", "Content-Type": "application/json"})
                    self.assertEqual(response.status_code, 200, response.text)
            self.f.sequence += 1
        later = replace(self.f.public, id=uid(70), title="Večerní okamžik",
                        captured=replace(self.f.capture, utc_ms=self.f.capture.utc_ms + 3600000,
                                         local_wall="2026-09-25T11:00:00"))
        self.f.send("create_moment", wire(later))
        self.viewer.build_pending()
        page = (await self.request("/viewer/days/2026-09-25")).text
        self.assertEqual(page.count('<details>'), 2)
        self.assertNotIn('<details open', page)
        self.assertIn('Foto: 1 · Audio: 1', page)  # Two segments remain one comment.
        self.assertIn('Most &lt;script&gt;', page)
        self.assertNotIn('<script>bad()', page)
        self.assertEqual(page.count('<h3>Celý komentář</h3>'), 1)
        self.assertLess(page.index('10:00'), page.index('Večerní okamžik'))
        self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
            "type": "hidden", "hidden": True}}, expected=3)
        hidden = (await self.request("/viewer/days/2026-09-25")).text
        self.assertNotIn('Celý komentář', hidden)
        self.assertNotIn('Most &lt;script&gt;', hidden)
        self.assertNotIn('Foto: 1', hidden)
        self.assertEqual((await self.request(f'/viewer/media/{uid(30)}/preview.jpg')).status_code, 404)

    async def test_offline_trip_revoke_closes_old_media_url_without_rewriting_trip(self):
        asset = self.f.upload(30, "photo", self.payloads["photo"])
        self.viewer.build_pending()
        url = f"/viewer/media/{asset['id']}/preview.jpg"
        self.assertEqual((await self.request(url)).status_code, 200)
        self.f.store.set_viewer_permission(self.f.trip.id, enabled=False)
        self.assertEqual((await self.request(url)).status_code, 404)
        self.assertNotIn("2026-09-25", (await self.request("/viewer/")).text)
        self.f.store.set_viewer_permission(self.f.trip.id, enabled=True)
        self.assertEqual((await self.request(url)).status_code, 200)
        self.f.lock()
        self.assertEqual((await self.request(url)).status_code, 404)

    async def test_recorded_audio_order_pause_and_private_layout(self):
        for n in (30, 31, 32):
            self.f.upload(n, "audio", self.payloads["audio"])
        self.f.upload(40, "audio", self.payloads["audio"], private=True)
        self.f.send("create_audio_layout", layout(51, [31], session=50, previous=50, gap=12_345, missing=True))
        self.f.send("create_audio_layout", layout(50, [32, 30]))
        self.f.send("create_audio_layout", layout(60, [40], moment=4))
        self.assertEqual(self.viewer.build_pending(), {"ready": 3, "waiting": 0})
        page = await self.request("/viewer/days/2026-09-25")
        self.assertEqual(page.status_code, 200)
        positions = [page.text.index(f'id="audio-{uid(n)}"') for n in (32, 30, 31)]
        self.assertEqual(positions, sorted(positions))
        self.assertIn(f'id="audio-{uid(32)}" data-next="audio-{uid(30)}"', page.text)
        self.assertNotIn(f'id="audio-{uid(30)}" data-next=', page.text)
        self.assertIn("12.345 s", page.text)
        self.assertIn("Konec této části není úplný", page.text)
        self.assertNotIn(uid(40), page.text)
        self.assertNotIn(uid(60), page.text)
        self.assertEqual((await self.request("/viewer/player.js", headers={})).status_code, 401)
        script = await self.request("/viewer/player.js")
        self.assertEqual(script.status_code, 200)
        self.assertIn("script-src 'self'", page.headers["content-security-policy"])
        self.f.lock()
        for n in (30, 31, 32):
            self.assertEqual((await self.request(f"/viewer/media/{uid(n)}/audio.m4a")).status_code, 404)

    async def test_pending_middle_segment_is_not_skipped_and_late_upload_restores_chain(self):
        for n in (30, 31, 32):
            self.f.upload(n, "audio", self.payloads["audio"], complete=n != 30)
        self.f.send("create_audio_layout", layout(50, [32, 30, 31]))
        self.assertEqual(self.viewer.build_pending(), {"ready": 2, "waiting": 1})
        page = await self.request("/viewer/days/2026-09-25")
        self.assertNotIn(f'id="audio-{uid(32)}" data-next=', page.text)
        self.assertIn("úsek 2: čeká", page.text)
        self.f.upload(30, "audio", self.payloads["audio"])
        self.assertEqual(self.viewer.build_pending(), {"ready": 3, "waiting": 0})
        page = await self.request("/viewer/days/2026-09-25")
        self.assertIn(f'id="audio-{uid(32)}" data-next="audio-{uid(30)}"', page.text)
        self.assertIn(f'id="audio-{uid(30)}" data-next="audio-{uid(31)}"', page.text)

    async def test_missing_predecessor_and_segment_hole_are_explicit_no_false_continuity(self):
        for n in (30, 31):
            self.f.upload(n, "audio", self.payloads["audio"])
        value = layout(51, [30, 31], session=50, previous=50)
        value["parts"][1].update(index=2, discontinuity_before=True)
        self.f.send("create_audio_layout", value)
        self.viewer.build_pending()
        page = await self.request("/viewer/days/2026-09-25")
        self.assertIn("návaznost není ověřená", page.text)
        self.assertIn("Pauza před pokračováním: délka neznámá", page.text)
        self.assertIn("Zde chybí úsek nahrávky", page.text)
        self.assertNotIn("data-next=", page.text)

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

    async def test_map_link_is_click_only_allowlisted_and_has_no_referrer_or_credentials(self):
        self.f.moment(70, Privacy.DIARY,
                      location=LocationFix(12.25, 34.5, self.f.capture.utc_ms, 150))
        self.f.moment(71, Privacy.OWNER_ONLY,
                      location=LocationFix(66.123456, 77.654321, self.f.capture.utc_ms, 5))
        page = await self.request("/viewer/days/2026-09-25")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.headers["referrer-policy"], "no-referrer")
        self.assertEqual(page.headers["x-dns-prefetch-control"], "off")
        self.assertIn("Přibližná poloha", page.text)
        self.assertIn("±150 m", page.text)
        self.assertIn("Kliknutím předáš tento bod Apple Mapám", page.text)
        tags = []
        class Parser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                tags.append((tag, dict(attrs)))
        Parser().feed(page.text)
        external = [(tag, attrs) for tag, attrs in tags
                    if any(value and "maps.apple.com" in value for value in attrs.values())]
        self.assertEqual(len(external), 1)
        tag, attrs = external[0]
        self.assertEqual(tag, "a")
        self.assertEqual(attrs["rel"], "noopener noreferrer")
        self.assertEqual(attrs["referrerpolicy"], "no-referrer")
        self.assertEqual(attrs["target"], "_blank")
        url = urlsplit(attrs["href"])
        self.assertEqual((url.scheme, url.netloc), ("https", "maps.apple.com"))
        self.assertEqual(parse_qs(url.query), {"ll": ["12.250000,34.500000"], "q": ["Místo záznamu"]})
        for secret in ("66.123456", "77.654321", self.owner_token, self.reader_token, uid(71)):
            self.assertNotIn(secret, page.text)
        self.assertNotIn("maps.apple.com", (await self.request("/viewer/")).text)
        self.assertNotIn("maps.apple.com", (await self.request("/viewer/days/2026-09-25", headers={})).text)

    async def test_map_link_disappears_on_new_lock_hidden_revision_and_revocation(self):
        moment = self.f.moment(70, Privacy.DIARY,
                               location=LocationFix(12.25, 34.5, self.f.capture.utc_ms, 8))
        path = "/viewer/days/2026-09-25"
        self.assertIn("±8 m", (await self.request(path)).text)
        changes = [("privacy", {"new_privacy": "owner_only", "user_action": "lock"}),
                   ("privacy", {"new_privacy": "diary", "user_action": "unlock"}),
                   ("hidden", {"hidden": True})]
        for revision, (kind, fields) in enumerate(changes, 1):
            self.f.send("update_metadata", {"moment_id": moment.id,
                        "change": {"type": kind, **fields}}, expected=revision)
            html = (await self.request(path)).text
            self.assertEqual("maps.apple.com" in html, revision == 2)
        self.f.store.set_viewer_permission(self.f.trip.id, enabled=False)
        self.assertNotIn("maps.apple.com", (await self.request(path)).text)
        self.reader.revoke(self.reader_id)
        self.assertEqual((await self.request(path)).status_code, 401)

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

    async def test_photo_video_media_use_two_column_grid_and_wrapped_titles(self):
        photo = self.f.upload(30, "photo", self.payloads["photo"])
        video_one = self.f.upload(31, "video", self.payloads["video"])
        video_two = self.f.upload(32, "video", self.payloads["video"])
        photo_two = self.f.upload(33, "photo", self.payloads["photo"])
        self.assertEqual(self.viewer.build_pending(), {"ready": 4, "waiting": 0})
        long_title = "Dlouhý název fotografie, který se musí v mřížce zalomit na další řádek"
        revision = self.f.store.moment(self.f.public.id)["revision"]
        self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
            "type": "attachment_title", "attachment": {
                "kind": "asset", "target_id": photo["id"], "title": long_title
            }}}, expected=revision)
        page = (await self.request("/viewer/days/2026-09-25")).text
        self.assertIn('class="media-grid" aria-label="Fotografie a videa"', page)
        self.assertEqual(page.count('class="media-tile"'), 4)
        self.assertEqual(page.count('class="media-title"'), 4)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", page)
        self.assertIn("overflow-wrap:anywhere", page)
        self.assertIn("Dlouhý název fotografie, který se musí v mřížce zalomit", page)
        for asset in (video_one, video_two, photo_two):
            self.assertIn(asset["id"], page)

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
