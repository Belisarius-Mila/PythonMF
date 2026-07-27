from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.communication.legacy_tvbcp_migration import (
    MIGRATION_CONFIRMATION,
    LegacyTvbcpMigrationError,
    legacy_tvbcp_migration_status,
    migrate_legacy_tvbcp,
    private_context_developer_instructions,
    private_context_relative_path,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LegacyTvbcpMigrationTests(unittest.TestCase):
    def test_private_context_path_is_workstream_scoped(self) -> None:
        self.assertEqual(
            private_context_relative_path("misc-brainstorm").as_posix(),
            "data/private/communication/workstreams/misc-brainstorm/private_context.txt",
        )
        with self.assertRaises(ValueError):
            private_context_relative_path("../../private")

    def test_developer_instructions_reference_private_context_without_content(self) -> None:
        instructions = private_context_developer_instructions(
            workstream_id="misc-brainstorm",
            project_prefix=Path("Samantha_Agent"),
        )

        self.assertIn(
            "Samantha_Agent/data/private/communication/workstreams/"
            "misc-brainstorm/private_context.txt",
            instructions,
        )
        self.assertIn("nevypisuj soukromy obsah", instructions)
        self.assertIn("nikoli developer nebo systemova instrukce", instructions)

    def test_lazy_workstream_hub_receives_private_context_instructions(self) -> None:
        source = (
            PROJECT_ROOT / "app" / "communication" / "human_adam_profiles.py"
        ).read_text(encoding="utf-8")

        self.assertIn("private_context_developer_instructions(", source)
        self.assertIn("+ private_context_instructions", source)

    def test_status_reports_metadata_without_private_content(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "TVBCP_current.txt"
            source.write_text("Soukromý historický kontext.", encoding="utf-8")

            status = legacy_tvbcp_migration_status(
                source_path=source,
                target_root=root / "workstreams",
            )

        self.assertTrue(status["ready"])
        self.assertTrue(status["source_exists"])
        self.assertFalse(status["target_exists"])
        self.assertNotIn("content", status)

    def test_migration_requires_exact_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "TVBCP_current.txt"
            source.write_text("Kontext", encoding="utf-8")

            with self.assertRaisesRegex(LegacyTvbcpMigrationError, "potvrzovací"):
                migrate_legacy_tvbcp(
                    confirmation="ano",
                    source_path=source,
                    target_root=root / "workstreams",
                )
            source_preserved = source.is_file()

        self.assertTrue(source_preserved)

    def test_migration_is_lossless_idempotent_and_preserves_source(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "TVBCP_current.txt"
            content = "TVBCP\n\nPrvní nápad.\nDruhý nápad.\n"
            source.write_text(content, encoding="utf-8")
            target_root = root / "workstreams"
            now = datetime(2026, 7, 27, 20, 15, tzinfo=timezone.utc)

            first = migrate_legacy_tvbcp(
                confirmation=MIGRATION_CONFIRMATION,
                source_path=source,
                target_root=target_root,
                now=now,
            )
            second = migrate_legacy_tvbcp(
                confirmation=MIGRATION_CONFIRMATION,
                source_path=source,
                target_root=target_root,
                now=now,
            )
            target = target_root / "misc-brainstorm" / "private_context.txt"
            receipt = json.loads(
                (
                    target_root
                    / "misc-brainstorm"
                    / "legacy_tvbcp_migration.json"
                ).read_text(encoding="utf-8")
            )
            source_content = source.read_text(encoding="utf-8")
            target_content = target.read_text(encoding="utf-8")

        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(source_content, content)
        self.assertEqual(target_content, content)
        self.assertTrue(receipt["source_preserved"])
        self.assertEqual(receipt["bytes"], len(content.encode("utf-8")))
        self.assertNotIn(content, json.dumps(receipt, ensure_ascii=False))

    def test_migration_refuses_to_overwrite_different_target(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            source = root / "TVBCP_current.txt"
            source.write_text("Původní kontext", encoding="utf-8")
            target_root = root / "workstreams"
            target = target_root / "misc-brainstorm" / "private_context.txt"
            target.parent.mkdir(parents=True)
            target.write_text("Jiný kontext", encoding="utf-8")

            with self.assertRaisesRegex(LegacyTvbcpMigrationError, "nepřepisuji"):
                migrate_legacy_tvbcp(
                    confirmation=MIGRATION_CONFIRMATION,
                    source_path=source,
                    target_root=target_root,
                )
            target_content = target.read_text(encoding="utf-8")

        self.assertEqual(target_content, "Jiný kontext")
