from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.codex_appserver import AppServerError
from app.communication.human_adam_workstream_catalog import CanonicalWorkstream
from app.communication.human_adam_workstream_memory import (
    WorkstreamMemoryRegistry,
    canonical_memory_path,
)


class WorkstreamMemoryRegistryTests(unittest.TestCase):
    def test_every_catalog_stream_has_one_unique_canonical_pair(self) -> None:
        registry = WorkstreamMemoryRegistry()
        bindings = registry.bindings()
        paths = [
            path
            for binding in bindings
            for path in (binding.handoff_relative_path, binding.tvbcp_relative_path)
        ]

        self.assertEqual(len(bindings), 29)
        self.assertEqual(len(paths), 58)
        self.assertEqual(len(set(paths)), 58)
        self.assertTrue(
            all(path.startswith("memory/handoffs/") for path in paths[0::2])
        )
        self.assertTrue(all(path.startswith("memory/tvbcp/") for path in paths[1::2]))

    def test_human_adam_and_knihovna_preserve_confirmed_legacy_documents(self) -> None:
        registry = WorkstreamMemoryRegistry()
        human_adam = registry.binding("layer-human-adam-development")
        knihovna = registry.binding("project-knowledge-library")

        self.assertTrue(human_adam.legacy_document)
        self.assertEqual(
            human_adam.handoff_relative_path,
            "memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md",
        )
        self.assertEqual(
            human_adam.tvbcp_relative_path,
            "memory/tvbcp/architektura_komunikace_samantha.txt",
        )
        self.assertTrue(knihovna.legacy_document)
        self.assertEqual(
            knihovna.handoff_relative_path,
            "memory/handoffs/knowledge_library_article_editing_2026_07_16.md",
        )
        self.assertEqual(knihovna.tvbcp_relative_path, "memory/tvbcp/knihovna_cockpit.txt")

    def test_new_streams_use_stable_nested_paths_without_creating_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry = WorkstreamMemoryRegistry()
            mmtx = registry.binding("project-mmtx")

            status = registry.status(project_root=root)

        self.assertEqual(
            mmtx.handoff_relative_path,
            "memory/handoffs/workstreams/project-mmtx.md",
        )
        self.assertEqual(
            mmtx.tvbcp_relative_path,
            "memory/tvbcp/workstreams/project-mmtx.md",
        )
        self.assertEqual(status["ready_count"], 0)
        self.assertEqual(status["workstream_count"], 29)
        self.assertFalse((root / "memory").exists())

    def test_initial_templates_are_bounded_git_safe_skeletons(self) -> None:
        registry = WorkstreamMemoryRegistry()
        binding = registry.binding("project-mmtx")
        handoff = registry.initial_handoff(binding)
        tvbcp = registry.initial_tvbcp(binding)

        self.assertIn("Pracovni proud: project-mmtx", handoff)
        self.assertIn("Bezpecnost / neukladat", handoff)
        self.assertIn("# TVBCP: MMTX", tvbcp)
        self.assertIn("Chronologicke zaznamy", tvbcp)
        self.assertNotIn("thread_id", handoff + tvbcp)

    def test_unknown_stream_and_unsafe_or_duplicate_paths_fail_closed(self) -> None:
        registry = WorkstreamMemoryRegistry()
        with self.assertRaisesRegex(AppServerError, "kanonickou paměťovou vazbu"):
            registry.binding("project-unknown")
        with self.assertRaisesRegex(ValueError, "platnou cestu"):
            canonical_memory_path("../outside.md", kind="handoff")

        records = (
            CanonicalWorkstream(
                "project-one",
                "Project",
                "One",
                "active",
                "1",
                ("Source one",),
            ),
            CanonicalWorkstream(
                "project-two",
                "Project",
                "Two",
                "active",
                "2",
                ("Source two",),
            ),
        )
        shared = (
            "memory/handoffs/shared.md",
            "memory/tvbcp/shared.md",
        )
        with self.assertRaisesRegex(ValueError, "sdílet"):
            WorkstreamMemoryRegistry(
                catalog=records,
                legacy_paths={"project-one": shared, "project-two": shared},
            )


if __name__ == "__main__":
    unittest.main()
