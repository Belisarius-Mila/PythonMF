from __future__ import annotations

import base64
import json
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import interior_ai_activation as activation
from app.communication import agent_roles
from app.interior_ai import InteriorAI, CodexInteriorDriver, PROTOCOL
from app.interior_atelier import AtelierError, InteriorAtelier
from tests.test_interior_atelier import image_bytes


class InteriorActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.probes = self.home / "data/private/neuberk_interier_design/ai_probes"
        self.store = InteriorAtelier(self.home / "atelier")
        p = self.command("create_project", title="Test", room_title="Room")
        self.project, self.room = p["project_id"], p["room_id"]
        source = self.command("add_source", project_id=self.project, room_id=self.room, kind="photo",
            title="Photo", data=base64.b64encode(image_bytes()).decode())["asset_id"]
        d = self.store.state(self.project, self.room)["draft"]
        self.command("save_draft", project_id=self.project, room_id=self.room, base_id="base", expected_revision=0,
            draft={k: v for k, v in d.items() if k != "revision"} | {"source_ids": [source], "image_source_id": source})
        self.config = self.home / "config/agent_roles.json"
        self.config.parent.mkdir()
        self.document = json.loads(agent_roles.CONFIG_PATH.read_bytes())
        self.config.write_text(json.dumps(self.document))
        self.calls, self.threads = [], []
        self.emit_image, self.fail = True, False
        real_load = agent_roles.load_role
        def load(path=None, *, role=agent_roles.ROLE):
            return real_load(path or self.config, role=role)
        for target, value in (("PROBES", self.probes), ("PROJECT", self.home)):
            context = patch.object(activation, target, value); context.start(); self.addCleanup(context.stop)
        context = patch.object(agent_roles, "CONFIG_PATH", self.config); context.start(); self.addCleanup(context.stop)
        context = patch.object(agent_roles, "load_role", side_effect=load); context.start(); self.addCleanup(context.stop)
        context = patch.object(activation, "source_digest", return_value="code-unchanged"); context.start(); self.addCleanup(context.stop)
        context = patch.object(activation, "role_consumer_readiness", return_value={"ready":True,"email_service":"compatible"}); context.start(); self.addCleanup(context.stop)

    def command(self, action, **kwargs):
        return self.store.execute({"action": action, "request_id": uuid.uuid4().hex, **kwargs})

    def client(self):
        parent = self
        class Client:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def list_models(self):
                return [{"model": "test-architect", "inputModalities": ["text", "image"],
                         "supportedReasoningEfforts": [{"reasoningEffort": "high"}]}]
            def read_effective_config(self, **_): return {"mcp_servers": {"other-service": {"enabled": True}}}
            def start_thread(self, **kwargs):
                parent.threads.append(kwargs); return "synthetic-thread"
            def send_text(self, **kwargs):
                parent.calls.append(kwargs)
                if parent.fail: raise TimeoutError("PRIVATE_REMOTE_ERROR")
                mode = json.loads(kwargs["text"])["mode"]
                images = ({"result": base64.b64encode(image_bytes()).decode()},) if mode == "image" and parent.emit_image else ()
                return SimpleNamespace(delivered=True, answer="Zachovej okno a ověř rozměry.", generated_images=images,
                    as_dict=lambda: {"delivered": True, "generated_image_count": len(images)})
        return Client()

    def probe(self, **kwargs):
        return activation.probe_candidate(model="test-architect", reasoning_effort="high",
            cost_review="Explicit synthetic price review", project_id=self.project, room_id=self.room,
            store=self.store, client_factory=self.client, **kwargs)

    def test_unconfirmed_probe_never_calls_model_or_creates_proof(self):
        self.assertEqual(self.probe()["state"], "not_started")
        self.assertFalse(self.probes.exists())
        self.assertEqual(self.calls, [])

    def test_one_analysis_one_image_and_replayed_probe_never_calls_model_again(self):
        probe_id = uuid.uuid4().hex
        result = self.probe(confirmed=True, include_image=True, probe_id=probe_id)
        self.assertEqual(result["state"], "review_required")
        self.assertTrue(result["chat_passed"] and result["image_passed"])
        self.assertEqual(len(self.calls), 2)
        self.assertTrue(self.probe(confirmed=True, include_image=True, probe_id=probe_id)["replayed"])
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(json.loads(self.config.read_text()), self.document)
        self.assertEqual(len(self.store.state(self.project, self.room)["room"]["variants"]), 1)
        thread = self.threads[0]
        self.assertFalse(thread["ephemeral"])
        self.assertEqual(thread["config_overrides"]["mcp_servers"], {"other-service": {"enabled": False}})
        self.assertFalse(thread["config_overrides"]["features"]["multi_agent"])
        self.assertFalse(thread["config_overrides"]["features"]["shell_tool"])
        self.assertFalse(thread["config_overrides"]["features"]["view_image"])
        self.assertFalse(thread["config_overrides"]["features"]["image_generation"])
        self.assertTrue(self.threads[1]["config_overrides"]["features"]["image_generation"])
        self.assertEqual(self.calls[0]["sandbox_policy"]["type"], "readOnly")
        self.assertEqual(self.calls[0]["sandbox_policy"]["access"]["type"], "restricted")
        self.assertEqual(len(self.calls[0]["local_image_paths"]), 1)

    def test_chat_only_pilot_does_not_generate_a_picture(self):
        result = self.probe(confirmed=True)
        self.assertEqual(result["state"], "review_required")
        self.assertTrue(result["chat_passed"])
        self.assertFalse(result["image_passed"])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.store.state(self.project, self.room)["room"]["variants"], {})

    def test_uncertain_analysis_stops_before_image_and_cannot_be_replayed(self):
        self.fail = True
        probe_id = uuid.uuid4().hex
        first = self.probe(confirmed=True, include_image=True, probe_id=probe_id)
        self.assertEqual(first["state"], "attention")
        self.assertFalse(first["chat_passed"])
        self.assertTrue(self.probe(confirmed=True, include_image=True, probe_id=probe_id)["replayed"])
        self.assertEqual(len(self.calls), 1)
        with self.assertRaises(AtelierError): activation.accept_probe(probe_id, confirmed=True)

    def test_missing_image_does_not_fake_success_or_enable_generation(self):
        self.emit_image = False
        result = self.probe(confirmed=True, include_image=True)
        self.assertEqual(result["state"], "attention")
        self.assertTrue(result["chat_passed"])
        self.assertFalse(result["image_passed"])
        with self.assertRaises(AtelierError): activation.accept_probe(result["probe_id"], confirmed=True)

    def test_activation_waits_for_compatible_live_parser_and_preserves_other_roles(self):
        result = self.probe(confirmed=True, include_image=True)
        activation.accept_probe(result["probe_id"], confirmed=True)
        with self.assertRaises(AtelierError): activation.activation_plan(result["probe_id"], call=lambda _: {"ok": True})
        runtime = {"ok": True, "protocol": PROTOCOL, "role_schema": 1, "role": agent_roles.INTERIOR_ROLE}
        def git(args, **_):
            if args[-1] == "--porcelain": return ""
            if args[-1] == "--show-current": return "main\n"
            return "frozen-head\n"
        with patch.object(activation, "http_call", return_value=runtime), patch.object(activation.subprocess, "check_output", side_effect=git):
            with patch.object(activation, "role_consumer_readiness", return_value={"ready":False}), self.assertRaises(AtelierError):
                activation.activation_plan(result["probe_id"])
            plan = activation.activation_plan(result["probe_id"])
            self.assertEqual(activation.activate(plan)["state"], "not_applied")
            self.assertEqual(activation.activate(plan, confirmed=True)["state"], "active")
        updated = json.loads(self.config.read_text())
        for role in self.document["roles"]:
            self.assertEqual(updated["roles"][role], self.document["roles"][role])
        proof_path, proof = activation._proof(result["probe_id"])
        candidate = updated["roles"][agent_roles.INTERIOR_ROLE]["approved_models"][0]
        self.assertTrue(proof["accepted"] and proof["chat_passed"] and proof["image_passed"])
        self.assertEqual(candidate["dry_run_evidence"], str(proof_path.relative_to(self.home)))
        service = InteriorAI(self.store, driver=CodexInteriorDriver(roles_path=self.config))
        self.assertTrue(service.capabilities()["enabled"])
        self.assertTrue(service.capabilities()["image_generation"])
        updated["roles"][agent_roles.INTERIOR_ROLE]["approved_models"][0]["cost_review"] = "Changed approval after service startup"
        self.config.write_text(json.dumps(updated))
        self.assertFalse(service.capabilities()["enabled"], "A changed policy waits for compatible deployment/restart")

    def test_modified_source_or_unaccepted_pilot_cannot_activate(self):
        result = self.probe(confirmed=True)
        with self.assertRaises(AtelierError): activation.activation_plan(result["probe_id"])
        with patch.object(activation, "source_digest", return_value="changed-code"), self.assertRaises(AtelierError):
            activation.accept_probe(result["probe_id"], confirmed=True)


