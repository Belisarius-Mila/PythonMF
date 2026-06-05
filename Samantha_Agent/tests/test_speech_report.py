from __future__ import annotations

import json
import unittest

from app.speech.report import speak_report


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class SpeechReportTests(unittest.TestCase):
    def test_speak_report_uses_cockpit_endpoint(self) -> None:
        calls = []

        def fake_opener(request, timeout):
            calls.append((request, timeout))
            body = json.loads(request.data.decode("utf-8"))
            self.assertEqual(body["text"], "Hotovo. Report.")
            return FakeResponse({"ok": True, "message": "Přečteno."})

        result = speak_report("Hotovo. Report.", opener=fake_opener)

        self.assertTrue(result["ok"])
        self.assertEqual(result["transport"], "cockpit")
        self.assertEqual(result["message"], "Přečteno.")
        self.assertEqual(len(calls), 1)

    def test_speak_report_returns_cockpit_error_without_fallback(self) -> None:
        def fake_opener(request, timeout):
            return FakeResponse({"ok": False, "message": "Audio chyba."})

        result = speak_report("Test", opener=fake_opener, allow_local_fallback=False)

        self.assertFalse(result["ok"])
        self.assertEqual(result["transport"], "cockpit")
        self.assertEqual(result["message"], "Audio chyba.")


if __name__ == "__main__":
    unittest.main()
