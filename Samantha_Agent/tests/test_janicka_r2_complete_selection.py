from __future__ import annotations

import tempfile
import unittest
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from app.communication.janicka_r2_backend import JanickaR2Backend
from app.communication.janicka_r2_compiler import (
    R2_DOCUMENT_INSPECTION_PREFIX,
    R2_DOCUMENT_SEARCH_CAPABILITY,
)
from app.communication.janicka_r2_document_selection import (
    MAX_R2_COMPLETE_SOURCES,
    JanickaR2DocumentSelectionError,
)
from app.communication.janicka_r2_documents import R2_DOCUMENTS_RELATIVE_ROOT
from app.documents.search_service import document_reference


def _document_row(number: int, *, title: str | None = None) -> dict[str, object]:
    document_id = f"doc-recept-{number:03d}"
    return {
        "source_type": "document",
        "document_id": document_id,
        "document_ref": document_reference(document_id),
        "title": title or f"Recept {number:03d}",
        "document_type": "recipe",
        "domain": "knihovna",
        "reading_status_label": "OK",
        "snippet": f"Syntetický náhled receptu {number:03d}.",
    }


class _PagedSearch:
    def __init__(
        self,
        rows: list[dict[str, object]],
        *,
        forced_page_size: int = 4,
    ) -> None:
        self.rows = rows
        self.forced_page_size = forced_page_size
        self.calls: list[tuple[str, int, int]] = []

    def __call__(
        self,
        query: str,
        offset: int,
        page_size: int,
    ) -> Mapping[str, object]:
        self.calls.append((query, offset, page_size))
        size = min(page_size, self.forced_page_size)
        page = self.rows[offset : offset + size]
        next_offset = offset + len(page)
        has_more = next_offset < len(self.rows)
        return {
            "ok": True,
            "count": len(page),
            "total_count": len(self.rows),
            "offset": offset,
            "has_more": has_more,
            "next_offset": next_offset if has_more else None,
            "results": page,
        }


