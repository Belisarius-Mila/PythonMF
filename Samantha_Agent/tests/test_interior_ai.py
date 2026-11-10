from __future__ import annotations

import base64
import copy
import io
import tempfile
import unittest
import uuid
from unittest.mock import patch
from pathlib import Path

from PIL import Image

from app.interior_ai import InteriorAI, CodexInteriorDriver, interior_ai_start_action
from app.interior_atelier import AtelierConflict, AtelierError, InteriorAtelier
from app.codex_appserver import AppServerTurnError
from tests.test_interior_atelier import image_bytes


class FakeDriver:
    def __init__(self):
        self.calls = []
        self.fail = False
        self.with_image = False
        self.outputs = None
        self.answer = "Ponech dveře a ověř rozměry."

    def selection(self):
        return {"role": "interior_architect", "model": "approved-test", "reasoning_effort": "high", "policy_digest": "a" * 64}

    def __call__(self, job, images, on_thread):
        self.calls.append((copy.deepcopy(job), images))
        on_thread("synthetic-thread")
        if self.fail:
            raise TimeoutError("PRIVATE_TRANSPORT_ERROR")
        images = [{"result": base64.b64encode(image_bytes()).decode()}] if self.with_image else []
        return {"answer": self.answer, "receipt": {"delivered": True}, "images": self.outputs if self.outputs is not None else images}


class InteriorAITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = InteriorAtelier(Path(self.temp.name).resolve() / "atelier")
        self.driver = FakeDriver()
        self.queue = []
        self.ai = InteriorAI(self.store, driver=self.driver, launcher=self.queue.append, require_activation=False)
        p = self.action("create_project", title="Private project", room_title="Room A")
        self.project, self.room = p["project_id"], p["room_id"]
        self.asset = self.action("add_source", project_id=self.project, room_id=self.room,
            title="Photo", kind="photo", data=base64.b64encode(image_bytes()).decode())["asset_id"]
        self.draft = {k: v for k, v in self.store.state(self.project, self.room)["draft"].items() if k != "revision"}
        self.draft.update(title="Test proposal", source_ids=[self.asset], image_source_id=self.asset,
                          prompt="Zachovej okno", fixed_elements="Dveře")
        self.action("save_draft", project_id=self.project, room_id=self.room, base_id="base",
                    expected_revision=0, draft=self.draft)

    def action(self, action, **values):
        return self.store.execute({"action": action, "request_id": uuid.uuid4().hex, **values})

    def payload(self, **values):
        return {"project_id": self.project, "room_id": self.room, "base_id": "base", "expected_revision": 1,
                "request_id": uuid.uuid4().hex, "message": "Navrhni lepší uspořádání.", "mode": "chat", **values}

    def jobs(self):
        return self.ai.status(self.project, self.room)["jobs"]

    def test_double_submit_and_restart_never_repeat_model_request(self):
        payload = self.payload()
        first = self.ai.start(payload)
        self.assertEqual(self.ai.start(payload)["request_id"], first["request_id"])
        self.assertEqual(len(self.queue), 1)
        self.assertEqual(self.jobs()[0]["status"], "queued")
        restarted = InteriorAI(self.store, driver=self.driver, launcher=self.queue.append)
        self.assertEqual(restarted.status(self.project, self.room)["jobs"][0]["status"], "delivery_unknown")
        self.assertTrue(restarted.start(payload)["replayed"])
        self.queue.pop()()
        self.assertEqual(len(self.driver.calls), 1)
        self.assertEqual(self.jobs()[0]["status"], "completed")
        self.assertTrue(restarted.start(payload)["replayed"])
        self.assertEqual(len(self.queue), 0)

    def test_changed_payload_with_same_id_and_stale_revision_stop_before_model(self):
        payload = self.payload(); self.ai.start(payload)
        with self.assertRaises(AtelierConflict): self.ai.start({**payload, "message": "jiné"})
        with self.assertRaises(AtelierConflict): self.ai.start(self.payload(expected_revision=0))
        self.assertEqual(self.driver.calls, [])

    def test_current_scope_gets_only_selected_verified_images_and_not_foreign_sources(self):
        other = self.action("add_source", project_id=self.project, room_id=self.room,
            title="Unselected", kind="inspiration", data=base64.b64encode(image_bytes((40, 40))).decode())["asset_id"]
        self.ai.start(self.payload()); self.queue.pop()()
        job, paths = self.driver.calls[0]
        self.assertEqual(len(paths), 1)
        self.assertEqual(job["image_count"], 1)
        self.assertEqual(job["context"]["draft"]["source_ids"], [self.asset])
        self.assertNotIn(other, str(job["context"]))
        self.assertEqual(job["context"]["draft"]["fixed_elements"], "Dveře")
        self.assertNotIn("ai_requests", self.store.state(self.project, self.room)["room"])

    def test_uncertain_delivery_is_durable_does_not_leak_error_and_blocks_resend(self):
        self.driver.fail = True
        payload = self.payload(); self.ai.start(payload); self.queue.pop()()
        self.assertEqual(self.jobs()[0]["status"], "delivery_unknown")
        self.assertNotIn("PRIVATE_TRANSPORT_ERROR", str(self.jobs()))
        self.assertTrue(self.ai.start(payload)["replayed"])
        self.assertEqual(len(self.driver.calls), 1)
        with self.assertRaises(AtelierConflict): self.ai.start(self.payload())

    def test_frozen_input_is_used_after_user_changes_draft_while_running(self):
        self.ai.start(self.payload())
        self.action("save_draft", project_id=self.project, room_id=self.room, base_id="base", expected_revision=1,
                    draft={**self.draft, "prompt": "Novější neodeslaná změna"})
        self.queue.pop()()
        self.assertEqual(self.driver.calls[0][0]["context"]["draft"]["prompt"], "Zachovej okno")
        self.assertEqual(self.store.state(self.project, self.room)["draft"]["prompt"], "Novější neodeslaná změna")

    def test_generated_picture_is_an_immutable_editable_child_variant(self):
        self.driver.with_image = True
        self.ai.start(self.payload(mode="image")); self.queue.pop()()
        job = self.jobs()[0]
        self.assertEqual(job["status"], "completed")
        variant = self.store.state(self.project, self.room)["room"]["variants"][job["variant_id"]]
        self.assertEqual(variant["kind"], "ai_proposal")
        self.assertIn(variant["image_source_id"], variant["source_ids"])
        child = self.store.state(self.project, self.room, job["variant_id"])["draft"]
        values = {k: v for k, v in child.items() if k != "revision"}
        self.action("save_draft", project_id=self.project, room_id=self.room, base_id=job["variant_id"],
                    expected_revision=0, draft=values)
        self.assertTrue(self.ai.status(self.project, self.room, job["variant_id"])["jobs"])

    def test_no_image_result_is_honest_and_does_not_create_fake_variant(self):
        self.ai.start(self.payload(mode="image")); self.queue.pop()()
        self.assertEqual(self.jobs()[0]["status"], "no_image")
        self.assertEqual(self.store.state(self.project, self.room)["room"]["variants"], {})

    def test_multiple_real_outputs_survive_false_error_text_and_recovery_without_model(self):
        self.driver.outputs = [{"result":base64.b64encode(image_bytes(size=size)).decode()} for size in ((600,400),(800,400))]
        self.driver.answer = "PRIVATE_FALSE_ERROR: send again"
        payload = self.payload(mode="image")
        job_id = self.ai.start(payload)["request_id"]; self.queue.pop()()
        job = self.jobs()[0]
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["output_count"], 2)
        self.assertEqual(len(job["variant_ids"]), 2)
        self.assertNotIn("PRIVATE_FALSE_ERROR", str(job))
        state = self.store.state(self.project,self.room)
        self.assertEqual(len(state["room"]["variants"]), 2)
        self.assertEqual(state["draft"]["revision"], 1)
        self.assertNotIn("PRIVATE_FALSE_ERROR", str(state))
        for variant_id in job["variant_ids"]:
            variant = state["room"]["variants"][variant_id]
            raw,_ = self.store.asset(self.project,self.room,variant["image_source_id"],"preview")
            with Image.open(io.BytesIO(raw)) as image: image.verify()
        self.ai.recover(self.project,self.room,job_id)
        self.assertTrue(self.ai.start(payload)["replayed"])
        self.assertEqual(len(self.driver.calls), 1)
        self.assertEqual(len(self.store.state(self.project,self.room)["room"]["variants"]), 2)

    def test_identical_encoded_outputs_create_one_variant(self):
        image = {"result":base64.b64encode(image_bytes()).decode()}
        self.driver.outputs = [image, image.copy()]
        self.ai.start(self.payload(mode="image")); self.queue.pop()()
        self.assertEqual(self.jobs()[0]["output_count"], 1)

    def test_excessive_output_count_is_retained_and_blocks_new_paid_request(self):
        self.driver.outputs = [{"result":base64.b64encode(image_bytes()).decode()} for _ in range(5)]
        job_id = self.ai.start(self.payload(mode="image"))["request_id"]; self.queue.pop()()
        self.assertEqual(self.jobs()[0]["status"], "result_ready")
        self.assertTrue((self.store.root/"ai_inputs"/job_id/"result.json").exists())
        self.assertEqual(self.store.state(self.project,self.room)["room"]["variants"], {})
        with self.assertRaises(AtelierConflict):self.ai.start(self.payload(mode="image"))
        self.assertEqual(len(self.driver.calls), 1)

    def test_altered_snapshot_stops_without_a_paid_turn(self):
        job_id = self.ai.start(self.payload())["request_id"]
        (self.store.root / "ai_inputs" / job_id / "input_1.png").write_bytes(b"changed")
        self.queue.pop()()
        self.assertEqual(self.driver.calls, [])
        self.assertEqual(self.jobs()[0]["status"], "not_started")

    def test_annotations_are_visible_in_model_snapshot_without_modifying_original(self):
        self.action("save_draft", project_id=self.project, room_id=self.room, base_id="base", expected_revision=1,
            draft={**self.draft, "annotations": [[[0, 0.5], [1, 0.5]]]})
        original = self.store.asset(self.project, self.room, self.asset, "original")
        self.ai.start(self.payload(expected_revision=2)); self.queue.pop()()
        with Image.open(self.driver.calls[0][1][0]) as image:
            self.assertEqual(image.getpixel((image.width // 2, image.height // 2))[:3], (209, 109, 57))
        self.assertEqual(self.store.asset(self.project, self.room, self.asset, "original"), original)

    def test_action_rejects_untrusted_extra_fields_and_missing_scope(self):
        self.assertFalse(interior_ai_start_action({**self.payload(), "path": "/private"}, service=self.ai)["ok"])
        self.assertFalse(interior_ai_start_action(self.payload(room_id="0" * 32), service=self.ai)["ok"])
        self.assertEqual(self.driver.calls, [])

    def test_production_requests_require_activation_before_catalog_or_paid_turn(self):
        def forbidden(): self.fail("Missing policy must stop before opening a model connection")
        service = InteriorAI(self.store, driver=CodexInteriorDriver(roles_path=self.store.root / "missing.json", client_factory=forbidden))
        self.assertFalse(service.capabilities()["enabled"])
        result = interior_ai_start_action(self.payload(), service=service)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "request_rejected")
        self.assertFalse((self.store.root / "ai_inputs").exists())

    def test_duplicate_worker_callback_cannot_make_a_second_paid_turn(self):
        self.ai.start(self.payload())
        callback = self.queue.pop()
        callback(); callback()
        self.assertEqual(len(self.driver.calls), 1)

    def test_durable_result_can_finish_after_storage_failure_without_model_retry(self):
        self.driver.with_image = True
        job_id = self.ai.start(self.payload(mode="image"))["request_id"]
        with patch.object(self.ai, "_complete_result", side_effect=OSError("PRIVATE_STORAGE_ERROR")):
            self.queue.pop()()
        self.assertEqual(self.jobs()[0]["status"], "result_ready")
        self.assertEqual(self.store.state(self.project, self.room)["room"]["variants"], {})
        self.assertTrue(self.ai.recover(self.project, self.room, job_id)["verified"])
        self.ai.recover(self.project, self.room, job_id)
        self.assertEqual(len(self.driver.calls), 1)
        self.assertEqual(len(self.store.state(self.project, self.room)["room"]["variants"]), 1)

    def test_remote_recovery_only_reads_original_thread_and_prefers_final_answer(self):
        self.driver.fail = True
        job_id = self.ai.start(self.payload())["request_id"]; self.queue.pop()()
        requests = []
        class Client:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            @property
            def transport(self): return self
            def request(self, method, payload):
                requests.append((method, payload))
                return {"thread":{"id":"synthetic-thread","turns":[{"id":"original-turn","status":"completed","items":[
                    {"type":"userMessage","clientId":"atelier-"+job_id},
                    {"type":"agentMessage","phase":"commentary","text":"PRIVATE_PARTIAL"},
                    {"type":"agentMessage","phase":"final_answer","text":"Confirmed original answer"}]}]}}
        self.driver.client_factory = Client
        self.assertTrue(self.ai.recover(self.project, self.room, job_id)["verified"])
        self.assertEqual([method for method, _ in requests], ["thread/read"])
        self.assertEqual(requests[0][1], {"threadId":"synthetic-thread","includeTurns":True})
        self.assertEqual(self.jobs()[0]["answer"], "Confirmed original answer")
        self.assertEqual(len(self.driver.calls), 1)

    def test_more_than_six_selected_images_stops_before_model(self):
        sources = [self.asset]
        for i in range(6):
            sources.append(self.action("add_source",project_id=self.project,room_id=self.room,title="Extra",kind="photo",
                data=base64.b64encode(image_bytes((20+i,20))).decode())["asset_id"])
        self.action("save_draft",project_id=self.project,room_id=self.room,base_id="base",expected_revision=1,
                    draft={**self.draft,"source_ids":sources})
        with self.assertRaises(AtelierError): self.ai.start(self.payload(expected_revision=2))
        self.assertEqual(self.driver.calls, [])

    def test_confirmed_terminal_failure_is_distinct_from_unknown_and_does_not_retry(self):
        class TerminalDriver(FakeDriver):
            def __call__(self, job, images, on_thread):
                self.calls.append(job)
                on_thread("synthetic-thread")
                raise AppServerTurnError("failed", {"message":"PRIVATE_PROVIDER_DETAIL"})
        driver = TerminalDriver()
        service = InteriorAI(self.store, driver=driver, launcher=self.queue.append, require_activation=False)
        payload = self.payload(); service.start(payload); self.queue.pop()()
        public = service.status(self.project,self.room)
        self.assertEqual(public["jobs"][0]["status"], "failed")
        self.assertNotIn("PRIVATE_PROVIDER_DETAIL", str(public))
        self.assertTrue(service.start(payload)["replayed"])
        self.assertEqual(len(driver.calls), 1)
        self.assertEqual(self.queue, [])


class InteriorAIDeletionTests(unittest.TestCase):
    setUp = InteriorAITests.setUp
    action = InteriorAITests.action
    payload = InteriorAITests.payload

    def deletion(self, asset):
        from app.interior_cleanup import DELETE_CONFIRMATION
        plan = self.store.deletion_preview(self.project, self.room, asset)
        return {"action":"delete_source", "request_id":uuid.uuid4().hex, "project_id":self.project,
                "room_id":self.room, "asset_id":asset, "plan_token":plan["plan_token"], "confirmation":DELETE_CONFIRMATION}

    def test_completed_generated_image_and_snapshot_cannot_be_resurrected_by_recover(self):
        output = io.BytesIO(); Image.new("RGB", (40, 40), "red").save(output, format="PNG")
        self.driver.outputs = [{"result":base64.b64encode(output.getvalue()).decode()}]
        job_id = self.ai.start(self.payload(mode="image"))["request_id"]
        self.queue.pop()()
        state = self.store.state(self.project, self.room)
        variant = next(iter(state["room"]["variants"].values()))
        generated = variant["image_source_id"]
        self.store.execute(self.deletion(generated))
        self.assertFalse((self.store.root / "ai_inputs" / job_id).exists())
        self.assertTrue(self.ai.recover(self.project, self.room, job_id)["source_deleted"])
        with self.assertRaises(AtelierConflict):
            self.ai._complete_result(self.project, self.room, job_id,
                {"answer":"Old result", "images":self.driver.outputs, "receipt":{}})
        self.assertEqual(len(self.driver.calls), 1)
        self.assertNotIn(generated, self.store.state(self.project, self.room)["room"]["sources"])
        self.assertEqual(self.store.asset(self.project, self.room, self.asset, "original")[0], image_bytes())

    def test_snapshot_preparation_serializes_with_deletion_and_queued_job_is_preserved(self):
        import threading
        selected = self.deletion(self.asset)
        entered, release = threading.Event(), threading.Event()
        real_asset = self.store.asset
        def pause(*args):
            entered.set()
            if not release.wait(4): raise RuntimeError("test release missing")
            return real_asset(*args)
        results = []
        def start():
            try: results.append(self.ai.start(self.payload()))
            except Exception as error: results.append(error)
        with patch.object(self.store, "asset", side_effect=pause):
            thread = threading.Thread(target=start); thread.start()
            self.assertTrue(entered.wait(3))
            removal = []
            def remove():
                try: removal.append(self.store.execute(selected))
                except Exception as error: removal.append(error)
            deleter = threading.Thread(target=remove); deleter.start()
            release.set(); thread.join(4); deleter.join(4)
        self.assertFalse(thread.is_alive()); self.assertFalse(deleter.is_alive())
        self.assertTrue(results[0]["ok"])
        self.assertIsInstance(removal[0], AtelierConflict)
        self.assertEqual(self.driver.calls, [])
        self.assertEqual(len(self.queue), 1)
        self.assertTrue(self.store.asset(self.project, self.room, self.asset)[0])


if __name__ == "__main__":
    unittest.main()
