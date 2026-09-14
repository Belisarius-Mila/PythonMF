from __future__ import annotations

import http.client
import json
import tempfile
import unittest
from contextlib import ExitStack
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import patch

from app import cockpit
from app.email.archive_browser import read_email_archive_embedded_attachments
from tests.test_cockpit_http_security import running_cockpit_server


ROUTES = (
    ("/email-archive/", None),
    ("/api/email-archive/list", "email_archive_list_status"),
    ("/api/email-archive/detail", "email_archive_detail_status"),
    ("/email-archive/file", "resolve_email_archive_file"),
    ("/email-archive/incoming", "resolve_email_archive_incoming_file"),
    ("/email-archive/attachment", "resolve_email_archive_embedded_attachment"),
)


def request(host, port, path, *, method="GET", headers=None):
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


class CockpitEmailArchiveRouteTests(unittest.TestCase):
    def assert_private_headers(self, headers):
        self.assertEqual(headers["Cache-Control"], "no-store, max-age=0")
        for name, value in cockpit.COCKPIT_SECURITY_HEADERS:
            self.assertEqual(headers[name], value)

    def test_archive_page_keeps_exact_html(self):
        with running_cockpit_server() as (host, port, _):
            status, headers, body = request(host, port, "/email-archive/?ignored=value")
        self.assertEqual(status, 200)
        self.assertEqual(body, cockpit.EMAIL_ARCHIVE_HTML.encode())
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assert_private_headers(headers)

    def test_list_and_detail_preserve_query_defaults_and_invalid_limits(self):
        cases = (
            ("/api/email-archive/list", "email_archive_list_status", {"query": "", "limit": 120}),
            ("/api/email-archive/list?q=%C4%8Desk%C3%BD+text&q=second&limit=7&limit=8", "email_archive_list_status", {"query": "český text", "limit": 7}),
            ("/api/email-archive/list?q=&limit=bad", "email_archive_list_status", {"query": "", "limit": 120}),
            ("/api/email-archive/list?limit=", "email_archive_list_status", {"query": "", "limit": 120}),
            ("/api/email-archive/list?limit=-1", "email_archive_list_status", {"query": "", "limit": -1}),
            ("/api/email-archive/detail", "email_archive_detail_status", {"archive_id": ""}),
            ("/api/email-archive/detail?archive_id=a%2Fb&archive_id=second", "email_archive_detail_status", {"archive_id": "a/b"}),
        )
        with running_cockpit_server() as (host, port, _):
            for path, provider, kwargs in cases:
                with self.subTest(path=path), patch(f"app.cockpit.{provider}", return_value={"ok": True, "items": ["synthetic"]}) as loader:
                    status, headers, body = request(host, port, path)
                    self.assertEqual(status, 200)
                    self.assertEqual(json.loads(body), {"ok": True, "items": ["synthetic"]})
                    self.assert_private_headers(headers)
                    loader.assert_called_once_with(**kwargs)

    def test_archive_and_incoming_files_preserve_bytes_and_fallback_headers(self):
        with tempfile.TemporaryDirectory() as temp, running_cockpit_server() as (host, port, _):
            target = Path(temp) / "sample.bin"
            target.write_bytes(b"synthetic\x00\xff\n")
            for path, provider, kwargs, fallback_name in (
                ("/email-archive/file?archive_id=a%2Fb&file=body_txt&file=other", "resolve_email_archive_file", {"archive_id": "a/b", "file_key": "body_txt"}, "email-archive"),
                ("/email-archive/incoming?name=icloud_uid_test.bin&name=other", "resolve_email_archive_incoming_file", {"name": "icloud_uid_test.bin"}, "attachment"),
            ):
                for extra in ({"content_type": "text/plain; charset=utf-8", "filename": "sample.txt"}, {}):
                    with self.subTest(path=path, extra=extra), patch(f"app.cockpit.{provider}", return_value={"ok": True, "path": target, **extra}) as loader:
                        status, headers, body = request(host, port, path)
                        self.assertEqual(status, 200)
                        self.assertEqual(body, target.read_bytes())
                        self.assertEqual(headers["Content-Type"], extra.get("content_type", "application/octet-stream"))
                        self.assertEqual(headers["Content-Disposition"], f'inline; filename="{extra.get("filename", fallback_name)}"')
                        self.assertEqual(int(headers["Content-Length"]), len(body))
                        self.assert_private_headers(headers)
                        loader.assert_called_once_with(**kwargs)

    def test_embedded_attachment_preserves_inline_and_download_policy(self):
        types = (("application/pdf", "inline"), ("image/png", "inline"),
                 ("text/plain; charset=utf-8", "inline"), ("image/svg+xml", "attachment"),
                 ("text/html", "attachment"), ("application/zip", "attachment"), ("", "attachment"))
        with running_cockpit_server() as (host, port, _):
            for content_type, disposition in types:
                resolved = {"ok": True, "data": b"synthetic\x00\xff", "filename": 'unsafe"name.bin', "content_type": content_type}
                with self.subTest(content_type=content_type), patch("app.cockpit.resolve_email_archive_embedded_attachment", return_value=resolved) as loader:
                    status, headers, body = request(host, port, "/email-archive/attachment?archive_id=archive&attachment=ref%2Fone&attachment=other")
                    self.assertEqual(status, 200)
                    self.assertEqual(body, resolved["data"])
                    self.assertEqual(headers["Content-Type"], content_type or "application/octet-stream")
                    self.assertEqual(headers["Content-Disposition"], f'{disposition}; filename="{cockpit.safe_filename(resolved["filename"])}"')
                    self.assert_private_headers(headers)
                    loader.assert_called_once_with(archive_id="archive", attachment_ref="ref/one")

    def test_missing_files_keep_404_and_empty_parameter_contracts(self):
        cases = (
            ("/email-archive/file", "resolve_email_archive_file", {"archive_id": "", "file_key": ""}),
            ("/email-archive/incoming?name=", "resolve_email_archive_incoming_file", {"name": ""}),
            ("/email-archive/attachment?archive_id=", "resolve_email_archive_embedded_attachment", {"archive_id": "", "attachment_ref": ""}),
        )
        with running_cockpit_server() as (host, port, _):
            for path, provider, kwargs in cases:
                with self.subTest(path=path), patch(f"app.cockpit.{provider}", return_value={"ok": False, "message": "Synthetic missing"}) as loader:
                    status, headers, body = request(host, port, path)
                    self.assertEqual(status, 404)
                    self.assertEqual(json.loads(body), {"error": "not_found", "message": "Synthetic missing"})
                    self.assert_private_headers(headers)
                    loader.assert_called_once_with(**kwargs)

    def test_foreign_host_rejected_before_backend_or_page_response(self):
        with running_cockpit_server() as (host, port, _), ExitStack() as stack:
            loaders = [stack.enter_context(patch(f"app.cockpit.{provider}")) for _, provider in ROUTES if provider]
            for path, _ in ROUTES:
                status, _, body = request(host, port, path, headers={"Host": "example.invalid"})
                self.assertEqual(status, 400)
                self.assertNotEqual(body, cockpit.EMAIL_ARCHIVE_HTML.encode())
            for loader in loaders:
                loader.assert_not_called()

    def test_unknown_paths_and_post_do_not_call_read_providers(self):
        with running_cockpit_server() as (host, port, _), ExitStack() as stack:
            loaders = [stack.enter_context(patch(f"app.cockpit.{provider}")) for _, provider in ROUTES if provider]
            for path, _ in ROUTES:
                for target, method in ((path + "extra", "GET"), (path, "POST")):
                    status, _, body = request(host, port, target, method=method, headers={"Origin": f"http://{host}:{port}"})
                    self.assertEqual(status, 404)
                    self.assertEqual(json.loads(body), {"error": "not_found"})
            for loader in loaders:
                loader.assert_not_called()

    def test_provider_errors_keep_central_redacted_response(self):
        with running_cockpit_server() as (host, port, _):
            for path, provider in ROUTES:
                if not provider:
                    continue
                with self.subTest(path=path), patch(f"app.cockpit.{provider}", side_effect=RuntimeError("SYNTHETIC_PRIVATE_DETAIL")):
                    status, headers, body = request(host, port, path)
                    self.assertEqual(status, 500)
                    self.assertEqual(json.loads(body)["error"], "internal_error")
                    self.assertNotIn(b"SYNTHETIC_PRIVATE_DETAIL", body)
                    self.assert_private_headers(headers)

    def test_real_resolvers_reject_escaping_paths_and_serve_only_referenced_eml_attachment(self):
        file_resolver = cockpit.resolve_email_archive_file
        incoming_resolver = cockpit.resolve_email_archive_incoming_file
        attachment_resolver = cockpit.resolve_email_archive_embedded_attachment
        with tempfile.TemporaryDirectory() as temp, running_cockpit_server() as (host, port, _):
            root = Path(temp)
            archive = root / "archives"
            folder = archive / "demo"
            folder.mkdir(parents=True)
            (folder / "metadata.json").write_text("{}")
            outside = root / "outside.txt"
            outside.write_bytes(b"SYNTHETIC_MUST_NOT_LEAK")
            (folder / "body.txt").symlink_to(outside)
            docs = root / "documents"
            incoming = docs / "inbox/incoming"
            incoming.mkdir(parents=True)
            (incoming / "icloud_uid_link.txt").symlink_to(outside)
            message = EmailMessage()
            message.set_content("Synthetic message")
            message.add_attachment(b"SYNTHETIC_PDF", maintype="application", subtype="pdf", filename="test.pdf")
            (folder / "original.eml").write_bytes(message.as_bytes())
            refs = read_email_archive_embedded_attachments("demo", archive_directory=archive)
            self.assertEqual(len(refs), 1)
            with patch("app.cockpit.resolve_email_archive_file", side_effect=lambda **kw: file_resolver(**kw, archive_directory=archive)), patch("app.cockpit.resolve_email_archive_incoming_file", side_effect=lambda **kw: incoming_resolver(**kw, documents_dir=docs)), patch("app.cockpit.resolve_email_archive_embedded_attachment", side_effect=lambda **kw: attachment_resolver(**kw, archive_directory=archive)):
                for target in (
                    "/email-archive/file?archive_id=demo&file=body_txt",
                    "/email-archive/file?archive_id=..%2Foutside&file=body_txt",
                    "/email-archive/file?archive_id=demo&file=..%2Foutside.txt",
                    "/email-archive/incoming?name=icloud_uid_link.txt",
                    "/email-archive/incoming?name=..%2Foutside.txt",
                    "/email-archive/attachment?archive_id=demo&attachment=..%2Foutside.txt",
                    "/email-archive/attachment?archive_id=demo&attachment=email-attachment-ref-0000000000000000",
                ):
                    status, _, body = request(host, port, target)
                    self.assertEqual(status, 404)
                    self.assertNotIn(outside.read_bytes(), body)
                status, headers, body = request(host, port, f'/email-archive/attachment?archive_id=demo&attachment={refs[0]["attachment_ref"]}')
                self.assertEqual(status, 200)
                self.assertEqual(body, b"SYNTHETIC_PDF")
                self.assertEqual(headers["Content-Disposition"], 'inline; filename="test.pdf"')
