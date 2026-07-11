from __future__ import annotations

import unittest

from app.documents.intake_models import (
    DocumentIntakeItem,
    DocumentIntakeSource,
    DocumentIntakeSourceSnapshot,
    DocumentIntakeState,
    unified_intake_items,
)


class DocumentIntakeModelTests(unittest.TestCase):
    def test_stable_reference_uses_private_key_without_exposing_it(self) -> None:
        first = DocumentIntakeItem.build(
            source=DocumentIntakeSource.EMAIL,
            title="Doklad",
            source_key="private-provider/inbox/123",
        )
        second = DocumentIntakeItem.build(
            source=DocumentIntakeSource.EMAIL,
            title="Přejmenovaný doklad",
            source_key="private-provider/inbox/123",
        )

        self.assertEqual(first.intake_ref, second.intake_ref)
        public = first.to_source_item()
        self.assertNotIn("source_key", public)
        self.assertNotIn("private-provider", str(public))

    def test_same_key_in_different_sources_has_different_reference(self) -> None:
        download = DocumentIntakeItem.build(
            source=DocumentIntakeSource.DOWNLOADS,
            title="Doklad",
            source_key="same.pdf",
        )
        local = DocumentIntakeItem.build(
            source=DocumentIntakeSource.LOCAL_INBOX,
            title="Doklad",
            source_key="same.pdf",
        )

        self.assertNotEqual(download.intake_ref, local.intake_ref)

    def test_unified_output_follows_source_policy(self) -> None:
        snapshots = [
            DocumentIntakeSourceSnapshot(
                source=DocumentIntakeSource.MOBILE,
                state=DocumentIntakeState.READY,
                total_count=1,
                next_action="Ruční kontrola.",
                items=(DocumentIntakeItem.build(source=DocumentIntakeSource.MOBILE, title="Mobil", source_key="m1"),),
            ),
            DocumentIntakeSourceSnapshot(
                source=DocumentIntakeSource.DOWNLOADS,
                state=DocumentIntakeState.READY,
                total_count=1,
                next_action="ScanDocu.",
                items=(DocumentIntakeItem.build(source=DocumentIntakeSource.DOWNLOADS, title="PDF", source_key="d1"),),
            ),
        ]

        result = unified_intake_items(snapshots)

        self.assertEqual([item["source_id"] for item in result], ["downloads", "mobile"])
        self.assertEqual(result[0]["action_kind"], "open_scandocu")
        self.assertEqual(result[1]["action_kind"], "manual")

    def test_snapshot_rejects_item_from_different_source(self) -> None:
        item = DocumentIntakeItem.build(
            source=DocumentIntakeSource.EMAIL,
            title="E-mail",
            source_key="mail-1",
        )

        with self.assertRaisesRegex(ValueError, "nepatří do zdroje"):
            DocumentIntakeSourceSnapshot(
                source=DocumentIntakeSource.DOWNLOADS,
                state=DocumentIntakeState.READY,
                total_count=1,
                next_action="ScanDocu.",
                items=(item,),
            )

    def test_snapshot_rejects_count_smaller_than_visible_items(self) -> None:
        item = DocumentIntakeItem.build(
            source=DocumentIntakeSource.MOBILE,
            title="Scan",
            source_key="scan-1",
        )

        with self.assertRaisesRegex(ValueError, "total_count"):
            DocumentIntakeSourceSnapshot(
                source=DocumentIntakeSource.MOBILE,
                state=DocumentIntakeState.READY,
                total_count=0,
                next_action="Zpracovat.",
                items=(item,),
            )


if __name__ == "__main__":
    unittest.main()
