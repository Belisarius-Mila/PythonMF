from __future__ import annotations

import os
import http.client
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from app import cockpit
from scripts.cockpit_server import load_cockpit_environment


class CockpitServerEnvironmentTests(unittest.TestCase):
    def test_loads_missing_value_from_local_dotenv(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("SAMANTHA_TEST_COCKPIT_ENV=from-dotenv\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                loaded = load_cockpit_environment(env_path)

                self.assertTrue(loaded)
                self.assertEqual(os.environ["SAMANTHA_TEST_COCKPIT_ENV"], "from-dotenv")

    def test_preserves_process_environment_value(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("SAMANTHA_TEST_COCKPIT_ENV=from-dotenv\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {"SAMANTHA_TEST_COCKPIT_ENV": "from-process"},
                clear=False,
            ):
                loaded = load_cockpit_environment(env_path)

                self.assertTrue(loaded)
                self.assertEqual(os.environ["SAMANTHA_TEST_COCKPIT_ENV"], "from-process")


class CaminoFilmReviewRouteTests(unittest.TestCase):
    def test_only_review_page_and_films_are_served_with_video_ranges(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            (root / "review.html").write_text("review", encoding="utf-8")
            (root / "final-fed41c8f9697").mkdir()
            (root / "final-fed41c8f9697" / "film.mp4").write_bytes(b"0123456789")
            (root / "secret.txt").write_text("hidden", encoding="utf-8")
            with patch.dict(cockpit.LOCAL_WEB_APPS, {"camino-p2a-review": root}):
                server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                    base = "/local-apps/camino-p2a-review/"
                    conn.request("GET", base + "review.html")
                    response = conn.getresponse()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), b"review")
                    conn.request("GET", base + "final-fed41c8f9697/film.mp4", headers={"Range": "bytes=2-5"})
                    response = conn.getresponse()
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.getheader("Content-Type"), "video/mp4")
                    self.assertEqual(response.getheader("Content-Range"), "bytes 2-5/10")
                    self.assertEqual(response.read(), b"2345")
                    conn.request("GET", base + "secret.txt")
                    response = conn.getresponse()
                    self.assertEqual(response.status, 404)
                    response.read()
                    conn.request("GET", base + "final-fed41c8f9697/film.mp4", headers={"Range": "bytes=99-"})
                    response = conn.getresponse()
                    self.assertEqual(response.status, 416)
                    self.assertEqual(response.getheader("Content-Range"), "bytes */10")
                    response.read()
                    conn.close()
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)


    def test_range_parser_handles_open_and_suffix_ranges(self) -> None:
        self.assertEqual(cockpit.parse_single_http_byte_range("bytes=4-", 10), (4, 9))
        self.assertEqual(cockpit.parse_single_http_byte_range("bytes=-3", 10), (7, 9))
        self.assertEqual(cockpit.parse_single_http_byte_range("bytes=0-99", 10), (0, 9))


if __name__ == "__main__":
    unittest.main()
