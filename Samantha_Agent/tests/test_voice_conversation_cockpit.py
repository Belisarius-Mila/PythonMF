"""Offline Cockpit integration contracts. No real credentials, services or model I/O."""
from __future__ import annotations

import copy
from functools import partial
import io
import json
import tempfile
import threading
import unittest
from email.message import Message
from http.cookies import SimpleCookie
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.communication import agent_roles
from app.communication.voice_conversation_cockpit import (
    CockpitVoiceRoutes, COOKIE, CONFIRMATION, PREFIX, capture_existing_thread,
)
from app.communication.voice_conversation_gateway import CandidateVoiceGateway, VoiceGatewayError
from app.communication.voice_conversation_roles import load_voice_role
from tests.test_voice_conversation_gateway import BINDING, SNAPSHOT, FakeProvider, FakeClock, ManualSupervisor

ROOT = Path(__file__).resolve().parents[1]
ROLE = {"role": "read_only_voice", "model": "gpt-live-1", "policy_digest": "a" * 64}


def role_binding():
    return {"label": "Čtecí hlasový pilot", "preferred_model": "gpt-live-1", "approved_models": [{
        "model": "gpt-live-1", "cost_review": "Mila 2026-11-05: approved candidate; 0.05 USD/min; per-session consent required",
        "dry_run_evidence": "memory/reports/voice_conversation_probe_20261105.json"}]}


class CockpitVoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "journal"
        self.provider = FakeProvider(FakeClock())
        self.factory = Mock(return_value=self.provider)
        self.reader = Mock(side_effect=lambda: copy.deepcopy(SNAPSHOT))
        self.role = Mock(return_value=copy.deepcopy(ROLE))
        self.routes = self.make_routes()
        self.headers = Message()
        for key, value in {"Host": "synthetic.example", "Origin": "https://synthetic.example", "Content-Type": "application/json"}.items():
            self.headers[key] = value
        self.page, cookie = self.routes.page(self.headers)
        parsed = SimpleCookie(); parsed.load(cookie)
        self.owner = parsed[COOKIE].value
        self.headers["Cookie"] = f"{COOKIE}={self.owner}"
        self.headers["X-Voice-CSRF"] = self.routes.contexts[self.owner]["csrf"]

    def make_routes(self):
        return CockpitVoiceRoutes(Mock(), journal_directory=self.directory, provider_factory=self.factory,
            role_loader=self.role, capture=lambda _: (BINDING, self.reader),
            gateway_factory=partial(CandidateVoiceGateway, supervisor_factory=ManualSupervisor))

    def post(self, value=None, suffix="session"):
        data = value if value is not None else {"sdp": "v=0 synthetic", "confirmation": CONFIRMATION}
        return self.routes.post(PREFIX + suffix, self.headers, json.dumps(data).encode())

    def test_page_is_inert_and_cookie_private(self):
        self.assertIn('data-ready="true"', self.page)
        self.assertNotIn("{{", self.page)
        self.factory.assert_not_called(); self.reader.assert_not_called()
        self.assertFalse(self.directory.exists())
        _, cookie = self.routes.page(self.headers)
        for attr in ("HttpOnly", "SameSite=Strict", "Secure"):
            self.assertIn(attr, cookie)

    def test_explicit_consent_and_bound_role_create_one_session(self):
        code, value = self.post()
        self.assertEqual(code, 201)
        self.assertEqual(value["session"]["id"], "synthetic-voice")
        self.assertEqual(len(self.provider.created), 1)
        sent = self.provider.created[0]
        self.assertEqual(sent["session"]["model"], "gpt-live-1")
        self.assertNotIn("SYNTHETIC PRIVATE", json.dumps(sent))
        self.assertEqual(sent["session"]["client"]["data_channel"]["allowed_client_events"], ["session.close"])
        self.assertEqual(self.post()[0], 409)
        self.assertEqual(len(self.provider.created), 1)

    def test_missing_or_altered_consent_never_loads_provider(self):
        for value in ({"sdp": "v=0"}, {"sdp": "v=0", "confirmation": "ano"},
                      {"sdp": "v=0", "confirmation": CONFIRMATION, "model": "untrusted"}):
            self.assertEqual(self.post(value)[0], 409)
        self.factory.assert_not_called()

    def test_cross_origin_no_cookie_bad_csrf_duplicate_authority(self):
        for key, value in (("Origin", "https://evil.example"), ("Cookie", ""), ("X-Voice-CSRF", "wrong")):
            saved = self.headers[key]; self.headers.replace_header(key, value)
            self.assertEqual(self.post()[0], 403)
            self.headers.replace_header(key, saved)
        self.headers["Origin"] = "https://synthetic.example"
        self.assertEqual(self.post()[0], 409)
        self.factory.assert_not_called()

    def test_changed_role_or_backend_blocks_before_provider(self):
        self.role.return_value = {**ROLE, "policy_digest": "b" * 64}
        self.assertEqual(self.post()[0], 409)
        self.role.return_value = ROLE
        self.reader.side_effect = VoiceGatewayError("changed")
        self.assertEqual(self.post()[0], 409)
        self.factory.assert_not_called()

    def test_uncertain_create_refresh_and_process_restart_do_not_replay(self):
        self.provider.create_error = TimeoutError("private provider details")
        self.assertEqual(self.post()[0], 409)
        page, _ = self.routes.page(self.headers)
        self.assertIn('data-ready="false"', page)
        self.assertEqual(self.post()[0], 409)
        self.routes = self.make_routes()
        page, _ = self.routes.page(self.headers)
        self.assertIn('data-ready="false"', page)
        self.headers.replace_header("X-Voice-CSRF", self.routes.contexts[self.owner]["csrf"])
        self.assertEqual(self.post()[0], 409)
        self.assertEqual(len(self.provider.created), 1)

    def test_close_only_owned_voice_never_calls_backend(self):
        self.post()
        self.assertEqual(self.post({"session_id": "other"}, "close")[0], 409)
        self.assertEqual(self.post({"session_id": "synthetic-voice"}, "close")[0], 200)
        gateway = self.routes.contexts[self.owner]["gateway"]
        self.assertTrue(gateway.supervisor.stop_requested.is_set())
        self.assertEqual(len(self.provider.created), 1)

    def test_missing_role_keeps_page_disabled_and_reload_can_recover(self):
        self.role.side_effect = agent_roles.AgentRoleError("not activated")
        page, _ = self.routes.page(self.headers)
        self.assertIn('data-ready="false"', page)
        self.role.side_effect = None
        page, _ = self.routes.page(self.headers)
        self.assertIn('data-ready="true"', page)
        self.factory.assert_not_called()

    def test_assets_are_exact_allowlist(self):
        self.assertIsNone(self.routes.asset("/human-adam/voice/../../config/agent_roles.json"))
        self.assertIn("requireConsent:true,maxSeconds:60", self.routes.asset("/human-adam/voice/cockpit.js"))

    def test_concurrent_double_click_has_one_create(self):
        entered, release = threading.Event(), threading.Event()
        create = self.provider.create
        def blocked(*args, **kwargs):
            entered.set(); release.wait(2)
            return create(*args, **kwargs)
        self.provider.create = blocked
        results = []
        thread = threading.Thread(target=lambda: results.append(self.post()))
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            self.assertEqual(self.post()[0], 409)
        finally:
            release.set(); thread.join(3)
        self.assertEqual(results[0][0], 201)
        self.assertEqual(len(self.provider.created), 1)

    def test_new_attempt_requires_final_server_usage_and_never_reuses_receipt(self):
        self.post()
        self.assertEqual(self.post({"confirmation": CONFIRMATION}, "new")[0], 409)
        self.routes.journal.record(self.owner, state="closed", seconds=12, final_usage_confirmed=True)
        page, _ = self.routes.page(self.headers)
        self.assertIn('data-can-renew="true"', page)
        code, result = self.post({"confirmation": CONFIRMATION}, "new")
        self.assertEqual(code, 200)
        self.assertIn("Max-Age=0", result["_voice_cookie"])
        self.assertEqual(self.post({"confirmation": CONFIRMATION}, "new")[0], 409)
        self.assertEqual(self.routes.journal.read(self.owner)["state"], "closed")
        self.assertEqual(len(self.provider.created), 1)


