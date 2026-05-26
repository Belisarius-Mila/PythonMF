from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.documents.tools import (
    apply_document_import_text,
    document_vault_status_text,
    inspect_document_text_text,
    prepare_document_import_text,
    prepare_mobile_document_batch_text,
    prepare_document_print_job_text,
    propose_document_inbox_cleanup_text,
    resolve_document_inbox_item_text,
    run_document_print_job_text,
    save_document_due_reminder_text,
    scan_document_inbox_text,
    scan_mobile_document_inbox_text,
    search_private_documents_text,
)
from app.documents.vault import format_document_inbox_reminder
from app.documents.vault import has_explicit_document_import_confirmation
from app.documents.vault import parse_macos_vision_ocr_json
from app.documents.vault import TableExtractionResult
from app.documents.vault import TextExtractionResult
from app.documents.vault import enrich_pdf_text_with_tables
from app.documents.vault import extract_text

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


class DocumentVaultToolsTests(unittest.TestCase):
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
