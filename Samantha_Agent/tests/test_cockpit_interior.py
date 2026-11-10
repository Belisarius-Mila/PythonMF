from __future__ import annotations

import base64
import json
import subprocess
import tempfile
import threading
import unittest
import uuid
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app import cockpit
from app.cockpit_frontend import INTERIOR_HTML
from app.cockpit_interior import interior_atelier_action
from app.interior_atelier import InteriorAtelier
from app.interior_ai import InteriorAI
from tests.test_interior_ai import FakeDriver
from scripts.cockpit_quality_gate import node_binary
from tests.test_interior_atelier import image_bytes


class CockpitInteriorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "private-atelier"
        self.store = InteriorAtelier(self.root)
        self.patch = patch("app.cockpit_interior.InteriorAtelier", return_value=self.store)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, path, payload=None, origin=None):
        body = None if payload is None else json.dumps(payload).encode()
        headers = {"Origin": origin or self.base}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        try:
            response = urlopen(Request(self.base + path, data=body, headers=headers), timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.read(), dict(response.headers)

    def command(self, action, **fields):
        return self.request("/api/interior/action", {"action": action, "request_id": uuid.uuid4().hex, **fields})

    def project(self):
        code, raw, _ = self.command("create_project", title="HTTP project", room_title="Room")
        self.assertEqual(code, 200)
        result = json.loads(raw)
        return result["project_id"], result["room_id"]

    def test_page_and_empty_state_are_readonly_and_registered_in_family_navigation(self):
        status, raw, headers = self.request("/interior/")
        self.assertEqual(status, 200)
        self.assertIn("Interiérový ateliér", raw.decode())
        self.assertNotIn("{{SAMANTHA", raw.decode())
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("no-store", headers["Cache-Control"])
        status, raw, _ = self.request("/api/interior/state")
        self.assertEqual(json.loads(raw)["projects"], [])
        self.assertFalse(self.root.exists())
        self.assertIn('href="/interior/"', cockpit.COCKPIT_HTML)

    def test_real_http_create_upload_read_and_save_variant(self):
        project, room = self.project()
        raw = image_bytes()
        _, body, _ = self.command("add_source", project_id=project, room_id=room,
                                 title="Synthetic source", kind="photo", data=base64.b64encode(raw).decode())
        asset = json.loads(body)["asset_id"]
        status, body, headers = self.request("/api/interior/asset?" + urlencode(
            {"project_id": project, "room_id": room, "asset_id": asset, "view": "original"}))
        self.assertEqual((status, body), (200, raw))
        self.assertEqual(headers["Content-Type"], "image/png")
        self.assertIn("no-store", headers["Cache-Control"])
        _, body, _ = self.request("/api/interior/state?" + urlencode({"project_id": project, "room_id": room}))
        state = json.loads(body)
        draft = state["draft"]
        draft.pop("revision")
        draft.update(title="First human proposal", source_ids=[asset], image_source_id=asset)
        status, _, _ = self.command("save_draft", project_id=project, room_id=room, base_id="base", expected_revision=0, draft=draft)
        self.assertEqual(status, 200)
        status, body, _ = self.command("create_variant", project_id=project, room_id=room, base_id="base", expected_revision=1)
        self.assertEqual(status, 200)
        self.assertIn(json.loads(body)["variant_id"], self.store.state(project, room)["room"]["variants"])

    def test_http_source_delete_requires_exact_confirmation_and_removes_owned_bytes(self):
        project, room = self.project()
        _, body, _ = self.command("add_source", project_id=project, room_id=room,
            title="Synthetic source", kind="photo", data=base64.b64encode(image_bytes()).decode())
        asset = json.loads(body)["asset_id"]
        query = urlencode({"project_id":project,"room_id":room,"asset_id":asset})
        status, body, _ = self.request("/api/interior/delete-preview?" + query)
        self.assertEqual(status, 200)
        plan = json.loads(body)
        self.assertNotIn("files", plan)
        payload = {"action":"delete_source","request_id":uuid.uuid4().hex,"project_id":project,
            "room_id":room,"asset_id":asset,"plan_token":plan["plan_token"],"confirmation":"ano"}
        self.assertEqual(self.request("/api/interior/action",payload)[0], 400)
        payload["confirmation"] = plan["confirmation_text"]
        self.assertEqual(self.request("/api/interior/action",payload,origin="https://evil.example")[0], 403)
        status, body, _ = self.request("/api/interior/action",payload)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["deleted_bytes"], plan["bytes"])
        self.assertEqual(list((self.root/"objects").iterdir()), [])
        self.assertEqual(self.request("/api/interior/asset?"+query)[0], 400)

    def test_stale_save_returns_conflict_and_keeps_newer_text(self):
        project, room = self.project()
        draft = self.store.state(project, room)["draft"]
        draft.pop("revision")
        self.command("save_draft", project_id=project, room_id=room, base_id="base", expected_revision=0,
                     draft={**draft, "prompt": "New"})
        status, body, _ = self.command("save_draft", project_id=project, room_id=room, base_id="base", expected_revision=0,
                                      draft={**draft, "prompt": "Old"})
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)["error"], "conflict")
        self.assertEqual(self.store.state(project, room)["draft"]["prompt"], "New")

    def test_foreign_origin_is_rejected_before_private_write(self):
        status, _, _ = self.request("/api/interior/action", {"action": "create_project"}, origin="https://evil.example")
        self.assertEqual(status, 403)
        self.assertFalse(self.root.exists())

    def test_cross_project_asset_and_duplicate_query_parameters_are_rejected(self):
        project, room = self.project()
        result = self.store.execute({"action": "add_source", "request_id": uuid.uuid4().hex, "project_id": project,
            "room_id": room, "title": "Source", "kind": "photo", "data": base64.b64encode(image_bytes()).decode()})
        project2, room2 = self.project()
        status, body, _ = self.request("/api/interior/asset?" + urlencode(
            {"project_id": project2, "room_id": room2, "asset_id": result["asset_id"]}))
        self.assertEqual(status, 400)
        self.assertNotIn(b"PNG", body)
        status, _, _ = self.request("/api/interior/state?project_id=" + project + "&project_id=" + project2)
        self.assertEqual(status, 400)

    def test_unknown_action_has_safe_error_without_path_or_traceback(self):
        status, raw, _ = self.command("delete_everything", path="/private/synthetic-secret")
        self.assertEqual(status, 400)
        self.assertNotIn(b"synthetic-secret", raw)
        self.assertNotIn(b"Traceback", raw)
        self.assertFalse(self.root.exists())

    def test_storage_error_is_redacted_and_still_reports_uncertainty(self):
        with patch.object(self.store, "execute", side_effect=OSError("/private/synthetic-secret")):
            result = interior_atelier_action({}, store=self.store)
        self.assertEqual(result["error"], "storage_error")
        self.assertNotIn("synthetic-secret", json.dumps(result))

    def test_frontend_model_checks_restore_conflict_xss_and_context_races(self):
        result = subprocess.run([node_binary(), "--test", str(Path(__file__).with_name("interior_atelier_frontend.test.cjs"))],
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ai_frontend_double_send_room_race_and_unknown_delivery(self):
        result = subprocess.run([node_binary(), "--test", str(Path(__file__).with_name("interior_ai_frontend.test.cjs"))],
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ai_capabilities_are_readonly_without_initializing_a_room(self):
        status, body, _ = self.request("/api/interior/ai/status")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["protocol"], "interior-ai-v1")
        self.assertFalse(self.root.exists())

    def test_ai_http_queues_one_request_and_hides_internal_context(self):
        project, room = self.project()
        _, body, _ = self.command("add_source", project_id=project, room_id=room, title="Photo", kind="photo",
                                  data=base64.b64encode(image_bytes()).decode())
        asset = json.loads(body)["asset_id"]
        draft = self.store.state(project, room)["draft"]
        self.command("save_draft", project_id=project, room_id=room, base_id="base", expected_revision=0,
            draft={k:v for k,v in draft.items() if k!="revision"} | {"source_ids":[asset],"image_source_id":asset})
        queue, driver = [], FakeDriver()
        service = InteriorAI(self.store, driver=driver, launcher=queue.append, require_activation=False)
        payload = {"project_id":project,"room_id":room,"base_id":"base","expected_revision":1,
                   "request_id":uuid.uuid4().hex,"message":"Describe the room","mode":"chat"}
        with patch("app.interior_ai.INTERIOR_AI", service), patch("app.cockpit_interior.INTERIOR_AI", service):
            for _ in range(2):
                code, body, _ = self.request("/api/interior/ai/start", payload)
                self.assertEqual(code, 200)
                self.assertTrue(json.loads(body)["ok"])
            self.assertEqual(len(queue), 1)
            queue.pop()()
            code, body, _ = self.request("/api/interior/ai/status?" + urlencode({"project_id":project,"room_id":room}))
            self.assertEqual(json.loads(body)["jobs"][0]["status"], "completed")
            self.assertNotIn(b"thread_id", body)
            self.assertNotIn(b"context", body)
            self.assertEqual(len(driver.calls), 1)
            _, body, _ = self.request("/api/interior/state?" + urlencode({"project_id":project,"room_id":room}))
            self.assertNotIn("ai_requests", json.loads(body)["room"])

    def test_http_room_basis_is_shared_and_rejects_stale_revision(self):
        project, room = self.project()
        _, body, _ = self.command("add_source", project_id=project, room_id=room, title="Room plan", kind="plan",
                                  data=base64.b64encode(image_bytes()).decode())
        plan = json.loads(body)["asset_id"]
        _, body, _ = self.command("save_room_basis", project_id=project, room_id=room,
                                  expected_basis_revision=0, plan_source_id=plan, measurements="300 x 220 cm")
        self.assertEqual(json.loads(body)["basis_revision"], 1)
        _, body, _ = self.request("/api/interior/state?" + urlencode({"project_id":project,"room_id":room}))
        self.assertEqual(json.loads(body)["room"]["room_basis"]["measurements"], "300 x 220 cm")
        _, body, _ = self.command("save_room_basis", project_id=project, room_id=room,
                                  expected_basis_revision=0, plan_source_id=plan, measurements="400 cm")
        self.assertEqual(json.loads(body)["error"], "conflict")

    def test_frontend_has_unique_controls_and_fullscreen_source_edit_views(self):
        from html.parser import HTMLParser
        class IDs(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids = []
            def handle_starttag(self, tag, attrs):
                for key, value in attrs:
                    if key == "id":
                        self.ids.append(value)
        parser = IDs()
        parser.feed(INTERIOR_HTML)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        for required in ("variantsRail", "sourcesView", "editor", "notesPanel", "fullscreen", "projectSelect", "roomSelect"):
            self.assertIn(required, parser.ids)
        self.assertNotIn("gpt-image", INTERIOR_HTML)
