from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.reminders.payment_case_documents import (
    has_explicit_payment_document_save_confirmation,
    save_payment_case_document_text,
)


class PaymentCaseDocumentTests(unittest.TestCase):
    def test_confirmation_requires_case_id_filename_save_and_document_words(self) -> None:
        self.assertTrue(
            has_explicit_payment_document_save_confirmation(
                case_id="sms-platba-3275111280-2026-07-31",
                filename="faktura.pdf",
                confirmation_text=(
                    "Potvrzuji, uloz fakturu faktura.pdf k case_id "
                    "sms-platba-3275111280-2026-07-31."
                ),
            )
        )
        self.assertFalse(
            has_explicit_payment_document_save_confirmation(
                case_id="sms-platba-3275111280-2026-07-31",
                filename="faktura.pdf",
                confirmation_text="Potvrzuji, uloz fakturu.",
            )
        )

    def test_without_confirmation_does_not_copy(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "faktura.pdf"
            source.write_bytes(b"PDF")
            vault = root / "vault"

            result = save_payment_case_document_text(
                case_id="sms-platba-3275111280-2026-07-31",
                source_path=str(source),
                user_confirmed=False,
                confirmation_text="",
                vault_dir=vault,
            )

            self.assertIn("nic nekopiruji", result)
            self.assertFalse(vault.exists())

    def test_confirmed_save_copies_document_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "faktura.pdf"
            source.write_bytes(b"PDF invoice")
            vault = root / "vault"
            case_id = "sms-platba-3275111280-2026-07-31"

            result = save_payment_case_document_text(
                case_id=case_id,
                source_path=str(source),
                document_type="invoice",
                description="Faktura z e-mailove prilohy pro uhradu pojistky.",
                user_confirmed=True,
                confirmation_text=(
                    f"Potvrzuji, uloz fakturu {source.name} k case_id {case_id}."
                ),
                vault_dir=vault,
            )
            manifest_path = vault / case_id / "documents_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertIn("Stav: ulozeno", result)
            self.assertTrue((vault / case_id / "documents" / "001_invoice_faktura.pdf").exists())
            self.assertEqual(manifest["documents"][0]["original_filename"], "faktura.pdf")
            self.assertEqual(manifest["documents"][0]["document_type"], "invoice")
            self.assertTrue(manifest["documents"][0]["safety_flags"]["do_not_commit"])

    def test_duplicate_content_is_not_copied_twice(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "faktura.pdf"
            source.write_bytes(b"PDF invoice")
            vault = root / "vault"
            case_id = "sms-platba-3275111280-2026-07-31"
            confirmation = f"Potvrzuji, uloz fakturu {source.name} k case_id {case_id}."

            first = save_payment_case_document_text(
                case_id=case_id,
                source_path=str(source),
                user_confirmed=True,
                confirmation_text=confirmation,
                vault_dir=vault,
            )
            second = save_payment_case_document_text(
                case_id=case_id,
                source_path=str(source),
                user_confirmed=True,
                confirmation_text=confirmation,
                vault_dir=vault,
            )

            self.assertIn("Stav: ulozeno", first)
            self.assertIn("Stav: uz existuje", second)
            self.assertEqual(len(list((vault / case_id / "documents").iterdir())), 1)

    def test_rejects_url_source(self) -> None:
        result = save_payment_case_document_text(
            case_id="case",
            source_path="https://example.com/faktura.pdf",
            user_confirmed=True,
            confirmation_text="Potvrzuji, uloz fakturu faktura.pdf k case_id case.",
        )

        self.assertIn("odmitnuto", result)
        self.assertIn("lokalni soubor", result)


if __name__ == "__main__":
    unittest.main()
