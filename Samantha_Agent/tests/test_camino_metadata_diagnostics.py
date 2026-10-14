"""Refusal diagnostics expose technical context, never owner data or secrets."""

import json
import unittest
from unittest.mock import patch

from camino.api.v1 import ApiResponse, MAX_REQUEST_BYTES
from camino.server.metadata_diagnostics import LOGGER, record_metadata_rejection


class MetadataDiagnosticsTests(unittest.TestCase):
    def request(self, **changes):
        body = {"kind": "update_metadata", "device_sequence": 741,
                "epoch": "private-epoch", "operation_id": "private-operation",
                "device_id": "private-phone", "payload": {"title": "private text",
                "location": {"latitude": 12.34567}, "token": "private-token"}}
        body.update(changes)
        return json.dumps(body).encode()

    def refusal(self, code="invalid_request", reason="title target must be an audio session of this Moment"):
        return ApiResponse(422, {"error": {"code": code, "message": reason}})

    def test_known_reason_kind_sequence_logged_and_private_fields_omitted(self):
        response = self.refusal()
        before = json.dumps(response.body)
        with self.assertLogs(LOGGER, level="WARNING") as logs:
            record_metadata_rejection(response, self.request())
        text = " ".join(logs.output)
        for value in ("status=422", "code=invalid_request", "kind=update_metadata", "sequence=741",
                      "title target must be an audio session of this Moment"):
            self.assertIn(value, text)
        for value in ("private", "12.34567", "payload", "latitude"):
            self.assertNotIn(value, text)
        self.assertEqual(json.dumps(response.body), before)

    def test_unknown_reason_code_and_kind_are_redacted(self):
        with self.assertLogs(LOGGER, level="WARNING") as logs:
            record_metadata_rejection(self.refusal("private_secret", "private text\nBearer private-token"),
                                      self.request(kind="private-text"))
        text = " ".join(logs.output)
        self.assertIn("code=redacted reason=redacted kind=unknown", text)
        self.assertNotIn("private", text)

    def test_success_has_no_log(self):
        with self.assertNoLogs(LOGGER, level="WARNING"):
            record_metadata_rejection(ApiResponse(200, {"cursor": 741}), self.request())

    def test_invalid_json_and_large_body_do_not_disclose_content(self):
        for raw in (b"private-token invalid JSON", b"private-token" * (MAX_REQUEST_BYTES // 5)):
            with self.subTest(size=len(raw)), self.assertLogs(LOGGER, level="WARNING") as logs:
                record_metadata_rejection(self.refusal(), raw)
            self.assertIn("kind=unknown sequence=None", logs.output[0])
            self.assertNotIn("private-token", logs.output[0])

    def test_invalid_sequences_are_omitted(self):
        for value in (True, -1, 0, 2**63, "private-sequence"):
            with self.subTest(value=value), self.assertLogs(LOGGER, level="WARNING") as logs:
                record_metadata_rejection(self.refusal(), self.request(device_sequence=value))
            self.assertIn("sequence=None", logs.output[0])

    def test_literal_field_template_can_be_logged(self):
        with self.assertLogs(LOGGER, level="WARNING") as logs:
            record_metadata_rejection(self.refusal(reason="device sequence must be a positive integer"),
                                      self.request())
        self.assertIn("reason=device sequence must be a positive integer", logs.output[0])

    def test_log_failure_cannot_change_api_result(self):
        response = self.refusal()
        with patch.object(LOGGER, "warning", side_effect=RuntimeError("synthetic logger failure")):
            self.assertIsNone(record_metadata_rejection(response, self.request()))
        self.assertEqual(response.status, 422)


if __name__ == "__main__":
    unittest.main()
