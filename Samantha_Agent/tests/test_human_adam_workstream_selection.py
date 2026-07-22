from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.communication.human_adam_workstream_catalog import CanonicalWorkstream
from app.communication.human_adam_workstream_backends import (
    CompatibilityWorkstreamAdapter,
    WorkstreamBackendRegistry,
)
from app.communication.human_adam_workstream_selection import GroupedWorkstreamSelection


class GroupedWorkstreamSelectionTests(unittest.TestCase):
    def selection(self) -> GroupedWorkstreamSelection:
        registry = WorkstreamBackendRegistry(
            compatibility_adapters=(
                CompatibilityWorkstreamAdapter(
                    "layer-human-adam-development",
                    "human_adam",
                    SimpleNamespace(work_profile_id="human_adam"),
                ),
                CompatibilityWorkstreamAdapter(
                    "project-knowledge-library",
                    "knihovna",
                    SimpleNamespace(work_profile_id="knihovna"),
                ),
            )
        )
        return GroupedWorkstreamSelection(
            backend_registry=registry,
        )

    @staticmethod
    def thread_status() -> dict[str, object]:
        return {
            "workstreams": [
                {
                    "id": "project-mmtx",
                    "available": True,
                    "initialized": False,
                },
                {
                    "id": "project-mobile-input",
                    "available": True,
                    "initialized": True,
                },
            ]
        }

    @staticmethod
    def memory_status() -> dict[str, object]:
        return {
            "workstreams": [
                {"id": "layer-human-adam-development", "memory_ready": True},
                {"id": "project-knowledge-library", "memory_ready": True},
            ]
        }

    def test_groups_all_active_catalog_rows_and_separates_paused(self) -> None:
        status = self.selection().status(
            active_workstream_id="layer-human-adam-development",
            thread_status=self.thread_status(),
            memory_status=self.memory_status(),
        )
        groups = {group["id"]: group for group in status["groups"]}

        self.assertTrue(status["ok"])
        self.assertEqual(status["workstream_count"], 30)
        self.assertEqual(status["active_count"], 27)
        self.assertEqual(status["paused_count"], 3)
        self.assertEqual(status["archived_count"], 0)
        self.assertEqual(groups["projects"]["count"], 21)
        self.assertEqual(groups["tools"]["count"], 4)
        self.assertEqual(groups["layers"]["count"], 0)
        self.assertEqual(groups["other"]["count"], 2)
        self.assertEqual(
            {row["id"] for row in status["paused"]},
            {"project-mobile-input", "project-vocabulary-fr", "project-vocabulary-it"},
        )

    def test_one_active_workstream_identity_selects_lazy_backend(self) -> None:
        status = self.selection().status(
            active_workstream_id="project-mmtx",
            thread_status=self.thread_status(),
            memory_status=self.memory_status(),
        )
        by_id = {row["id"]: row for row in status["workstreams"]}

        self.assertEqual(status["active"]["workstream_id"], "project-mmtx")
        self.assertEqual(status["active"]["backend"], "lazy_private_thread")
        self.assertTrue(by_id["project-mmtx"]["active"])
        self.assertFalse(by_id["layer-human-adam-development"]["active"])

    def test_rows_expose_only_redacted_readiness(self) -> None:
        status = self.selection().status(
            active_workstream_id="project-knowledge-library",
            thread_status=self.thread_status(),
            memory_status=self.memory_status(),
        )
        by_id = {row["id"]: row for row in status["workstreams"]}

        self.assertTrue(
            all("profile_id" not in row for row in status["workstreams"])
        )
        self.assertNotIn("profile_id", status["active"])
        self.assertEqual(
            by_id["project-knowledge-library"]["backend"],
            "compatibility_adapter",
        )
        self.assertTrue(by_id["project-knowledge-library"]["memory_ready"])
        self.assertFalse(by_id["project-mmtx"]["memory_ready"])
        self.assertFalse(by_id["project-mmtx"]["thread_initialized"])
        self.assertNotIn("thread_id", repr(status))
        self.assertNotIn("relative_path", repr(status))

    def test_archived_rows_are_counted_but_not_shown(self) -> None:
        archived = CanonicalWorkstream(
            "project-archived",
            "Project",
            "Archiv",
            "archived",
            "3",
            ("Archiv source",),
        )
        selection = GroupedWorkstreamSelection(
            backend_registry=WorkstreamBackendRegistry(catalog=(archived,))
        )

        status = selection.status(
            active_workstream_id="",
        )

        self.assertFalse(status["ok"])
        self.assertEqual(status["workstream_count"], 0)
        self.assertEqual(status["archived_count"], 1)

    def test_unknown_compatibility_binding_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "mimo katalog"):
            WorkstreamBackendRegistry(
                compatibility_adapters=(
                    CompatibilityWorkstreamAdapter(
                        "project-unknown",
                        "old-profile",
                        SimpleNamespace(work_profile_id="old-profile"),
                    ),
                )
            )


if __name__ == "__main__":
    unittest.main()
