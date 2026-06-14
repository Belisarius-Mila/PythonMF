from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.documents.tools import (
    apply_document_import_text,
    apply_mobile_document_final_import_text,
    document_vault_status_text,
    inspect_document_text_text,
    apply_document_reindex_text,
    prepare_document_import_text,
    prepare_mobile_document_final_import_text,
    prepare_mobile_document_batch_text,
    process_mobile_document_inbox_text,
    preview_document_reindex_text,
    prepare_document_print_job_text,
    propose_document_inbox_cleanup_text,
    resolve_document_inbox_item_text,
    run_document_print_job_text,
    save_document_due_reminder_text,
    scan_document_inbox_text,
    scan_downloaded_pdfs_text,
    scan_mobile_document_inbox_text,
    search_private_documents_text,
)
from app.documents.scandocu import import_scandocu_candidate
from app.documents.scandocu import get_scandocu_candidate
from app.documents.scandocu import prepare_next_scandocu_pdf
from app.documents.scandocu import prepare_scandocu_candidate
from app.documents.scandocu import prepare_specific_download_pdf
from app.documents.scandocu import prepare_next_stored_document_review
from app.documents.scandocu import scan_downloads_for_pdfs
from app.documents.scandocu import search_downloads_for_pdfs
from app.documents.scandocu import SCANDOCU_HTML
from app.documents.vault import format_document_inbox_reminder
from app.documents.vault import has_explicit_document_import_confirmation
from app.documents.vault import normalize_mobile_document_page
from app.documents.vault import normalize_domain
from app.documents.vault import parse_macos_vision_ocr_json
from app.documents.vault import propose_metadata
from app.documents.vault import resolve_pdftotext_binary
from app.documents.vault import safe_ascii_slug
from app.documents.vault import TableExtractionResult
from app.documents.vault import TextExtractionResult
from app.documents.vault import enrich_pdf_text_with_tables
from app.documents.vault import extract_text

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


