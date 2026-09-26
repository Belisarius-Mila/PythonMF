"""Synthetic proxy tests; no live network, launchd or personal data."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import camino_service_network as n
from camino.server.service_safety import private_write


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        private_write(self.root / "owner-token.txt", b"synthetic-token")
        self.endpoint = "synthetic.ts.net:443"
        self.serve = {"TCP": {"443": {"HTTPS": True}}, "Web": {
            self.endpoint: {"Handlers": {"/": {"Proxy": "http://127.0.0.1:8770"}}}}}
        self.original = copy.deepcopy(self.serve)
        self.calls = []
        self.public = False
        self.config = {"server_id": "synthetic-id", "epoch": "synthetic-epoch"}
        self.status = {"owned_definition": True, "running": True, "viewer_granted": False}
        for target, value in (("load_config", self.config), ("control", self.status)):
            p = patch.object(n.service, target, return_value=value)
            p.start()
            self.addCleanup(p.stop)

    def runner(self, argv):
        self.calls.append(argv)
        if argv[1] == "status":
            value = {"BackendState": "Running", "Self": {"Online": True, "DNSName": "synthetic.ts.net."}}
        elif argv[2] == "status":
            value = {"AllowFunnel": {"synthetic": True}} if self.public else self.serve
        else:
            handlers = self.serve["Web"][self.endpoint]["Handlers"]
            if argv[-1] == "off":
                handlers.pop(n.ROUTE)
            else:
                handlers[n.ROUTE] = {"Proxy": n.PROXY}
            value = {}
        return SimpleNamespace(returncode=0, stdout=json.dumps(value))

    def http(self, url, token):
        if not token:
            return 401, {}
        return 200, self.config if url.endswith("/state") else {"scope": "c05a_private_owner"}

    def control(self, action, **kw):
        return n.control(action, self.root, runner=self.runner, http=self.http,
                         cockpit=lambda _: True, **kw)

    def test_enable_status_disable_preserve_cockpit_and_data(self):
        self.assertTrue(self.control("enable")["private_https_checked"])
        count = len([x for x in self.calls if "--yes" in x])
        self.assertTrue(self.control("status")["route_present"])
        self.control("enable")
        self.assertEqual(count, len([x for x in self.calls if "--yes" in x]))
        self.assertFalse(self.control("disable")["route_present"])
        self.assertEqual(self.serve, self.original)
        self.assertEqual((self.root / "owner-token.txt").read_text(), "synthetic-token")
        self.assertFalse((self.root / "readers.sqlite").exists())

    def test_missing_route_status_does_not_write(self):
        before = list(self.root.iterdir())
        self.assertFalse(self.control("status")["route_present"])
        self.assertEqual(list(self.root.iterdir()), before)

    def test_foreign_route_even_same_proxy_requires_receipt(self):
        self.serve["Web"][self.endpoint]["Handlers"][n.ROUTE] = {"Proxy": n.PROXY}
        with self.assertRaises(ValueError):
            self.control("enable")
        self.assertFalse(any("--yes" in x for x in self.calls))

    def test_funnel_fails_closed(self):
        self.public = True
        with self.assertRaises(ValueError):
            self.control("enable")
        self.assertFalse(any("--yes" in x for x in self.calls))

    def test_ambiguous_and_foreign_routes_rejected(self):
        for path in (n.ROUTE, n.ROUTE + "/", n.ROUTE + "/viewer"):
            value = copy.deepcopy(self.original)
            value["Web"][self.endpoint]["Handlers"][path] = {"Proxy": "http://foreign"}
            with self.assertRaises(ValueError):
                n.route_state(value, self.endpoint)

    def test_running_service_required(self):
        self.status["running"] = False
        with self.assertRaises(ValueError):
            self.control("enable")
        self.assertFalse(any("--yes" in x for x in self.calls))

    def test_identity_mismatch_and_unauthorized_success_rejected(self):
        with self.assertRaises(ValueError):
            n.verify_api("http://synthetic", "token", {**self.config, "epoch": "different"}, self.http)
        with self.assertRaises(ValueError):
            n.verify_api("http://synthetic", "token", self.config, lambda url, _: self.http(url, "token"))

    def test_confirmation_required(self):
        with self.assertRaises(SystemExit):
            n.main(["enable"])


if __name__ == "__main__":
    unittest.main()