class RoleConsumerReadinessTests(unittest.TestCase):
    def test_owned_old_and_new_parsers_are_inspected_without_executing_service_code(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            runtime = home / "runtime"
            parser = runtime / "app/communication/agent_roles.py"
            parser.parent.mkdir(parents=True)
            receipt = home / "installation.json"
            receipt.write_text(json.dumps({"runtime":str(runtime)}))
            controller = SimpleNamespace(receipt_path=receipt,
                status=lambda: {"installed":True,"owned":True,"source_head":"owned-head"})
            parser.write_text('ROLE="release_executor"\nKNOWN_ROLES=frozenset({ROLE})\nraise RuntimeError("MUST_NOT_EXECUTE")\n')
            self.assertFalse(activation.role_consumer_readiness(controller)["ready"])
            parser.write_text('ROLE="release_executor"\nINTERIOR_ROLE="interior_architect"\nKNOWN_ROLES=frozenset({ROLE, INTERIOR_ROLE})\nraise RuntimeError("MUST_NOT_EXECUTE")\n')
            self.assertTrue(activation.role_consumer_readiness(controller)["ready"])
            controller.status = lambda: {"installed":True,"owned":False,"source_head":"unknown"}
            self.assertFalse(activation.role_consumer_readiness(controller)["ready"])


if __name__ == "__main__":
    unittest.main()
