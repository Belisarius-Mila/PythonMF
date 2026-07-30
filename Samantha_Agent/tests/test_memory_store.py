from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.memory_store import (
    MAX_MEMORY_SNIPPET_CHARS,
    _query_workstream_ids,
    format_memory_status,
    get_memory_index,
    load_full_memory_context,
    load_startup_memory_context,
    memory_snippets,
    query_terms,
    search_memory,
    search_memory_text,
)


class MemoryStoreTests(unittest.TestCase):
    def test_full_memory_context_loads_nested_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "MEMORY_INDEX.md").write_text("Index", encoding="utf-8")
            project_dir = memory_dir / "projects"
            project_dir.mkdir()
            (project_dir / "mmtx.md").write_text("MMTX detail", encoding="utf-8")

            context = load_full_memory_context(memory_dir=memory_dir)

        self.assertIn("# MEMORY_INDEX.md", context)
        self.assertIn("# projects/mmtx.md", context)
        self.assertIn("MMTX detail", context)

    def test_startup_memory_context_uses_only_core_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "samantha_core.md").write_text("Core", encoding="utf-8")
            (memory_dir / "ACTIVE_PROJECTS.md").write_text("Active", encoding="utf-8")
            (memory_dir / "MEMORY_INDEX.md").write_text("Index", encoding="utf-8")
            project_dir = memory_dir / "projects"
            project_dir.mkdir()
            (project_dir / "deep_context.md").write_text(
                "Deep project context",
                encoding="utf-8",
            )

            context = load_startup_memory_context(memory_dir=memory_dir)

        self.assertIn("Core", context)
        self.assertIn("Active", context)
        self.assertIn("Index", context)
        self.assertNotIn("Deep project context", context)

    def test_memory_snippets_split_structured_markdown_lines(self) -> None:
        snippets = memory_snippets(
            "| Oblast | Priorita | Stav |\n"
            "| --- | --- | --- |\n"
            "| Samantha Agent/RAG | 1 | Aktivni |\n"
            "| TTS | 3 | Ceka |\n\n"
            "- prvni bod\n"
            "- druhy bod\n\n"
            "Souvisly odstavec zustane pohromade."
        )

        self.assertIn("| Samantha Agent/RAG | 1 | Aktivni |", snippets)
        self.assertIn("- prvni bod", snippets)
        self.assertIn("Souvisly odstavec zustane pohromade.", snippets)
        self.assertNotIn("| --- | --- | --- |", snippets)

    def test_search_memory_scores_filename_and_snippet_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            project_dir = memory_dir / "projects"
            project_dir.mkdir()
            (project_dir / "email_readonly_oauth.md").write_text(
                "Bezpecny read-only workflow pro email.\n\n"
                "RIXO pojisteni je samostatny pripad.",
                encoding="utf-8",
            )

            matches = search_memory("email read-only", memory_dir=memory_dir)

        self.assertEqual(matches[0].path, "projects/email_readonly_oauth.md")
        self.assertEqual(matches[0].authority, "reference")
        self.assertGreaterEqual(matches[0].score, 2)
        self.assertIn("read-only workflow", matches[0].snippet)

    def test_query_terms_splits_underscores_in_paths(self) -> None:
        terms = query_terms("projects/email_readonly_oauth.md")

        self.assertIn("email", terms)
        self.assertIn("readonly", terms)
        self.assertIn("read", terms)
        self.assertIn("only", terms)
        self.assertIn("oauth", terms)

    def test_query_aliases_identify_only_unambiguous_short_names(self) -> None:
        self.assertEqual(
            _query_workstream_ids(query_terms("R2 Adam")),
            frozenset({"project-r2-adam-janicka"}),
        )
        self.assertEqual(
            _query_workstream_ids(query_terms("Kalendář")),
            frozenset({"project-family-calendar"}),
        )
        self.assertEqual(
            _query_workstream_ids(query_terms("Cockpit")),
            frozenset(),
        )

    def test_search_memory_prefers_filename_matches_over_generic_handoffs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            project_dir = memory_dir / "projects"
            handoffs_dir = memory_dir / "handoffs"
            project_dir.mkdir()
            handoffs_dir.mkdir()
            (project_dir / "rag_memory_store.md").write_text(
                "Startup kontext a search_memory pro Samanthu.",
                encoding="utf-8",
            )
            (handoffs_dir / "old_session.md").write_text(
                "RAG RAG RAG RAG RAG RAG obecna historicka poznamka.",
                encoding="utf-8",
            )

            matches = search_memory("rag memory", memory_dir=memory_dir)

        self.assertEqual(matches[0].path, "projects/rag_memory_store.md")

    def test_search_memory_deprioritizes_handoffs_unless_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            project_dir = memory_dir / "projects"
            handoffs_dir = memory_dir / "handoffs"
            project_dir.mkdir()
            handoffs_dir.mkdir()
            (project_dir / "email_readonly_oauth.md").write_text(
                "E-mail read-only OAuth integrace.",
                encoding="utf-8",
            )
            (handoffs_dir / "email_readonly_old_handoff.md").write_text(
                "Email readonly read only OAuth OAuth OAuth OAuth.",
                encoding="utf-8",
            )

            normal_matches = search_memory("email read-only oauth", memory_dir=memory_dir)
            handoff_matches = search_memory(
                "email read-only oauth handoff",
                memory_dir=memory_dir,
            )

        self.assertEqual(normal_matches[0].path, "projects/email_readonly_oauth.md")
        self.assertEqual(handoff_matches[0].path, "handoffs/email_readonly_old_handoff.md")

    def test_search_memory_returns_best_snippet_once_per_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "note.md").write_text(
                "Email obecne.\n\nEmail read-only workflow a UID.",
                encoding="utf-8",
            )

            matches = search_memory("email read-only", memory_dir=memory_dir)

        self.assertEqual(len(matches), 1)
        self.assertIn("read-only workflow", matches[0].snippet)

    def test_search_memory_text_compacts_long_snippets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            long_text = "RAG " + ("velmi dlouhy kontext " * 80)
            (memory_dir / "rag.md").write_text(long_text, encoding="utf-8")

            result = search_memory_text("rag", memory_dir=memory_dir)

        self.assertLessEqual(len(result), MAX_MEMORY_SNIPPET_CHARS + 40)
        self.assertIn("...", result)
        self.assertIn("[core]", result)

    def test_search_memory_text_includes_source_type_and_filters_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            project_dir = memory_dir / "projects"
            handoffs_dir = memory_dir / "handoffs"
            project_dir.mkdir()
            handoffs_dir.mkdir()
            (project_dir / "email_readonly_oauth.md").write_text(
                "Aktualni email read-only workflow.",
                encoding="utf-8",
            )
            (handoffs_dir / "email_readonly_old.md").write_text(
                "Historicky email read-only workflow.",
                encoding="utf-8",
            )

            all_results = search_memory_text("email read-only", memory_dir=memory_dir)
            handoff_results = search_memory_text(
                "email read-only",
                memory_dir=memory_dir,
                source_type="handoffs",
            )

        self.assertIn("[projects] projects/email_readonly_oauth.md", all_results)
        self.assertNotIn("[handoffs]", all_results.splitlines()[0])
        self.assertIn("[handoffs] handoffs/email_readonly_old.md", handoff_results)

    def test_search_memory_prefers_canonical_workstream_memory_over_aggregate_and_history(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            handoff_dir = memory_dir / "handoffs" / "workstreams"
            tvbcp_dir = memory_dir / "tvbcp" / "workstreams"
            historical_dir = memory_dir / "handoffs"
            handoff_dir.mkdir(parents=True)
            tvbcp_dir.mkdir(parents=True)
            (memory_dir / "ACTIVE_PROJECTS.md").write_text(
                "| Oblast | Priorita | Rezim | Stav |\n"
                "| --- | --- | --- | --- |\n"
                "| R2-Adam / Janička | 2 | active | R2 Adam Janička starý stav. |\n",
                encoding="utf-8",
            )
            (
                handoff_dir / "project-r2-adam-janicka.md"
            ).write_text(
                "R2 Adam Janička má současný potvrzený stav.",
                encoding="utf-8",
            )
            (
                tvbcp_dir / "project-r2-adam-janicka.md"
            ).write_text(
                "R2 Adam Janička má současné kanonické rozhodnutí.",
                encoding="utf-8",
            )
            (historical_dir / "r2_adam_janicka_old.md").write_text(
                "R2 Adam Janička historický stav a starý další krok.",
                encoding="utf-8",
            )

            matches = search_memory(
                "R2 Adam Janička handoff",
                memory_dir=memory_dir,
            )

        by_path = {match.path: match for match in matches}
        self.assertEqual(matches[0].authority, "canonical")
        self.assertEqual(matches[0].workstream_id, "project-r2-adam-janicka")
        self.assertEqual(
            by_path["ACTIVE_PROJECTS.md"].authority,
            "aggregate",
        )
        self.assertEqual(
            by_path["handoffs/r2_adam_janicka_old.md"].authority,
            "historical",
        )

    def test_search_memory_marks_aggregate_unverified_when_canonical_pair_is_missing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            handoffs_dir = memory_dir / "handoffs"
            tvbcp_dir = memory_dir / "tvbcp"
            handoffs_dir.mkdir()
            tvbcp_dir.mkdir()
            (memory_dir / "ACTIVE_PROJECTS.md").write_text(
                "| Oblast | Priorita | Rezim | Stav |\n"
                "| --- | --- | --- | --- |\n"
                "| Samantha Agent/RAG | 1 | active | Současný agregovaný stav. |\n",
                encoding="utf-8",
            )
            (handoffs_dir / "samantha_agent_rag_old.md").write_text(
                "Samantha Agent RAG historický stav.",
                encoding="utf-8",
            )
            (
                handoffs_dir / "human_adam_layer_workstream_start_2026_07_20.md"
            ).write_text(
                "Jiný kanonický proud zmiňuje Samantha Agent RAG.",
                encoding="utf-8",
            )
            (tvbcp_dir / "architektura_komunikace_samantha.txt").write_text(
                "Kanonický TVBCP jiného proudu.",
                encoding="utf-8",
            )

            matches = search_memory("Samantha Agent RAG", memory_dir=memory_dir)
            formatted = search_memory_text(
                "Samantha Agent RAG",
                memory_dir=memory_dir,
            )

        self.assertEqual(matches[0].path, "ACTIVE_PROJECTS.md")
        self.assertEqual(matches[0].authority, "aggregate_unverified")
        self.assertEqual(matches[0].workstream_id, "project-samantha-agent-rag")
        self.assertNotEqual(
            matches[0].workstream_id,
            "layer-human-adam-development",
        )
        self.assertIn("autorita aggregate_unverified", formatted)

    def test_search_memory_text_rejects_unknown_source_type(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "note.md").write_text("RAG kontext.", encoding="utf-8")

            result = search_memory_text(
                "rag",
                memory_dir=memory_dir,
                source_type="unknown",
            )

        self.assertIn("Neznamy typ zdroje", result)

    def test_search_memory_text_handles_short_and_missing_queries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "note.md").write_text("Jedna poznamka.", encoding="utf-8")

            short_result = search_memory_text("a", memory_dir=memory_dir)
            missing_result = search_memory_text("neexistujici", memory_dir=memory_dir)

        self.assertIn("prilis kratky", short_result)
        self.assertIn("nenasla relevantni", missing_result)

    def test_memory_index_is_reused_until_markdown_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            note_path = memory_dir / "note.md"
            note_path.write_text("Prvni poznamka.", encoding="utf-8")

            first_index = get_memory_index(memory_dir)
            second_index = get_memory_index(memory_dir)
            note_path.write_text("Prvni poznamka plus novy obsah.", encoding="utf-8")
            third_index = get_memory_index(memory_dir)

        self.assertIs(first_index, second_index)
        self.assertIsNot(second_index, third_index)
        self.assertGreater(third_index.markdown_chars, first_index.markdown_chars)

    def test_search_memory_uses_refreshed_index_after_markdown_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            note_path = memory_dir / "note.md"
            note_path.write_text("Stary obsah.", encoding="utf-8")

            before = search_memory_text("novy", memory_dir=memory_dir)
            note_path.write_text("Stary obsah.\n\nNovy projektovy kontext.", encoding="utf-8")
            after = search_memory_text("novy", memory_dir=memory_dir)

        self.assertIn("nenasla relevantni", before)
        self.assertIn("Novy projektovy kontext", after)

    def test_format_memory_status_reports_counts_priorities_and_reminders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "samantha_core.md").write_text("Core", encoding="utf-8")
            (memory_dir / "ACTIVE_PROJECTS.md").write_text(
                "| Oblast | Priorita | Stav | Memory soubor | Handoff | Dalsi krok |\n"
                "| --- | --- | --- | --- | --- | --- |\n"
                "| Samantha Agent/RAG | 1 | Aktivni | `samantha_core.md` | x | Live test |\n"
                "| TTS | 3 | Ceka | x | x | Pozdeji |\n",
                encoding="utf-8",
            )
            (memory_dir / "MEMORY_INDEX.md").write_text(
                "- `handoffs/test.md` - [PRIPOMENOUT] otestovat stav pameti\n",
                encoding="utf-8",
            )

            status = format_memory_status(
                memory_dir=memory_dir,
                reminder_formatter=lambda: "AKTIVNI PRIPOMINKY:\n- Test",
                email_activity_formatter=lambda: "EMAIL UDRZBA:\n- Test",
            )

        self.assertIn("Samantha Memory Status", status)
        self.assertIn("Markdown soubory: 3", status)
        self.assertIn("Startup kontext:", status)
        self.assertIn("Samantha Agent/RAG: Aktivni", status)
        self.assertIn("[PRIPOMENOUT] otestovat stav pameti", status)
        self.assertNotIn("TTS: Pozdeji", status)

    def test_format_memory_status_skips_archived_priority_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir)
            (memory_dir / "samantha_core.md").write_text("Core", encoding="utf-8")
            (memory_dir / "ACTIVE_PROJECTS.md").write_text(
                "| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| Dokumenty | 1 | active | Aktivni | `docs.md` | x | Test |\n"
                "| Stary projekt | 1 | archived | Hotovo | `old.md` | x | Archiv |\n",
                encoding="utf-8",
            )
            (memory_dir / "MEMORY_INDEX.md").write_text("", encoding="utf-8")

            status = format_memory_status(memory_dir=memory_dir)

        self.assertIn("Dokumenty: Aktivni", status)
        self.assertNotIn("Stary projekt", status)


if __name__ == "__main__":
    unittest.main()
