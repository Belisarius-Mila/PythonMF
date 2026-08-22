from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.request import Request, urlopen

from app import cockpit


class _SyntheticScanDocuHandler(BaseHTTPRequestHandler):
    received: list[tuple[str, str, dict[str, object]]] = []

    def do_GET(self) -> None:  # noqa: N802
        payload = b"<!doctype html><title>Synthetic ScanDocu</title>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or "0")
        data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        self.received.append((self.command, self.path, data))
        payload = json.dumps({"ok": True, "proxied": True}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


class CockpitScanDocuProxyTests(unittest.TestCase):
    def setUp(self) -> None:
        _SyntheticScanDocuHandler.received = []
        self.upstream = ThreadingHTTPServer(("127.0.0.1", 0), _SyntheticScanDocuHandler)
        self.upstream_thread = threading.Thread(target=self.upstream.serve_forever, daemon=True)
        self.upstream_thread.start()

        cockpit_app = cockpit.CockpitServer(host="127.0.0.1", port=0)
        self.cockpit = ThreadingHTTPServer(("127.0.0.1", 0), cockpit_app.make_handler())
        self.cockpit_thread = threading.Thread(target=self.cockpit.serve_forever, daemon=True)
        self.cockpit_thread.start()
        self.cockpit_url = f"http://127.0.0.1:{self.cockpit.server_address[1]}"
        self.patches = (
            patch(
                "app.cockpit.SCANDOCU_URL",
                f"http://127.0.0.1:{self.upstream.server_address[1]}",
            ),
            patch("app.cockpit.start_scandocu", return_value={"ok": True}),
        )
        for active_patch in self.patches:
            active_patch.start()

    def tearDown(self) -> None:
        for active_patch in reversed(self.patches):
            active_patch.stop()
        self.cockpit.shutdown()
        self.cockpit.server_close()
        self.cockpit_thread.join(timeout=5)
        self.upstream.shutdown()
        self.upstream.server_close()
        self.upstream_thread.join(timeout=5)

    def test_same_origin_get_forwards_scandocu_page_and_query(self) -> None:
        with urlopen(
            f"{self.cockpit_url}/scandocu/?mode=review&document_ref=docref-0123456789abcdef",
            timeout=5,
        ) as response:
            page = response.read().decode("utf-8")

        self.assertIn("Synthetic ScanDocu", page)
        self.assertEqual(response.headers.get("Cross-Origin-Resource-Policy"), "same-origin")

    def test_same_origin_post_forwards_only_allowlisted_scandocu_action(self) -> None:
        request = Request(
            f"{self.cockpit_url}/api/scandocu/save",
            data=json.dumps({"token": "synthetic-token", "title": "Test"}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Origin": self.cockpit_url,
            },
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))

        self.assertTrue(result["proxied"])
        self.assertEqual(
            _SyntheticScanDocuHandler.received,
            [("POST", "/api/save", {"token": "synthetic-token", "title": "Test"})],
        )

    def test_proxy_and_public_url_are_fail_closed(self) -> None:
        self.assertEqual(
            cockpit.scandocu_cockpit_url(
                mode="review",
                document_ref="docref-0123456789abcdef",
            ),
            "/scandocu/?mode=review&document_ref=docref-0123456789abcdef",
        )
        self.assertEqual(
            cockpit.scandocu_proxy_path("GET", "/scandocu/pdf/safe-token_1"),
            "/pdf/safe-token_1",
        )
        self.assertIsNone(cockpit.scandocu_proxy_path("GET", "/scandocu/../../private"))
        self.assertIsNone(cockpit.scandocu_proxy_path("POST", "/api/scandocu/unknown"))
        with self.assertRaises(ValueError):
            cockpit.scandocu_cockpit_url(mode="review", document_ref="selected-review-document")


if __name__ == "__main__":
    unittest.main()
