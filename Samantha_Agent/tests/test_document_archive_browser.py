from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from app.documents.archive_browser import (
    resolve_stored_document_file,
    stored_document_detail_status,
    stored_document_list_status,
)
from app.documents.scandocu import (
    SCANDOCU_ARCHIVE_HTML,
    SCANDOCU_HTML,
    ScanDocuServer,
)
from app.documents.search_service import document_reference


class DocumentArchiveBrowserTests(unittest.TestCase):
    def test_list_is_newest_first_filterable_and_hides_trashed_documents(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            first = self._document(
                vault,
                document_id="older-energy",
                title="Starší vyúčtování",
                domain="energy",
                imported_at="2026-07-01T10:00:00+00:00",
                text="Elektřina a zálohy.",
            )
            second = self._document(
                vault,
                document_id="newer-insurance",
                title="Nové pojištění",
                domain="insurance",
                imported_at="2026-07-30T10:00:00+00:00",
                text="Pojištění vozidla.",
                reading_status="needs_review",
            )
            trashed = self._document(
                vault,
                document_id="trashed-document",
                title="Koš",
                domain="other",
                imported_at="2026-07-31T10:00:00+00:00",
                text="Nemá být vidět.",
                lifecycle_status="trashed",
            )
            self._write_indexes(vault, [first, second, trashed])

            result = stored_document_list_status(vault_dir=vault)
            filtered = stored_document_list_status(
                vault_dir=vault,
                domain="insurance",
                reading_status="needs_review",
                query="vozidla",
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["read_only"])
        self.assertEqual(result["total_count"], 2)
        self.assertEqual(result["review_count"], 1)
        self.assertEqual(
            [item["title"] for item in result["items"]],
            ["Nové pojištění", "Starší vyúčtování"],
        )
        self.assertEqual(filtered["count"], 1)
        self.assertEqual(filtered["items"][0]["title"], "Nové pojištění")
        self.assertNotIn("document_id", json.dumps(result, ensure_ascii=False))
        self.assertNotIn("stored_path", json.dumps(result, ensure_ascii=False))

    def test_detail_uses_opaque_reference_and_returns_full_file_url(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            record = self._document(
                vault,
                document_id="insurance-card",
                title="Zelená karta",
                domain="insurance",
                imported_at="2026-07-30T10:00:00+00:00",
                text="Celý indexovaný text dokumentu.",
            )
            self._write_indexes(vault, [record])
            reference = document_reference("insurance-card")

            result = stored_document_detail_status(
                document_ref=reference,
                vault_dir=vault,
            )
            resolved = resolve_stored_document_file(
                document_ref=reference,
                vault_dir=vault,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["document_ref"], reference)
        self.assertEqual(result["viewer_kind"], "pdf")
        self.assertEqual(
            result["file_url"],
            f"/vault/document?document_ref={reference}",
        )
        self.assertIn("Celý indexovaný text", result["text_preview"])
        self.assertTrue(resolved["ok"])

    def test_outside_file_is_not_openable(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            outside = root / "outside.pdf"
            outside.write_bytes(b"%PDF-1.4\noutside\n")
            record = {
                "document_id": "outside-document",
                "title": "Mimo vault",
                "stored_path": str(outside),
                "domain": "other",
            }
            self._write_indexes(vault, [record])

            result = resolve_stored_document_file(
                document_ref=document_reference("outside-document"),
                vault_dir=vault,
            )

        self.assertFalse(result["ok"])
        self.assertIn("není dostupný", result["message"])

    def test_scandocu_serves_browser_list_detail_and_complete_file_read_only(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            downloads = root / "Downloads"
            downloads.mkdir()
            record = self._document(
                vault,
                document_id="browser-document",
                title="Dokument v prohlížeči",
                domain="home",
                imported_at="2026-07-30T10:00:00+00:00",
                text="Čitelný syntetický text.",
            )
            self._write_indexes(vault, [record])
            handler = ScanDocuServer(
                downloads_dir=downloads,
                vault_dir=vault,
            ).make_handler()
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            reference = document_reference("browser-document")
            try:
                with urlopen(f"{base_url}/?mode=browse", timeout=5) as response:
                    page = response.read().decode("utf-8")
                with urlopen(f"{base_url}/api/documents", timeout=5) as response:
                    listing = json.loads(response.read().decode("utf-8"))
                with urlopen(
                    f"{base_url}/api/document?document_ref={reference}",
                    timeout=5,
                ) as response:
                    detail = json.loads(response.read().decode("utf-8"))
                with urlopen(
                    f"{base_url}/vault/document?document_ref={reference}",
                    timeout=5,
                ) as response:
                    payload = response.read()
                    content_type = response.headers.get_content_type()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

        self.assertIn("Uložené dokumenty", page)
        self.assertEqual(listing["items"][0]["document_ref"], reference)
        self.assertEqual(detail["document_ref"], reference)
        self.assertEqual(content_type, "application/pdf")
        self.assertEqual(payload, b"%PDF-1.4\nsynthetic\n")

    def test_scandocu_frontends_keep_browser_discoverable_and_read_only(self) -> None:
        self.assertIn('id="archiveBtn">Uložené dokumenty', SCANDOCU_HTML)
        for expected in (
            "Všechny dokumenty",
            "Dokumenty k revizi",
            "/api/documents",
            "/api/document?document_ref=",
            "Text nalezený v dokumentu",
            "Otevřít samostatně",
            "Toto je pouze čtení místního trezoru",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, SCANDOCU_ARCHIVE_HTML)
        self.assertNotIn("/api/save", SCANDOCU_ARCHIVE_HTML)
        self.assertNotIn("/api/skip", SCANDOCU_ARCHIVE_HTML)

    @staticmethod
    def _document(
        vault: Path,
        *,
        document_id: str,
        title: str,
        domain: str,
        imported_at: str,
        text: str,
        reading_status: str = "ok",
        lifecycle_status: str = "active",
    ) -> dict[str, object]:
        directory = vault / "vault" / domain / document_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{document_id}.pdf"
        path.write_bytes(b"%PDF-1.4\nsynthetic\n")
        return {
            "document_id": document_id,
            "title": title,
            "original_filename": path.name,
            "stored_path": str(path),
            "domain": domain,
            "document_type": "document",
            "counterparty": "Test",
            "tags": ["test"],
            "imported_at": imported_at,
            "reading_status": reading_status,
            "lifecycle_status": lifecycle_status,
            "size_bytes": path.stat().st_size,
            "_text": text,
        }

    @staticmethod
    def _write_indexes(vault: Path, records: list[dict[str, object]]) -> None:
        index = vault / "index"
        index.mkdir(parents=True, exist_ok=True)
        public_records = []
        text_records = []
        for record in records:
            clean = dict(record)
            text = str(clean.pop("_text", ""))
            public_records.append(clean)
            text_records.append(
                {
                    "document_id": clean["document_id"],
                    "text": text,
                    "text_truncated": False,
                }
            )
        (index / "documents_index.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in public_records),
            encoding="utf-8",
        )
        (index / "text_index.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in text_records),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
