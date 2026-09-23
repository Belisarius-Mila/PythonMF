"""FastAPI integration checks for the private C05a owner API."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import httpx

from camino.api import CaminoV1Contract
from camino.domain.codec import wire
from camino.domain.model import (
    Asset, CaptureTime, JourneyDay, MomentKind, Privacy, TimeSource, Trip, create_moment,
)
from camino.domain.revision_store import RevisionStore
from camino.server.application import create_app
from camino.server.auth import RevocableTokenStore
from camino.server.media_store import MediaStore


def uid(number: int) -> str:
    return f"00000000-0000-0000-0000-{number:012x}"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class CaminoC05aFastAPITests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir="/private/tmp")
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.token = "synthetic-c05a-owner-token-long-enough"
        self.tokens = RevocableTokenStore(root / "auth.sqlite")
        self.token_id = self.tokens.add(self.token, label="synthetic iPhone")
        self.metadata = RevisionStore(root / "metadata.sqlite")
        self.contract = CaminoV1Contract(self.metadata, authenticate=self.tokens.authenticate)
        self.content = b"fastapi-streamed-synthetic-media"
        self.asset_id = uid(4)
        self._register_manifest()
        self.media = MediaStore(
            root / "media.sqlite",
            root / "media",
            asset_lookup=self.metadata.asset,
            max_asset_bytes=1024 * 1024,
            max_chunk_bytes=8,
            reserve_bytes=0,
        )
        self.app = create_app(
            metadata_api=self.contract,
            media_store=self.media,
            token_store=self.tokens,
        )
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def request(self, method: str, path: str, **kwargs):
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="https://camino.test") as client:
            return await client.request(method, path, **kwargs)

    def _register_manifest(self) -> None:
        trip = Trip(uid(1), "Synthetic trip", "cs", True, True)
        day = JourneyDay(uid(2), trip.id, "2026-09-23")
        captured = CaptureTime(
            int(datetime(2026, 9, 23, 18, tzinfo=timezone.utc).timestamp() * 1000),
            "2026-09-23T20:00:00", 120, "Europe/Prague", TimeSource.DEVICE_CAPTURE,
        )
        moment = create_moment(
            id=uid(3), trip=trip, day=day, kind=MomentKind.COMMENT,
            captured=captured, new_moment_privacy=Privacy.DIARY,
        )
        asset = Asset(
            self.asset_id, moment.id, "audio", "recording", len(self.content), digest(self.content), 1200,
        )
        epoch = self.metadata.state()["epoch"]
        for sequence, kind, value in (
            (1, "create_trip", trip),
            (2, "create_day", day),
            (3, "create_moment", moment),
            (4, "create_asset", asset),
        ):
            body = {
                "contract_version": 1,
                "epoch": epoch,
                "operation_id": uid(100 + sequence),
                "device_id": uid(90),
                "device_sequence": sequence,
                "kind": kind,
                "expected_revision": None,
                "payload": wire(value),
            }
            raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
            response = self.contract.handle(
                "POST", "/api/v1/operations", authorization=f"Bearer {self.token}",
                body=raw, content_type="application/json",
            )
            self.assertEqual(response.status, 200, response.body)

    async def test_auth_metadata_and_revocation_are_fail_closed(self) -> None:
        self.assertEqual((await self.request("GET", "/healthz")).status_code, 401)
        state = await self.request("GET", "/api/v1/state", headers=self.headers)
        self.assertEqual(state.status_code, 200)
        self.assertEqual(state.json()["cursor"], 4)
        self.assertEqual((await self.request(
            "GET", f"/api/v1/assets/{self.asset_id}/upload-status"
        )).status_code, 401)
        self.assertTrue(self.tokens.revoke(self.token_id))
        denied = await self.request("GET", "/api/v1/state", headers=self.headers)
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(denied.json()["error"]["code"], "unauthorized")

    async def test_streamed_chunks_finalize_and_lost_response_retry(self) -> None:
        created = await self.request(
            "POST",
            f"/api/v1/assets/{self.asset_id}/upload-session",
            headers={**self.headers, "Content-Type": "application/json"},
            content=json.dumps({"contract_version": 1, "chunk_size": 8}),
        )
        self.assertEqual(created.status_code, 201, created.text)
        chunk_count = created.json()["chunk_count"]
        for index in range(chunk_count):
            chunk = self.content[index * 8:(index + 1) * 8]
            response = await self.request(
                "PUT",
                f"/api/v1/assets/{self.asset_id}/chunks/{index}",
                headers={
                    **self.headers,
                    "Content-Type": "application/octet-stream",
                    "X-Camino-Chunk-SHA256": digest(chunk),
                },
                content=chunk,
            )
            self.assertEqual(response.status_code, 201, response.text)
        status = await self.request(
            "GET",
            f"/api/v1/assets/{self.asset_id}/upload-status", headers=self.headers,
        )
        self.assertEqual(status.json()["missing_chunks"], [])
        finalized = await self.request(
            "POST",
            f"/api/v1/assets/{self.asset_id}/finalize", headers=self.headers,
        )
        repeated = await self.request(
            "POST",
            f"/api/v1/assets/{self.asset_id}/finalize", headers=self.headers,
        )
        self.assertEqual(finalized.status_code, 201, finalized.text)
        self.assertEqual(repeated.status_code, 200, repeated.text)
        self.assertTrue(finalized.json()["created"])
        self.assertFalse(repeated.json()["created"])
        for key in ("asset_id", "byte_count", "sha256", "state", "verified_at"):
            self.assertEqual(finalized.json()[key], repeated.json()[key])

    async def test_media_errors_are_stable_and_do_not_leak_paths(self) -> None:
        missing = await self.request(
            "POST",
            f"/api/v1/assets/{uid(99)}/upload-session",
            headers={**self.headers, "Content-Type": "application/json"},
            content=json.dumps({"contract_version": 1, "chunk_size": 8}),
        )
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "asset_manifest_not_found")
        self.assertNotIn(str(Path(self.temporary.name)), missing.text)
        wrong_type = await self.request(
            "POST",
            f"/api/v1/assets/{self.asset_id}/upload-session",
            headers=self.headers,
            content=b"{}",
        )
        self.assertEqual(wrong_type.status_code, 415)

    async def test_openapi_contains_only_declared_c05a_network_routes(self) -> None:
        paths = set(self.app.openapi()["paths"])
        expected = {
            "/healthz",
            "/api/v1/assets/{asset_id}/upload-session",
            "/api/v1/assets/{asset_id}/upload-status",
            "/api/v1/assets/{asset_id}/chunks/{chunk_index}",
            "/api/v1/assets/{asset_id}/finalize",
        }
        self.assertEqual(paths, expected)
        declared = json.loads(
            (Path(__file__).resolve().parents[2] / "docs" / "C05a_MEDIA_OPENAPI_V1.json").read_text()
        )
        self.assertEqual(set(declared["paths"]), expected)
        self.assertEqual(declared["servers"], [])


if __name__ == "__main__":
    unittest.main()
