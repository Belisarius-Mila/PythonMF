from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.communication.human_adam_workstream_catalog import CanonicalWorkstream
from app.communication.human_adam_workstream_memory import WorkstreamMemoryRegistry
from app.memory_truth_audit import (
    GitFileEvidence,
    STATUS_CANDIDATE_DRIFT,
    STATUS_PROVEN_CONTRADICTION,
    STATUS_REGISTRY_CONSISTENT,
    STATUS_UNMATERIALIZED,
    STATUS_UNVERIFIABLE,
    format_memory_truth_audit,
    memory_truth_audit_json,
    parse_active_project_registry,
    run_memory_truth_audit,
)


ACTIVE_SAMPLE = """# Project Registry

| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- |
| Alpha source | 1 | active | Contains `data/private/secret`. | x | y | z |
| Drift source | 2 | active | Old text. | x | y | z |
| Conflict source | 3 | active | Old text. | x | y | z |
| Lazy source | 2 | active | Current text. | x | y | z |
"""


CATALOG = (
    CanonicalWorkstream(
        "project-alpha",
        "Project",
        "Alpha",
        "active",
        "1",
        ("Alpha source",),
    ),
    CanonicalWorkstream(
        "project-drift",
        "Project",
        "Drift",
        "active",
        "2",
        ("Drift source",),
    ),
    CanonicalWorkstream(
        "project-conflict",
        "Project",
        "Conflict",
        "paused",
        "2",
        ("Conflict source",),
    ),
    CanonicalWorkstream(
        "project-lazy",
        "Project",
        "Lazy",
        "active",
        "2",
        ("Lazy source",),
    ),
    CanonicalWorkstream(
        "misc-unverified",
        "Misc",
        "Unverified",
        "active",
        "2",
        (),
    ),
)


class MemoryTruthAuditTests(unittest.TestCase):
    def test_registry_parser_keeps_only_coordinates_and_line_number(self) -> None:
        rows = parse_active_project_registry(ACTIVE_SAMPLE)

        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0].name, "Alpha source")
        self.assertEqual(rows[0].priority, "1")
        self.assertEqual(rows[0].mode, "active")
        self.assertGreater(rows[0].line_number, 1)
        self.assertFalse(hasattr(rows[0], "status"))

    def test_audit_classifies_only_machine_verifiable_evidence_without_writes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory = root / "memory"
            memory.mkdir()
            (memory / "ACTIVE_PROJECTS.md").write_text(
                ACTIVE_SAMPLE,
                encoding="utf-8",
            )
            registry = WorkstreamMemoryRegistry(catalog=CATALOG, legacy_paths={})
            for stream_id in ("project-alpha", "project-drift", "misc-unverified"):
                binding = registry.binding(stream_id)
                for relative_path in (
                    binding.handoff_relative_path,
                    binding.tvbcp_relative_path,
                ):
                    path = root / relative_path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("git-safe fixture\n", encoding="utf-8")

            aggregate_time = "2026-07-20T10:00:00+02:00"
            evidence = {
                "memory/ACTIVE_PROJECTS.md": GitFileEvidence(aggregate_time, "a" * 40),
            }
            for binding in registry.bindings():
                for relative_path in (
                    binding.handoff_relative_path,
                    binding.tvbcp_relative_path,
                ):
                    if (root / relative_path).is_file():
                        timestamp = (
                            "2026-07-21T10:00:00+02:00"
                            if binding.workstream_id == "project-drift"
                            else "2026-07-19T10:00:00+02:00"
                        )
                        evidence[relative_path] = GitFileEvidence(timestamp, "b" * 40)

            before = tuple(sorted(path.relative_to(root) for path in root.rglob("*")))
            result = run_memory_truth_audit(
                project_root=root,
                catalog=CATALOG,
                registry=registry,
                evidence_loader=lambda path: evidence.get(path, GitFileEvidence()),
                generated_at="2026-07-29T20:00:00+02:00",
            )
            after = tuple(sorted(path.relative_to(root) for path in root.rglob("*")))

        rows = {row.workstream_id: row for row in result.rows}
        self.assertEqual(before, after)
        self.assertEqual(result.workstream_count, 5)
        self.assertEqual(result.memory_ready_count, 3)
        self.assertEqual(result.proven_contradiction_count, 1)
        self.assertEqual(result.candidate_drift_count, 1)
        self.assertEqual(rows["project-alpha"].status, STATUS_REGISTRY_CONSISTENT)
        self.assertEqual(rows["project-drift"].status, STATUS_CANDIDATE_DRIFT)
        self.assertEqual(rows["project-conflict"].status, STATUS_PROVEN_CONTRADICTION)
        self.assertEqual(rows["project-lazy"].status, STATUS_UNMATERIALIZED)
        self.assertEqual(rows["misc-unverified"].status, STATUS_UNVERIFIABLE)
        self.assertEqual(
            rows["project-conflict"].contradictions,
            (
                "priority_mismatch:Conflict source:expected=2:actual=3",
                "mode_mismatch:Conflict source:expected=paused:actual=active",
            ),
        )

    def test_text_and_json_outputs_are_git_safe_and_explain_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            memory = root / "memory"
            memory.mkdir()
            (memory / "ACTIVE_PROJECTS.md").write_text(
                ACTIVE_SAMPLE,
                encoding="utf-8",
            )
            registry = WorkstreamMemoryRegistry(catalog=CATALOG, legacy_paths={})
            result = run_memory_truth_audit(
                project_root=root,
                catalog=CATALOG,
                registry=registry,
                evidence_loader=lambda path: GitFileEvidence(),
                generated_at="2026-07-29T20:00:00+02:00",
            )

        text = format_memory_truth_audit(result)
        payload = memory_truth_audit_json(result)
        self.assertIn("READ-ONLY AUDIT PRAVDIVOSTI PAMETI", text)
        self.assertIn("nic nevytvoril", text.casefold())
        self.assertIn("mode_mismatch", text)
        self.assertIn('"workstream_count": 5', payload)
        self.assertNotIn("data/private/secret", text + payload)


if __name__ == "__main__":
    unittest.main()
