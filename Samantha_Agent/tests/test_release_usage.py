from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.release_usage import estimate_standard_credits, native_usage_snapshot, normalize_usage, usage_delta


USAGE = dict(input_tokens=1000, cached_input_tokens=800, output_tokens=100,
             reasoning_output_tokens=40, total_tokens=1100)


class ReleaseUsageTests(unittest.TestCase):
    def test_cached_and_reasoning_tokens_are_not_double_billed(self):
        self.assertEqual(estimate_standard_credits("gpt-6.1-sol", USAGE), .037)
        self.assertEqual(estimate_standard_credits("gpt-6-luna", USAGE), .00195)
        self.assertIsNone(estimate_standard_credits("unknown", USAGE))

    def test_missing_or_inconsistent_telemetry_is_unknown(self):
        for value in (None, {}, {**USAGE, "input_tokens": True},
                      {**USAGE, "cached_input_tokens": 1001},
                      {**USAGE, "reasoning_output_tokens": 101}, {**USAGE, "total_tokens": 1140}):
            with self.subTest(value=value):
                self.assertIsNone(normalize_usage(value))

    def test_projection_discards_private_extras(self):
        self.assertEqual(normalize_usage({**USAGE, "secret": "private"}), USAGE)

    def test_delta_rejects_reset_and_changed_model(self):
        before = dict(thread_id="thread", model="gpt-6.1-sol", usage=USAGE)
        after = {**before, "usage": {key: value * 2 for key, value in USAGE.items()}}
        self.assertEqual(usage_delta(before, after)["usage"], USAGE)
        with self.assertRaises(ValueError):
            usage_delta(after, before)
        with self.assertRaises(ValueError):
            usage_delta(before, {**after, "model": "gpt-6-luna"})

    def test_native_snapshot_reads_only_selected_numeric_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); day = root / "2026/10/17"; day.mkdir(parents=True)
            identity = "00000000-0000-0000-0000-000000000001"
            events = [
                {"type":"turn_context","payload":{"model":"gpt-6.1-sol","effort":"high","private":"secret"}},
                {"type":"response_item","payload":{"private":"prompt and answer"}},
                {"type":"event_msg","timestamp":"now","payload":{"type":"token_count","info":{"total_token_usage":USAGE}}},
            ]
            (day / f"rollout-{identity}.jsonl").write_text("\n".join(map(json.dumps, events)) + "\n{")
            result = native_usage_snapshot(identity, sessions_root=root)
            self.assertEqual(result["usage"], USAGE)
            self.assertNotIn("private", json.dumps(result))
            self.assertNotIn("prompt", json.dumps(result))
            with self.assertRaises(ValueError):
                native_usage_snapshot("../other", sessions_root=root)