class JanickaR2CompleteSelectionTests(unittest.TestCase):
    def _flow(
        self,
        private_root: Path,
        *,
        rows: list[dict[str, object]],
        inspector,
        forced_page_size: int = 4,
    ):
        backend = JanickaR2Backend.bind(
            canonical_private_root=private_root,
            document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
        )
        paged_search = _PagedSearch(
            rows,
            forced_page_size=forced_page_size,
        )
        flow = backend.document_selection_flow(
            document_search=lambda _query, _limit: {
                "ok": True,
                "results": [],
            },
            document_page_search=paged_search,
            document_inspector=inspector,
        )
        return backend, flow, paged_search

    def test_complete_search_collects_all_pages_as_title_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            backend, flow, paged_search = self._flow(
                private_root,
                rows=[_document_row(number) for number in range(1, 13)],
                inspector=lambda _document_id: R2_DOCUMENT_INSPECTION_PREFIX,
            )

            result = flow.search_complete_document_set("všechny recepty")
            public = result.as_dict()

            self.assertEqual(result.count, 12)
            self.assertRegex(result.result_set_ref, r"^r2results-[0-9a-f]{32}$")
            self.assertEqual([call[1] for call in paged_search.calls], [0, 4, 8])
            self.assertEqual(
                [item["title"] for item in public["candidates"]],
                [f"Recept {number:03d}" for number in range(1, 13)],
            )
            self.assertNotIn("snippet", str(public))
            self.assertNotIn("Syntetický náhled", repr(result))
            self.assertEqual(backend.document_store().list_documents(), ())

    def test_complete_title_list_reads_metadata_only_and_contains_every_title(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            inspected_ids: list[str] = []
            backend, flow, _paged_search = self._flow(
                private_root,
                rows=[_document_row(number) for number in range(1, 13)],
                inspector=lambda document_id: (
                    inspected_ids.append(document_id)
                    or R2_DOCUMENT_INSPECTION_PREFIX
                ),
            )
            search_result = flow.search_complete_document_set("všechny recepty")

            compiled = flow.compile_complete_title_list(
                name="Soupis receptů.txt",
                query="všechny recepty",
                result_set_ref=search_result.result_set_ref,
                now=datetime(2026, 7, 28, 19, 0, tzinfo=timezone.utc),
            )
            stored = backend.document_store().read_text("Soupis receptů.txt")

        self.assertEqual(inspected_ids, [])
        self.assertEqual(compiled.source_type, R2_DOCUMENT_SEARCH_CAPABILITY)
        self.assertEqual(compiled.source_count, 12)
        self.assertIn("Počet potvrzených zdrojů: 12", stored)
        for number in range(1, 13):
            self.assertIn(f"{number}. Recept {number:03d}", stored)
            self.assertNotIn(f"doc-recept-{number:03d}", stored)

    def test_complete_six_source_overview_requires_five_plus_one_batches(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            inspected_ids: list[str] = []

            def inspect_document(document_id: str) -> str:
                inspected_ids.append(document_id)
                return (
                    f"{R2_DOCUMENT_INSPECTION_PREFIX}\n"
                    f"Syntetický obsah {document_id}."
                )

            backend, flow, _paged_search = self._flow(
                private_root,
                rows=[_document_row(number) for number in range(1, 7)],
                inspector=inspect_document,
            )
            search_result = flow.search_complete_document_set("všechny recepty")
            first = flow.prepare_complete_source_batch(
                query="všechny recepty",
                result_set_ref=search_result.result_set_ref,
                batch_number=1,
            )
            second = flow.prepare_complete_source_batch(
                query="všechny recepty",
                result_set_ref=search_result.result_set_ref,
                batch_number=2,
            )

            compiled = flow.compile_complete_overview(
                name="Přehled receptů.txt",
                query="všechny recepty",
                result_set_ref=search_result.result_set_ref,
                batch_refs=[first.batch_ref, second.batch_ref],
                overview_text="Souhrn šesti syntetických receptů.",
            )
            stored = backend.document_store().read_text("Přehled receptů.txt")

        self.assertEqual(first.batch_count, 2)
        self.assertEqual(len(first.sources), 5)
        self.assertEqual(len(second.sources), 1)
        self.assertNotIn("Syntetický obsah", repr(first))
        self.assertEqual(compiled.source_count, 6)
        self.assertEqual(len(inspected_ids), 12)
        self.assertIn("Počet potvrzených zdrojů: 6", stored)
        self.assertIn("Souhrn šesti syntetických receptů.", stored)
        self.assertNotIn("doc-recept-", stored)

    def test_changed_complete_result_set_requires_new_human_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            rows = [_document_row(number) for number in range(1, 7)]
            backend, flow, paged_search = self._flow(
                private_root,
                rows=rows,
                inspector=lambda _document_id: R2_DOCUMENT_INSPECTION_PREFIX,
            )
            search_result = flow.search_complete_document_set("všechny recepty")
            paged_search.rows = [
                *rows[:-1],
                _document_row(6, title="Změněný recept"),
            ]

            with self.assertRaisesRegex(
                JanickaR2DocumentSelectionError,
                "Výsledková sada se změnila",
            ):
                flow.compile_complete_title_list(
                    name="Neaktuální soupis.txt",
                    query="všechny recepty",
                    result_set_ref=search_result.result_set_ref,
                )

            self.assertEqual(backend.document_store().list_documents(), ())

    def test_changed_fulltext_batch_blocks_complete_overview(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            inspection_counts: dict[str, int] = {}

            def inspect_document(document_id: str) -> str:
                count = inspection_counts.get(document_id, 0) + 1
                inspection_counts[document_id] = count
                version = "původní" if count == 1 else "změněná"
                return (
                    f"{R2_DOCUMENT_INSPECTION_PREFIX}\n"
                    f"{version} verze {document_id}."
                )

            backend, flow, _paged_search = self._flow(
                private_root,
                rows=[_document_row(number) for number in range(1, 7)],
                inspector=inspect_document,
            )
            search_result = flow.search_complete_document_set("všechny recepty")
            batches = [
                flow.prepare_complete_source_batch(
                    query="všechny recepty",
                    result_set_ref=search_result.result_set_ref,
                    batch_number=batch_number,
                )
                for batch_number in (1, 2)
            ]

            with self.assertRaisesRegex(
                JanickaR2DocumentSelectionError,
                "zdroj se změnil",
            ):
                flow.compile_complete_overview(
                    name="Neaktuální přehled.txt",
                    query="všechny recepty",
                    result_set_ref=search_result.result_set_ref,
                    batch_refs=[batch.batch_ref for batch in batches],
                    overview_text="Souhrn ze starých podkladů.",
                )

            self.assertEqual(backend.document_store().list_documents(), ())

    def test_overly_broad_complete_search_fails_instead_of_truncating(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            backend, flow, _paged_search = self._flow(
                private_root,
                rows=[
                    _document_row(number)
                    for number in range(1, MAX_R2_COMPLETE_SOURCES + 2)
                ],
                inspector=lambda _document_id: R2_DOCUMENT_INSPECTION_PREFIX,
            )

            with self.assertRaisesRegex(
                JanickaR2DocumentSelectionError,
                f"více než {MAX_R2_COMPLETE_SOURCES}",
            ):
                flow.search_complete_document_set("příliš široký dotaz")

            self.assertEqual(backend.document_store().list_documents(), ())


if __name__ == "__main__":
    unittest.main()
