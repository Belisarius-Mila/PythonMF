"""Small offline tests: worker lifecycle and the configuration-only Cockpit link."""

import json
import os
import subprocess
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.camino_viewer_link import camino_viewer_link_status
from camino.server.viewer_worker import ViewerWorker
from scripts.cockpit_quality_gate import node_binary


class ViewerRuntimeTests(unittest.TestCase):
    def test_link_accepts_only_private_https_without_credentials_or_queries(self):
        valid = ["https://mac.tail123.ts.net/viewer/", "https://mac.tail123.ts.net/camino-api/viewer/"]
        invalid = ["", "https://example.com/viewer/", "http://mac.tail123.ts.net/viewer/",
                   "https://user:secret@mac.tail123.ts.net/viewer/", valid[0] + "?token=secret",
                   valid[0] + "#secret", "https://mac.tail123.ts.net.evil.test/viewer/",
                   "https://mac.tail123.ts.net/../viewer/", "https://mac.tail123.ts.net/viewer/\n"]
        for url in valid + invalid:
            with self.subTest(url=url), patch.dict(os.environ, {"CAMINO_VIEWER_URL": url}):
                state = camino_viewer_link_status()
                self.assertEqual(state["configured"], url in valid)
                self.assertEqual(state["url"], url if url in valid else "")
                self.assertNotIn("running", state)
                self.assertNotIn("secret", json.dumps(state))

    def test_cockpit_shortcut_updates_and_removes_stale_link_without_network(self):
        source = Path("app/frontend/cockpit/app.js").read_text()
        function = source[source.index("    function renderCaminoViewerLink("):source.index("\t    function renderDashboard(")]
        javascript = r'''
const assert = require('node:assert/strict');
const link = {hidden: true, href: undefined, classList: {toggle(_key, value) {link.hidden = value;}},
  setAttribute(_key, value) {this.href = value;}, removeAttribute() {this.href = undefined;}};
const status = {};
const document = {getElementById(id) {return id === 'caminoViewerLink' ? link : status;}};
'''
        javascript += function + r'''
renderCaminoViewerLink({configured: true, url: 'https://mac.tail123.ts.net/camino-api/viewer/'});
assert.equal(link.hidden, false);
assert.match(link.href, /camino-api\/viewer\/$/);
for (const url of ['javascript:alert(1)', 'https://public.example/viewer/',
  'https://mac.tail123.ts.net/viewer/?token=secret', 'https://mac.tail123.ts.net/viewer/\n']) {
  renderCaminoViewerLink({configured: true, url});
  assert.equal(link.hidden, true);
  assert.equal(link.href, undefined);
}
renderCaminoViewerLink(null);
assert.equal(link.hidden, true);
assert.ok(!status.textContent.includes('běží'));
'''
        run = subprocess.run([node_binary(), "-"], input=javascript, text=True, capture_output=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        html = Path("app/frontend/cockpit/page.html").read_text()
        self.assertIn('id="caminoViewerLink" target="_blank" rel="noopener noreferrer"', html)

    def test_worker_is_serial_cooperative_and_can_restart(self):
        entered, leave = threading.Event(), threading.Event()
        calls = []
        cancelled = []
        def build(*, should_stop):
            calls.append(1)
            entered.set()
            leave.wait(3)
            cancelled.append(should_stop())
            return {"ready": 0, "waiting": 1}
        viewer = SimpleNamespace(build_pending=build, build_state="manual")
        worker = ViewerWorker(viewer, interval=60)
        worker.start()
        self.assertTrue(entered.wait(3))
        with self.assertRaises(RuntimeError):
            worker.start()
        worker.stopping.set()
        leave.set()
        worker.stop()
        self.assertEqual(len(calls), 1)
        self.assertEqual(cancelled, [True])
        self.assertFalse(worker.thread.is_alive())
        self.assertEqual(viewer.build_state, "stopped")
        entered.clear()
        def second(*, should_stop):
            entered.set()
            return {"ready": 1, "waiting": 0}
        viewer.build_pending = second
        worker.start()
        try:
            self.assertTrue(entered.wait(3))
        finally:
            worker.stop()
        self.assertFalse(worker.thread.is_alive())

    def test_worker_retries_failure_without_exporting_exception_detail(self):
        recovered = threading.Event()
        calls = []
        viewer = SimpleNamespace(build_state="manual")
        def build(*, should_stop):
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("PRIVATE-TEXT-AND-PATH")
            self.assertEqual(viewer.build_state, "building")
            recovered.set()
            return {"ready": 1, "waiting": 0}
        viewer.build_pending = build
        worker = ViewerWorker(viewer, interval=1)
        worker.start()
        try:
            self.assertTrue(recovered.wait(4))
        finally:
            worker.stop()
        self.assertEqual(len(calls), 2)
        self.assertNotIn("PRIVATE", viewer.build_state)

    def test_invalid_worker_intervals_are_rejected(self):
        for interval in (0, -1, 3601, float("inf"), float("nan")):
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                ViewerWorker(None, interval=interval)
