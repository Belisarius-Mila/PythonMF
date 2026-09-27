"""Synthetic GPS contract: actual Swift envelope -> owner API -> durable archive.

Run with the isolated Camino server environment, like test_application.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import httpx

from camino.api import CaminoV1Contract
from camino.domain.revision_store import RevisionStore
from camino.server.application import create_app
from camino.server.auth import RevocableTokenStore
from camino.server.media_store import MediaStore
from camino.server.tests import test_application as api_fixture

uid = api_fixture.uid


class GPSAPITests(unittest.IsolatedAsyncioTestCase):
    setUp = api_fixture.CaminoC05aFastAPITests.setUp
    request = api_fixture.CaminoC05aFastAPITests.request
    _register_manifest = api_fixture.CaminoC05aFastAPITests._register_manifest

    async def test_invalid_and_stale_gps_cannot_enter_archive(self):
        moment = dict(self.metadata.moment(uid(3)))
        moment["id"] = uid(800)
        point = {"latitude": 12.25, "longitude": 34.5,
                 "measured_at_utc_ms": moment["captured"]["utc_ms"],
                 "horizontal_accuracy_m": 8.0}
        for change in ({"latitude": 91}, {"longitude": -181}, {"horizontal_accuracy_m": -1},
                       {"measured_at_utc_ms": point["measured_at_utc_ms"] - 120_001},
                       {"measured_at_utc_ms": point["measured_at_utc_ms"] + 1}):
            with self.subTest(change=change):
                body = {"contract_version": 1, "epoch": self.metadata.state()["epoch"],
                        "operation_id": uid(801), "device_id": uid(90), "device_sequence": 5,
                        "kind": "create_moment", "expected_revision": None,
                        "payload": {**moment, "location": {**point, **change}}}
                response = await self.request("POST", "/api/v1/operations", json=body, headers=self.headers)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(self.metadata.state()["cursor"], 4)

    async def test_gps_roundtrip_retry_and_reopen(self):
        moment = dict(self.metadata.moment(uid(3)))
        moment["id"] = uid(700)
        point = {"latitude": 12.25, "longitude": 34.5,
                 "measured_at_utc_ms": moment["captured"]["utc_ms"],
                 "horizontal_accuracy_m": 150.0}
        moment["location"] = point
        body = {"contract_version": 1, "epoch": self.metadata.state()["epoch"],
                "operation_id": uid(701), "device_id": uid(90), "device_sequence": 5,
                "kind": "create_moment", "expected_revision": None, "payload": moment}
        raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        headers = {**self.headers, "Content-Type": "application/json"}
        for _ in range(2):
            response = await self.request("POST", "/api/v1/operations", content=raw, headers=headers)
            self.assertEqual(response.status_code, 200, response.text)
        reopened = RevisionStore(Path(self.temporary.name) / "metadata.sqlite")
        self.assertEqual(reopened.moment(uid(700))["location"], point)
        self.assertEqual(reopened.state()["cursor"], 5)
        self.assertIsNone(reopened.moment(uid(3))["location"])
        reopened.set_viewer_permission(uid(1), enabled=True)  # Isolated synthetic DB only.
        projection = reopened.viewer_snapshot(uid(1))["moments"]
        self.assertEqual(len(projection), 2)
        for projected in projection:
            self.assertNotIn("location", projected)
            if projected["id"] == uid(700):
                self.assertEqual(projected["map_point"],
                                 {"latitude": 12.25, "longitude": 34.5, "accuracy_m": 150.0})
            else:
                self.assertIsNone(projected["map_point"])


class SwiftTitleWireTests(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(os.environ.get("CAMINO_TITLE_WIRE_FIXTURE"), "optional generated Swift title fixture")
    async def test_actual_swift_titles_retry_reopen_and_viewer(self):
        envelopes = json.loads(Path(os.environ["CAMINO_TITLE_WIRE_FIXTURE"]).read_text())
        with tempfile.TemporaryDirectory(prefix="camino-title-api-") as directory:
            root = Path(directory)
            metadata = RevisionStore(root / "metadata.sqlite")
            tokens = RevocableTokenStore(root / "auth.sqlite")
            token = "synthetic-title-owner-token-at-least-32"
            tokens.add(token, label="synthetic")
            media = MediaStore(root / "media.sqlite", root / "media", asset_lookup=metadata.asset,
                               reserve_bytes=0)
            app = create_app(metadata_api=CaminoV1Contract(metadata, tokens.authenticate),
                             media_store=media, token_store=tokens)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://synthetic.test") as client:
                for envelope in envelopes:
                    envelope["epoch"] = metadata.state()["epoch"]
                    raw = json.dumps(envelope, sort_keys=True, ensure_ascii=False).encode()
                    for _ in range(2):
                        response = await client.post("/api/v1/operations", content=raw,
                            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
                        self.assertEqual(response.status_code, 200, response.text)
            reopened = RevisionStore(root / "metadata.sqlite")
            moment = next(e["payload"] for e in envelopes if e["kind"] == "create_moment")
            self.assertNotIn("title", moment)
            self.assertEqual(reopened.moment(moment["id"])["title"], "Opravený název")
            self.assertEqual(reopened.moment(moment["id"])["revision"], 3)
            reopened.set_viewer_permission(moment["trip_id"], enabled=True)
            self.assertEqual(reopened.viewer_snapshot(moment["trip_id"])["moments"][0]["title"], "Opravený název")


class SwiftGPSWireTests(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(os.environ.get("CAMINO_GPS_WIRE_FIXTURE"), "optional generated Swift wire fixture")
    async def test_actual_swift_envelopes(self):
        envelopes = json.loads(Path(os.environ["CAMINO_GPS_WIRE_FIXTURE"]).read_text())
        with tempfile.TemporaryDirectory(prefix="camino-gps-api-") as directory:
            root = Path(directory)
            metadata = RevisionStore(root / "metadata.sqlite")
            tokens = RevocableTokenStore(root / "auth.sqlite")
            token = "synthetic-gps-only-owner-token-long-enough"
            tokens.add(token, label="synthetic")
            media = MediaStore(root / "media.sqlite", root / "media", asset_lookup=metadata.asset,
                               reserve_bytes=0)
            app = create_app(metadata_api=CaminoV1Contract(metadata, tokens.authenticate),
                             media_store=media, token_store=tokens)
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="https://synthetic.test") as client:
                for envelope in envelopes:
                    # Only transport epoch changes to this isolated recipient; payload is Swift's.
                    envelope["epoch"] = metadata.state()["epoch"]
                    raw = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()
                    for _ in range(2):
                        response = await client.post("/api/v1/operations", content=raw,
                            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
                        self.assertEqual(response.status_code, 200, response.text)
                reopened = RevisionStore(root / "metadata.sqlite")
                moments = [item["payload"] for item in envelopes if item["kind"] == "create_moment"]
                self.assertEqual(len(moments), 2)
                self.assertEqual(sum(item["location"] is not None for item in moments), 1)
                for moment in moments:
                    self.assertEqual(reopened.moment(moment["id"])["location"], moment["location"])
                self.assertEqual(reopened.state()["cursor"], len(envelopes))
