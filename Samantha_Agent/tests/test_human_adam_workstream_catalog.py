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


def _all_registry_names() -> list[str]:
    rows: list[str] = []
    for line in (PROJECT_ROOT / "memory/ACTIVE_PROJECTS.md").read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or "Oblast |" in line:
            continue
        rows.append(line.strip().strip("|").split("|", 1)[0].strip())
    return rows


class WorkstreamCatalogTests(unittest.TestCase):
    def test_every_workstream_has_one_primary_aggregate_row(self) -> None:
        registry_names = _all_registry_names()

        for record in WORKSTREAM_CATALOG:
            primary_name = (
                record.source_names[0]
                if record.source_names
                else record.name
            )
            with self.subTest(workstream_id=record.workstream_id):
                self.assertEqual(registry_names.count(primary_name), 1)

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
        misc_names = {
            record.name
            for record in WORKSTREAM_CATALOG
            if record.workstream_type == "Misc"
        }

        self.assertEqual(
            set(source_names) | misc_names,
            _active_project_names()
            | {
                "iPhone Shortcuts / Mobile Input Layer",
                "Vocabulary FR",
                "Vocabulary IT",
            },
        )
        self.assertEqual(
            Counter(source_names)["TTS / české audio nástroje"],
            2,
        )
        self.assertEqual(
            {
                source_name: count
                for source_name, count in Counter(source_names).items()
                if count > 1
            },
            {"TTS / české audio nástroje": 2},
        )
        self.assertEqual(
            misc_ids,
            {"misc-brainstorm", "misc-unclassified-development"},
        )
        self.assertEqual(len(WORKSTREAM_CATALOG), 31)

    def test_catalog_has_expected_type_distribution(self) -> None:
        self.assertEqual(
            Counter(record.workstream_type for record in WORKSTREAM_CATALOG),
            {"Project": 25, "Tool": 4, "Misc": 2},
        )
        self.assertEqual(
            Counter(record.mode for record in WORKSTREAM_CATALOG),
            {"active": 28, "paused": 3},
        )

    def test_to_be_to_have_is_an_active_project_with_legacy_name_aliases(self) -> None:
        project = next(
            record
            for record in WORKSTREAM_CATALOG
            if record.workstream_id == "project-to-be-to-have"
        )

        self.assertEqual(project.name, "ToBeToHave")
        self.assertEqual(project.workstream_type, "Project")
        self.assertEqual(project.mode, "active")
        self.assertEqual(project.priority, "2")
        self.assertEqual(project.source_names, ("ToBeToHave",))
        self.assertEqual(project.query_aliases, ("To Be Training", "ToBeTraining"))

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

    def test_query_aliases_are_unique_and_exclude_ambiguous_cockpit(self) -> None:
        by_id = {record.workstream_id: record for record in WORKSTREAM_CATALOG}
        aliases = [
            alias.casefold()
            for record in WORKSTREAM_CATALOG
            for alias in record.query_aliases
        ]

        self.assertEqual(
            by_id["project-r2-adam-janicka"].query_aliases,
            ("R2 Adam",),
        )
        self.assertEqual(
            by_id["project-family-calendar"].query_aliases,
            ("Kalendář",),
        )
        self.assertEqual(by_id["project-cockpit"].query_aliases, ())
        self.assertEqual(len(aliases), len(set(aliases)))

    def test_all_workstreams_allow_read_only_network_research(self) -> None:
        self.assertTrue(WORKSTREAM_CATALOG)
        self.assertTrue(
            all(
                record.capabilities.network_read_only_research
                for record in WORKSTREAM_CATALOG
            )
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
                network_read_only_research=True,
                private_archive_direct=True,
                private_archive_read=True,
                private_archive_single_edit=True,
                private_archive_confirmation_required=(
                    PRIVATE_ARCHIVE_CONFIRMATION_CATEGORIES
                ),
                private_archive_root="data/private/article_archive",
            ),
        )
        self.assertTrue(
            knihovna.capabilities.status_fields()["network_read_only_research"]
        )
        self.assertTrue(other_records)
        self.assertTrue(
            all(
                record.capabilities == CanonicalWorkstreamCapabilities()
                for record in other_records
                if record.workstream_id != "project-r2-adam-janicka"
            )
        )

    def test_r2_adam_declares_read_only_source_data(self) -> None:
        r2_adam = next(
            record
            for record in WORKSTREAM_CATALOG
            if record.workstream_id == "project-r2-adam-janicka"
        )

        self.assertTrue(r2_adam.capabilities.source_data_read_only)
        self.assertEqual(
            r2_adam.capabilities.owned_private_root,
            (
                "data/private/communication/workstreams/"
                "project-r2-adam-janicka/documents"
            ),
        )
        self.assertTrue(r2_adam.capabilities.status_fields()["owned_private_write"])
        self.assertTrue(r2_adam.capabilities.network_read_only_research)
        self.assertFalse(r2_adam.capabilities.private_archive_direct)
        self.assertFalse(r2_adam.capabilities.private_archive_single_edit)

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
            private_archive_root="data/private/example_archive",
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
        self.assertTrue(record.capabilities.status_fields()["private_archive_direct"])

    def test_invalid_private_archive_capability_fails_closed(self) -> None:
        invalid = CanonicalWorkstream(
            "project-invalid-private-archive",
            "Project",
            "Neplatný private archiv",
            "active",
            "2",
            ("Zdroj neplatného archivu",),
            capabilities=CanonicalWorkstreamCapabilities(
                private_archive_direct=True,
                private_archive_read=True,
                private_archive_single_edit=True,
                private_archive_confirmation_required=(
                    PRIVATE_ARCHIVE_CONFIRMATION_CATEGORIES
                ),
                private_archive_root="../private/article_archive",
            ),
        )

        with self.assertRaisesRegex(ValueError, "private archive root"):
            validate_workstream_catalog((invalid,))

    def test_owned_private_root_requires_read_only_sources_and_safe_path(self) -> None:
        for capabilities in (
            CanonicalWorkstreamCapabilities(
                owned_private_root="data/private/r2-documents",
            ),
            CanonicalWorkstreamCapabilities(
                source_data_read_only=True,
                owned_private_root="../private/r2-documents",
            ),
            CanonicalWorkstreamCapabilities(
                source_data_read_only=True,
                owned_private_root="data/private/../r2-documents",
            ),
        ):
            with self.subTest(capabilities=capabilities):
                record = CanonicalWorkstream(
                    "project-invalid-owned-private",
                    "Project",
                    "Neplatný vlastněný prostor",
                    "active",
                    "2",
                    ("Neplatný vlastněný prostor",),
                    capabilities=capabilities,
                )

                with self.assertRaises(ValueError):
                    validate_workstream_catalog((record,))

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

    def test_validation_rejects_duplicate_query_aliases(self) -> None:
        records = (
            CanonicalWorkstream(
                "project-first",
                "Project",
                "První projekt",
                "active",
                "1",
                ("Zdroj A",),
                query_aliases=("Krátký název",),
            ),
            CanonicalWorkstream(
                "project-second",
                "Project",
                "Druhý projekt",
                "active",
                "2",
                ("Zdroj B",),
                query_aliases=("krátký název",),
            ),
        )

        with self.assertRaisesRegex(ValueError, "aliasy dotazu"):
            validate_workstream_catalog(records)


if __name__ == "__main__":
    unittest.main()
