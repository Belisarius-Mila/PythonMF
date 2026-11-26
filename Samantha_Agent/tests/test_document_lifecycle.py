from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import json
import uuid
import threading
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image
from app.documents import lifecycle, scan_inbox, transactions
from app.documents.archive_browser import resolve_stored_document_file, stored_document_list_status
from app.documents.search_service import document_reference, search_document_index
from app.documents.vault import write_json, write_jsonl


class DocumentLifecycle(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.document_id = "doc-synthetic-quality-test"
        self.ref = document_reference(self.document_id)
        self.source = self.root / "vault/other" / self.document_id / "document.pdf"
        self.source.parent.mkdir(parents=True)
        output = BytesIO()
        with Image.new("RGB", (20, 30), "white") as image:
            image.save(output, "PDF")
        self.raw = output.getvalue()
        self.source.write_bytes(self.raw)
        self.record = {"document_id": self.document_id, "title": "Syntetický dokument",
                       "stored_path": str(self.source), "domain": "other", "reading_status": "needs_review"}
        write_jsonl(self.root / "index/documents_index.jsonl", [self.record])
        write_jsonl(self.root / "index/text_index.jsonl", [{"document_id": self.document_id, "text": "syntetický dokument"}])
        write_json(self.source.parent / "manifest.json", self.record)
        self.scan_id = "a" * 32
        scan_inbox.save_scan(scan_id=self.scan_id, title="Syntetický sken", raw=self.raw, confirmed=True, vault_dir=self.root)

    def payload(self, kind="document", reference=None, action="trash"):
        ref = reference or (self.ref if kind == "document" else self.scan_id)
        preview = lifecycle.preview(kind, ref, vault_dir=self.root)
        return {"kind": kind, "reference": ref, "action": action, "confirmed": True,
                "expected_revision": preview["revision"], "request_id": uuid.uuid4().hex}

    def apply(self, payload):
        return lifecycle.apply_action(payload, vault_dir=self.root)

    def test_saved_document_trash_hides_search_readers_and_restores(self):
        self.assertTrue(self.apply(self.payload())["ok"])
        self.assertEqual(stored_document_list_status(vault_dir=self.root)["count"], 0)
        self.assertFalse(resolve_stored_document_file(document_ref=self.ref, vault_dir=self.root)["ok"])
        self.assertEqual(search_document_index("syntetický", vault_dir=self.root, source_type="document")["count"], 0)
        from app.cockpit import resolve_openable_document_file
        self.assertFalse(resolve_openable_document_file(self.ref, vault_dir=self.root)["ok"])
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertTrue(self.apply(self.payload(action="restore"))["ok"])
        self.assertEqual(stored_document_list_status(vault_dir=self.root)["count"], 1)
        self.assertTrue(resolve_stored_document_file(document_ref=self.ref, vault_dir=self.root)["ok"])
        self.assertEqual(search_document_index("syntetický", vault_dir=self.root, source_type="document")["count"], 1)

    def test_scan_trash_restores_exact_bytes_without_touching_vault_copy(self):
        self.assertTrue(self.apply(self.payload("scan"))["ok"])
        self.assertEqual(scan_inbox.list_scans(vault_dir=self.root), [])
        with self.assertRaises(ValueError):
            scan_inbox.resolve_scan(self.scan_id, vault_dir=self.root)
        items = lifecycle.trash_status(vault_dir=self.root)["items"]
        self.assertEqual([(item["kind"], item["reference"]) for item in items], [("scan", self.scan_id)])
        self.assertEqual(stored_document_list_status(vault_dir=self.root)["count"], 1)
        self.assertTrue(self.apply(self.payload("scan", action="restore"))["ok"])
        self.assertEqual(scan_inbox.resolve_scan(self.scan_id, vault_dir=self.root).read_bytes(), self.raw)

    def test_cancel_invalid_and_stale_confirmation_do_not_change_record(self):
        payload = self.payload()
        self.assertFalse(self.apply({**payload, "confirmed": False})["ok"])
        self.assertFalse(self.apply({**payload, "expected_revision": "old"})["ok"])
        self.assertFalse(self.apply({**payload, "request_id": "../bad"})["ok"])
        self.assertFalse(lifecycle.preview("document", self.ref, vault_dir=self.root)["trashed"])

    def test_concurrent_repeat_and_old_retry_after_restore_never_remove_twice(self):
        for kind in ("document", "scan"):
            payload = self.payload(kind)
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(self.apply, [payload, payload]))
            self.assertTrue(all(result["ok"] for result in results))
            self.assertTrue(self.apply(self.payload(kind, action="restore"))["ok"])
            self.assertTrue(self.apply(payload)["ok"])
            ref = self.ref if kind == "document" else self.scan_id
            self.assertFalse(lifecycle.preview(kind, ref, vault_dir=self.root)["trashed"])
            self.assertFalse(self.apply({**payload, "action": "restore"})["ok"])

    def test_index_and_manifest_rollback_on_failed_write_then_retry(self):
        payload = self.payload()
        with patch.object(transactions, "_write_manifest", side_effect=OSError("synthetic disk failure")):
            self.assertFalse(self.apply(payload)["ok"])
        self.assertFalse(lifecycle.preview("document", self.ref, vault_dir=self.root)["trashed"])
        self.assertTrue(self.apply(payload)["ok"])
        manifest = json.loads((self.source.parent / "manifest.json").read_text())
        self.assertEqual(manifest["lifecycle_status"], "trashed")
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_read_only_trash_does_not_create_storage(self):
        root = self.root / "unused"
        self.assertEqual(lifecycle.trash_status(vault_dir=root), {"ok": True, "items": []})
        self.assertFalse(root.exists())

    def test_traversal_symlink_and_foreign_reference_refused(self):
        for ref in ("../escape", "f"*32):
            self.assertFalse(self.apply({**self.payload("scan"), "reference": ref})["ok"])
        scan_path = self.root / "scans" / ("b"*32)
        scan_path.symlink_to(self.root / "scans" / self.scan_id, target_is_directory=True)
        self.assertFalse(self.apply({**self.payload("scan"), "reference": "b"*32})["ok"])
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_trash_of_one_doc_preserves_other_index_rows(self):
        other = {**self.record, "document_id": "doc-other"}
        write_jsonl(self.root / "index/documents_index.jsonl", [self.record, other])
        self.assertTrue(self.apply(self.payload())["ok"])
        rows = [json.loads(line) for line in (self.root / "index/documents_index.jsonl").read_text().splitlines()]
        self.assertEqual(rows[1], other)

    def test_changed_scan_bytes_cannot_be_removed_or_restored_as_original(self):
        payload = self.payload("scan")
        path = scan_inbox.resolve_scan(self.scan_id, vault_dir=self.root)
        path.write_bytes(b"changed synthetic file")
        self.assertFalse(self.apply(payload)["ok"])

    def test_scan_reader_fallback_has_explicit_return_and_no_print_action(self):
        from app.cockpit_document_readers import document_reader_page_html
        html = document_reader_page_html("", "<test>", scan_id=self.scan_id)
        self.assertIn("Zpět do Dokumentů", html)
        self.assertIn("/#dokumenty", html)
        self.assertIn("/api/documents/scans/pdf?scan_id=", html)
        self.assertIn("&lt;test&gt;", html)
        self.assertIn('id="readerPrintBtn" hidden disabled', html)

    def test_file_change_and_manifest_alias_cannot_modify_another_document(self):
        payload = self.payload()
        self.source.write_bytes(b"changed")
        self.assertFalse(self.apply(payload)["ok"])
        self.source.write_bytes(self.raw)
        manifest = self.source.parent / "manifest.json"
        write_json(manifest, {"document_id": "different-document"})
        self.assertFalse(self.apply(payload)["ok"])
        write_json(manifest, self.record)
        real = self.source.with_name("real.pdf")
        self.source.rename(real)
        self.source.symlink_to(real)
        self.assertFalse(self.apply(payload)["ok"])
        self.assertEqual(json.loads(manifest.read_text()), self.record)

    def test_cached_scandocu_candidate_cannot_reopen_or_import_trashed_item(self):
        from app.documents import scandocu
        extraction = SimpleNamespace(text="synthetic", method="test", ocr_needed=False, warning="")
        with patch.object(scandocu, "extract_text", return_value=extraction):
            candidate = scandocu.prepare_stored_document_review_candidate(
                document_record=self.record, stored_path=self.source, vault_dir=self.root)
            scan = scandocu.prepare_scandocu_candidate(
                scan_inbox.resolve_scan(self.scan_id, vault_dir=self.root), vault_dir=self.root)
        self.assertEqual(candidate.to_api()["lifecycle_reference"], self.ref)
        self.assertEqual(scan.to_api()["lifecycle_reference"], self.scan_id)
        for kind, item in (("document", candidate), ("scan", scan)):
            self.assertTrue(self.apply(self.payload(kind))["ok"])
            with self.assertRaisesRegex(ValueError, "koši"):
                scandocu.get_scandocu_candidate(item.token, vault_dir=self.root)

    def test_http_confirmation_origin_reader_and_restore(self):
        from app import cockpit
        actual_get = lifecycle.dispatch_get
        actual_resolve = scan_inbox.resolve_scan
        self.enterContext(patch.object(lifecycle, "dispatch_get", side_effect=lambda parsed, responder: actual_get(parsed, responder, vault_dir=self.root)))
        self.enterContext(patch.object(cockpit, "document_trash_action", side_effect=self.apply))
        self.enterContext(patch.object(scan_inbox, "resolve_scan", side_effect=lambda ref: actual_resolve(ref, vault_dir=self.root)))
        server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer(host="127.0.0.1", port=0).make_handler())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), thread.join()))
        base = f"http://127.0.0.1:{server.server_address[1]}"
        with urlopen(base + "/documents/scans/read?scan_id=" + self.scan_id) as response:
            self.assertIn(b"/#dokumenty", response.read())
        payload = self.payload("scan")

        def send(data, origin):
            return urlopen(Request(base + "/api/documents/trash", data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json", "Origin": origin}))

        with self.assertRaises(HTTPError) as error:
            send(payload, "https://foreign.invalid")
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            send({**payload, "confirmed": False}, base)
        self.assertEqual(error.exception.code, 400)
        with send(payload, base) as response:
            self.assertTrue(json.load(response)["ok"])
        with urlopen(base + "/api/documents/trash") as response:
            self.assertEqual(len(json.load(response)["items"]), 1)
        with self.assertRaises(HTTPError) as error:
            urlopen(base + "/api/documents/scans/pdf?scan_id=" + self.scan_id)
        self.assertEqual(error.exception.code, 404)
        with send(self.payload("scan", action="restore"), base) as response:
            self.assertTrue(json.load(response)["ok"])
        with urlopen(base + "/api/documents/scans/pdf?scan_id=" + self.scan_id) as response:
            self.assertEqual(response.read(), self.raw)
