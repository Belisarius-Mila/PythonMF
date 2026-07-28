from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import cockpit as cockpit_module
from app.communication.janicka_r2_backend import JanickaR2Backend
from app.communication.janicka_r2_cockpit import (
    JANICKA_R2_DOCUMENTS_HTML,
    JanickaR2CockpitAdapter,
    janicka_r2_document_compile_action,
    janicka_r2_document_search_action,
)
from app.communication.janicka_r2_compiler import R2_DOCUMENT_INSPECTION_PREFIX
from app.communication.janicka_r2_documents import R2_DOCUMENTS_RELATIVE_ROOT
from app.documents.search_service import document_reference


class JanickaR2CockpitTests(unittest.TestCase):
    def make_adapter(
        self,
        temp_dir: str,
    ) -> tuple[JanickaR2CockpitAdapter, JanickaR2Backend, list[str]]:
        private_root = Path(temp_dir) / "canonical-private"
        private_root.mkdir()
        backend = JanickaR2Backend.bind(
            canonical_private_root=private_root,
            document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
        )
        inspected_ids: list[str] = []

        def search_documents(_query: str, _limit: int) -> dict[str, object]:
            return {
                "ok": True,
                "results": [
                    {
                        "source_type": "document",
                        "document_id": "doc-ui-test",
                        "document_ref": document_reference("doc-ui-test"),
                        "title": "Testovací list",
                        "document_type": "výpis",
                        "domain": "nemovitost",
                        "reading_status_label": "OK",
                        "snippet": (
                            "Kontakt test@example.com a "
                            "https://example.com/private."
                        ),
                        "stored_path": "private/source/test.pdf",
                    }
                ],
            }

        def inspect_document(document_id: str) -> str:
            inspected_ids.append(document_id)
            return (
                f"{R2_DOCUMENT_INSPECTION_PREFIX}\n"
                "Bezpečný syntetický výtah pro UI."
            )

        return (
            JanickaR2CockpitAdapter(
                backend=backend,
                document_search=search_documents,
                document_inspector=inspect_document,
            ),
            backend,
            inspected_ids,
        )

    def test_search_action_returns_redacted_choices_without_read_or_write(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            adapter, backend, inspected_ids = self.make_adapter(temp_dir)

            result = janicka_r2_document_search_action(
                {"query": "testovací list"},
                adapter=adapter,
            )
            serialized = str(result)

            self.assertTrue(result["ok"])
            self.assertEqual(result["count"], 1)
            self.assertIn("[e-mail redigovan]", serialized)
            self.assertIn("[URL redigovano]", serialized)
            self.assertNotIn("doc-ui-test", serialized)
            self.assertNotIn("private/source", serialized)
            self.assertEqual(inspected_ids, [])
            self.assertEqual(backend.document_store().list_documents(), ())

    def test_compile_action_requires_selection_and_never_replaces_output(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            adapter, backend, inspected_ids = self.make_adapter(temp_dir)
            search_result = janicka_r2_document_search_action(
                {"query": "testovací list"},
                adapter=adapter,
            )
            candidate = search_result["candidates"][0]

            rejected = janicka_r2_document_compile_action(
                {
                    "query": "testovací list",
                    "selection_ref": "docref-0000000000000000",
                    "name": "UI test.txt",
                },
                adapter=adapter,
            )

            self.assertFalse(rejected["ok"])
            self.assertEqual(inspected_ids, [])
            self.assertEqual(backend.document_store().list_documents(), ())

            created = janicka_r2_document_compile_action(
                {
                    "query": "testovací list",
                    "selection_ref": candidate["selection_ref"],
                    "name": "UI test.txt",
                },
                adapter=adapter,
            )
            serialized = str(created)

            self.assertTrue(created["ok"])
            self.assertEqual(created["status"], "created")
            self.assertEqual(created["document"]["name"], "UI test.txt")
            self.assertEqual(created["source_count"], 1)
            self.assertEqual(inspected_ids, ["doc-ui-test"])
            self.assertNotIn("doc-ui-test", serialized)
            self.assertNotIn("Bezpečný syntetický", serialized)

            repeated = janicka_r2_document_compile_action(
                {
                    "query": "testovací list",
                    "selection_ref": candidate["selection_ref"],
                    "name": "UI test.txt",
                },
                adapter=adapter,
            )

            self.assertFalse(repeated["ok"])
            self.assertEqual(inspected_ids, ["doc-ui-test"])
            self.assertIn(
                "Bezpečný syntetický výtah pro UI.",
                backend.document_store().read_text("UI test.txt"),
            )

    def test_standalone_page_has_two_step_ui_without_private_identifiers(self) -> None:
        self.assertIn('id="queryInput"', JANICKA_R2_DOCUMENTS_HTML)
        self.assertIn('id="results"', JANICKA_R2_DOCUMENTS_HTML)
        self.assertIn('id="nameInput"', JANICKA_R2_DOCUMENTS_HTML)
        self.assertIn('id="createBtn"', JANICKA_R2_DOCUMENTS_HTML)
        self.assertIn(
            "/api/janicka-r2/documents/search",
            JANICKA_R2_DOCUMENTS_HTML,
        )
        self.assertIn(
            "/api/janicka-r2/documents/compile",
            JANICKA_R2_DOCUMENTS_HTML,
        )
        self.assertIn("textContent", JANICKA_R2_DOCUMENTS_HTML)
        self.assertNotIn("innerHTML", JANICKA_R2_DOCUMENTS_HTML)
        self.assertNotIn("document_id", JANICKA_R2_DOCUMENTS_HTML)
        self.assertNotIn("stored_path", JANICKA_R2_DOCUMENTS_HTML)
        self.assertNotIn("/api/email", JANICKA_R2_DOCUMENTS_HTML)

    def test_cockpit_keeps_legacy_page_and_narrow_post_registry_cards(self) -> None:
        self.assertNotIn('id="janickaR2DocumentsBtn"', cockpit_module.COCKPIT_HTML)
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        self.assertIn(
            'if parsed.path == "/janicka-r2-documents/":',
            source,
        )

        cards = {
            item["path"]: item
            for item in cockpit_module.COCKPIT_POST_ACTIONS
            if item["path"].startswith("/api/janicka-r2/documents/")
        }

        self.assertEqual(
            set(cards),
            {
                "/api/janicka-r2/documents/search",
                "/api/janicka-r2/documents/compile",
            },
        )
        self.assertEqual(cards["/api/janicka-r2/documents/search"]["risk"], "read_only_via_post")
        self.assertEqual(cards["/api/janicka-r2/documents/search"]["confirmation"], "none_readonly")
        self.assertEqual(cards["/api/janicka-r2/documents/compile"]["risk"], "private_write")
        self.assertEqual(
            cards["/api/janicka-r2/documents/compile"]["confirmation"],
            "explicit_ui_selection_create_only",
        )


if __name__ == "__main__":
    unittest.main()
