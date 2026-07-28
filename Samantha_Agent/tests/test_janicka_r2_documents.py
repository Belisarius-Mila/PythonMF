from __future__ import annotations

import json
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.capabilities.models import AuditPolicy, RiskLevel
from app.capabilities.registry import CAPABILITIES
from app.communication.janicka_r2_backend import JanickaR2Backend
from app.communication.janicka_r2_compiler import (
    MAX_R2_SOURCE_TEXT_BYTES,
    R2_DOCUMENT_INSPECTION_CAPABILITY,
    R2_DOCUMENT_INSPECTION_PREFIX,
    JanickaR2CompilationError,
)
from app.communication.janicka_r2_document_selection import (
    R2_DOCUMENT_SEARCH_CAPABILITY,
    JanickaR2DocumentSelectionError,
)
from app.communication.janicka_r2_documents import (
    MAX_R2_DOCUMENT_TEXT_BYTES,
    R2_DOCUMENTS_RELATIVE_ROOT,
    JanickaR2DocumentConfirmationError,
    JanickaR2DocumentError,
    JanickaR2DocumentExistsError,
    JanickaR2DocumentNotFoundError,
    JanickaR2DocumentStore,
    normalize_r2_document_name,
    r2_document_trash_confirmation,
)
from app.documents.search_service import document_reference