class ExistingThreadTests(unittest.TestCase):
    def manager(self, *, lazy=False, hub=True):
        self.hub = Mock()
        self.hub.snapshot.side_effect = lambda: {**copy.deepcopy(SNAPSHOT["session"]), "connected": True}
        self.service = SimpleNamespace(_hub=self.hub if hub else None)
        record = SimpleNamespace(compatibility_adapter=None if lazy else SimpleNamespace(service=self.service))
        return SimpleNamespace(_state_lock=threading.RLock(), active_workstream_id=BINDING.workstream_id,
            workstream_backends=SimpleNamespace(binding=Mock(return_value=record)),
            _lazy_services={BINDING.workstream_id: self.service} if lazy else {})

    def test_existing_compatibility_and_lazy_hubs_remain_identical(self):
        for lazy in (False, True):
            manager = self.manager(lazy=lazy)
            binding, read = capture_existing_thread(manager)
            self.assertEqual(binding, BINDING)
            self.assertEqual(read(), {**SNAPSHOT, "session": {**SNAPSHOT["session"], "connected": True}})
            self.hub.connect.assert_not_called(); self.hub.send_message.assert_not_called()

    def test_detached_and_uninitialized_services_fail_without_factory(self):
        for lazy in (False, True):
            manager = self.manager(lazy=lazy, hub=False)
            with self.assertRaises(VoiceGatewayError):
                capture_existing_thread(manager)

    def test_selection_thread_or_hub_replacement_fails(self):
        for change in ("selection", "thread", "hub"):
            manager = self.manager(); _, read = capture_existing_thread(manager)
            if change == "selection": manager.active_workstream_id = "other"
            elif change == "thread": self.hub.snapshot.side_effect = None; self.hub.snapshot.return_value = {"thread_id": "other", "connected": True}
            else: self.service._hub = Mock()
            with self.assertRaises(ValueError if change == "thread" else VoiceGatewayError): read()

    def test_real_flat_hub_snapshot_is_wrapped_without_cold_recovery(self):
        from app.communication.session_hub import CanonicalSessionHub
        manager = self.manager()
        hub = object.__new__(CanonicalSessionHub)
        hub._state_lock = threading.RLock(); hub._turn_lock = threading.Lock()
        hub._client = SimpleNamespace(running=True)
        hub._state = {**copy.deepcopy(SNAPSHOT["session"]), "previous_threads": []}
        self.service._hub = hub
        binding, read = capture_existing_thread(manager)
        self.assertEqual(binding, BINDING)
        self.assertTrue(read()["session"]["connected"])
        hub._client.running = False
        with self.assertRaises(VoiceGatewayError): read()
        with self.assertRaises(VoiceGatewayError): capture_existing_thread(manager)


class VoiceRoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "roles.json"
        self.doc = json.loads((ROOT / "config/agent_roles.json").read_text())
        self.doc["roles"]["read_only_voice"] = role_binding()

    def load(self):
        self.path.write_text(json.dumps(self.doc)); return load_voice_role(self.path)

    def test_audio_role_has_no_fake_reasoning_and_text_roles_still_resolve(self):
        role = self.load()
        self.assertEqual(role["model"], "gpt-live-1")
        self.assertNotIn("reasoning_effort", role)
        agent_roles.load_role(self.path, role=agent_roles.ROLE)
        with self.assertRaises(agent_roles.AgentRoleError): agent_roles.load_role(self.path, role="read_only_voice")

    def test_unapproved_model_fake_effort_missing_proof_and_unknown_role_block(self):
        original = copy.deepcopy(self.doc)
        for mutation in ("model", "effort", "proof", "unknown"):
            self.doc = copy.deepcopy(original)
            approved = self.doc["roles"]["read_only_voice"]["approved_models"][0]
            if mutation == "model": approved["model"] = "unapproved"
            if mutation == "effort": approved["reasoning_effort"] = "low"
            if mutation == "proof": approved["dry_run_evidence"] = "other.json"
            if mutation == "unknown": self.doc["roles"]["unknown"] = {}
            with self.assertRaises(agent_roles.AgentRoleError): self.load()

    def test_failed_trial_cannot_activate_role(self):
        self.path.write_text(json.dumps(self.doc))
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "memory/reports/voice_conversation_probe_20261105.json"
            target.parent.mkdir(parents=True)
            proof = json.loads((ROOT / "memory/reports/voice_conversation_probe_20261105.json").read_text())
            proof["result"]["final_usage_confirmed"] = False
            target.write_text(json.dumps(proof))
            with self.assertRaises(agent_roles.AgentRoleError): load_voice_role(self.path, root=Path(root))


class MountedRouteTests(unittest.TestCase):
    def test_real_handler_serves_panel_cookie_and_same_origin_assets_without_model(self):
        from app import cockpit
        with patch("app.communication.voice_conversation_cockpit.project_provider") as provider:
            handler_class = cockpit.CockpitServer().make_handler()
            def handler(path):
                h = object.__new__(handler_class)
                h.path = path; h.headers = Message(); h.headers["Host"] = "localhost:8771"
                h.wfile = io.BytesIO(); h.validate_request_access = Mock()
                h.send_response = Mock(); h.send_header = Mock(); h.end_headers = Mock()
                return h
            h = handler("/human-adam/voice/"); h.do_GET()
            self.assertIn(b"voiceConfig", h.wfile.getvalue())
            self.assertTrue(any(call.args[0] == "Set-Cookie" for call in h.send_header.call_args_list))
            h = handler("/human-adam/voice/cockpit.js"); h.do_GET()
            self.assertIn(b"requireConsent:true", h.wfile.getvalue())
            provider.assert_not_called()


if __name__ == "__main__": unittest.main()
