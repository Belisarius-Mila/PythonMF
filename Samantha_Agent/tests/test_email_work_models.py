from __future__ import annotations

import unittest

from app.email.work_models import (
    EmailWorkItem,
    EmailWorkState,
    classify_email_processing_category,
    email_processing_batch_groups,
    email_processing_is_inbound_work_folder,
    email_processing_item_id,
    normalize_email_work_item,
)


class EmailWorkModelTests(unittest.TestCase):
    def test_reference_is_stable_for_provider_folder_uid(self) -> None:
        first = EmailWorkItem.from_mapping({
            "provider": "iCloud",
            "folder": "INBOX",
            "uid": "123",
            "subject": "Původní",
            "is_new_header": True,
        })
        second = EmailWorkItem.from_mapping({
            "provider": "iCloud",
            "folder": "INBOX",
            "uid": "123",
            "subject": "Změněný předmět",
            "action": "process",
        })

        self.assertEqual(first.work_ref, second.work_ref)
        self.assertEqual(first.item_id, second.item_id)
        self.assertNotEqual(first.state, second.state)

    def test_provider_is_part_of_identity(self) -> None:
        icloud = email_processing_item_id("", "iCloud", "INBOX", "123", "", "")
        seznam = email_processing_item_id("", "Seznam", "INBOX", "123", "", "")

        self.assertNotEqual(icloud, seznam)

    def test_normalized_item_preserves_payload_and_adds_work_contract(self) -> None:
        result = normalize_email_work_item({
            "provider": "Seznam",
            "folder": "INBOX",
            "uid": "456",
            "subject": "Faktura",
            "custom": {"kept": True},
            "action": "trash_requested",
        })

        self.assertEqual(result["custom"], {"kept": True})
        self.assertEqual(result["work_state"], EmailWorkState.TRASH_REVIEW.value)
        self.assertEqual(result["work_action"], "trash_requested")
        self.assertTrue(result["work_ref"].startswith("emailworkref-"))

    def test_outbound_folders_are_not_work_inbox(self) -> None:
        self.assertTrue(email_processing_is_inbound_work_folder("INBOX"))
        self.assertFalse(email_processing_is_inbound_work_folder("Sent Messages"))
        self.assertFalse(email_processing_is_inbound_work_folder("Koncepty"))

    def test_classification_and_batch_groups_are_part_of_work_model(self) -> None:
        category = classify_email_processing_category("Daňový doklad")
        groups = email_processing_batch_groups({
            "category": category,
            "pdf_attachment_count": 1,
            "amount_scan": {"max_amount_czk": 2500},
        })

        self.assertEqual(category, "faktury/e-shopy")
        self.assertIn({"id": "invoice", "label": "Faktury / e-shopy"}, groups)
        self.assertIn({"id": "invoice_over_2000", "label": "Faktury nad 2000 Kč"}, groups)
        self.assertIn({"id": "pdf", "label": "S PDF přílohou"}, groups)


if __name__ == "__main__":
    unittest.main()
