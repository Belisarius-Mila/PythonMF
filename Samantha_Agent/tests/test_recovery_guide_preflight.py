from dataclasses import replace
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app import recovery_guide_preflight as f
from app import recovery_guide_maintainer as m
from tests import test_recovery_guide as fixtures

snapshot = fixtures.snapshot
USAGE = fixtures.USAGE


class Encoding:
    name = "test_reference"
    def encode_ordinary(self, text):
        return list(text)


class Tokenizers:
    def __init__(self, mapped=False):
        self.mapped = mapped
        self.references = []
    def encoding_for_model(self, model):
        assert model == "gpt-6.1-sol"
        if not self.mapped:
            raise KeyError(model)
        return Encoding()
    def get_encoding(self, name):
        self.references.append(name)
        return Encoding()


class Preflight(unittest.TestCase):
    def test_unknown_model_has_no_silent_encoding_fallback(self):
        module = Tokenizers()
        self.assertFalse(f.tokenizer_probe(module)["exact_model_mapping"])
        with self.assertRaises(f.TokenizerUnavailable):
            f.exact_text_counter(module)
        self.assertEqual(module.references, [])

    def test_upstream_mapping_is_explicit_and_does_not_prove_entire_prompt(self):
        module = Tokenizers(mapped=True)
        probe = f.tokenizer_probe(module)
        self.assertTrue(probe["exact_model_mapping"])
        self.assertFalse(probe["full_appserver_prompt_exact"])
        self.assertEqual(f.exact_text_counter(module)("žluťoučký"), 9)

    def test_reference_count_is_blocked_not_a_live_approval(self):
        module = Tokenizers()
        result = f.reference_preflight(snapshot(), limits=m.Limits(10_000,1000,8,50,100,60), module=module)
        self.assertEqual(result["state"], "blocked_for_live_pilot")
        self.assertFalse(result["reference_is_model_mapping"])
        self.assertEqual(result["coverage_planned"]["ratio"], 1)
        self.assertFalse(result["billing_hard_cap"])
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(module.references, ["o200k_base"])
        self.assertEqual(result["planned_calls_including_synthesis"], 2)
        self.assertNotIn("1. OBNOVA MACU", json.dumps(result))

    def test_reference_diagnostic_still_does_not_activate_with_known_text_map(self):
        result = f.reference_preflight(snapshot(), limits=m.Limits(10_000,1000,8,50,100,60), module=Tokenizers(True))
        self.assertEqual(result["state"], "blocked_for_live_pilot")
        self.assertFalse(result["reference_is_model_mapping"])

    def test_separate_inspection_and_synthesis_reservations(self):
        limits = m.Limits(10_000,1000,8,50,100,60)
        original = m.plan(snapshot(), len, limits)
        split = m.plan(snapshot(), len, replace(limits,inspection_output_tokens=100))
        self.assertEqual(split["output_bound"], 1100)
        self.assertLess(split["reserved_credits"], original["reserved_credits"])
        with self.assertRaises(ValueError):
            m.plan(snapshot(), len, replace(limits,inspection_output_tokens=0))

    def test_no_tiktoken_is_not_an_auto_install(self):
        with patch.object(f.importlib,"import_module",side_effect=ImportError()):
            self.assertEqual(f.tokenizer_probe()["state"], "unavailable")

    def test_runtime_projection_omits_prompt_and_secret_config(self):
        from tests.test_routine_tasks import FakeClient
        client = FakeClient()
        client.version = SimpleNamespace(raw="local-test")
        client.server_version = SimpleNamespace(raw="server-test")
        result = f.runtime_observation(lambda: client)
        self.assertEqual(result["state"], "observed")
        self.assertTrue(result["model_medium_available"])
        self.assertFalse(result["live_isolation_proven"])
        self.assertNotIn("SECRET",json.dumps(result))
        self.assertFalse(client.turns)
        self.assertFalse(client.starts)

    def test_runtime_failure_does_not_start_replacement_service(self):
        def fail():
            raise OSError("do not expose private details")
        result = f.runtime_observation(fail)
        self.assertEqual(result["state"], "unavailable")
        self.assertFalse(result["automatic_retry"])
        self.assertNotIn("private",json.dumps(result))

    def test_fast_runtime_is_observed_but_never_declared_ready(self):
        from tests.test_routine_tasks import FakeClient
        client = FakeClient()
        client.version = client.server_version = SimpleNamespace(raw="test")
        client.read_effective_config = lambda **_: {"service_tier":"fast"}
        result = f.runtime_observation(lambda: client)
        self.assertFalse(result["standard_preference_compatible"])
        self.assertFalse(result["ready_for_paid_pilot"])
        self.assertFalse(client.turns)


class BudgetReceipts(unittest.TestCase):
    setUp = fixtures.Pilot.setUp
    run_pilot = fixtures.Pilot.run_pilot
    call = fixtures.Pilot.call
    def test_split_inspection_cap_stops_before_synthesis_and_preserves_usage(self):
        usage = {**USAGE,"output_tokens":101,"total_tokens":201}
        result = self.run_pilot(limits=replace(self.limits,inspection_output_tokens=100),
                               call=lambda *_: {"answer":{},"usage":usage})
        self.assertEqual(result["state"], "attention")
        self.assertEqual(result["model_calls"], 1)
        self.assertGreater(result["credits"], 0)
        self.assertEqual(result["turns"][0]["usage"], usage)

    def test_month_uses_known_overrun_instead_of_smaller_reservation(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        usage = {**USAGE,"input_tokens":2_000_000,"output_tokens":101,"total_tokens":2_000_101}
        result = self.run_pilot(limits=replace(self.limits,inspection_output_tokens=100),
                               call=lambda *_: {"answer":{},"usage":usage})
        self.assertGreater(result["credits"], result["reserved_credits"])
        self.now = datetime(2026,11,15,10,tzinfo=ZoneInfo("Europe/Prague"))
        next_week = self.run_pilot(limits=replace(self.limits,month_credits=50))
        self.assertEqual(next_week["state"], "budget_blocked")


if __name__ == "__main__":
    unittest.main()
