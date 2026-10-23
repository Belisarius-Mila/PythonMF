"""FastAPI integration checks for the private C05a owner API."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

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
from camino.film.closed_day import ClosedDayStore


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

    async def test_project_catalog_is_owner_only_and_defaults_to_existing_trip(self):
        path = "/api/v1/projects"
        self.assertEqual((await self.request("GET", path)).status_code, 401)
        response = await self.request("GET", path, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        project = response.json()["projects"][0]
        self.assertEqual(project["id"], uid(1))
        self.assertEqual(project["status"], "active")
        self.assertIsNone(project["end_date"])
        detail = await self.request("GET", path + "/" + uid(1), headers=self.headers)
        self.assertEqual(detail.json()["project"], project)
        state = await self.request("GET", "/api/v1/state", headers=self.headers)
        self.assertIn("project_details_v1", state.json()["features"])

    async def test_closed_day_requires_phone_inventory_and_verified_private_originals(self):
        video = b"synthetic-video-bytes"
        private_audio = b"synthetic-private-audio"
        trip = Trip(uid(1), "Synthetic trip", "cs", True, True)
        day = JourneyDay(uid(2), trip.id, "2026-09-23")
        captured = CaptureTime(
            int(datetime(2026, 9, 23, 19, tzinfo=timezone.utc).timestamp() * 1000),
            "2026-09-23T21:00:00", 120, "Europe/Prague", TimeSource.DEVICE_CAPTURE,
        )
        reflection = create_moment(id=uid(6), trip=trip, day=day,
                                   kind=MomentKind.REFLECTION, captured=captured,
                                   new_moment_privacy=Privacy.OWNER_ONLY)
        operations = (
            (5, "create_asset", Asset(uid(5), uid(3), "video", "camera",
                                      len(video), digest(video), 2500)),
            (6, "create_moment", reflection),
            (7, "create_asset", Asset(uid(7), uid(6), "audio", "recording",
                                      len(private_audio), digest(private_audio), 1000)),
        )
        epoch = self.metadata.state()["epoch"]
        for sequence, kind, value in operations:
            envelope = {
                "contract_version": 1, "epoch": epoch,
                "operation_id": uid(100 + sequence), "device_id": uid(90),
                "device_sequence": sequence, "kind": kind,
                "expected_revision": None, "payload": wire(value),
            }
            raw = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()
            accepted = self.contract.handle(
                "POST", "/api/v1/operations", authorization=f"Bearer {self.token}",
                body=raw, content_type="application/json")
            self.assertEqual(accepted.status, 200, accepted.body)
        film = ClosedDayStore(Path(self.temporary.name) / "film-projects", self.metadata, self.media)
        self.app = create_app(metadata_api=self.contract, media_store=self.media,
                              token_store=self.tokens, closed_day_store=film)
        state = await self.request("GET", "/api/v1/state", headers=self.headers)
        self.assertIn("film_closed_day_v1", state.json()["features"])
        proof = {
            "contract_version": 1, "request_id": uid(99), "trip_id": uid(1),
            "day_id": uid(2), "device_id": uid(90),
            "server_id": state.json()["server_id"], "epoch": epoch,
            "cursor": 7, "pending_metadata": 0, "pending_media": 0,
            "active_uploads": 0,
        }
        with self.metadata._connection() as connection:
            proof["moments"] = [
                {key: row[key] for key in ("id", "revision", "privacy", "hidden", "chapter_date")}
                for (body,) in connection.execute("SELECT body FROM moments")
                for row in [json.loads(body)]
            ]
            proof["assets"] = [
                {key: row[key] for key in ("id", "moment_id", "media_kind", "byte_count", "sha256")}
                for (body,) in connection.execute("SELECT body FROM assets")
                for row in [json.loads(body)]
            ]
        route = "/api/v1/film/closed-days"
        headers = {**self.headers, "Content-Type": "application/json"}
        self.assertEqual((await self.request("POST", route, json=proof)).status_code, 401)
        pending = {**proof, "pending_media": 1}
        self.assertEqual((await self.request("POST", route, headers=headers, json=pending)).status_code, 409)
        unverified = await self.request("POST", route, headers=headers, json=proof)
        self.assertEqual(unverified.json()["error"]["code"], "media_missing")
        for asset_id, content in ((self.asset_id, self.content), (uid(5), video), (uid(7), private_audio)):
            created = await self.request("POST", f"/api/v1/assets/{asset_id}/upload-session",
                                         headers=headers, json={"contract_version": 1, "chunk_size": 8})
            self.assertEqual(created.status_code, 201, created.text)
            for index in range(created.json()["chunk_count"]):
                chunk = content[index * 8:(index + 1) * 8]
                sent = await self.request("PUT", f"/api/v1/assets/{asset_id}/chunks/{index}",
                                          headers={**self.headers,
                                                   "Content-Type": "application/octet-stream",
                                                   "X-Camino-Chunk-SHA256": digest(chunk)}, content=chunk)
                self.assertEqual(sent.status_code, 201, sent.text)
            finalized = await self.request("POST", f"/api/v1/assets/{asset_id}/finalize",
                                           headers=self.headers)
            self.assertEqual(finalized.status_code, 201, finalized.text)
        first = await self.request("POST", route, headers=headers, json=proof)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual((first.json()["source_count"], first.json()["shot_count"],
                          first.json()["voice_choice_count"]), (2, 1, 1))
        self.assertEqual((await self.request("POST", route, headers=headers, json=proof)).json(), first.json())
        status_path = f"/api/v1/film/projects/{proof['request_id']}"
        self.assertTrue((await self.request("GET", status_path, headers=self.headers)).json()["valid"])
        reopened = ClosedDayStore(film.root, self.metadata, self.media)
        self.assertTrue(reopened.status(proof["request_id"])["valid"])
        project = json.loads((film.root / proof["request_id"] / "project-r1.json").read_text())
        manifest = json.loads((film.root / proof["request_id"] / "manifest.json").read_text())
        self.assertEqual(project["shots"][0]["asset_id"], uid(5))
        self.assertEqual((project["shots"][0]["in_ms"], project["shots"][0]["out_ms"]),
                         (0, 2500))
        self.assertEqual({row["asset_id"] for row in manifest["sources"]}, {uid(4), uid(5)})
        changed = {**proof, "request_id": uid(98), "assets": proof["assets"][:-1]}
        mismatch = await self.request("POST", route, headers=headers, json=changed)
        self.assertEqual(mismatch.json()["error"]["code"], "asset_mismatch")
        with self.metadata._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = json.loads(connection.execute(
                "SELECT body FROM moments WHERE id=?", (uid(3),)).fetchone()[0])
            row["privacy"] = "owner_only"
            row["revision"] += 1
            connection.execute("UPDATE moments SET revision=?,body=? WHERE id=?",
                               (row["revision"], json.dumps(row), uid(3)))
            connection.commit()
        stale = await self.request("GET", status_path, headers=self.headers)
        self.assertEqual(stale.json()["reason"], "day_inventory_changed")
        self.assertFalse(stale.json()["valid"])
        retry = await self.request("POST", route, headers=headers, json=proof)
        self.assertEqual(retry.json()["error"]["code"], "closed_day_stale")

    async def test_recovery_is_owner_only_and_requires_complete_media(self):
        from tests.test_camino_recovery import proof_for
        self.metadata.rotate_epoch_for_restore()
        proof = proof_for(self.metadata)
        route = "/api/v1/recovery/complete"
        response = await self.request("POST", route, json=proof)
        self.assertEqual(response.status_code, 401)
        response = await self.request("POST", route, json=proof, headers=self.headers)
        self.assertEqual(response.status_code, 409)
        self.assertTrue(self.metadata.state()["exports_blocked"])
        state = await self.request("GET", "/api/v1/state", headers=self.headers)
        self.assertIn("identical_recovery_v1", state.json()["features"])
        # No assets required after creating an independent metadata-only fixture.
        from tests.camino_viewer_fixture import ViewerFixture
        other = Path(self.temporary.name) / "metadata-only"
        other.mkdir()
        fixture = ViewerFixture(other)
        fixture.store.rotate_epoch_for_restore()
        self.app = create_app(metadata_api=CaminoV1Contract(fixture.store, self.tokens.authenticate),
                              media_store=fixture.media, token_store=self.tokens)
        proof = proof_for(fixture.store)
        first = await self.request("POST", route, json=proof, headers=self.headers)
        second = await self.request("POST", route, json=proof, headers=self.headers)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json(), second.json())
        self.assertFalse(fixture.store.state()["reconciliation_required"])

    async def test_empty_bootstrap_is_owner_only_and_pristine_only(self):
        route = "/api/v1/bootstrap/empty"
        denied = await self.request(
            "POST", route,
            headers={"Content-Type": "application/json"},
            json={"contract_version": 1},
        )
        self.assertEqual(denied.status_code, 401)
        blocked = await self.request(
            "POST", route,
            headers={**self.headers, "Content-Type": "application/json"},
            json={"contract_version": 1},
        )
        self.assertEqual(blocked.status_code, 409)
        root = Path(self.temporary.name) / "empty-bootstrap"
        root.mkdir()
        tokens = RevocableTokenStore(root / "auth.sqlite")
        token = "synthetic-empty-bootstrap-token-long-enough"
        tokens.add(token, label="synthetic iPhone")
        metadata = RevisionStore(root / "metadata.sqlite")
        # Exercise the seeded empty server shape used by the managed service:
        # create_day references create_trip and must be removed first.
        seed_trip = Trip(uid(11), "Seed trip", "cs", True, True)
        seed_day = JourneyDay(uid(12), seed_trip.id, "2026-10-02")
        seed_contract = CaminoV1Contract(metadata, authenticate=tokens.authenticate)
        seed_epoch = metadata.state()["epoch"]
        for sequence, kind, value in ((1, "create_trip", seed_trip), (2, "create_day", seed_day)):
            body = {
                "contract_version": 1,
                "epoch": seed_epoch,
                "operation_id": uid(200 + sequence),
                "device_id": uid(300),
                "device_sequence": sequence,
                "kind": kind,
                "expected_revision": None,
                "payload": wire(value),
            }
            raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
            response = seed_contract.handle(
                "POST", "/api/v1/operations", authorization=f"Bearer {token}",
                body=raw, content_type="application/json",
            )
            self.assertEqual(response.status, 200, response.body)
        media = MediaStore(
            root / "media.sqlite", root / "media", asset_lookup=metadata.asset,
            max_asset_bytes=1024 * 1024, max_chunk_bytes=8, reserve_bytes=0,
        )
        app = create_app(
            metadata_api=CaminoV1Contract(metadata, authenticate=tokens.authenticate),
            media_store=media, token_store=tokens,
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="https://camino.test") as client:
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            first = await client.post(route, headers=headers, json={"contract_version": 1})
            second = await client.post(route, headers=headers, json={"contract_version": 1})
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()["cursor"], 0)
        self.assertTrue(first.json()["bootstrapped"])
        self.assertEqual(first.json(), second.json())

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

    async def test_metadata_rejection_reports_safe_reason_without_changing_response_or_state(self):
        raw = json.dumps({
            "contract_version": 1, "epoch": self.metadata.state()["epoch"],
            "operation_id": uid(105), "device_id": uid(90), "device_sequence": 5,
            "kind": "update_metadata", "expected_revision": 1,
            "payload": {"moment_id": uid(3), "change": {"type": "attachment_title",
                "attachment": {"kind": "asset", "target_id": uid(99), "title": "private title"}}},
        }).encode()
        before = self.metadata.state()
        expected = self.contract.handle("POST", "/api/v1/operations",
            authorization=f"Bearer {self.token}", body=raw, content_type="application/json")
        with self.assertLogs("camino.metadata", level="WARNING") as logs:
            response = await self.request("POST", "/api/v1/operations", content=raw,
                headers={**self.headers, "Content-Type": "application/json"})
        self.assertEqual(response.status_code, expected.status)
        self.assertEqual(response.json(), expected.body)
        self.assertEqual(self.metadata.state(), before)
        text = " ".join(logs.output)
        self.assertIn("title target must be a photo or video of this Moment", text)
        self.assertIn("kind=update_metadata sequence=5", text)
        for private in (self.token, "private title", uid(99), uid(105), before["epoch"]):
            self.assertNotIn(private, text)

    async def test_metadata_exact_retry_and_reads_have_no_rejection_log(self):
        with self.metadata._connection() as db:
            raw = db.execute("SELECT request_body FROM accepted_operations ORDER BY device_sequence DESC LIMIT 1").fetchone()[0]
        before = self.metadata.state()
        with self.assertNoLogs("camino.metadata", level="WARNING"):
            response = await self.request("POST", "/api/v1/operations", content=raw,
                headers={**self.headers, "Content-Type": "application/json"})
            unknown = await self.request("GET", "/api/v1/unknown", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(unknown.status_code, 404)
        self.assertEqual(self.metadata.state(), before)

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

    async def test_finalize_delay_is_bounded_and_precedes_server_truth(self) -> None:
        with self.assertRaises(ValueError):
            create_app(
                metadata_api=self.contract,
                media_store=self.media,
                token_store=self.tokens,
                finalize_delay_seconds=16,
            )
        delayed = create_app(
            metadata_api=self.contract,
            media_store=self.media,
            token_store=self.tokens,
            finalize_delay_seconds=5,
        )
        with mock.patch(
            "camino.server.application.asyncio.sleep", new=mock.AsyncMock()
        ) as sleep:
            transport = httpx.ASGITransport(app=delayed)
            async with httpx.AsyncClient(
                transport=transport, base_url="https://camino.test"
            ) as client:
                response = await client.post(
                    f"/api/v1/assets/{self.asset_id}/finalize", headers=self.headers
                )
        sleep.assert_awaited_once_with(5)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "upload_session_not_found")

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
