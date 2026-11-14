from __future__ import annotations

import copy
import http.client
import json
import os
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch

from app import cockpit
from app.cockpit_https_entry import HttpsCockpitEntry, private_https_origin, read_serve_status


ORIGIN = "https://samantha.example.ts.net"
STATUS = {
    "TCP": {"443": {"HTTPS": True}, "8770": {"TCPForward": "127.0.0.1:8770"}},
    "Web": {"samantha.example.ts.net:443": {"Handlers": {
        "/": {"Proxy": "http://127.0.0.1:8770"},
        "/camino-api": {"Proxy": "http://127.0.0.1:8767"},
    }}},
}
HEADERS = {"Host": "100.64.0.1:8770", "Accept": "text/html", "Sec-Fetch-Dest": "document"}


class HttpsCockpitEntryTests(unittest.TestCase):
    def test_requires_one_private_https_root_for_this_server(self):
        self.assertEqual(private_https_origin(STATUS), ORIGIN)
        for invalid in [None, [], {}, {**STATUS, "TCP": {"443": {"HTTPS": False}}},
                        {**STATUS, "AllowFunnel": {"samantha.example.ts.net:443": True}},
                        {**STATUS, "Web": []}, {**STATUS, "AllowFunnel": []}]:
            with self.subTest(invalid=invalid):
                self.assertIsNone(private_https_origin(invalid))

    def test_rejects_ambiguous_hosts_wrong_proxy_and_untrusted_authorities(self):
        ambiguous = copy.deepcopy(STATUS)
        ambiguous["Web"]["other.example.ts.net:443"] = copy.deepcopy(next(iter(STATUS["Web"].values())))
        self.assertIsNone(private_https_origin(ambiguous))
        for authority in ["example.com:443", "user@samantha.example.ts.net:443",
                          "samantha.example.ts.net:8443", "samantha.example.ts.net:443/",
                          "samantha.example.ts.net.evil.com:443", "x\r\n.ts.net:443"]:
            bad = copy.deepcopy(STATUS)
            bad["Web"] = {authority: next(iter(STATUS["Web"].values()))}
            self.assertIsNone(private_https_origin(bad))
        for proxy in ["http://127.0.0.1:8767", "https://example.com", "http://127.0.0.1:8770/other"]:
            bad = copy.deepcopy(STATUS)
            next(iter(bad["Web"].values()))["Handlers"]["/"]["Proxy"] = proxy
            self.assertIsNone(private_https_origin(bad))

    def test_only_browser_root_on_legacy_remote_port_redirects(self):
        loader = Mock(return_value=STATUS)
        entry = HttpsCockpitEntry(status_loader=loader)
        self.assertEqual(entry.redirect_target('/?next=https%3A%2F%2Fevil.com&x=1', HEADERS),
                         ORIGIN + '/?next=https%3A%2F%2Fevil.com&x=1')
        self.assertEqual(entry.redirect_target('/', {"Host": "old.example.ts.net:8770", "Accept": "text/html"}), ORIGIN + '/')
        self.assertEqual(loader.call_count, 1)

    def test_apis_fetches_local_hosts_and_https_never_even_discover(self):
        loader = Mock(return_value=STATUS)
        entry = HttpsCockpitEntry(status_loader=loader)
        for path, headers in [
            ('/api/server/health', HEADERS), ('/calendar/task/', HEADERS),
            ('//evil.com/', HEADERS), ('http://evil.com/', HEADERS),
            *[('/', {**HEADERS, 'Host': host}) for host in
              ['localhost:8770', 'localhost.:8770', '127.0.0.1:8770', '127.0.0.1.:8770', '[::1]:8770', 'samantha.example.ts.net',
               'samantha.example.ts.net:443', '100.64.0.1:9000', 'bad:port']],
            ('/', {'Host':'100.64.0.1:8770'}),
            ('/', {**HEADERS, 'Sec-Fetch-Dest':'empty'}),
            ('/', {**HEADERS, 'Sec-Fetch-Mode':'cors'}),
        ]:
            with self.subTest(path=path, headers=headers):
                self.assertIsNone(entry.redirect_target(path, headers))
        HttpsCockpitEntry(enabled=False, status_loader=loader).redirect_target('/', HEADERS)
        loader.assert_not_called()

    def test_discovery_failure_preserves_http_and_retries_only_after_cache_expiry(self):
        now = [100.0]
        loader = Mock(side_effect=[subprocess.TimeoutExpired('tailscale', 2), STATUS])
        entry = HttpsCockpitEntry(status_loader=loader, clock=lambda: now[0])
        self.assertIsNone(entry.redirect_target('/', HEADERS))
        self.assertIsNone(entry.redirect_target('/', HEADERS))
        self.assertEqual(loader.call_count, 1)
        now[0] += 11
        self.assertEqual(entry.redirect_target('/', HEADERS), ORIGIN + '/')
        now[0] += 59
        self.assertEqual(entry.redirect_target('/', HEADERS), ORIGIN + '/')
        self.assertEqual(loader.call_count, 2)

    def test_discovery_only_reads_configuration_with_bounded_timeout(self):
        result = subprocess.CompletedProcess([], 0, '{"TCP":{},"Web":{}}', '')
        with patch('app.cockpit_https_entry.subprocess.run', return_value=result) as run:
            self.assertEqual(read_serve_status(), {'TCP':{},'Web':{}})
        args, kwargs = run.call_args
        self.assertEqual(args[0][1:], ['serve','status','--json'])
        self.assertEqual(kwargs['timeout'], 2)
        self.assertEqual(kwargs['env']['TAILSCALE_BE_CLI'], '1')

    def test_launchd_environment_gets_cli_json_without_changing_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / 'tailscale'
            binary.write_text('#!/bin/sh\nif [ "$TAILSCALE_BE_CLI" = 1 ]; then\n'
                              + 'printf \'%s\\n\' ' + "'" + json.dumps(STATUS) + "'\n"
                              + 'else\nprintf "GUI mode is not JSON\\n"\nfi\n')
            binary.chmod(0o700)
            with patch.dict(os.environ, {'SAMANTHA_TAILSCALE_BIN': str(binary)}, clear=True):
                self.assertEqual(read_serve_status(), STATUS)
                self.assertNotIn('TAILSCALE_BE_CLI', os.environ)
                self.assertNotIn('TERM', os.environ)
                self.assertNotIn('TERM_PROGRAM', os.environ)