class JanickaR2DocumentStoreTests(unittest.TestCase):
    def make_store(
        self,
        temp_dir: str,
    ) -> tuple[JanickaR2DocumentStore, Path]:
        private_root = Path(temp_dir) / "canonical-private"
        private_root.mkdir(mode=0o700)
        store = JanickaR2DocumentStore(canonical_private_root=private_root)
        return store, private_root

    def test_create_read_list_and_replace_text_document(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            store, private_root = self.make_store(temp_dir)

            created = store.create_text(
                name="Rodinný přehled.txt",
                text="První verze.\n",
            )
            listed = store.list_documents()
            replaced = store.replace_text(
                name="Rodinný přehled.txt",
                text="Druhá verze.\n",
            )

            document_path = (
                private_root / R2_DOCUMENTS_RELATIVE_ROOT / "Rodinný přehled.txt"
            )
            self.assertEqual(created.name, "Rodinný přehled.txt")
            self.assertEqual([item.name for item in listed], ["Rodinný přehled.txt"])
            self.assertEqual(replaced.name, "Rodinný přehled.txt")
            self.assertEqual(store.read_text("Rodinný přehled.txt"), "Druhá verze.\n")
            self.assertEqual(stat.S_IMODE(document_path.stat().st_mode), 0o600)
            self.assertNotIn(str(private_root), str(created.as_dict()))

    def test_create_refuses_to_replace_existing_document(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            store, _private_root = self.make_store(temp_dir)
            store.create_text(name="Poznámky.txt", text="Původní text")

            with self.assertRaises(JanickaR2DocumentExistsError):
                store.create_text(name="Poznámky.txt", text="Nový text")

            self.assertEqual(store.read_text("Poznámky.txt"), "Původní text")

    def test_replace_requires_existing_regular_document(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            store, _private_root = self.make_store(temp_dir)

            with self.assertRaises(JanickaR2DocumentNotFoundError):
                store.replace_text(name="Chybí.txt", text="Nový text")

            self.assertEqual(store.list_documents(), ())

    def test_names_are_flat_normalized_txt_only(self) -> None:
        valid = normalize_r2_document_name("  Žlutý plán 1.txt  ")
        self.assertEqual(valid, "Žlutý plán 1.txt")

        for invalid in (
            "../únik.txt",
            "vnořený/únik.txt",
            r"vnořený\únik.txt",
            "/absolutní.txt",
            ".env.txt",
            "bez-pripony",
            "jiný.pdf",
            "tajný:plán.txt",
            "řídicí\nznak.txt",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(JanickaR2DocumentError):
                    normalize_r2_document_name(invalid)

    def test_invalid_names_cannot_write_outside_owned_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            store, private_root = self.make_store(temp_dir)
            outside = private_root / "outside.txt"

            with self.assertRaises(JanickaR2DocumentError):
                store.create_text(name="../../../outside.txt", text="únik")

            self.assertFalse(outside.exists())
            self.assertFalse((Path(temp_dir) / "outside.txt").exists())

    def test_document_symlink_is_never_read_replaced_or_trashed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            store, private_root = self.make_store(temp_dir)
            document_root = private_root / R2_DOCUMENTS_RELATIVE_ROOT
            document_root.mkdir(parents=True)
            outside = Path(temp_dir) / "outside.txt"
            outside.write_text("mimo hranici", encoding="utf-8")
            linked = document_root / "Odkaz.txt"
            linked.symlink_to(outside)

            with self.assertRaises(JanickaR2DocumentNotFoundError):
                store.read_text("Odkaz.txt")
            with self.assertRaises(JanickaR2DocumentNotFoundError):
                store.replace_text(name="Odkaz.txt", text="změna")
            with self.assertRaises(JanickaR2DocumentNotFoundError):
                store.move_to_trash(
                    name="Odkaz.txt",
                    confirmation=r2_document_trash_confirmation("Odkaz.txt"),
                )

            self.assertEqual(outside.read_text(encoding="utf-8"), "mimo hranici")

    def test_symlinked_private_subtree_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            store, private_root = self.make_store(temp_dir)
            outside = Path(temp_dir) / "outside"
            outside.mkdir()
            communication = private_root / "communication"
            communication.symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(
                JanickaR2DocumentError,
                "není bezpečný",
            ):
                store.create_text(name="Plán.txt", text="text")
            with self.assertRaisesRegex(
                JanickaR2DocumentError,
                "není bezpečný",
            ):
                store.list_documents()

            self.assertEqual(list(outside.iterdir()), [])

    def test_trash_requires_exact_confirmation_and_preserves_document(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            store, private_root = self.make_store(temp_dir)
            store.create_text(name="Ke kontrole.txt", text="zachovatelný text")

            with self.assertRaises(JanickaR2DocumentConfirmationError):
                store.move_to_trash(
                    name="Ke kontrole.txt",
                    confirmation="ano",
                )

            self.assertEqual(store.read_text("Ke kontrole.txt"), "zachovatelný text")

            result = store.move_to_trash(
                name="Ke kontrole.txt",
                confirmation=r2_document_trash_confirmation("Ke kontrole.txt"),
            )

            trash_path = (
                private_root
                / R2_DOCUMENTS_RELATIVE_ROOT
                / "trash"
                / result.trash_id
            )
            self.assertEqual(result.original_name, "Ke kontrole.txt")
            self.assertTrue(trash_path.is_file())
            self.assertEqual(
                trash_path.read_text(encoding="utf-8"),
                "zachovatelný text",
            )
            self.assertEqual(store.list_documents(), ())
            with self.assertRaises(JanickaR2DocumentNotFoundError):
                store.read_text("Ke kontrole.txt")

    def test_text_limit_and_null_byte_are_rejected_before_directory_creation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            store, private_root = self.make_store(temp_dir)

            with self.assertRaises(JanickaR2DocumentError):
                store.create_text(name="Nulový.txt", text="a\x00b")
            with self.assertRaises(JanickaR2DocumentError):
                store.create_text(
                    name="Velký.txt",
                    text="x" * (MAX_R2_DOCUMENT_TEXT_BYTES + 1),
                )

            self.assertFalse(
                (private_root / R2_DOCUMENTS_RELATIVE_ROOT).exists()
            )

    def test_exact_ten_mib_text_limit_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            store, _private_root = self.make_store(temp_dir)
            content = "x" * MAX_R2_DOCUMENT_TEXT_BYTES

            created = store.create_text(name="Deset MiB.txt", text=content)

            self.assertEqual(created.size_bytes, 10 * 1024 * 1024)
            self.assertEqual(len(store.read_text("Deset MiB.txt")), 10 * 1024 * 1024)

    def test_store_requires_existing_absolute_non_symlink_private_root(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            base = Path(temp_dir)
            missing = base / "missing"
            real_root = base / "real"
            real_root.mkdir()
            linked_root = base / "linked"
            linked_root.symlink_to(real_root, target_is_directory=True)

            with self.assertRaises(JanickaR2DocumentError):
                JanickaR2DocumentStore(canonical_private_root=Path("relative"))
            with self.assertRaises(JanickaR2DocumentError):
                JanickaR2DocumentStore(canonical_private_root=missing)
            with self.assertRaises(JanickaR2DocumentError):
                JanickaR2DocumentStore(canonical_private_root=linked_root)

    def test_backend_binding_rejects_any_root_other_than_r2_documents(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()

            with self.assertRaisesRegex(ValueError, "mimo"):
                JanickaR2Backend.bind(
                    canonical_private_root=private_root,
                    document_root=private_root / "documents",
                )

    def test_compiler_creates_new_txt_from_one_registered_read_only_source(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            document_root = private_root / R2_DOCUMENTS_RELATIVE_ROOT
            backend = JanickaR2Backend.bind(
                canonical_private_root=private_root,
                document_root=document_root,
            )
            inspected_ids: list[str] = []

            def inspect_document(document_id: str) -> str:
                inspected_ids.append(document_id)
                return (
                    f"{R2_DOCUMENT_INSPECTION_PREFIX}\n"
                    "- Soubor: synteticky.pdf\n\n"
                    "Nahled textu:\nBezpečný syntetický výtah."
                )

            result = backend.document_compiler(
                document_inspector=inspect_document,
            ).compile_document_inspection(
                name="Kompilovaný přehled.txt",
                document_id="doc-zaruka",
                now=datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc),
            )
            stored = backend.document_store().read_text(
                "Kompilovaný přehled.txt"
            )

        self.assertEqual(inspected_ids, ["doc-zaruka"])
        self.assertEqual(result.document.name, "Kompilovaný přehled.txt")
        self.assertEqual(result.source_type, R2_DOCUMENT_INSPECTION_CAPABILITY)
        self.assertEqual(result.source_count, 1)
        self.assertEqual(result.compiled_at, "2026-07-28T12:00:00+00:00")
        self.assertIn("R2-Adam – kompilovaný dokument", stored)
        self.assertIn("Zdroj: inspect_document_text", stored)
        self.assertIn("Document ID: doc-zaruka", stored)
        self.assertIn("Bezpečný syntetický výtah.", stored)
        self.assertNotIn("doc-zaruka", str(result.as_dict()))
        self.assertNotIn(str(private_root), str(result.as_dict()))

    def test_compiler_refuses_existing_output_before_reading_source(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            backend = JanickaR2Backend.bind(
                canonical_private_root=private_root,
                document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
            )
            backend.document_store().create_text(
                name="Existující.txt",
                text="Původní obsah.",
            )
            source_called = False

            def inspect_document(_document_id: str) -> str:
                nonlocal source_called
                source_called = True
                return R2_DOCUMENT_INSPECTION_PREFIX

            with self.assertRaises(JanickaR2DocumentExistsError):
                backend.document_compiler(
                    document_inspector=inspect_document,
                ).compile_document_inspection(
                    name="Existující.txt",
                    document_id="doc-test",
                )

            self.assertFalse(source_called)
            self.assertEqual(
                backend.document_store().read_text("Existující.txt"),
                "Původní obsah.",
            )

    def test_search_returns_redacted_human_choices_without_reading_or_writing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            backend = JanickaR2Backend.bind(
                canonical_private_root=private_root,
                document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
            )
            inspected_ids: list[str] = []

            def search_documents(_query: str, max_results: int) -> dict[str, object]:
                self.assertEqual(max_results, 5)
                return {
                    "ok": True,
                    "results": [
                        {
                            "source_type": "document",
                            "document_id": "doc-katastr",
                            "document_ref": document_reference("doc-katastr"),
                            "title": "Katastrální dokument",
                            "document_type": "výpis",
                            "domain": "nemovitost",
                            "reading_status_label": "OK",
                            "snippet": (
                                "Kontakt test@example.com a odkaz "
                                "https://example.com/private."
                            ),
                            "stored_path": "soukroma/cesta/dokument.pdf",
                        },
                        {
                            "source_type": "purchase",
                            "document_id": "purchase-hidden",
                            "document_ref": "purref-0123456789abcdef",
                            "title": "Nákup",
                        },
                    ],
                }

            flow = backend.document_selection_flow(
                document_search=search_documents,
                document_inspector=lambda document_id: (
                    inspected_ids.append(document_id)
                    or R2_DOCUMENT_INSPECTION_PREFIX
                ),
            )
            result = flow.search_documents("katastrální dokument")
            serialized = str(result.as_dict())

            self.assertEqual(result.count, 1)
            self.assertEqual(
                result.candidates[0].selection_ref,
                document_reference("doc-katastr"),
            )
            self.assertIn("[e-mail redigovan]", serialized)
            self.assertIn("[URL redigovano]", serialized)
            self.assertNotIn("doc-katastr", serialized)
            self.assertNotIn("soukroma/cesta", serialized)
            self.assertEqual(inspected_ids, [])
            self.assertEqual(backend.document_store().list_documents(), ())

    def test_compile_requires_current_human_selection_before_one_inspection(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            backend = JanickaR2Backend.bind(
                canonical_private_root=private_root,
                document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
            )
            inspected_ids: list[str] = []
            payload = {
                "ok": True,
                "results": [
                    {
                        "source_type": "document",
                        "document_id": "doc-vybrany",
                        "document_ref": document_reference("doc-vybrany"),
                        "title": "Vybraný dokument",
                        "document_type": "document",
                        "domain": "home",
                        "reading_status_label": "OK",
                        "snippet": "Bezpečný náhled.",
                    }
                ],
            }
            flow = backend.document_selection_flow(
                document_search=lambda _query, _limit: payload,
                document_inspector=lambda document_id: (
                    inspected_ids.append(document_id)
                    or f"{R2_DOCUMENT_INSPECTION_PREFIX}\nBezpečný výtah."
                ),
            )
            search_result = flow.search_documents("vybraný dokument")

            with self.assertRaises(JanickaR2DocumentSelectionError):
                flow.compile_selected_document(
                    name="Odmítnutý výběr.txt",
                    query="vybraný dokument",
                    selection_ref="docref-0000000000000000",
                )

            self.assertEqual(inspected_ids, [])
            self.assertEqual(backend.document_store().list_documents(), ())

            result = flow.compile_selected_document(
                name="Lidsky vybraný.txt",
                query="vybraný dokument",
                selection_ref=search_result.candidates[0].selection_ref,
                now=datetime(2026, 7, 28, 15, 0, tzinfo=timezone.utc),
            )

            self.assertEqual(inspected_ids, ["doc-vybrany"])
            self.assertEqual(result.document.name, "Lidsky vybraný.txt")
            self.assertEqual(
                backend.document_store().list_documents(),
                (result.document,),
            )

    def test_compile_rejects_selection_that_disappeared_before_write(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            private_root = Path(temp_dir) / "canonical-private"
            private_root.mkdir()
            backend = JanickaR2Backend.bind(
                canonical_private_root=private_root,
                document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
            )
            inspected_ids: list[str] = []
            responses: list[dict[str, object]] = [
                {
                    "ok": True,
                    "results": [
                        {
                            "source_type": "document",
                            "document_id": "doc-docasny",
                            "document_ref": document_reference("doc-docasny"),
                            "title": "Dočasný dokument",
                            "document_type": "document",
                            "domain": "home",
                            "reading_status_label": "OK",
                            "snippet": "Bezpečný náhled.",
                        }
                    ],
                },
                {"ok": True, "results": []},
            ]
            flow = backend.document_selection_flow(
                document_search=lambda _query, _limit: responses.pop(0),
                document_inspector=lambda document_id: (
                    inspected_ids.append(document_id)
                    or R2_DOCUMENT_INSPECTION_PREFIX
                ),
            )
            search_result = flow.search_documents("dočasný dokument")

            with self.assertRaises(JanickaR2DocumentSelectionError):
                flow.compile_selected_document(
                    name="Zmizelý.txt",
                    query="dočasný dokument",
                    selection_ref=search_result.candidates[0].selection_ref,
                )

            self.assertEqual(inspected_ids, [])
            self.assertEqual(backend.document_store().list_documents(), ())

    def test_default_selection_flow_binds_search_and_inspection_to_backend_vault(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            project_root = Path(temp_dir) / "canonical-project"
            private_root = project_root / "data" / "private"
            vault = private_root / "documents"
            stored = vault / "vault" / "home" / "doc-bound" / "bound.txt"
            stored.parent.mkdir(parents=True)
            stored.write_text("Svazany synteticky dokument.", encoding="utf-8")
            index = vault / "index"
            index.mkdir()
            metadata = {
                "document_id": "doc-bound",
                "title": "Svázaný dokument",
                "original_filename": "bound.txt",
                "stored_path": (
                    "data/private/documents/vault/home/doc-bound/bound.txt"
                ),
                "domain": "home",
                "document_type": "document",
                "reading_status": "ok",
            }
            (index / "documents_index.jsonl").write_text(
                json.dumps(metadata, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            (index / "text_index.jsonl").write_text(
                json.dumps(
                    {
                        "document_id": "doc-bound",
                        "text": "Svazany synteticky dokument.",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            backend = JanickaR2Backend.bind(
                canonical_private_root=private_root,
                document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
            )
            flow = backend.document_selection_flow()

            search_result = flow.search_documents("svazany synteticky")
            result = flow.compile_selected_document(
                name="Svázaný výstup.txt",
                query="svazany synteticky",
                selection_ref=search_result.candidates[0].selection_ref,
            )

            self.assertEqual(search_result.count, 1)
            self.assertEqual(result.document.name, "Svázaný výstup.txt")
            self.assertIn(
                "Svazany synteticky dokument.",
                backend.document_store().read_text("Svázaný výstup.txt"),
            )

    def test_compiler_rejects_unsafe_id_and_unverified_source_output(self) -> None:
        invalid_cases = (
            ("../doc-test", R2_DOCUMENT_INSPECTION_PREFIX),
            ("doc-test", "Document ID nebyl nalezen."),
            ("doc-test", f"{R2_DOCUMENT_INSPECTION_PREFIX}\x00"),
            (
                "doc-test",
                R2_DOCUMENT_INSPECTION_PREFIX
                + ("x" * (MAX_R2_SOURCE_TEXT_BYTES + 1)),
            ),
        )
        for document_id, source_text in invalid_cases:
            with self.subTest(document_id=document_id, source_size=len(source_text)):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    private_root = Path(temp_dir) / "canonical-private"
                    private_root.mkdir()
                    backend = JanickaR2Backend.bind(
                        canonical_private_root=private_root,
                        document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
                    )

                    with self.assertRaises(JanickaR2CompilationError):
                        backend.document_compiler(
                            document_inspector=lambda _document_id: source_text,
                        ).compile_document_inspection(
                            name="Odmítnutý.txt",
                            document_id=document_id,
                        )

                    self.assertEqual(backend.document_store().list_documents(), ())

    def test_first_compiler_source_is_registered_read_only_and_redacted(self) -> None:
        inspect_capability = next(
            item
            for item in CAPABILITIES
            if item.capability_id == R2_DOCUMENT_INSPECTION_CAPABILITY
        )
        search_capability = next(
            item
            for item in CAPABILITIES
            if item.capability_id == R2_DOCUMENT_SEARCH_CAPABILITY
        )

        for capability in (search_capability, inspect_capability):
            with self.subTest(capability=capability.capability_id):
                self.assertEqual(capability.risk, RiskLevel.READ_ONLY)
                self.assertEqual(capability.writes, ())
                self.assertFalse(capability.requires_confirmation)
                self.assertEqual(capability.audit, AuditPolicy.REDACTED)
                self.assertEqual(capability.tool, capability.capability_id)


if __name__ == "__main__":
    unittest.main()
