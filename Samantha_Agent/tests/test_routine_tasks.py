from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import routine_tasks as tasks


class FakeClient:
    def __init__(self, answer=None, usage=None):
        self.answer = answer or {"summary": "Bez doložených rozporů.", "findings": []}
        self.usage = usage or {"input_tokens": 100, "cached_input_tokens": 0,
            "output_tokens": 20, "reasoning_output_tokens": 5, "total_tokens": 120}
        self.starts = []
        self.turns = []
        self.transport = SimpleNamespace(request=lambda *_: {"data": [
            {"skills": [{"path": "/tmp/test/SKILL.md"}], "errors": []}]})

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def list_models(self, **_):
        return [{"model": "gpt-6.1-sol", "supportedReasoningEfforts": [{"reasoningEffort": "medium"}]}]

    def read_effective_config(self, **_):
        return {"mcp_servers": {"test_server": {"env": {"SECRET": "must-not-leak"}}}}

    def start_thread(self, **kwargs):
        self.starts.append(kwargs)
        return "isolated-thread"

    def send_text(self, **kwargs):
        self.turns.append(kwargs)
        return SimpleNamespace(answer=json.dumps(self.answer), thread_token_usage=self.usage, duration_ms=10)


class RoutineTaskTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.selected = {"role": tasks.ROLE, "model": "gpt-6.1-sol", "reasoning_effort": "medium",
                         "policy_digest": "a" * 64}
        self.sources = {"catalogue": [], "documentation": "Report žádné soubory neukládá."}
        self.enterContext(patch.object(tasks, "ROOT", self.root))
        self.enterContext(patch.object(tasks, "_sources", return_value=self.sources))
        self.enterContext(patch.object(tasks.agent_roles, "resolve_role", return_value=self.selected))
        self.assert_current = self.enterContext(patch.object(tasks.agent_roles, "assert_current"))

    def run_task(self, client):
        return tasks.run_routine_task(tasks.TASK, confirmed=True, client_factory=lambda: client)

    def test_unknown_type_and_missing_confirmation_make_no_model_call(self):
        def unexpected():
            self.fail("Unapproved routing started a model")
        result = tasks.run_routine_task("change_camino", confirmed=True, client_factory=unexpected)
        self.assertEqual(result["action"], "return_to_adam")
        result = tasks.run_routine_task(tasks.TASK, client_factory=unexpected)
        self.assertEqual(result["action"], "confirmation_required")

    def test_one_isolated_turn_disables_tools_and_does_not_send_credentials(self):
        client = FakeClient()
        result = self.run_task(client)
        self.assertEqual(result["state"], "completed")
        self.assertEqual(len(client.starts), 1)
        self.assertEqual(len(client.turns), 1)
        start, turn = client.starts[0], client.turns[0]
        self.assertTrue(start["ephemeral"])
        self.assertEqual(start["sandbox"], "read-only")
        self.assertFalse(start["config_overrides"]["mcp_servers.test_server.enabled"])
        self.assertFalse(start["config_overrides"]["features.apps"])
        self.assertFalse(start["config_overrides"]["features.shell_tool"])
        self.assertFalse(start["config_overrides"]["features.memories"])
        self.assertEqual(start["config_overrides"]["skills.config"], [{"path": "/tmp/test", "enabled": False}])
        self.assertEqual(start["base_instructions"], tasks.INSTRUCTIONS)
        self.assertFalse(turn["sandbox_policy"]["networkAccess"])
        self.assertEqual(turn["sandbox_policy"], {"type": "readOnly", "networkAccess": False})
        self.assertNotIn("must-not-leak", json.dumps(client.turns))
        self.assertNotIn("must-not-leak", json.dumps(result))
        self.assert_current.assert_called_once()

    def test_oversized_sources_stop_before_model_turn(self):
        self.sources["documentation"] = "x" * tasks.MAX_INPUT_BYTES
        client = FakeClient()
        self.assertEqual(self.run_task(client)["state"], "attention")
        self.assertEqual(client.turns, [])

    def test_fabricated_quote_is_rejected_without_retry(self):
        client = FakeClient({"summary": "Rozpor", "findings": [
            {"quote": "Tato citace v podkladu není.", "explanation": "Vymyšlený nález."}]})
        self.assertEqual(self.run_task(client)["state"], "attention")
        self.assertEqual(len(client.turns), 1)

    def test_evidenced_finding_requires_human_review(self):
        client = FakeClient({"summary": "Rozpor", "findings": [
            {"quote": self.sources["documentation"], "explanation": "Ověřit proti katalogu."}]})
        self.assertEqual(self.run_task(client)["state"], "review")

    def test_missing_usage_and_exceeded_budget_do_not_trigger_retry(self):
        for usage in ({"input_tokens": -1}, {"input_tokens": 40_000, "cached_input_tokens": 0,
                "output_tokens": 0, "reasoning_output_tokens": 0, "total_tokens": 40_000}):
            client = FakeClient(usage=usage)
            with self.subTest(usage=usage):
                self.assertEqual(self.run_task(client)["state"], "attention")
                self.assertEqual(len(client.turns), 1)

    def test_source_drift_requires_review_instead_of_accepting_stale_result(self):
        with patch.object(tasks, "_sources", side_effect=[self.sources, {**self.sources, "catalogue": ["changed"]}]):
            self.assertEqual(self.run_task(FakeClient())["state"], "attention")

    def test_changed_role_does_not_accept_the_completed_result(self):
        self.assert_current.side_effect = tasks.agent_roles.AgentRoleError("Policy changed")
        result = self.run_task(FakeClient())
        self.assertEqual(result["state"], "attention")
        self.assertIsNotNone(result["token_usage"])

    def test_provider_rejection_is_returned_without_retry_or_raw_error(self):
        client = FakeClient()
        with patch.object(client, "send_text", side_effect=tasks.AppServerError("private diagnostic")) as send:
            result = self.run_task(client)
        self.assertEqual(result["state"], "attention")
        self.assertEqual(send.call_count, 1)
        self.assertNotIn("private diagnostic", json.dumps(result))

    def test_synthetic_probe_does_not_approve_role(self):
        client = FakeClient({"summary": "Rozpor", "findings": [{
            "quote": "automaticky ukládá soubor", "explanation": "Katalog uvádí report bez ukládání."}]})
        result = tasks.probe_routine_reviewer("gpt-6.1-sol", "medium", client_factory=lambda: client)
        self.assertTrue(result["passed"])
        self.assert_current.assert_not_called()


if __name__ == "__main__":
    unittest.main()
