"""Private staged update download, authentication and integrity over real HTTP."""

import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import httpx
from fastapi import FastAPI

from camino.domain.revision_store import RevisionStore
from camino.server.auth import RevocableTokenStore
from camino.server.viewer import CaminoViewer


class ClientUpdateTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="camino-client-update-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.stage = self.root / "update"
        self.stage.mkdir(mode=0o700)
        self.name = "Camino-SyncRepair-18-20261014.ipa"
        self.data = b"PK\x03\x04synthetic-update-archive" * 4
        self.path = self.stage / self.name
        self.path.write_bytes(self.data)
        self.path.chmod(0o600)
        self.manifest = self.stage / "update.json"
        self.proof = {"filename": self.name, "bytes": len(self.data),
                      "sha256": hashlib.sha256(self.data).hexdigest(),
                      "bundle_id": "cz.pythonmf.camino.app"}
        self.write_manifest(self.proof)
        self.tokens = RevocableTokenStore(self.root / "readers.sqlite")
        self.token = "synthetic-reader-token-" + "r" * 32
        self.token_id = self.tokens.add(self.token, label="synthetic reader")
        self.headers = {"Authorization": "Basic " + base64.b64encode(("jana:" + self.token).encode()).decode()}
        self.viewer = CaminoViewer(SimpleNamespace(_uuid=RevisionStore._uuid), None, None,
            self.tokens, "00000000-0000-4000-8000-000000000001")

    def write_manifest(self, proof):
        self.manifest.write_text(json.dumps(proof))
        self.manifest.chmod(0o600)

    async def request(self, root, method="GET", headers=None):
        app = FastAPI()
        app.include_router(self.viewer.router(client_update_root=root))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, "/viewer/client-update", headers=headers or self.headers)

    async def test_authenticated_download_head_range_and_revocation(self):
        response = await self.request(self.stage)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.data)
        self.assertIn(self.name, response.headers["content-disposition"])
        self.assertIn("no-store", response.headers["cache-control"])
        head = await self.request(self.stage, method="HEAD")
        self.assertEqual(head.status_code, 200)
        self.assertEqual(head.content, b"")
        partial = await self.request(self.stage, headers={**self.headers, "Range": "bytes=0-7"})
        self.assertEqual(partial.status_code, 206)
        self.assertEqual(partial.content, self.data[:8])
        self.tokens.revoke(self.token_id)
        self.assertEqual((await self.request(self.stage)).status_code, 401)

    async def test_anonymous_wrong_reader_and_owner_bearer_cannot_download(self):
        for header in ({"Authorization": ""}, {"Authorization": "Bearer " + self.token},
                       {"Authorization": "Basic " + base64.b64encode(("other:" + self.token).encode()).decode()}):
            self.assertEqual((await self.request(self.stage, headers=header)).status_code, 401)
        self.assertEqual((await self.request(None)).status_code, 404)

    async def test_bad_hash_identity_manifest_and_traversal_are_unavailable(self):
        for change in ({"sha256": "0" * 64}, {"bytes": len(self.data) + 1},
                       {"bundle_id": "other.app"}, {"filename": "../secret.ipa"},
                       {"filename": "/secret.ipa"}, {"filename": "Camino-secret.txt"}):
            self.write_manifest({**self.proof, **change})
            self.assertEqual((await self.request(self.stage)).status_code, 404)
        self.manifest.write_text("not JSON")
        self.assertEqual((await self.request(self.stage)).status_code, 404)

    async def test_symlinks_public_permissions_and_changed_bytes_are_unavailable(self):
        alias = self.root / "alias"
        alias.symlink_to(self.stage)
        self.assertEqual((await self.request(alias)).status_code, 404)
        self.path.chmod(0o644)
        self.assertEqual((await self.request(self.stage)).status_code, 404)
        self.path.chmod(0o600)
        self.path.write_bytes(b"different update bytes")
        self.assertEqual((await self.request(self.stage)).status_code, 404)