class HttpsCockpitHttpTests(unittest.TestCase):
    def setUp(self):
        self.loader = Mock(return_value=STATUS)
        entry = HttpsCockpitEntry(status_loader=self.loader)
        with patch.object(cockpit, 'HttpsCockpitEntry', return_value=entry):
            handler = cockpit.CockpitServer().make_handler()
        self.server = ThreadingHTTPServer(('127.0.0.1',0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.shutdown)

    def shutdown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=3)

    def request(self, path='/', headers=None, method='GET', body=None):
        connection = http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        try:
            connection.request(method,path,body=body,headers=headers or HEADERS)
            response = connection.getresponse()
            return response.status, dict(response.headers), response.read()
        finally:
            connection.close()

    def test_browser_redirect_is_temporary_uncached_and_preserves_query(self):
        status, headers, body = self.request('/?entry=home&next=https://evil.example/')
        self.assertEqual(status,302); self.assertEqual(body,b'')
        self.assertEqual(headers['Location'], ORIGIN+'/?entry=home&next=https://evil.example/')
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertEqual(headers['Content-Length'],'0')

    def test_https_host_and_local_navigation_still_serve_page(self):
        for host in ['samantha.example.ts.net','samantha.example.ts.net:443','127.0.0.1:8770']:
            status, headers, body = self.request(headers={**HEADERS,'Host':host})
            self.assertEqual(status,200); self.assertNotIn('Location',headers)
            self.assertIn(b'Znovu otev',body)
        self.loader.assert_not_called()

    def test_api_and_post_are_not_redirected_and_access_checks_remain(self):
        with patch.object(cockpit,'server_health_status',return_value={'ok':True}):
            status, headers, _ = self.request('/api/server/health')
        self.assertEqual(status,200); self.assertNotIn('Location',headers)
        status, headers, _ = self.request(method='POST',body=b'{}',headers={
            **HEADERS,'Content-Type':'application/json','Origin':'https://evil.example'})
        self.assertEqual(status,403); self.assertNotIn('Location',headers)
        status, headers, _ = self.request(headers={**HEADERS,'Host':'evil.example:8770'})
        self.assertEqual(status,400); self.assertNotIn('Location',headers)
        self.loader.assert_not_called()

    def test_missing_https_config_falls_back_to_existing_page(self):
        self.loader.return_value = None
        status, headers, _ = self.request()
        self.assertEqual(status,200); self.assertNotIn('Location',headers)

    def test_forwarded_headers_cannot_choose_destination(self):
        status, headers, _ = self.request(headers={**HEADERS,
            'X-Forwarded-Host':'evil.example','X-Forwarded-Proto':'https'})
        self.assertEqual(status,302); self.assertEqual(headers['Location'],ORIGIN+'/')
