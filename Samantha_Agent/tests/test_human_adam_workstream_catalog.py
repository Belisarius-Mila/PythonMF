from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path

from app.communication.human_adam_workstream_catalog import (
    PRIVATE_ARCHIVE_CONFIRMATION_CATEGORIES,
    WORKSTREAM_CATALOG,
    CanonicalWorkstream,
    CanonicalWorkstreamCapabilities,
    validate_workstream_catalog,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _active_project_names() -> set[str]:
    rows: set[str] = set()
    for line in (PROJECT_ROOT / "memory/ACTIVE_PROJECTS.md").read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or "Oblast |" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[2] == "active":
            rows.add(cells[0])
    return rows


class WorkstreamCatalogTests(unittest.TestCase):
    def test_catalog_covers_every_active_registry_row_and_two_default_misc_streams(self) -> None:
        source_names = [
            source_name
            for record in WORKSTREAM_CATALOG
            for source_name in record.source_names
        ]
        misc_ids = {
            record.workstream_id
            for record in WORKSTREAM_CATALOG
            if record.workstream_type == "Misc"
        }

        self.assertEqual(
            set(source_names),
            _active_project_names() | {"Vocabulary FR", "Vocabulary IT"},
        )
        self.assertEqual(
            Counter(source_names)["TTS / Adam Voice Remote Cockpit"],
            2,
        )
        self.assertEqual(
            {
                source_name: count
                for source_name, count in Counter(source_names).items()
                if count > 1
            },
            {"TTS / Adam Voice Remote Cockpit": 2},
        )
        self.assertEqual(
            misc_ids,
            {"misc-brainstorm", "misc-unclassified-development"},
        )
        self.assertEqual(len(WORKSTREAM_CATALOG), 30)

    def test_catalog_has_expected_type_distribution(self) -> None:
        self.assertEqual(
            Counter(record.workstream_type for record in WORKSTREAM_CATALOG),
            {"Project": 24, "Tool": 4, "Misc": 2},
        )
        self.assertEqual(
            Counter(record.mode for record in WORKSTREAM_CATALOG),
            {"active": 27, "paused": 3},
        )

    def test_family_calendar_is_a_distinct_active_project(self) -> None:
        calendar = next(
            record
            for record in WORKSTREAM_CATALOG
            if record.workstream_id == "project-family-calendar"
        )
        knihovna = next(
            record
            for record in WORKSTREAM_CATALOG
            if record.workstream_id == "project-knowledge-library"
        )

        self.assertEqual(calendar.name, "Rodinný kalendář")
        self.assertEqual(calendar.workstream_type, "Project")
        self.assertEqual(calendar.mode, "active")
        self.assertEqual(calendar.priority, "1")
        self.assertEqual(calendar.source_names, ("Rodinný kalendář",))
        self.assertNotEqual(calendar.workstream_id, knihovna.workstream_id)

    def test_human_adam_is_a_project_with_legacy_runtime_aliases(self) -> None:
        human_adam = next(
            record
            for record in WORKSTREAM_CATALOG
            if record.workstream_id == "layer-human-adam-development"
        )

        self.assertEqual(human_adam.workstream_type, "Project")
        self.assertEqual(human_adam.name, "Human–Adam")
        self.assertEqual(human_adam.binding_type_aliases, ("Layer",))
        self.assertEqual(
            human_adam.binding_aliases,
            ("Human–Adam / vývojové prostředí",),
        )

    def test_private_archive_capabilities_are_declared_only_for_knihovna(self) -> None:
        knihovna = next(
            record
            for record in WORKSTREAM_CATALOG
            if record.workstream_id == "project-knowledge-library"
        )
        other_records = tuple(
            record
            for record in WORKSTREAM_CATALOG
            if record.workstream_id != knihovna.workstream_id
        )

        self.assertEqual(
            knihovna.capabilities,
            CanonicalWorkstreamCapabilities(
                private_archive_direct=True,
                private_archive_read=True,
                private_archive_single_edit=True,
                private_archive_confirmation_required=(
                    PRIVATE_ARCHIVE_CONFIRMATION_CATEGORIES
                ),
            ),
        )
        self.assertTrue(other_records)
        self.assertTrue(
            all(
                record.capabilities == CanonicalWorkstreamCapabilities()
                for record in other_records
            )
        )

    def test_private_archive_capability_metadata_is_not_tied_to_one_catalog_id(
        self,
    ) -> None:
        capabilities = CanonicalWorkstreamCapabilities(
            private_archive_direct=True,
            private_archive_read=True,
            private_archive_single_edit=True,
            private_archive_confirmation_required=(
                PRIVATE_ARCHIVE_CONFIRMATION_CATEGORIES
            ),
        )
        record = CanonicalWorkstream(
            "project-capable-example",
            "Project",
            "Schopný příklad",
            "active",
            "2",
            ("Zdroj schopného příkladu",),
            capabilities=capabilities,
        )

        self.assertEqual(validate_workstream_catalog((record,)), (record,))
        self.assertEqual(record.capabilities.status_fields()["private_archive_direct"], True)

    def test_paused_vocabulary_projects_come_from_confirmed_capability_map(self) -> None:
        capability_map = (PROJECT_ROOT / "memory/technical/project_capability_map.md").read_text(
            encoding="utf-8"
        )
        paused_ids = {
            record.workstream_id
            for record in WORKSTREAM_CATALOG
            if record.mode == "paused"
        }

        self.assertEqual(
            paused_ids,
            {"project-mobile-input", "project-vocabulary-fr", "project-vocabulary-it"},
        )
        self.assertIn("| Vocabulary FR |", capability_map)
        self.assertIn("| Vocabulary IT |", capability_map)

    def test_memory_catalog_lists_every_code_catalog_id_once(self) -> None:
        text = (PROJECT_ROOT / "memory/WORKSTREAMS.md").read_text(encoding="utf-8")
        catalog_section = text.split("## Uplny kanonicky katalog", 1)[1].split(
            "## Stavajici runtime vazby", 1
        )[0]
        listed_ids = re.findall(r"^\| `([^`]+)` \|", catalog_section, flags=re.MULTILINE)

        self.assertEqual(
            listed_ids,
            [record.workstream_id for record in WORKSTREAM_CATALOG],
        )

    def test_catalog_contains_no_private_thread_or_workspace_state(self) -> None:
        serialized = repr(WORKSTREAM_CATALOG).casefold()
        self.assertNotIn("thread_id", serialized)
        self.assertNotIn("workspace_root", serialized)
        self.assertNotIn("profile_id", serialized)

    def test_validation_accepts_paused_and_archived_modes_for_later_phases(self) -> None:
        records = (
            CanonicalWorkstream(
                "project-paused",
                "Project",
                "Pozastavený projekt",
                "paused",
                "2",
                ("Zdroj A",),
            ),
            CanonicalWorkstream(
                "tool-archived",
                "Tool",
                "Archivní nástroj",
                "archived",
                "3",
                ("Zdroj B",),
            ),
        )

        self.assertEqual(validate_workstream_catalog(records), records)

    def test_validation_rejects_duplicate_ids(self) -> None:
        records = (
            CanonicalWorkstream(
                "project-same",
                "Project",
                "První projekt",
                "active",
                "1",
                ("Zdroj A",),
            ),
            CanonicalWorkstream(
                "project-same",
                "Project",
                "Druhý projekt",
                "active",
                "2",
                ("Zdroj B",),
            ),
        )

        with self.assertRaisesRegex(ValueError, "duplicitní ID"):
            validate_workstream_catalog(records)


if __name__ == "__main__":
    unittest.main()
