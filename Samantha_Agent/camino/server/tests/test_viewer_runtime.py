"""Optional startup and background preparation, only synthetic data and no socket."""

import argparse
import asyncio
import base64
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from camino.api import CaminoV1Contract
from camino.server.application import create_app
from camino.server.auth import RevocableTokenStore
from camino.server.main import _viewer_options, main
from camino.server.viewer import CaminoViewer
from camino.server.viewer_media import ViewerMedia
from tests.camino_viewer_fixture import ViewerFixture, synthetic_media


class ViewerStartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.f = ViewerFixture(self.root)
        self.owner = RevocableTokenStore(self.root / "owner.sqlite")
        self.owner.add("synthetic-owner-password-at-least-32", label="owner")
        self.reader = RevocableTokenStore(self.root / "reader.sqlite")
        self.reader.add("synthetic-reader-password-at-least-32", label="reader")
        self.env = {"CAMINO_VIEWER_ENABLED": "1", "CAMINO_VIEWER_AUTH_DB": str(self.reader.path),
                    "CAMINO_VIEWER_TRIP_ID": self.f.trip.id, "CAMINO_VIEWER_MEDIA_ROOT": str(self.root / "copies")}

    def options(self):
        return _viewer_options(argparse.ArgumentParser(), self.f.store, self.f.media, self.owner)

    def test_default_off_explicit_optin_and_no_privacy_mutation(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.options(), {})
        before = self.f.store.state()
        with patch.dict(os.environ, self.env, clear=True), patch("camino.server.main.shutil.which", return_value="/synthetic/ffmpeg"):
            options = self.options()
        self.assertEqual(options["viewer_interval_seconds"], 60)
        self.assertEqual(options["viewer"].tokens.path, self.reader.path)
        self.assertEqual(before, self.f.store.state())

    def test_invalid_config_never_falls_back_to_owner_credentials(self):
        cases = [{"CAMINO_VIEWER_ENABLED": "yes"}, {"CAMINO_VIEWER_AUTH_DB": str(self.owner.path)},
                 {"CAMINO_VIEWER_AUTH_DB": str(self.root / "missing.sqlite")},
                 {"CAMINO_VIEWER_TRIP_ID": "wrong"}, {"CAMINO_VIEWER_INTERVAL_SECONDS": "0"},
                 {"CAMINO_VIEWER_INTERVAL_SECONDS": "nan"}]
        for change in cases:
            with self.subTest(change=change), patch.dict(os.environ, {**self.env, **change}, clear=True):
                with self.assertRaises(SystemExit):
                    self.options()
        self.assertFalse((self.root / "missing.sqlite").exists())
        with patch.dict(os.environ, self.env, clear=True), patch("camino.server.main.shutil.which", return_value=None):
            with self.assertRaises(SystemExit):
                self.options()
        with patch.dict(os.environ, {**self.env, "CAMINO_VIEWER_AUTH_DB": str(self.root / "empty.sqlite")}, clear=True), patch("camino.server.main.shutil.which", return_value="/synthetic/ffmpeg"):
            RevocableTokenStore(self.root / "empty.sqlite")
            with self.assertRaises(SystemExit):
                self.options()

    def test_launcher_wires_worker_and_prefix_without_starting_listener(self):
        environment = {**self.env, "CAMINO_C05A_METADATA_DB": str(self.f.store.path),
                       "CAMINO_C05A_AUTH_DB": str(self.owner.path),
                       "CAMINO_C05A_MEDIA_DB": str(self.root / "media.sqlite"),
                       "CAMINO_C05A_MEDIA_ROOT": str(self.root / "originals")}
        with patch.dict(os.environ, environment, clear=True), patch("camino.server.main.shutil.which", return_value="/synthetic/ffmpeg"), patch("camino.server.main.uvicorn.run") as run:
            self.assertEqual(main(["--port", "8767", "--root-path", "/camino-api"]), 0)
        app = run.call_args.args[0]
        self.assertEqual(app.root_path, "/camino-api")
        self.assertIsNotNone(app.state.viewer_worker)
        self.assertIsNone(app.state.viewer_worker.thread)
        self.assertEqual(run.call_args.kwargs["workers"], 1)
        self.assertEqual(run.call_args.kwargs["host"], "127.0.0.1")
        self.assertFalse(run.call_args.kwargs["access_log"])

    def test_bad_media_conversion_is_bounded_and_cancelled_batch_does_no_work(self):
        asset = self.f.upload(30, "audio", b"synthetic-not-audio")
        viewer = CaminoViewer(self.f.store, self.f.media, ViewerMedia(self.root / "copies"), self.reader, self.f.trip.id)
        with patch.object(viewer.copies, "build", return_value=False) as build:
            self.assertEqual(viewer.build_pending(should_stop=lambda: True), {"ready": 0, "waiting": 0})
            build.assert_not_called()
            for _ in range(5):
                self.assertEqual(viewer.build_pending(), {"ready": 0, "waiting": 1})
            self.assertEqual(build.call_count, 3)
        self.assertEqual(viewer._conversion_failures[asset["id"]], 3)

    def test_help_and_invalid_bind_never_lock_or_migrate(self):
        with patch.dict(os.environ, {}, clear=True), patch("camino.server.main.database_lock") as lock:
            for args, code in ((["--help"], 0), (["--host", "0.0.0.0"], 2)):
                with self.assertRaises(SystemExit) as caught:
                    main(args)
                self.assertEqual(caught.exception.code, code)
            lock.assert_not_called()


