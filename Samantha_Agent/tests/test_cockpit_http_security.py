from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock, patch

from app.cockpit import COCKPIT_SECURITY_HEADERS, MAX_JSON_BODY_BYTES, CockpitServer, log_cockpit_http_event
from app.file_persistence import lock_path_for
from app.speech.transcribe import MAX_AUDIO_BYTES


@contextmanager
def running_cockpit_server() -> Iterator[tuple[str, int, MagicMock]]:
    host = "127.0.0.1"
    handler = CockpitServer(host=host, port=0).make_handler()
    server = ThreadingHTTPServer((host, 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    with patch("app.cockpit.log_cockpit_http_event") as event_logger:
        thread.start()
        try:
            yield host, int(server.server_address[1]), event_logger
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3.0)


def request_json(
    host: str,
    port: int,
    method: str,
    path: str,
    *,
    body: str | bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, object], http.client.HTTPMessage]:
    connection = http.client.HTTPConnection(host, port, timeout=5.0)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        return response.status, payload, response.headers
    finally:
        connection.close()


class CockpitHttpSecurityTests(unittest.TestCase):
    def test_security_headers_are_present_on_normal_response(self) -> None:
        with running_cockpit_server() as (host, port, _logger):
            status, payload, headers = request_json(host, port, "GET", "/api/server/health")

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        for name, value in COCKPIT_SECURITY_HEADERS:
            self.assertEqual(headers.get(name), value)
        self.assertNotIn("Python", headers.get("Server", ""))

    def test_command_cheatsheet_endpoint_is_read_only_text_data(self) -> None:
        with running_cockpit_server() as (host, port, _logger):
            status, payload, headers = request_json(host, port, "GET", "/api/command-cheatsheet")

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["sections"]), 4)
        self.assertNotIn("action", json.dumps(payload, ensure_ascii=False))
        self.assertNotIn("html", json.dumps(payload, ensure_ascii=False).casefold())
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")

    def test_invalid_json_returns_controlled_400(self) -> None:
        with running_cockpit_server() as (host, port, logger):
            status, payload, _headers = request_json(
                host,
                port,
                "POST",
                "/api/speech/speak",
                body="{",
                headers={
                    "Content-Type": "application/json",
                    "Origin": f"http://{host}:{port}",
                },
            )

        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "invalid_json")
        logger.assert_called_once()

    def test_non_json_content_type_returns_415(self) -> None:
        with running_cockpit_server() as (host, port, _logger):
            status, payload, _headers = request_json(
                host,
                port,
                "POST",
                "/api/speech/speak",
                body="{}",
                headers={
                    "Content-Type": "text/plain",
                    "Origin": f"http://{host}:{port}",
                },
            )

        self.assertEqual(status, 415)
        self.assertEqual(payload["error"], "json_content_type_required")

    def test_oversized_json_is_rejected_before_body_read(self) -> None:
        with running_cockpit_server() as (host, port, _logger):
            connection = http.client.HTTPConnection(host, port, timeout=5.0)
            try:
                connection.putrequest("POST", "/api/speech/speak", skip_host=True)
                connection.putheader("Host", f"{host}:{port}")
                connection.putheader("Origin", f"http://{host}:{port}")
                connection.putheader("Content-Type", "application/json")
                connection.putheader("Content-Length", str(MAX_JSON_BODY_BYTES + 1))
                connection.endheaders()
                response = connection.getresponse()
                payload = json.loads(response.read().decode("utf-8"))
            finally:
                connection.close()

        self.assertEqual(response.status, 413)
        self.assertEqual(payload["error"], "request_too_large")

    def test_body_limit_keeps_maximum_voice_recording_available(self) -> None:
        maximum_base64_size = ((MAX_AUDIO_BYTES + 2) // 3) * 4
        self.assertGreater(MAX_JSON_BODY_BYTES, maximum_base64_size + 1024)

    def test_cross_origin_post_is_rejected_before_action(self) -> None:
        with running_cockpit_server() as (host, port, _logger):
            with patch("app.cockpit.cockpit_speak_action") as action:
                status, payload, _headers = request_json(
                    host,
                    port,
                    "POST",
                    "/api/speech/speak",
                    headers={"Origin": "https://example.invalid"},
                )

        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "origin_forbidden")
        action.assert_not_called()

    def test_tailscale_host_and_matching_origin_are_allowed(self) -> None:
        with running_cockpit_server() as (host, port, _logger):
            with patch("app.cockpit.cockpit_speak_action", return_value={"ok": True, "status": "ready"}):
                connection = http.client.HTTPConnection(host, port, timeout=5.0)
                try:
                    connection.putrequest("POST", "/api/speech/speak", skip_host=True)
                    connection.putheader("Host", "100.64.0.10:8770")
                    connection.putheader("Origin", "http://100.64.0.10:8770")
                    connection.putheader("Content-Length", "0")
                    connection.endheaders()
                    response = connection.getresponse()
                    payload = json.loads(response.read().decode("utf-8"))
                finally:
                    connection.close()

        self.assertEqual(response.status, 200)
        self.assertTrue(payload["ok"])

    def test_invalid_host_is_rejected(self) -> None:
        with running_cockpit_server() as (host, port, _logger):
            connection = http.client.HTTPConnection(host, port, timeout=5.0)
            try:
                connection.putrequest("GET", "/api/server/health", skip_host=True)
                connection.putheader("Host", "example.invalid")
                connection.endheaders()
                response = connection.getresponse()
                payload = json.loads(response.read().decode("utf-8"))
            finally:
                connection.close()

        self.assertEqual(response.status, 400)
        self.assertEqual(payload["error"], "invalid_host")

    def test_internal_error_returns_generic_500_without_exception_text(self) -> None:
        with running_cockpit_server() as (host, port, logger):
            with patch("app.cockpit.server_health_status", side_effect=RuntimeError("private detail")):
                status, payload, headers = request_json(host, port, "GET", "/api/server/health")

        self.assertEqual(status, 500)
        self.assertEqual(payload["error"], "internal_error")
        self.assertNotIn("private detail", json.dumps(payload))
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(logger.call_args.kwargs["detail"], "RuntimeError")

    def test_private_event_log_strips_query_and_never_receives_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "http_events.jsonl"
            log_cockpit_http_event(
                event="invalid_json",
                method="POST",
                request_path="/api/example?private=value",
                status=400,
                detail="JSONDecodeError",
                path=path,
            )
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(lock_path_for(path).exists())

        self.assertEqual(record["path"], "/api/example")
        self.assertNotIn("private", json.dumps(record))
        self.assertEqual(set(record), {"created_at", "event", "method", "path", "status", "detail"})


if __name__ == "__main__":
    unittest.main()
