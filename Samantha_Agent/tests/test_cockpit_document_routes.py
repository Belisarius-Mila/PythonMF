from __future__ import annotations

import http.client
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from app import cockpit
from tests.test_cockpit_http_security import running_cockpit_server


ROUTES = (
    ("/api/documents/search", "search_document_index"),
    ("/api/documents/review-report", "document_review_report_status"),
    ("/api/documents/case-detail", "document_case_detail_status"),
    ("/documents/read", "resolve_openable_document_file"),
    ("/documents/pdf", "resolve_openable_document_file"),
    ("/purchases/read", "resolve_openable_purchase_pdf"),
    ("/purchases/pdf", "resolve_openable_purchase_pdf"),
)


def request(host, port, path, *, method="GET", headers=None):
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


class CockpitDocumentRouteTests(unittest.TestCase):
    def assert_private_headers(self, headers):
        self.assertEqual(headers["Cache-Control"], "no-store, max-age=0")
        for name, value in cockpit.COCKPIT_SECURITY_HEADERS:
            self.assertEqual(headers[name], value)

    def test_json_routes_preserve_parameters_defaults_and_response(self):
        cases = (
            ("/api/documents/search?q=%C5%BElu%C5%A5ou%C4%8Dk%C3%BD+text&q=second", "search_document_index", {"query": "žluťoučký text", "limit": 8, "offset": 0}),
            ("/api/documents/search?q=", "search_document_index", {"query": "", "limit": 8, "offset": 0}),
            ("/api/documents/search", "search_document_index", {"query": "", "limit": 8, "offset": 0}),
            ("/api/documents/review-report?ignored=value", "document_review_report_status", {}),
            ("/api/documents/case-detail?case_ref=case%2Fone&case_ref=two", "document_case_detail_status", {"case_ref": "case/one"}),
            ("/api/documents/case-detail", "document_case_detail_status", {"case_ref": ""}),
        )
        with running_cockpit_server() as (host, port, _):
            for path, provider, kwargs in cases:
                with self.subTest(path=path), patch(f"app.cockpit.{provider}", return_value={"ok": True, "items": ["synthetic"]}) as loader:
                    status, headers, body = request(host, port, path)
                    self.assertEqual(status, 200)
                    self.assertEqual(json.loads(body), {"ok": True, "items": ["synthetic"]})
                    self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
                    self.assert_private_headers(headers)
                    loader.assert_called_once_with(**kwargs)

    def test_search_pagination_validates_before_provider_and_caps_page_size(self):
        with running_cockpit_server() as (host, port, _):
            for query in ("offset=-1", "offset=x", "offset=1.5", "offset=", "offset=0&offset=8", "limit=0", "limit=-1", "limit=", "limit=x", "limit=8&limit=9"):
                with self.subTest(query=query), patch("app.cockpit.search_document_index") as loader:
                    status, headers, body = request(host, port, "/api/documents/search?q=fixture&" + query)
                    self.assertEqual(status, 400)
                    self.assertEqual(json.loads(body)["error"], "invalid_pagination")
                    self.assert_private_headers(headers)
                    loader.assert_not_called()
            for query, limit, offset in (("limit=8&offset=8", 8, 8), ("limit=999&offset=0", 20, 0), ("offset=99999", 8, 99999)):
                with self.subTest(query=query), patch("app.cockpit.search_document_index", return_value={"ok": True}) as loader:
                    self.assertEqual(request(host, port, "/api/documents/search?q=fixture&" + query)[0], 200)
                    loader.assert_called_once_with(query="fixture", limit=limit, offset=offset)

    def test_search_pages_over_http_use_real_index_without_duplicates_or_omissions(self):
        search = cockpit.search_document_index
        with tempfile.TemporaryDirectory() as temp, running_cockpit_server() as (host, port, _):
            vault = Path(temp) / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            rows = [{"document_id": f"fixture-{i:02}", "title": f"Fixture document {i:02}"} for i in range(23)]
            (index / "documents_index.jsonl").write_text("\n".join(json.dumps(row) for row in [*rows, rows[0]]) + "\n")
            with patch("app.cockpit.search_document_index", side_effect=lambda **kwargs: search(vault_dir=vault, **kwargs)):
                pages = []
                for offset in (0, 8, 16, 24):
                    status, headers, body = request(host, port, f"/api/documents/search?q=fixture&limit=8&offset={offset}")
                    self.assertEqual(status, 200)
                    self.assert_private_headers(headers)
                    data = json.loads(body)
                    self.assertEqual(data["total_count"], 23)
                    self.assertEqual(data["offset"], offset)
                    pages.append(data)
                self.assertEqual([p["count"] for p in pages], [8, 8, 7, 0])
                self.assertEqual([p["next_offset"] for p in pages], [8, 16, None, None])
                refs = [item["document_ref"] for page in pages for item in page["results"]]
                self.assertEqual(len(refs), 23)
                self.assertEqual(len(set(refs)), 23)
                repeated = json.loads(request(host, port, "/api/documents/search?q=fixture&offset=8")[2])
                self.assertEqual(repeated["results"], pages[1]["results"])

    def test_readers_preserve_rendered_html_and_viewer_kind(self):
        cases = (
            ("/documents/read?document_id=doc%2Fone", "resolve_openable_document_file", "doc/one",
             {"ok": True, "document_ref": "doc-ref", "title": "Doklad & test", "viewer_kind": "image"},
             cockpit.document_reader_page_html("doc-ref", "Doklad & test", "image")),
            ("/purchases/read?purchase_id=purchase-one", "resolve_openable_purchase_pdf", "purchase-one",
             {"ok": True, "purchase_ref": "purchase-ref", "title": "Faktura & test"},
             cockpit.purchase_reader_page_html("purchase-ref", "Faktura & test")),
        )
        with running_cockpit_server() as (host, port, _):
            for path, provider, reference, resolved, expected in cases:
                with self.subTest(path=path), patch(f"app.cockpit.{provider}", return_value=resolved) as loader:
                    status, headers, body = request(host, port, path)
                    self.assertEqual(status, 200)
                    self.assertEqual(body, expected.encode())
                    self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
                    self.assert_private_headers(headers)
                    loader.assert_called_once_with(reference)

    def test_files_preserve_bytes_content_type_and_inline_headers(self):
        with tempfile.TemporaryDirectory() as temp, running_cockpit_server() as (host, port, _):
            for route, provider, name, content_type in (
                ("/documents/pdf?document_id=doc", "resolve_openable_document_file", "document.pdf", "application/pdf"),
                ("/documents/pdf?document_id=doc", "resolve_openable_document_file", "scan.png", "image/png"),
                ("/purchases/pdf?purchase_id=purchase", "resolve_openable_purchase_pdf", "invoice.pdf", "application/pdf"),
            ):
                target = Path(temp) / name
                target.write_bytes(b"synthetic\x00\xff\n")
                with self.subTest(name=name), patch(f"app.cockpit.{provider}", return_value={"ok": True, "path": target, "content_type": content_type}):
                    status, headers, body = request(host, port, route)
                    self.assertEqual(status, 200)
                    self.assertEqual(body, target.read_bytes())
                    self.assertEqual(headers["Content-Type"], content_type)
                    self.assertEqual(headers["Content-Disposition"], f'inline; filename="{name}"')
                    self.assertEqual(int(headers["Content-Length"]), len(body))
                    self.assert_private_headers(headers)

    def test_missing_and_encoded_references_keep_404_contract(self):
        with running_cockpit_server() as (host, port, _):
            for path, provider in ROUTES[3:]:
                key = "document_id" if path.startswith("/documents/") else "purchase_id"
                for query, reference in (("", ""), (f"?{key}=", ""), (f"?{key}=a%2Fb&{key}=ignored", "a/b")):
                    with self.subTest(path=path, query=query), patch(f"app.cockpit.{provider}", return_value={"ok": False, "message": "Synthetic missing"}) as loader:
                        status, headers, body = request(host, port, path + query)
                        self.assertEqual(status, 404)
                        self.assert_private_headers(headers)
                        loader.assert_called_once_with(reference)
                        if path.endswith("/pdf"):
                            self.assertEqual(json.loads(body), {"error": "not_found", "message": "Synthetic missing"})
                        else:
                            renderer = cockpit.document_reader_page_html if key == "document_id" else cockpit.purchase_reader_page_html
                            self.assertEqual(body, renderer(reference, "Synthetic missing").encode())

    def test_foreign_host_is_rejected_before_any_document_provider(self):
        with running_cockpit_server() as (host, port, _), ExitStack() as stack:
            loaders = [stack.enter_context(patch(f"app.cockpit.{name}")) for name in dict.fromkeys(dict(ROUTES).values())]
            for path, _ in ROUTES:
                with self.subTest(path=path):
                    status, _, _ = request(host, port, path, headers={"Host": "example.invalid"})
                    self.assertEqual(status, 400)
            for loader in loaders:
                loader.assert_not_called()

    def test_unknown_paths_and_post_do_not_dispatch_document_reads(self):
        with running_cockpit_server() as (host, port, _), ExitStack() as stack:
            loaders = [stack.enter_context(patch(f"app.cockpit.{name}")) for name in dict.fromkeys(dict(ROUTES).values())]
            for path, _ in ROUTES:
                for target, method in ((path + "/extra", "GET"), (path, "POST")):
                    with self.subTest(path=target, method=method):
                        status, _, body = request(host, port, target, method=method, headers={"Origin": f"http://{host}:{port}"})
                        self.assertEqual(status, 404)
                        self.assertEqual(json.loads(body), {"error": "not_found"})
            for loader in loaders:
                loader.assert_not_called()

    def test_provider_errors_use_central_redacted_500_response(self):
        with running_cockpit_server() as (host, port, _):
            for path, provider in ROUTES:
                with self.subTest(path=path), patch(f"app.cockpit.{provider}", side_effect=RuntimeError("SYNTHETIC_PRIVATE_DETAIL")):
                    status, headers, body = request(host, port, path)
                    self.assertEqual(status, 500)
                    self.assertEqual(json.loads(body)["error"], "internal_error")
                    self.assertNotIn(b"SYNTHETIC_PRIVATE_DETAIL", body)
                    self.assert_private_headers(headers)

    def test_real_resolvers_reject_external_paths_and_symlinks_over_http(self):
        document_resolver = cockpit.resolve_openable_document_file
        purchase_resolver = cockpit.resolve_openable_purchase_pdf
        with tempfile.TemporaryDirectory() as temp, running_cockpit_server() as (host, port, _):
            root = Path(temp)
            outside = root / "outside.pdf"
            outside.write_bytes(b"SYNTHETIC_FILE_MUST_NOT_LEAK")
            vault = root / "vault"
            (vault / "index").mkdir(parents=True)
            link = vault / "linked.pdf"
            link.symlink_to(outside)
            rows = [{"document_id": name, "stored_path": str(target)} for name, target in (("outside", outside), ("symlink", link))]
            (vault / "index/documents_index.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
            purchases = root / "purchases"
            folder = purchases / "2026" / "test"
            folder.mkdir(parents=True)
            purchase_link = folder / "invoice.pdf"
            purchase_link.symlink_to(outside)
            manifest = folder / "invoice_manifest.json"
            with patch("app.cockpit.resolve_openable_document_file", side_effect=lambda ref: document_resolver(ref, vault_dir=vault)), patch("app.cockpit.resolve_openable_purchase_pdf", side_effect=lambda ref: purchase_resolver(ref, purchases_dir=purchases)):
                for ref in ("outside", "symlink", "../outside.pdf"):
                    for route in ("/documents/read", "/documents/pdf"):
                        status, _, body = request(host, port, f"{route}?document_id={ref}")
                        self.assertEqual(status, 404)
                        self.assertNotIn(outside.read_bytes(), body)
                for target in (outside, purchase_link):
                    manifest.write_text(json.dumps({"attachments": [{"stored_path": str(target)}]}))
                    for route in ("/purchases/read", "/purchases/pdf"):
                        status, _, body = request(host, port, f"{route}?purchase_id=purchase-2026-test")
                        self.assertEqual(status, 404)
                        self.assertNotIn(outside.read_bytes(), body)