class ViewerLifespanTests(unittest.IsolatedAsyncioTestCase):
    async def test_late_media_worker_restart_proxy_links_and_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payloads = synthetic_media(root)
            f = ViewerFixture(root)
            owner = RevocableTokenStore(root / "owner.sqlite")
            owner_token = "synthetic-owner-health-credential-32"
            owner.add(owner_token, label="owner")
            reader = RevocableTokenStore(root / "reader.sqlite")
            token = "synthetic-reader-credential-at-least-32"
            reader.add(token, label="reader")
            viewer = CaminoViewer(f.store, f.media, ViewerMedia(root / "copies"), reader, f.trip.id)
            app = create_app(metadata_api=CaminoV1Contract(f.store, authenticate=owner.authenticate),
                             media_store=f.media, token_store=owner, viewer=viewer,
                             viewer_interval_seconds=1, root_path="/camino-api")
            auth = {"Authorization": "Basic " + base64.b64encode(("jana:" + token).encode()).decode()}
            checked = threading.Event()
            entered, release = threading.Event(), threading.Event()
            original = viewer.build_pending
            def batch(**kwargs):
                entered.set()
                release.wait(4)
                result = original(**kwargs)
                checked.set()
                return result
            with patch.object(viewer, "build_pending", side_effect=batch):
                async with app.router.lifespan_context(app):
                    self.assertTrue(await asyncio.to_thread(entered.wait, 4))
                    try:
                        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://camino.test") as client:
                            health = await asyncio.wait_for(client.get("/camino-api/healthz", headers={"Authorization": "Bearer " + owner_token}), timeout=1)
                            self.assertEqual(health.status_code, 200)
                    finally:
                        release.set()
                    self.assertTrue(await asyncio.to_thread(checked.wait, 4))
                    asset = f.upload(30, "photo", payloads["photo"])
                    checked.clear()
                    self.assertTrue(await asyncio.to_thread(checked.wait, 4))
                    self.assertTrue(viewer.copies.ready(asset))
                    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://camino.test", headers=auth) as client:
                        page = await client.get("/camino-api/viewer/days/2026-09-25")
                        self.assertEqual(page.status_code, 200)
                        url = f'/camino-api/viewer/media/{asset["id"]}/preview.jpg'
                        self.assertIn(f'src="{url}"', page.text)
                        self.assertIn('href="/camino-api/viewer/"', page.text)
                        self.assertEqual((await client.get(url)).status_code, 200)
                        self.assertEqual((await client.get("/camino-api/viewer/", headers={"Authorization": ""})).status_code, 401)
                        f.lock()
                        self.assertEqual((await client.get(url, headers={"Range": "bytes=0-5"})).status_code, 404)
                self.assertFalse(app.state.viewer_worker.thread.is_alive())
                checked.clear()
                async with app.router.lifespan_context(app):
                    self.assertTrue(await asyncio.to_thread(checked.wait, 4))
                    self.assertEqual(f.store.viewer_snapshot(f.trip.id)["moments"], [])
                self.assertFalse(app.state.viewer_worker.thread.is_alive())

    async def test_invalid_worker_or_prefix_are_not_accepted(self):
        for options in ({"viewer_interval_seconds": 60}, {"root_path": "//evil.example"}):
            with self.assertRaises(ValueError):
                create_app(metadata_api=None, media_store=None, token_store=None, **options)