class DocumentVaultToolsTests(unittest.TestCase):
    def test_normalize_domain_preserves_custom_manual_domain(self) -> None:
        self.assertEqual(normalize_domain("ČEZ smlouvy"), "cez-smlouvy")
        self.assertEqual(normalize_domain("energie"), "energy")
        self.assertEqual(normalize_domain(""), "other")

    def test_safe_ascii_slug_transliterates_czech_metadata(self) -> None:
        self.assertEqual(safe_ascii_slug("Daňové přiznání", default="document", limit=50), "danove-priznani")
        self.assertEqual(safe_ascii_slug("ČEZ smlouvy 2026", default="", limit=100), "cez-smlouvy-2026")

    def test_prepare_is_read_only_and_finds_due_date_candidates(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "servis-kotle.pdf"
            source.write_bytes(
                b"%PDF-1.4\nServisni protokol kotle\nPristi servis do 31.7.2026\n"
            )
            vault = root / "documents"

            result = prepare_document_import_text(
                source_path=str(source),
                document_hint="service_report",
                vault_dir=vault,
            )

            self.assertIn("Navrh importu dokumentu", result)
            self.assertIn("service_due", result)
            self.assertIn("2026-07-31", result)
            self.assertFalse(vault.exists())

    def test_scan_document_inbox_lists_pending_files_read_only(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            incoming = vault / "inbox" / "incoming"
            incoming.mkdir(parents=True)
            source = incoming / "nova-faktura.pdf"
            source.write_text("Faktura", encoding="utf-8")

            result = scan_document_inbox_text(vault_dir=vault)

            self.assertIn("Document inbox", result)
            self.assertIn("nova-faktura.pdf", result)
            self.assertIn("prepare_document_import", result)

    def test_scan_mobile_document_inbox_groups_pages_by_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir) / "SamanthaDocumentInbox"
            inbox.mkdir()
            (inbox / "process_request.json").write_text(
                '{"request":"process_mobile_document_inbox"}',
                encoding="utf-8",
            )
            (inbox / "scan_B_manifest.json").write_text(
                json.dumps(
                    {
                        "batch_id": "scan_B",
                        "document_title": "Test",
                        "page_count": "2",
                    }
                ),
                encoding="utf-8",
            )
            (inbox / "scan_B_page_1.jpeg").write_bytes(b"page1")
            (inbox / "scan_B_page_2.jpeg").write_bytes(b"page2")

            result = scan_mobile_document_inbox_text(mobile_inbox_dir=inbox)

            self.assertIn("Mobile document inbox", result)
            self.assertIn("Process request: ano", result)
            self.assertIn("Batch: scan_B", result)
            self.assertIn("Nazev: Test", result)
            self.assertIn("2 nalezeno / 2", result)

    @unittest.skipIf(Image is None, "Pillow is not installed")
    def test_prepare_mobile_document_batch_creates_working_pdf_without_deleting_source(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "SamanthaDocumentInbox"
            vault = root / "documents"
            inbox.mkdir()
            (inbox / "scan_B_manifest.json").write_text(
                json.dumps(
                    {
                        "batch_id": "scan_B",
                        "document_title": "Test",
                        "page_count": "2",
                    }
                ),
                encoding="utf-8",
            )
            Image.new("RGB", (40, 50), "white").save(inbox / "scan_B_page_1.jpeg")
            Image.new("RGB", (40, 50), "white").save(inbox / "scan_B_page_2.jpeg")

            result = prepare_mobile_document_batch_text(
                batch_id="scan_B",
                mobile_inbox_dir=inbox,
                vault_dir=vault,
            )

            self.assertIn("Mobilni dokument je pripraveny", result)
            self.assertTrue((vault / "mobile_inbox" / "processing" / "scan_b" / "scan_b.pdf").exists())
            self.assertTrue((vault / "mobile_inbox" / "processing" / "scan_b" / "manifest.json").exists())
            self.assertTrue((inbox / "scan_B_page_1.jpeg").exists())
            self.assertTrue((inbox / "scan_B_page_2.jpeg").exists())

    @unittest.skipIf(Image is None, "Pillow is not installed")
    @patch.dict("os.environ", {"SAMANTHA_DOCUMENT_CLEAN_PROFILE": "bw"})
    def test_normalize_mobile_document_page_crops_borders(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "page.jpeg"
            target = root / "normalized.jpg"
            image = Image.new("RGB", (800, 1000), "white")
            for y in range(300, 701, 40):
                for x in range(220, 581):
                    for dy in range(0, 5):
                        image.putpixel((x, y + dy), (20, 20, 20))
            image.save(source)

            normalize_mobile_document_page(source, target)

            with Image.open(target) as normalized:
                self.assertEqual(normalized.size, (1240, 1754))
                grayscale = normalized.convert("L")
                histogram = grayscale.histogram()
                total = sum(histogram)
                dark_pixels = sum(histogram[:80])
                light_pixels = sum(histogram[220:])
                self.assertGreater(dark_pixels, 500)
                self.assertGreater(light_pixels / total, 0.8)

    @unittest.skipIf(Image is None, "Pillow is not installed")
    @patch.dict("os.environ", {"SAMANTHA_DOCUMENT_CLEAN_PROFILE": "raw"})
    def test_normalize_mobile_document_page_raw_profile_preserves_geometry(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "page.jpeg"
            target = root / "normalized.jpg"
            Image.new("RGB", (800, 1000), "white").save(source)

            normalize_mobile_document_page(source, target)

            with Image.open(target) as normalized:
                self.assertEqual(normalized.size, (800, 1000))

    def test_process_mobile_document_inbox_requires_process_request(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            inbox = Path(temp_dir) / "SamanthaDocumentInbox"
            vault = Path(temp_dir) / "documents"
            inbox.mkdir()

            result = process_mobile_document_inbox_text(
                mobile_inbox_dir=inbox,
                vault_dir=vault,
            )

            self.assertIn("chybi process_request.json", result)
            self.assertFalse(vault.exists())

    @unittest.skipIf(Image is None, "Pillow is not installed")
    @patch.dict(
        "os.environ",
        {
            "SAMANTHA_DOCUMENT_TESSERACT_OCR": "0",
            "SAMANTHA_DOCUMENT_OCR": "0",
        },
    )
    def test_process_mobile_document_inbox_creates_pdf_analysis_and_marks_request(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "SamanthaDocumentInbox"
            vault = root / "documents"
            inbox.mkdir()
            (inbox / "process_request.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "request": "process_mobile_document_inbox",
                        "source": "iphone_shortcut",
                        "status": "requested",
                    }
                ),
                encoding="utf-8",
            )
            (inbox / "scan_B_manifest.json").write_text(
                json.dumps(
                    {
                        "batch_id": "scan_B",
                        "document_title": "Test",
                        "page_count": "2",
                    }
                ),
                encoding="utf-8",
            )
            Image.new("RGB", (80, 100), "white").save(inbox / "scan_B_page_1.jpeg")
            Image.new("RGB", (80, 100), "white").save(inbox / "scan_B_page_2.jpeg")

            result = process_mobile_document_inbox_text(
                mobile_inbox_dir=inbox,
                vault_dir=vault,
            )

            processing = vault / "mobile_inbox" / "processing" / "scan_b"
            self.assertIn("Zpracovani mobilniho inboxu probehlo", result)
            self.assertIn("Batch: scan_B", result)
            self.assertTrue((processing / "scan_b.pdf").exists())
            self.assertTrue((processing / "manifest.json").exists())
            self.assertTrue((processing / "analysis.json").exists())
            self.assertTrue((processing / "extracted_text.txt").exists())
            self.assertTrue((inbox / "scan_B_page_1.jpeg").exists())
            self.assertTrue((inbox / "scan_B_page_2.jpeg").exists())
            self.assertTrue((inbox / "process_result.json").exists())
            request = json.loads((inbox / "process_request.json").read_text(encoding="utf-8"))
            self.assertEqual(request["status"], "processed")

            second = process_mobile_document_inbox_text(
                mobile_inbox_dir=inbox,
                vault_dir=vault,
            )
            self.assertIn("uz oznaceny jako processed", second)

    @unittest.skipIf(Image is None, "Pillow is not installed")
    @patch.dict(
        "os.environ",
        {
            "SAMANTHA_DOCUMENT_TESSERACT_OCR": "0",
            "SAMANTHA_DOCUMENT_OCR": "0",
        },
    )
    def test_mobile_document_final_import_requires_preview_and_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "SamanthaDocumentInbox"
            vault = root / "documents"
            inbox.mkdir()
            (inbox / "process_request.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1",
                        "request": "process_mobile_document_inbox",
                        "source": "iphone_shortcut",
                        "status": "requested",
                    }
                ),
                encoding="utf-8",
            )
            (inbox / "scan_R_manifest.json").write_text(
                json.dumps(
                    {
                        "batch_id": "scan_R",
                        "document_title": "Recept test",
                        "page_count": "1",
                    }
                ),
                encoding="utf-8",
            )
            Image.new("RGB", (80, 100), "white").save(inbox / "scan_R_page_1.jpeg")
            process_mobile_document_inbox_text(
                batch_id="scan_R",
                mobile_inbox_dir=inbox,
                vault_dir=vault,
            )

            preview = prepare_mobile_document_final_import_text(
                batch_id="scan_R",
                target_domain="food",
                document_type="recipe",
                tags="recept",
                case_id="rodinne-recepty",
                vault_dir=vault,
            )

            self.assertIn("Navrh finalniho importu", preview)
            self.assertIn("scan_r.pdf", preview)
            self.assertIn("rodinne-recepty", preview)

            rejected = apply_mobile_document_final_import_text(
                batch_id="scan_R",
                target_domain="food",
                document_type="recipe",
                tags="recept",
                case_id="rodinne-recepty",
                vault_dir=vault,
            )
            self.assertIn("Nejdrive potrebuji samostatne potvrzeni", rejected)

            imported = apply_mobile_document_final_import_text(
                batch_id="scan_R",
                target_domain="food",
                document_type="recipe",
                tags="recept",
                document_id="recept-test",
                case_id="rodinne-recepty",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument scan_r.pdf do oblasti food.",
                vault_dir=vault,
            )

            self.assertIn("Stav: ulozeno", imported)
            self.assertTrue((vault / "vault" / "food" / "recept-test" / "scan_r.pdf").exists())
            manifest = json.loads(
                (vault / "mobile_inbox" / "processing" / "scan_r" / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(manifest["final_import_done"])
            self.assertEqual(manifest["final_document_id"], "recept-test")
            docs_index = (vault / "index" / "documents_index.jsonl").read_text(encoding="utf-8")
            self.assertIn('"case_id": "rodinne-recepty"', docs_index)

    def test_scandocu_processes_newest_download_pdf_into_vault(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            downloads = root / "Downloads"
            vault = root / "documents"
            downloads.mkdir()
            older = downloads / "older.pdf"
            newer = downloads / "gpt-recept.pdf"
            older.write_bytes(b"%PDF-1.4\nStarsi dokument\n")
            newer.write_bytes(
                "%PDF-1.4\nRecept\nPrisady: brambory, mrkev, sul a olej.\nDoba pripravy 30 minut.\n".encode(
                    "utf-8"
                )
            )
            now = time.time()
            os.utime(older, (now - 60, now - 60))
            os.utime(newer, (now, now))

            scan = scan_downloaded_pdfs_text(downloads_dir=downloads, vault_dir=vault)
            self.assertIn("gpt-recept.pdf", scan)
            self.assertIn("stav: new", scan)

            candidate = prepare_next_scandocu_pdf(downloads_dir=downloads, vault_dir=vault)
            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertEqual(candidate.source_path.name, "gpt-recept.pdf")
            self.assertTrue(candidate.working_path.exists())

            result = import_scandocu_candidate(
                token=candidate.token,
                title="Rodinne recepty salat",
                domain="food",
                document_type="recipe",
                tags="recept, test",
                case_id="rodinne-recepty",
                vault_dir=vault,
            )

            self.assertEqual(result["status"], "imported")
            self.assertEqual(result["document_id"], "rodinne-recepty-salat")
            stored = vault / "vault" / "food" / "rodinne-recepty-salat" / "gpt-recept.pdf"
            self.assertTrue(stored.exists())
            manifest = json.loads((stored.parent / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["title"], "Rodinne recepty salat")
            self.assertEqual(manifest["case_id"], "rodinne-recepty")

    def test_scandocu_default_download_scan_ignores_files_older_than_week(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            downloads = root / "Downloads"
            vault = root / "documents"
            downloads.mkdir()
            old_pdf = downloads / "stary-dokument.pdf"
            recent_pdf = downloads / "novy-dokument.pdf"
            old_pdf.write_bytes(b"%PDF-1.4\nStary dokument\n")
            recent_pdf.write_bytes(b"%PDF-1.4\nNovy dokument\n")
            now = time.time()
            os.utime(old_pdf, (now - 9 * 24 * 60 * 60, now - 9 * 24 * 60 * 60))
            os.utime(recent_pdf, (now, now))

            default_items = scan_downloads_for_pdfs(downloads_dir=downloads, vault_dir=vault)
            all_items = scan_downloads_for_pdfs(downloads_dir=downloads, vault_dir=vault, max_age_days=None)

            self.assertEqual([item["name"] for item in default_items], ["novy-dokument.pdf"])
            self.assertEqual({item["name"] for item in all_items}, {"novy-dokument.pdf", "stary-dokument.pdf"})

    def test_scandocu_search_downloads_finds_old_pdf_by_name_or_date(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            downloads = root / "Downloads"
            vault = root / "documents"
            downloads.mkdir()
            old_pdf = downloads / "NajemniSmlouvaErbenovaUlice.pdf"
            old_pdf.write_bytes(b"%PDF-1.4\nNajemni smlouva\n")
            old_timestamp = 1_715_940_000
            os.utime(old_pdf, (old_timestamp, old_timestamp))
            old_date = time.strftime("%Y-%m-%d", time.localtime(old_timestamp))

            by_name = search_downloads_for_pdfs(query="Erbenova", downloads_dir=downloads, vault_dir=vault)
            by_date = search_downloads_for_pdfs(modified_date=old_date, downloads_dir=downloads, vault_dir=vault)
            candidate = prepare_specific_download_pdf(
                source_path=str(old_pdf),
                downloads_dir=downloads,
                vault_dir=vault,
            )

            self.assertEqual(by_name[0]["name"], old_pdf.name)
            self.assertEqual(by_date[0]["name"], old_pdf.name)
            self.assertEqual(candidate.source_path.name, old_pdf.name)

    def test_scandocu_select_download_already_in_vault_opens_review_candidate(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            downloads = root / "Downloads"
            vault = root / "documents"
            downloads.mkdir()
            pdf = downloads / "NajemniSmlouvaErbenovaUlice.pdf"
            pdf.write_bytes(b"%PDF-1.4\nNajemni smlouva Erbenova ulice\n")

            imported = apply_document_import_text(
                source_path=str(pdf),
                target_domain="home",
                document_type="lease",
                document_id="najemni-smlouva-erbenova-ulice",
                document_title="Najemni smlouva Erbenova ulice",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument NajemniSmlouvaErbenovaUlice.pdf do oblasti home.",
                vault_dir=vault,
            )
            found = search_downloads_for_pdfs(query="Erbenova", downloads_dir=downloads, vault_dir=vault)
            candidate = prepare_specific_download_pdf(
                source_path=str(pdf),
                downloads_dir=downloads,
                vault_dir=vault,
            )

            self.assertIn("Stav: ulozeno", imported)
            self.assertEqual(found[0]["status"], "already_in_vault")
            self.assertEqual(found[0]["duplicate_document_id"], "najemni-smlouva-erbenova-ulice")
            self.assertEqual(candidate.source_mode, "vault_review")
            self.assertEqual(candidate.review_document_id, "najemni-smlouva-erbenova-ulice")

    def test_scandocu_review_candidate_keeps_long_token_for_pdf_preview(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            source = root / "pojisteni.pdf"
            source.write_bytes(b"%PDF-1.4\nPojisteni vozidla\n")
            long_id = "kooperativa-pojisteni-vozidla-6300720621-2023"
            imported = apply_document_import_text(
                source_path=str(source),
                target_domain="insurance",
                document_type="insurance_policy",
                document_id=long_id,
                document_title="Pojisteni vozidla 6300720621",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument pojisteni.pdf do oblasti insurance.",
                vault_dir=vault,
            )
            self.assertIn("Stav: ulozeno", imported)
            self.mark_document_needs_review(vault, long_id)

            candidate = prepare_next_stored_document_review(vault_dir=vault)
            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertGreater(len(candidate.token), 64)
            self.assertEqual(candidate.to_api()["pdf_url"], f"/pdf/{candidate.token}")

            loaded = get_scandocu_candidate(candidate.token, vault_dir=vault)
            self.assertEqual(loaded.token, candidate.token)
            self.assertEqual(loaded.working_path, candidate.working_path)

    def test_scandocu_retries_stale_no_text_candidate_cache(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            source = root / "reportlab-text.pdf"
            source.write_bytes(b"%PDF-1.4\nText layer available\n")
            no_text = TextExtractionResult(
                text="",
                method="pdf-no-text",
                ocr_needed=True,
                warning="old cache",
            )
            with_text = TextExtractionResult(
                text="Text layer available",
                method="pdftotext",
                ocr_needed=False,
                warning="",
            )
            metadata = {
                "domain": "other",
                "document_type": "document",
                "counterparty": "",
                "related_asset": "",
                "tags": [],
            }
            with patch("app.documents.scandocu.extract_text", return_value=no_text), patch(
                "app.documents.scandocu.propose_metadata",
                return_value=metadata,
            ):
                stale = prepare_scandocu_candidate(source=source, vault_dir=vault)

            stale_data = json.loads(stale.metadata_path.read_text(encoding="utf-8"))
            stale_data.pop("extractor_retry_version", None)
            stale.metadata_path.write_text(json.dumps(stale_data, ensure_ascii=False, indent=2), encoding="utf-8")

            with patch("app.documents.scandocu.extract_text", return_value=with_text), patch(
                "app.documents.scandocu.propose_metadata",
                return_value=metadata,
            ):
                refreshed = prepare_scandocu_candidate(source=source, vault_dir=vault)

            refreshed_data = json.loads(refreshed.metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(refreshed.extraction_method, "pdftotext")
            self.assertFalse(refreshed.ocr_needed)
            self.assertEqual(refreshed_data["extractor_retry_version"], "2026-06-03-pdf-text-cache-v3")

    def test_scandocu_retries_stale_ocr_candidate_cache(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            source = root / "reportlab-text.pdf"
            source.write_bytes(b"%PDF-1.4\nText layer available\n")
            ocr_text = TextExtractionResult(
                text="OCR text",
                method="macos-vision-ocr",
                ocr_needed=False,
                warning="",
            )
            with_text = TextExtractionResult(
                text="Text layer available",
                method="pdftotext",
                ocr_needed=False,
                warning="",
            )
            metadata = {
                "domain": "other",
                "document_type": "document",
                "counterparty": "",
                "related_asset": "",
                "tags": [],
            }
            with patch("app.documents.scandocu.extract_text", return_value=ocr_text), patch(
                "app.documents.scandocu.propose_metadata",
                return_value=metadata,
            ):
                stale = prepare_scandocu_candidate(source=source, vault_dir=vault)

            stale_data = json.loads(stale.metadata_path.read_text(encoding="utf-8"))
            stale_data["extractor_retry_version"] = "2026-06-03-pdf-text-cache-v2"
            stale.metadata_path.write_text(json.dumps(stale_data, ensure_ascii=False, indent=2), encoding="utf-8")

            with patch("app.documents.scandocu.extract_text", return_value=with_text), patch(
                "app.documents.scandocu.propose_metadata",
                return_value=metadata,
            ):
                refreshed = prepare_scandocu_candidate(source=source, vault_dir=vault)

            refreshed_data = json.loads(refreshed.metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(refreshed.extraction_method, "pdftotext")
            self.assertFalse(refreshed.ocr_needed)
            self.assertEqual(refreshed_data["extractor_retry_version"], "2026-06-03-pdf-text-cache-v3")

    def test_scandocu_blocks_probable_duplicate_until_confirmed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            downloads = root / "Downloads"
            vault = root / "documents"
            downloads.mkdir()
            existing = root / "najemni-smlouva-jan-novak-dubova.pdf"
            existing.write_bytes(
                b"%PDF-1.4\n"
                b"Najemni smlouva\n"
                b"Najemce: Jan Novak\n"
                b"Adresa bytu: Dubova ulice\n"
            )
            imported = apply_document_import_text(
                source_path=str(existing),
                target_domain="home",
                document_type="lease",
                counterparty="Jan Novak",
                tags="najem, dubova",
                document_id="najemni-smlouva-jan-novak-dubova",
                document_title="Najemni smlouva Jan Novak Dubova",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument najemni-smlouva-jan-novak-dubova.pdf do oblasti home.",
                vault_dir=vault,
            )
            self.assertIn("Stav: ulozeno", imported)

            new_pdf = downloads / "gpt-najem-dubova-novak.pdf"
            new_pdf.write_bytes(
                b"%PDF-1.4\n"
                b"Najemni smlouva k bytu v ulici Dubova.\n"
                b"Jmeno najemce: Jan Novak.\n"
                b"Dokument vytvoreny z noveho PDF exportu.\n"
            )

            candidate = prepare_next_scandocu_pdf(downloads_dir=downloads, vault_dir=vault)
            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertTrue(candidate.probable_duplicates)
            duplicate = candidate.probable_duplicates[0]
            self.assertEqual(duplicate["document_id"], "najemni-smlouva-jan-novak-dubova")
            self.assertIn("vault/home/najemni-smlouva-jan-novak-dubova", duplicate["stored_path"])

            blocked = import_scandocu_candidate(
                token=candidate.token,
                title="Najemni smlouva Jan Novak Dubova kopie",
                domain="home",
                document_type="lease",
                tags="najem, dubova",
                vault_dir=vault,
            )
            self.assertEqual(blocked["status"], "probable_duplicate")
            self.assertIn("pravdepodobne", blocked["message"])

            confirmed = import_scandocu_candidate(
                token=candidate.token,
                title="Najemni smlouva Jan Novak Dubova kopie",
                domain="home",
                document_type="lease",
                tags="najem, dubova",
                allow_probable_duplicate=True,
                vault_dir=vault,
            )
            self.assertEqual(confirmed["status"], "imported")

    def test_scandocu_blocks_insurance_auto_consistency_conflict_until_confirmed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            downloads = root / "Downloads"
            vault = root / "documents"
            downloads.mkdir()
            existing = root / "cpp-predpis-3270612451.pdf"
            existing.write_bytes(
                b"%PDF-1.4\n"
                b"PREDPIS POJISTNEHO POJISTNA SMLOUVA | 3270612451\n"
                b"Obdobi: 1. 8. 2026 - 31. 7. 2027\n"
                b"RZ / VIN: 4SN 8981 / YV1MV79L1G2335020\n"
                b"VOLVO V40 CROSS COUNTRY\n"
                b"Ceska podnikatelska pojistovna, a. s., Vienna Insurance Group\n"
                b"Vase nove predepsane pojistne cini 4 512 Kc/ rocne\n"
            )
            imported = apply_document_import_text(
                source_path=str(existing),
                target_domain="insurance",
                document_type="insurance_payment_notice",
                counterparty="CPP",
                related_asset="auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981",
                document_id="cpp-predpis-pojistne-smlouvy-3270612451-2026",
                document_title="CPP predpis pojistne smlouvy 3270612451",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument cpp-predpis-3270612451.pdf do oblasti insurance.",
                vault_dir=vault,
            )
            self.assertIn("Stav: ulozeno", imported)

            new_pdf = downloads / "rixo-novy-navrh.pdf"
            new_pdf.write_bytes(
                b"%PDF-1.4\n"
                b"Cislo navrhu pojistne smlouvy 3275111280\n"
                b"POJISTITEL Ceska podnikatelska pojistovna, a. s., Vienna Insurance Group\n"
                b"Pocatek pojisteni: 01.08.2026 00:00\n"
                b"Registracni znacka (SPZ): 4SN8981\n"
                b"VOLVO V40 CROSS COUNTRY\n"
                b"Pojistne za pojistne obdobi - castka k uhrade: 4 956 Kc\n"
            )

            candidate = prepare_next_scandocu_pdf(downloads_dir=downloads, vault_dir=vault)
            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertFalse(candidate.probable_duplicates)

            blocked = import_scandocu_candidate(
                token=candidate.token,
                title="RIXO navrh pojistne smlouvy 3275111280",
                domain="insurance",
                document_type="insurance_policy",
                counterparty="CPP",
                related_asset="auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981",
                tags="auto, pojisteni",
                vault_dir=vault,
            )
            self.assertEqual(blocked["status"], "consistency_conflict")
            self.assertEqual(blocked["consistency_conflicts"][0]["asset"], "VOLVO V40 SPZ 4SN8981")
            self.assertIn("4 956 Kč", str(blocked["consistency_conflicts"]))
            self.assertIn("4 512 Kč", str(blocked["consistency_conflicts"]))

            confirmed = import_scandocu_candidate(
                token=candidate.token,
                title="RIXO navrh pojistne smlouvy 3275111280",
                domain="insurance",
                document_type="insurance_policy",
                counterparty="CPP",
                related_asset="auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981",
                tags="auto, pojisteni",
                allow_probable_duplicate=True,
                vault_dir=vault,
            )
            self.assertEqual(confirmed["status"], "imported")

    def test_importing_unlocked_pdf_skips_related_encrypted_download_variant(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            downloads = root / "Downloads"
            vault = root / "documents"
            downloads.mkdir()
            encrypted = downloads / "review-auto-pojisteni-navrh-2025-c04557f68165.pdf"
            unlocked = downloads / "review-auto-pojisteni-navrh-2025-Odemknute.pdf"
            encrypted.write_bytes(b"%PDF-1.4\n/Encrypt\n")
            unlocked.write_bytes(b"%PDF-1.4\nPojistna smlouva Volvo V40\n")
            now = time.time()
            os.utime(encrypted, (now - 60, now - 60))
            os.utime(unlocked, (now, now))

            candidate = prepare_next_scandocu_pdf(downloads_dir=downloads, vault_dir=vault)
            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertEqual(candidate.source_path.name, unlocked.name)

            result = import_scandocu_candidate(
                token=candidate.token,
                title="Auto pojisteni Volvo V40",
                domain="insurance",
                document_type="insurance_policy",
                allow_probable_duplicate=True,
                vault_dir=vault,
            )

            self.assertEqual(result["status"], "imported")
            self.assertIn(encrypted.name, result["skipped_related_download_variants"])
            statuses = {item["name"]: item["status"] for item in scan_downloads_for_pdfs(downloads_dir=downloads, vault_dir=vault)}
            self.assertEqual(statuses[unlocked.name], "already_in_vault")
            self.assertEqual(statuses[encrypted.name], "skipped")

    def test_recipe_metadata_does_not_treat_kostky_as_stk(self) -> None:
        metadata = propose_metadata(
            source=Path("scan_d.pdf"),
            text=(
                "Ruský salát\n"
                "Přísady na 4 porce: brambory a mrkev nakrájíme na kostky. "
                "Přidáme lžíce octa, olej a sůl. Doba přípravy 45 minut."
            ),
        )

        self.assertEqual(metadata["document_type"], "recipe")
        self.assertEqual(metadata["domain"], "food")
        self.assertIn("recept", metadata["tags"])
        self.assertNotIn("technicka-kontrola", metadata["tags"])

    def test_diet_guidance_metadata_is_health_not_car(self) -> None:
        metadata = propose_metadata(
            source=Path("scan_f.pdf"),
            text=(
                "Potraviny z hlediska obsahu purinových látek. Dieta při dně "
                "a jídelníček pacienta s cukrovkou musí respektovat sacharidy "
                "a optimální množství bílkovin."
            ),
        )

        self.assertEqual(metadata["document_type"], "diet_guidance")
        self.assertEqual(metadata["domain"], "health")
        self.assertIn("dieta", metadata["tags"])

    def test_auto_substring_does_not_classify_as_car(self) -> None:
        metadata = propose_metadata(
            source=Path("lekarna.pdf"),
            text=(
                "Lékárna vydala automaticky připravený přehled doporučení. "
                "Dokument obsahuje poznámky k užívání a běžné položky domácí lékárny."
            ),
        )

        self.assertNotEqual(metadata["domain"], "car")
        self.assertNotIn("auto", metadata["tags"])

    def test_povinne_text_does_not_trigger_vin_car_domain(self) -> None:
        metadata = propose_metadata(
            source=Path("vyuctovani.pdf"),
            text=(
                "Vyuctovani sluzeb. Povinne informace k platbe. "
                "Variabilni symbol a datum splatnosti."
            ),
        )

        self.assertEqual(metadata["document_type"], "invoice")
        self.assertNotEqual(metadata["domain"], "car")
        self.assertNotIn("auto", metadata["tags"])

    def test_insurance_without_vehicle_data_is_not_car(self) -> None:
        metadata = propose_metadata(
            source=Path("pojisteni.pdf"),
            text=(
                "Povinne pojisteni a potvrzeni o zaplaceni. "
                "Variabilni symbol 1234567890. Bez udaju o vozidle."
            ),
        )

        self.assertEqual(metadata["document_type"], "invoice")
        self.assertEqual(metadata["domain"], "insurance")
        self.assertEqual(metadata["related_asset"], "")
        self.assertNotIn("auto", metadata["tags"])

    def test_tmobile_invoice_metadata_is_telecom_not_car(self) -> None:
        metadata = propose_metadata(
            source=Path("Vyuctovani_40580553_2606.pdf"),
            text=(
                "T-Mobile Elektronické vyúčtování. Vyúčtování služeb za telefon "
                "a mobilní služby. Variabilní symbol a splatnost platby."
            ),
        )

        self.assertEqual(metadata["document_type"], "invoice")
        self.assertEqual(metadata["domain"], "telecom")
        self.assertEqual(metadata["related_asset"], "T-Mobile / mobilní služby")
        self.assertNotIn("auto", metadata["tags"])

    def test_travel_insurance_metadata_suggests_travel_asset(self) -> None:
        metadata = propose_metadata(
            source=Path("cestovni-pojisteni-zaplaceno.pdf"),
            text=(
                "Cestovní pojištění. Potvrzení o zaplacení cestovního pojištění "
                "pro cestu do zahraničí."
            ),
        )

        self.assertEqual(metadata["domain"], "insurance")
        self.assertEqual(metadata["related_asset"], "cestovní pojištění")

    def test_lease_contract_metadata_is_home_without_year_tags(self) -> None:
        metadata = propose_metadata(
            source=Path("NajemniSmlouvaDubovaUlice.pdf"),
            text=(
                "Nájemní smlouva k bytu v ulici Dubova. "
                "Nájemce: Jan Novak. Pronajímatel předává byt k užívání. "
                "Smlouva obsahuje data 2025, 2026 a 2036."
            ),
        )

        self.assertEqual(metadata["document_type"], "lease")
        self.assertEqual(metadata["domain"], "home")
        self.assertEqual(metadata["counterparty"], "Jan Novak")
        self.assertEqual(metadata["related_asset"], "Dubova ulice")
        self.assertIn("najem", metadata["tags"])
        self.assertIn("bydleni", metadata["tags"])
        self.assertNotIn("2025", metadata["tags"])
        self.assertNotIn("2026", metadata["tags"])

    def test_booking_travel_metadata_is_not_lease(self) -> None:
        metadata = propose_metadata(
            source=Path("Bibione_2026_prakticke_informace_pro_dceru.pdf"),
            text=(
                "Bibione 2026 - praktické informace z potvrzení Booking.com. "
                "Rezervace ubytování, check-in a check-out, adresa apartmánu, "
                "pokyny k pobytu, parkování pro auto a informace k dovolené."
            ),
        )

        self.assertEqual(metadata["document_type"], "travel_booking")
        self.assertEqual(metadata["domain"], "travel")
        self.assertEqual(metadata["related_asset"], "")
        self.assertIn("cestovani", metadata["tags"])
        self.assertNotIn("auto", metadata["tags"])
        self.assertNotIn("bydleni", metadata["tags"])

    def test_lease_counterparty_from_party_block(self) -> None:
        metadata = propose_metadata(
            source=Path("NajemniSmlouvaDubovaUlice.pdf"),
            text=(
                "Jako pronajímatel na straně jedné\n"
                "Titul, jméno a příjmení: Miloslav Falta\n"
                "jako pronajímatel\n"
                "Titul, jméno a příjmení: Jan Novak\n"
                "Titul, jméno a příjmení: Eva Novak\n"
                "jako nájemce na straně druhé\n"
                "Byt se nachází v Dubova ulice."
            ),
        )

        self.assertEqual(metadata["document_type"], "lease")
        self.assertEqual(metadata["domain"], "home")
        self.assertEqual(metadata["counterparty"], "Jan Novak; Eva Novak")
        self.assertEqual(metadata["related_asset"], "Dubova ulice")

    def test_document_inbox_startup_reminder_hides_filenames(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            incoming = vault / "inbox" / "incoming"
            incoming.mkdir(parents=True)
            (incoming / "citlivy-nazev-smlouvy.pdf").write_text("PDF", encoding="utf-8")

            result = format_document_inbox_reminder(vault_dir=vault)

            self.assertIn("1 cekajici", result)
            self.assertIn("scan_document_inbox", result)
            self.assertNotIn("citlivy-nazev-smlouvy.pdf", result)

    def test_import_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "faktura.pdf"
            source.write_text("Faktura za FVE. Splatnost 31.7.2026.", encoding="utf-8")
            vault = root / "documents"

            result = apply_document_import_text(
                source_path=str(source),
                target_domain="energy",
                document_type="invoice",
                user_confirmed=False,
                confirmation_text="",
                vault_dir=vault,
            )

            self.assertIn("nic nekopiruji", result)
            self.assertFalse(vault.exists())

    def test_confirmed_import_copies_document_and_writes_indexes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "faktura.pdf"
            source.write_text(
                "Faktura za fotovoltaiku. Dodavatel FVE Servis s.r.o. "
                "Splatnost 31.7.2026. Castka 4956 Kc.",
                encoding="utf-8",
            )
            vault = root / "documents"

            result = apply_document_import_text(
                source_path=str(source),
                target_domain="pojištění",
                document_type="invoice",
                counterparty="FVE Servis s.r.o.",
                related_asset="fotovoltaika",
                tags="fve; faktura",
                document_id="doc-test",
                user_confirmed=True,
                confirmation_text=(
                    "Potvrzuji, uloz dokument faktura.pdf do oblasti pojištění."
                ),
                vault_dir=vault,
            )

            self.assertIn("Stav: ulozeno", result)
            stored = vault / "vault" / "insurance" / "doc-test" / "faktura.pdf"
            self.assertTrue(stored.exists())
            manifest = json.loads((stored.parent / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["document_id"], "doc-test")
            self.assertTrue(manifest["safety_flags"]["do_not_commit"])

            docs_index = (vault / "index" / "documents_index.jsonl").read_text(encoding="utf-8")
            text_index = (vault / "index" / "text_index.jsonl").read_text(encoding="utf-8")
            due_index = (vault / "index" / "due_dates.jsonl").read_text(encoding="utf-8")
            self.assertIn("doc-test", docs_index)
            self.assertIn("fotovoltaiku", text_index)
            self.assertIn("2026-07-31", due_index)

    def test_car_document_import_suggests_asset_and_tags(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "volvo-v40-faktura.txt"
            source.write_text(
                "Danovy doklad za Volvo V40. Servisni prohlidka a vymena oleje. "
                "Splatnost 31.7.2026.",
                encoding="utf-8",
            )
            vault = root / "documents"

            preview = prepare_document_import_text(
                source_path=str(source),
                vault_dir=vault,
            )
            self.assertIn("Navrzena oblast: car", preview)
            self.assertIn("Vazba na majetek/zarizeni: Volvo V40", preview)

            result = apply_document_import_text(
                source_path=str(source),
                target_domain="car",
                document_id="volvo-v40-servis-2026",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument volvo-v40-faktura.txt do oblasti car.",
                vault_dir=vault,
            )

            self.assertIn("Stav: ulozeno", result)
            manifest = json.loads(
                (
                    vault
                    / "vault"
                    / "car"
                    / "volvo-v40-servis-2026"
                    / "manifest.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["document_type"], "invoice")
            self.assertEqual(manifest["related_asset"], "Volvo V40")
            self.assertIn("volvo-v40", manifest["tags"])
            self.assertIn("faktura", manifest["tags"])
            self.assertIn("servis", manifest["tags"])

    def test_motorcycle_registration_metadata_is_suggested(self) -> None:
        metadata = propose_metadata(
            source=Path("pojistna-smlouva-motocykl.pdf"),
            text=(
                "Pojistna smlouva\n"
                "Tovarni znacka YAMAHA Registracni znacka 1A2 3456\n"
                "Obchodni oznaceni TRACER 9 GT Rozlisovaci znacka statu CZ\n"
                "Druh vozidla: motocykl\n"
                "RZ vozidla: 1A2 3456\n"
                "Pojistovna Test a.s.\n"
            ),
        )

        self.assertEqual(metadata["domain"], "insurance")
        self.assertEqual(metadata["document_type"], "insurance_policy")
        self.assertEqual(metadata["related_asset"], "motocykl YAMAHA TRACER 9 GT SPZ 1A23456")
        self.assertIn("motocykl", metadata["tags"])
        self.assertIn("spz", metadata["tags"])
        self.assertIn("spz-1a23456", metadata["tags"])

    def test_motorcycle_without_registration_uses_make_and_model(self) -> None:
        metadata = propose_metadata(
            source=Path("pojistna-smlouva-motocykl.pdf"),
            text=(
                "Pojistna smlouva\n"
                "Tovarni znacka YAMAHA Registracni znacka NENI\n"
                "Obchodni oznaceni TRACER 9 GT Rozlisovaci znacka statu CZ\n"
                "Druh vozidla motocykl\n"
            ),
        )

        self.assertEqual(metadata["related_asset"], "motocykl YAMAHA TRACER 9 GT")
        self.assertIn("motocykl", metadata["tags"])
        self.assertIn("auto", metadata["tags"])
        self.assertNotIn("spz", metadata["tags"])

    def test_volvo_v40_policy_metadata_uses_clean_vehicle_asset(self) -> None:
        metadata = propose_metadata(
            source=Path("auto-pojisteni-volvo.pdf"),
            text=(
                "Pojistná smlouva\n"
                "Česká podnikatelská pojišťovna, a. s., Vienna Insurance Group\n"
                "Tovární značka: VOLVO VIN (výrobní číslo karoserie): TESTVIN1234567890\n"
                "Obchodní označení / Typ: V40 CROSS COUNTRY Série a číslo TP: TEST1234\n"
                "Registrační značka (SPZ): 9Z99999 Celková hmotnost v kg: 1980\n"
            ),
        )

        self.assertEqual(metadata["counterparty"], "Česká podnikatelská pojišťovna, a. s., Vienna Insurance Group")
        self.assertEqual(metadata["related_asset"], "auto VOLVO V40 CROSS COUNTRY SPZ 9Z99999")
        self.assertIn("volvo-v40", metadata["tags"])
        self.assertIn("spz-9z99999", metadata["tags"])

    def test_document_reindex_previews_and_applies_weak_metadata_updates(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "najemni-smlouva-dubova.txt"
            source.write_text(
                "Nájemní smlouva k bytu v ulici Dubova.\n"
                "Titul, jméno a příjmení: Jan Novak\n"
                "jako nájemce na straně druhé\n",
                encoding="utf-8",
            )
            vault = root / "documents"

            imported = apply_document_import_text(
                source_path=str(source),
                target_domain="other",
                document_type="document",
                document_id="stary-dokument",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument najemni-smlouva-dubova.txt do oblasti other.",
                vault_dir=vault,
            )
            self.assertIn("Stav: ulozeno", imported)
            manifest_path = vault / "vault" / "other" / "stary-dokument" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["counterparty"] = ""
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            index_path = vault / "index" / "documents_index.jsonl"
            rows = _read_jsonl(index_path)
            rows[0]["counterparty"] = ""
            with index_path.open("w", encoding="utf-8") as handle:
                for row in rows:
                    json.dump(row, handle, ensure_ascii=False)
                    handle.write("\n")

            preview = preview_document_reindex_text(vault_dir=vault)
            self.assertIn("Dokumentu s navrzenou zmenou: 1", preview)
            self.assertIn("document_type: document -> lease", preview)
            self.assertIn("counterparty: [prazdne] -> [vyplneno]", preview)

            blocked = apply_document_reindex_text(vault_dir=vault)
            self.assertIn("nebyl spusten", blocked)

            applied = apply_document_reindex_text(
                vault_dir=vault,
                user_confirmed=True,
                confirmation_text="Potvrzuji reindex ulozenych dokumentu.",
            )
            self.assertIn("Upravenych dokumentu: 1", applied)
            self.assertIn("reindex_backups", applied)

            manifest = json.loads(
                (
                    vault
                    / "vault"
                    / "other"
                    / "stary-dokument"
                    / "manifest.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["domain"], "home")
            self.assertEqual(manifest["document_type"], "lease")
            self.assertEqual(manifest["counterparty"], "Jan Novak")
            self.assertIn("najem", manifest["tags"])

            docs = _read_jsonl(vault / "index" / "documents_index.jsonl")
            self.assertEqual(docs[0]["domain"], "home")
            self.assertEqual(docs[0]["document_type"], "lease")

    def test_scandocu_review_updates_existing_document_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "najemni-smlouva-dubova.txt"
            source.write_text(
                "Nájemní smlouva k bytu v ulici Dubova.\n"
                "Titul, jméno a příjmení: Jan Novak\n"
                "jako nájemce na straně druhé\n",
                encoding="utf-8",
            )
            vault = root / "documents"

            imported = apply_document_import_text(
                source_path=str(source),
                target_domain="other",
                document_type="document",
                document_id="stary-dokument-review",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument najemni-smlouva-dubova.txt do oblasti other.",
                vault_dir=vault,
            )
            self.assertIn("Stav: ulozeno", imported)
            self.mark_document_needs_review(vault, "stary-dokument-review")

            candidate = prepare_next_stored_document_review(vault_dir=vault)
            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertEqual(candidate.source_mode, "vault_review")
            self.assertEqual(candidate.review_document_id, "stary-dokument-review")
            self.assertEqual(candidate.domain, "home")
            self.assertEqual(candidate.document_type, "lease")

            result = import_scandocu_candidate(
                token=candidate.token,
                title="Najemni smlouva Dubova",
                domain="home",
                document_type="Daňové přiznání",
                counterparty="Jan Novak",
                related_asset="Dubova ulice",
                tags="home, lease, najem, bydleni, dubova-ulice",
                case_id="Daňové přiznání 2025",
                vault_dir=vault,
            )
            self.assertEqual(result["status"], "reviewed")
            self.assertEqual(result["document_id"], "stary-dokument-review")
            self.assertIn("review_backups", result["backup_dir"])

            manifest = json.loads(
                (
                    vault
                    / "vault"
                    / "other"
                    / "stary-dokument-review"
                    / "manifest.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["title"], "Najemni smlouva Dubova")
            self.assertEqual(manifest["domain"], "home")
            self.assertEqual(manifest["document_type"], "danove-priznani")
            self.assertEqual(manifest["counterparty"], "Jan Novak")
            self.assertEqual(manifest["related_asset"], "Dubova ulice")
            self.assertEqual(manifest["case_id"], "danove-priznani-2025")
            self.assertEqual(manifest["reading_status"], "ok")
            self.assertEqual(manifest["reading_status_note"], "Potvrzeno revizí ve ScanDocu.")
            self.assertIn("dubova-ulice", manifest["tags"])
            docs = _read_jsonl(vault / "index" / "documents_index.jsonl")
            self.assertEqual(docs[0]["reading_status"], "ok")
            self.assertEqual(docs[0]["document_type"], "danove-priznani")
            self.assertEqual(docs[0]["case_id"], "danove-priznani-2025")

            next_candidate = prepare_next_stored_document_review(vault_dir=vault)
            self.assertIsNone(next_candidate)

    def test_scandocu_review_skips_trashed_documents(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            trashed_dir = vault / "trash" / "trashed-doc"
            active_dir = vault / "vault" / "tax" / "active-doc"
            trashed_dir.mkdir(parents=True)
            active_dir.mkdir(parents=True)
            trashed_pdf = trashed_dir / "trashed.pdf"
            active_pdf = active_dir / "active.pdf"
            trashed_pdf.write_bytes(b"%PDF-1.4\nTrashed\n")
            active_pdf.write_bytes(b"%PDF-1.4\nActive\n")
            index.mkdir(parents=True)
            (index / "documents_index.jsonl").write_text(
                "\n".join(
                    json.dumps(row, ensure_ascii=False)
                    for row in [
                        {
                            "document_id": "trashed-doc",
                            "title": "Trashed",
                            "stored_path": str(trashed_pdf),
                            "lifecycle_status": "trashed",
                        },
                        {
                            "document_id": "active-doc",
                            "title": "Active",
                            "stored_path": str(active_pdf),
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            candidate = prepare_next_stored_document_review(vault_dir=vault)

            self.assertIsNotNone(candidate)
            assert candidate is not None
            self.assertEqual(candidate.review_document_id, "active-doc")

    @staticmethod
    def mark_document_needs_review(vault: Path, document_id: str) -> None:
        index_path = vault / "index" / "documents_index.jsonl"
        rows = _read_jsonl(index_path)
        for row in rows:
            if str(row.get("document_id", "")) == document_id:
                row["reading_status"] = "needs_review"
        index_path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    def test_scandocu_ui_contains_encrypted_pdf_guidance(self) -> None:
        self.assertIn("PDF je šifrované nebo zamčené", SCANDOCU_HTML)
        self.assertIn("Heslo nepiš do chatu", SCANDOCU_HTML)
        self.assertIn("renderEncryptedHelp", SCANDOCU_HTML)

    def test_scandocu_ui_contains_completion_actions(self) -> None:
        self.assertIn("Zpět do Cockpitu", SCANDOCU_HTML)
        self.assertIn("function returnToCockpit", SCANDOCU_HTML)
        self.assertIn("window.opener.focus", SCANDOCU_HTML)
        self.assertIn('window.open(cockpitUrl, "SamanthaCockpit"', SCANDOCU_HTML)
        self.assertNotIn('document.getElementById("cockpitBtn").addEventListener("click", () => {\n      window.location.href = "http://127.0.0.1:8770";', SCANDOCU_HTML)
        self.assertIn("Ano, další dokument", SCANDOCU_HTML)
        self.assertIn("Hledat jiné PDF", SCANDOCU_HTML)
        self.assertIn("Ne, hotovo", SCANDOCU_HTML)
        self.assertIn("Revidovat z vaultu", SCANDOCU_HTML)
        self.assertIn("consistency_conflict", SCANDOCU_HTML)
        self.assertIn("renderImportWarnings", SCANDOCU_HTML)
        self.assertIn("let saving = false", SCANDOCU_HTML)
        self.assertIn("fields.saveBtn.disabled = true", SCANDOCU_HTML)
        self.assertIn("U větších PDF může krok trvat desítky sekund", SCANDOCU_HTML)

    def test_duplicate_content_is_not_imported_twice(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "smlouva.pdf"
            source.write_text("Pojistna smlouva. Platnost do 31.7.2026.", encoding="utf-8")
            vault = root / "documents"
            confirmation = "Potvrzuji, uloz dokument smlouva.pdf do oblasti insurance."

            first = apply_document_import_text(
                source_path=str(source),
                target_domain="insurance",
                document_type="contract",
                user_confirmed=True,
                confirmation_text=confirmation,
                vault_dir=vault,
            )
            second = apply_document_import_text(
                source_path=str(source),
                target_domain="insurance",
                document_type="contract",
                user_confirmed=True,
                confirmation_text=confirmation,
                vault_dir=vault,
            )

            self.assertIn("Stav: ulozeno", first)
            self.assertIn("Stav: uz existuje", second)
            self.assertEqual(len(list((vault / "vault" / "insurance").glob("*/smlouva.pdf"))), 1)

    def test_propose_inbox_cleanup_after_import(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            incoming = vault / "inbox" / "incoming"
            incoming.mkdir(parents=True)
            source = incoming / "potvrzeni.pdf"
            source.write_text("Potvrzeni prijmu 2025.", encoding="utf-8")

            apply_document_import_text(
                source_path=str(source),
                target_domain="tax",
                document_type="tax_income_confirmation",
                document_id="doc-tax",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument potvrzeni.pdf do oblasti tax.",
                vault_dir=vault,
            )

            result = propose_document_inbox_cleanup_text(
                source_path=str(source),
                vault_dir=vault,
            )

            self.assertIn("Dokument potvrzeni.pdf je zpracovan", result)
            self.assertIn("1. presunout", result)
            self.assertIn("2. smazat", result)
            self.assertIn("doc-tax", result)

    def test_resolve_inbox_item_moves_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            incoming = vault / "inbox" / "incoming"
            incoming.mkdir(parents=True)
            source = incoming / "potvrzeni.pdf"
            source.write_text("Potvrzeni prijmu 2025.", encoding="utf-8")
            apply_document_import_text(
                source_path=str(source),
                target_domain="tax",
                document_type="tax_income_confirmation",
                document_id="doc-tax",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument potvrzeni.pdf do oblasti tax.",
                vault_dir=vault,
            )

            result = resolve_document_inbox_item_text(
                source_path=str(source),
                action="move",
                user_confirmed=True,
                confirmation_text="Potvrzuji, presunout dokument potvrzeni.pdf do processed.",
                vault_dir=vault,
            )

            self.assertIn("Dokument byl presunut", result)
            self.assertFalse(source.exists())
            self.assertTrue((vault / "inbox" / "processed" / "potvrzeni.pdf").exists())
            actions = (vault / "index" / "inbox_actions.jsonl").read_text(encoding="utf-8")
            self.assertIn("move_to_processed", actions)
            self.assertIn("doc-tax", actions)
            self.assertIn("inbox/processed/potvrzeni.pdf", actions)

            search_result = search_private_documents_text(
                query="potvrzeni prijmu",
                vault_dir=vault,
            )

            self.assertIn("Zdrojova kopie", search_result)
            self.assertIn("inbox/processed/potvrzeni.pdf", search_result)

    def test_resolve_inbox_item_delete_requires_second_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            incoming = vault / "inbox" / "incoming"
            incoming.mkdir(parents=True)
            source = incoming / "potvrzeni.pdf"
            source.write_text("Potvrzeni prijmu 2025.", encoding="utf-8")

            result = resolve_document_inbox_item_text(
                source_path=str(source),
                action="delete",
                user_confirmed=True,
                confirmation_text="Chci smazat dokument potvrzeni.pdf z inboxu.",
                vault_dir=vault,
            )

            self.assertIn("vyzaduje druhe vyslovne potvrzeni", result)
            self.assertTrue(source.exists())

    def test_resolve_inbox_item_deletes_after_second_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            incoming = vault / "inbox" / "incoming"
            incoming.mkdir(parents=True)
            source = incoming / "potvrzeni.pdf"
            source.write_text("Potvrzeni prijmu 2025.", encoding="utf-8")
            apply_document_import_text(
                source_path=str(source),
                target_domain="tax",
                document_type="tax_income_confirmation",
                document_id="doc-tax",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument potvrzeni.pdf do oblasti tax.",
                vault_dir=vault,
            )

            result = resolve_document_inbox_item_text(
                source_path=str(source),
                action="delete",
                user_confirmed=True,
                confirmation_text="Ano, smazat dokument potvrzeni.pdf z inboxu.",
                vault_dir=vault,
            )

            self.assertIn("Dokument byl smazan", result)
            self.assertFalse(source.exists())
            actions = (vault / "index" / "inbox_actions.jsonl").read_text(encoding="utf-8")
            self.assertIn("delete_from_inbox", actions)
            self.assertIn("doc-tax", actions)

    def test_document_vault_status_returns_safe_aggregate_counts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = Path(temp_dir) / "documents"
            incoming = vault / "inbox" / "incoming"
            incoming.mkdir(parents=True)
            source = incoming / "potvrzeni.pdf"
            source.write_text("Potvrzeni prijmu 2025. Splatnost 31.7.2026.", encoding="utf-8")

            apply_document_import_text(
                source_path=str(source),
                target_domain="tax",
                document_type="tax_income_confirmation",
                document_id="doc-tax",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument potvrzeni.pdf do oblasti tax.",
                vault_dir=vault,
            )
            resolve_document_inbox_item_text(
                source_path=str(source),
                action="move",
                user_confirmed=True,
                confirmation_text="Potvrzuji, presunout dokument potvrzeni.pdf do processed.",
                vault_dir=vault,
            )

            result = document_vault_status_text(vault_dir=vault)

            self.assertIn("Document vault status", result)
            self.assertIn("Dokumentu v indexu: 1", result)
            self.assertIn("Inbox incoming (ceka na zpracovani): 0", result)
            self.assertIn("Zdrojove kopie ulozene v processed: 1", result)
            self.assertIn("Vyresenych souboru z incoming celkem: 1", result)
            self.assertIn("presunuto do processed", result)
            self.assertIn("trvale smazano po druhem potvrzeni: 0", result)
            self.assertIn("Inbox audit obdobi:", result)
            self.assertIn("Inbox audit akci za poslednich 30 dni: 1", result)
            self.assertIn("nezobrazuje zmeny od posledniho spusteni", result)
            self.assertIn("ne ulozena pripominka", result)
            self.assertIn("tax: 1", result)
            self.assertIn("tax_income_confirmation: 1", result)
            self.assertNotIn("Potvrzeni prijmu", result)

    def test_search_returns_safe_snippets(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "revize.pdf"
            source.write_text(
                "Revizni protokol fotovoltaika. Kontrola do 31.7.2026. "
                "Kontakt servis@example.com, rodne cislo 641215/0987 "
                "a odkaz https://example.com/private.",
                encoding="utf-8",
            )
            vault = root / "documents"
            apply_document_import_text(
                source_path=str(source),
                target_domain="energy",
                document_type="inspection_report",
                document_id="doc-revize",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument revize.pdf do oblasti energy.",
                vault_dir=vault,
            )

            result = search_private_documents_text(
                query="fotovoltaika kontrola",
                vault_dir=vault,
            )

            self.assertIn("doc-revize", result)
            self.assertIn("[e-mail redigovan]", result)
            self.assertIn("[rodne cislo redigovano]", result)
            self.assertIn("[URL redigovano]", result)
            self.assertNotIn("641215/0987", result)
            self.assertNotIn("https://example.com/private", result)

    def test_inspect_document_by_id_uses_private_index(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "zaruka.pdf"
            source.write_text("Zarucni list. Platnost do 31.7.2026.", encoding="utf-8")
            vault = root / "documents"
            apply_document_import_text(
                source_path=str(source),
                target_domain="warranty",
                document_type="warranty",
                document_id="doc-zaruka",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument zaruka.pdf do oblasti warranty.",
                vault_dir=vault,
            )

            result = inspect_document_text_text(document_id="doc-zaruka", vault_dir=vault)

            self.assertIn("valid_until", result)
            self.assertIn("2026-07-31", result)

    def test_save_document_due_reminder_requires_second_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reminders_path = Path(temp_dir) / "reminders.json"

            result = save_document_due_reminder_text(
                document_id="doc-test",
                title="Zaplatit fakturu z dokumentu",
                due_date="2026-07-31",
                due_date_type="payment_due",
                user_confirmed=False,
                confirmation_text="",
                reminders_path=reminders_path,
            )

            self.assertIn("Bez toho na disk nic nezapisuji", result)
            self.assertFalse(reminders_path.exists())

    def test_save_document_due_reminder_after_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reminders_path = Path(temp_dir) / "reminders.json"
            reminder_id = "document-doc-test-payment_due-2026-07-31"

            result = save_document_due_reminder_text(
                document_id="doc-test",
                title="Zaplatit fakturu z dokumentu",
                due_date="2026-07-31",
                due_date_type="payment_due",
                notes="Due date byl potvrzen z private dokumentu.",
                user_confirmed=True,
                confirmation_text=f"Potvrzuji, uloz pripominku {reminder_id}.",
                reminders_path=reminders_path,
            )

            data = json.loads(reminders_path.read_text(encoding="utf-8"))
            self.assertIn("Ulozeno", result)
            self.assertEqual(data["reminders"][0]["id"], reminder_id)
            self.assertEqual(data["reminders"][0]["source"]["type"], "private_document")

    def test_confirmation_accepts_czech_or_canonical_domain(self) -> None:
        self.assertTrue(
            has_explicit_document_import_confirmation(
                filename="faktura.pdf",
                target_domain="pojištění",
                confirmation_text="Potvrzuji, uloz dokument faktura.pdf do oblasti pojištění.",
            )
        )
        self.assertTrue(
            has_explicit_document_import_confirmation(
                filename="faktura.pdf",
                target_domain="pojištění",
                confirmation_text="Potvrzuji, uloz dokument faktura.pdf do oblasti insurance.",
            )
        )

    def test_confirmation_accepts_unicode_and_wrapped_filename(self) -> None:
        self.assertTrue(
            has_explicit_document_import_confirmation(
                filename="Daňové potvrzení za rok 2024 0109500617.pdf",
                target_domain="tax",
                confirmation_text=(
                    "Potvrzuji, uloz dokumenty Daňové potvrzení za rok 2024\n"
                    "  0109500617.pdf do oblasti tax."
                ),
            )
        )

    def test_prepare_print_job_copies_document_without_printing(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "smlouva.pdf"
            source.write_text("Puvodni smlouva o penzijnim pripojisteni.", encoding="utf-8")
            vault = root / "documents"

            apply_document_import_text(
                source_path=str(source),
                target_domain="tax",
                document_type="contract",
                document_id="penzijni-smlouva",
                user_confirmed=True,
                confirmation_text="Potvrzuji, uloz dokument smlouva.pdf do oblasti tax.",
                vault_dir=vault,
            )

            result = prepare_document_print_job_text(
                document_id="penzijni-smlouva",
                vault_dir=vault,
            )

            jobs = _read_jsonl(vault / "index" / "print_jobs.jsonl")
            queue_path = _job_queue_path(jobs[-1])
            self.assertIn("Dokument je pripraven k tisku", result)
            self.assertEqual(jobs[-1]["status"], "prepared")
            self.assertTrue(queue_path.exists())
            self.assertTrue((vault / "vault" / "tax" / "penzijni-smlouva" / "smlouva.pdf").exists())

    def test_run_print_job_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            print_job_id = _prepare_test_print_job(root=root, vault=vault)

            result = run_document_print_job_text(
                print_job_id=print_job_id,
                user_confirmed=False,
                confirmation_text="",
                vault_dir=vault,
                print_runner=_fake_successful_print,
            )

            self.assertIn("Tisk byl odmitnut", result)
            self.assertIn("samostatne potvrzeni", result)

    def test_successful_print_deletes_only_queue_copy(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            print_job_id = _prepare_test_print_job(root=root, vault=vault)
            before_jobs = _read_jsonl(vault / "index" / "print_jobs.jsonl")
            queue_path = _job_queue_path(before_jobs[-1])

            result = run_document_print_job_text(
                print_job_id=print_job_id,
                user_confirmed=True,
                confirmation_text=f"Potvrzuji, vytiskni print job {print_job_id}.",
                vault_dir=vault,
                print_runner=_fake_successful_print,
            )

            after_jobs = _read_jsonl(vault / "index" / "print_jobs.jsonl")
            original = vault / "vault" / "tax" / "penzijni-smlouva" / "smlouva.pdf"
            self.assertIn("Tisk byl predan systemu", result)
            self.assertFalse(queue_path.exists())
            self.assertTrue(original.exists())
            self.assertEqual(after_jobs[-1]["status"], "printed")

    def test_failed_print_keeps_queue_copy(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            print_job_id = _prepare_test_print_job(root=root, vault=vault)
            before_jobs = _read_jsonl(vault / "index" / "print_jobs.jsonl")
            queue_path = _job_queue_path(before_jobs[-1])

            result = run_document_print_job_text(
                print_job_id=print_job_id,
                user_confirmed=True,
                confirmation_text=f"Potvrzuji, vytiskni print job {print_job_id}.",
                vault_dir=vault,
                print_runner=_fake_failed_print,
            )

            after_jobs = _read_jsonl(vault / "index" / "print_jobs.jsonl")
            self.assertIn("Tisk se nedari", result)
            self.assertTrue(queue_path.exists())
            self.assertEqual(after_jobs[-1]["status"], "failed")

    def test_parse_macos_vision_ocr_json(self) -> None:
        raw = json.dumps(
            {
                "page_count": 2,
                "processed_pages": 2,
                "pages": [
                    {"page": 1, "text": "Pojistna smlouva"},
                    {"page": 2, "text": "Splatnost 31.7.2026"},
                ],
            }
        )

        parsed = parse_macos_vision_ocr_json(raw)

        self.assertIsInstance(parsed, dict)
        assert isinstance(parsed, dict)
        self.assertIn("[page 1]", parsed["text"])
        self.assertIn("Splatnost 31.7.2026", parsed["text"])

    def test_pdf_encryption_marker_does_not_block_readable_text(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            source = Path(temp_dir) / "readable-owner-encrypted.pdf"
            source.write_bytes(b"%PDF-1.4\n/Encrypt\n")

            with (
                patch("app.documents.vault.is_pdf_encrypted", return_value=True),
                patch(
                    "app.documents.vault.extract_pdf_with_pdftotext",
                    return_value=TextExtractionResult(
                        text="Tabulka asistenčních služeb",
                        method="pdftotext",
                        ocr_needed=False,
                    ),
                ),
            ):
                result = extract_text(source)

        self.assertEqual(result.method, "pdftotext")
        self.assertIn("Tabulka", result.text)

    def test_resolve_pdftotext_uses_common_homebrew_path_when_path_is_sparse(self) -> None:
        def fake_is_file(path: Path) -> bool:
            return str(path) == "/usr/local/bin/pdftotext"

        with patch("app.documents.vault.shutil.which", return_value=None), patch(
            "app.documents.vault.Path.is_file",
            fake_is_file,
        ):
            resolved = resolve_pdftotext_binary()

        self.assertEqual(resolved, "/usr/local/bin/pdftotext")

    def test_pdfplumber_tables_enrich_existing_text(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            source = Path(temp_dir) / "tabulka.pdf"
            source.write_bytes(b"%PDF-1.4\n")
            base = TextExtractionResult(
                text="Puvodni text smlouvy",
                method="pdftotext",
                ocr_needed=False,
            )

            with patch(
                "app.documents.vault.extract_pdf_tables_with_pdfplumber",
                return_value=TableExtractionResult(
                    text="[page 1 table 1]\nSluzba | Limit\nOdtah | 50 km",
                    method="pdfplumber-tables",
                    table_count=1,
                ),
            ):
                result = enrich_pdf_text_with_tables(source, base)

        self.assertEqual(result.method, "pdftotext+pdfplumber-tables")
        self.assertIn("Puvodni text smlouvy", result.text)
        self.assertIn("Sluzba | Limit", result.text)


def _prepare_test_print_job(root: Path, vault: Path) -> str:
    source = root / "smlouva.pdf"
    source.write_text("Puvodni smlouva o penzijnim pripojisteni.", encoding="utf-8")
    apply_document_import_text(
        source_path=str(source),
        target_domain="tax",
        document_type="contract",
        document_id="penzijni-smlouva",
        user_confirmed=True,
        confirmation_text="Potvrzuji, uloz dokument smlouva.pdf do oblasti tax.",
        vault_dir=vault,
    )
    prepare_document_print_job_text(document_id="penzijni-smlouva", vault_dir=vault)
    return str(_read_jsonl(vault / "index" / "print_jobs.jsonl")[-1]["print_job_id"])


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return rows


def _job_queue_path(job: dict[str, object]) -> Path:
    return Path(str(job["queue_path"]))


def _fake_successful_print(*args: object, **kwargs: object) -> object:
    return SimpleNamespace(returncode=0, stdout="request id is printer-1", stderr="")


def _fake_failed_print(*args: object, **kwargs: object) -> object:
    return SimpleNamespace(returncode=1, stdout="", stderr="printer offline")


if __name__ == "__main__":
    unittest.main()
