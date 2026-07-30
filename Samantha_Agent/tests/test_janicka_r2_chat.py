from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import cockpit as cockpit_module
from app.communication.human_adam_service import HumanAdamService
from app.communication.janicka_r2_backend import JanickaR2Backend
from app.communication.janicka_r2_chat import (
    R2_ADAM_CHAT_HTML,
    R2_ADAM_DOCUMENT_READER_HTML,
    R2_CHAT_DEVELOPER_INSTRUCTIONS,
    R2_CHAT_PROFILE_ID,
    JanickaR2ChatAdapter,
    janicka_r2_chat_document_action,
    janicka_r2_chat_documents_action,
    janicka_r2_chat_send_action,
)
from app.communication.janicka_r2_documents import R2_DOCUMENTS_RELATIVE_ROOT


class _Workspace:
    def __init__(self, root: Path) -> None:
        self.canonical_private_root = root / "private"
        self.canonical_project_root = root
        self.project_root = root / "workspace"


class _Hub:
    def snapshot(self) -> dict[str, object]:
        return {
            "connected": True,
            "connection_state": "connected",
            "turn_busy": False,
            "active_turn": None,
            "messages": [],
            "thread_id": "private-thread-must-not-leak",
        }


class _Conversation:
    def __init__(self) -> None:
        self.hub = _Hub()
        self.sent: dict[str, object] = {}

    def status(self) -> dict[str, object]:
        return {
            "ok": True,
            "runtime": {"reachable": True, "socket_path": "/private/socket"},
            "workspace": {"path": "/private/workspace"},
            "profile": {"model": "private-model"},
            "session": {
                "connected": True,
                "connection_state": "connected",
                "turn_busy": False,
                "active_turn": None,
                "thread_id": "private-thread-must-not-leak",
                "messages": [
                    {
                        "client_message_id": "r2-adam-message-0001",
                        "user_text": "Syntetický dotaz",
                        "answer": "Syntetická odpověď",
                        "status": "completed",
                        "thread_id": "private-thread-must-not-leak",
                        "turn_id": "private-turn-must-not-leak",
                    }
                ],
            },
        }

    def connect(self) -> dict[str, object]:
        return self.status()

    def send(self, **kwargs: object) -> dict[str, object]:
        self.sent = dict(kwargs)
        return {
            "ok": True,
            "session": self.status()["session"],
        }


class JanickaR2ChatTests(unittest.TestCase):
    def _adapter(
        self,
        root: Path,
        *,
        service: object | None = None,
    ) -> JanickaR2ChatAdapter:
        private_root = root / "private"
        backend = JanickaR2Backend.bind(
            canonical_private_root=private_root,
            document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
        )
        return JanickaR2ChatAdapter(
            service=service or _Conversation(),
            backend=backend,
        )

    def test_document_list_is_metadata_only_and_reader_uses_opaque_ref(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            (root / "private").mkdir()
            adapter = self._adapter(root)
            store = adapter.backend.document_store()
            store.create_text(
                name="Syntetický přehled.txt",
                text="Pouze syntetický obsah čtečky.",
            )

            listing = janicka_r2_chat_documents_action(adapter=adapter)
            document = listing["documents"][0]
            opened = janicka_r2_chat_document_action(
                document["document_ref"],
                adapter=adapter,
            )

        self.assertTrue(listing["ok"])
        self.assertEqual(listing["count"], 1)
        self.assertEqual(document["name"], "Syntetický přehled.txt")
        self.assertRegex(str(document["document_ref"]), r"^r2doc-[0-9a-f]{32}$")
        self.assertNotIn("path", document)
        self.assertNotIn("text", document)
        self.assertTrue(opened["ok"])
        self.assertEqual(opened["text"], "Pouze syntetický obsah čtečky.")
        self.assertEqual(opened["document"], document)

    def test_document_reader_rejects_name_path_and_unknown_ref(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            (root / "private").mkdir()
            adapter = self._adapter(root)
            adapter.backend.document_store().create_text(
                name="Bezpečný dokument.txt",
                text="Syntetický text.",
            )

            raw_name = janicka_r2_chat_document_action(
                "Bezpečný dokument.txt",
                adapter=adapter,
            )
            unknown = janicka_r2_chat_document_action(
                "r2doc-00000000000000000000000000000000",
                adapter=adapter,
            )

        self.assertFalse(raw_name["ok"])
        self.assertFalse(unknown["ok"])
        self.assertNotIn("text", raw_name)
        self.assertNotIn("text", unknown)

    def test_document_reader_hides_legacy_compiler_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            (root / "private").mkdir()
            adapter = self._adapter(root)
            store = adapter.backend.document_store()
            store.create_text(
                name="Starší přehled.txt",
                text=(
                    "R2-Adam – kompilovaný dokument\n"
                    "Název: Starší přehled.txt\n"
                    "Vytvořeno: 2026-07-30T07:00:00+00:00\n"
                    "Zdroj: inspect_document_text\n"
                    "Document ID: doc-private\n\n"
                    "Inspekce dokumentu (read-only):\n"
                    "- Soubor: private.pdf\n"
                    "- Textova extrakce: pdftotext\n"
                    "- OCR potreba: ne\n\n"
                    "Kandidati na due date:\n"
                    "- 2018-05-25 | unknown_date | confidence=low | technický šum\n\n"
                    "Nahled textu:\n"
                    "Lidsky užitečný obsah. [extracted tables: pdfplumber-tables]\n"
                    "[page 1 table 1]\n\n"
                    "Bezpecnost: technická poznámka.\n"
                ),
            )
            listing = adapter.documents()
            opened = adapter.document(
                listing["documents"][0]["document_ref"]
            )

        self.assertEqual(opened["text"], "Lidsky užitečný obsah.")
        self.assertNotIn("Kandidati na due date", opened["text"])
        self.assertNotIn("Document ID", opened["text"])
        self.assertNotIn("pdfplumber", opened["text"])

    def test_bind_owns_separate_session_and_only_document_write_root(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            workspace = _Workspace(root)
            base = HumanAdamService(
                runtime=object(),
                workspace=workspace,
                state_path=root / "human-adam-session.json",
                profile_getter=lambda **_kwargs: {},
            )

            adapter = JanickaR2ChatAdapter.bind(
                base_service=base,
                state_path=root / "r2-session.json",
            )

            self.assertEqual(adapter.service.work_profile_id, R2_CHAT_PROFILE_ID)
            self.assertEqual(adapter.service.state_path, root / "r2-session.json")
            self.assertNotEqual(adapter.service.state_path, base.state_path)
            self.assertEqual(
                adapter.service.sandbox_policy["writableRoots"],
                [str(workspace.canonical_private_root / R2_DOCUMENTS_RELATIVE_ROOT)],
            )
            self.assertFalse(adapter.service.sandbox_policy["networkAccess"])
            self.assertIn("Nejsi vyvojovy Adam", R2_CHAT_DEVELOPER_INSTRUCTIONS)
            self.assertIn(
                "Do chatu nevkladej jeho plny obsah",
                R2_CHAT_DEVELOPER_INSTRUCTIONS,
            )
            self.assertIn(
                "nikdy nevyvijej",
                adapter.service.developer_instructions,
            )
            self.assertIn(
                "prepare_selected_sources",
                adapter.service.developer_instructions,
            )
            self.assertIn(
                "compile_selected_overview",
                adapter.service.developer_instructions,
            )
            self.assertIn(
                "dvou az peti",
                adapter.service.developer_instructions,
            )
            self.assertIn(
                "search_complete_document_set",
                adapter.service.developer_instructions,
            )
            self.assertIn(
                "compile_complete_title_list",
                adapter.service.developer_instructions,
            )
            self.assertIn(
                "prepare_complete_source_batch",
                adapter.service.developer_instructions,
            )
            self.assertIn(
                "compile_complete_overview",
                adapter.service.developer_instructions,
            )
            self.assertIn(
                "nezjisteno",
                adapter.service.developer_instructions,
            )

    def test_public_status_keeps_chat_but_hides_runtime_and_thread_details(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            adapter = self._adapter(Path(temp_dir))

            payload = adapter.status()

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["runtime"], {"reachable": True})
        self.assertNotIn("workspace", payload)
        self.assertNotIn("profile", payload)
        self.assertNotIn("thread_id", payload["session"])
        self.assertNotIn("thread_id", payload["session"]["messages"][0])
        self.assertNotIn("turn_id", payload["session"]["messages"][0])
        self.assertEqual(
            payload["session"]["messages"][0]["answer"],
            "Syntetická odpověď",
        )

    def test_send_is_non_development_and_carries_fixed_r2_boundary(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            conversation = _Conversation()
            adapter = self._adapter(Path(temp_dir), service=conversation)

            result = janicka_r2_chat_send_action(
                {
                    "message": "Připrav syntetický přehled.",
                    "client_message_id": "r2-adam-message-0002",
                    "client_sent_at": "2026-07-28T15:30:00+02:00",
                },
                adapter=adapter,
            )

        self.assertTrue(result["ok"])
        self.assertFalse(conversation.sent["write_intent"])
        control = str(conversation.sent["development_control_block"])
        self.assertIn("source=janicka_r2_chat_policy", control)
        self.assertIn("workspace_writable=false", control)
        self.assertIn("r2_document_access=manage_owned_txt_documents", control)
        self.assertIn("Never change project files", control)
        self.assertNotIn("thread_id", result["session"])

    def test_page_is_plain_chat_without_human_adam_work_controls(self) -> None:
        self.assertIn("<h1>R2-Adam</h1>", R2_ADAM_CHAT_HTML)
        self.assertIn('id="chat"', R2_ADAM_CHAT_HTML)
        self.assertIn('id="messageInput"', R2_ADAM_CHAT_HTML)
        self.assertIn('id="sendBtn"', R2_ADAM_CHAT_HTML)
        self.assertIn("/api/r2-adam/status", R2_ADAM_CHAT_HTML)
        self.assertIn("/api/r2-adam/connect", R2_ADAM_CHAT_HTML)
        self.assertIn("/api/r2-adam/send", R2_ADAM_CHAT_HTML)
        self.assertIn("/api/r2-adam/documents", R2_ADAM_CHAT_HTML)
        self.assertIn('id="documentShelf"', R2_ADAM_CHAT_HTML)
        self.assertIn('id="currentDocumentOpenBtn"', R2_ADAM_CHAT_HTML)
        self.assertIn("textContent", R2_ADAM_CHAT_HTML)
        self.assertNotIn("innerHTML", R2_ADAM_CHAT_HTML)
        for forbidden in (
            "TVBCP",
            "Pracovní proud",
            "Zahájit vývoj",
            "threadRotationOpenBtn",
            "workOpenBtn",
            "profileSelect",
        ):
            self.assertNotIn(forbidden, R2_ADAM_CHAT_HTML)

    def test_full_page_reader_loads_text_outside_chat_without_private_path(self) -> None:
        self.assertIn('id="documentText"', R2_ADAM_DOCUMENT_READER_HTML)
        self.assertIn("/api/r2-adam/document?ref=", R2_ADAM_DOCUMENT_READER_HTML)
        self.assertIn('href="/r2-adam/"', R2_ADAM_DOCUMENT_READER_HTML)
        self.assertIn("documentText.textContent", R2_ADAM_DOCUMENT_READER_HTML)
        self.assertNotIn("innerHTML", R2_ADAM_DOCUMENT_READER_HTML)
        self.assertNotIn("stored_path", R2_ADAM_DOCUMENT_READER_HTML)
        self.assertNotIn("document_id", R2_ADAM_DOCUMENT_READER_HTML)

    def test_cockpit_opens_r2_chat_and_exposes_only_chat_post_actions(self) -> None:
        self.assertIn('id="janickaR2ChatBtn"', cockpit_module.COCKPIT_HTML)
        self.assertNotIn('id="janickaR2DocumentsBtn"', cockpit_module.COCKPIT_HTML)
        self.assertIn("/r2-adam/", cockpit_module.COCKPIT_HTML)
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        self.assertIn('if parsed.path == "/r2-adam/":', source)
        self.assertIn('if parsed.path == "/r2-adam/document/":', source)
        self.assertIn('if parsed.path == "/api/r2-adam/status":', source)
        self.assertIn('if parsed.path == "/api/r2-adam/documents":', source)
        self.assertIn('if parsed.path == "/api/r2-adam/document":', source)

        cards = {
            item["path"]: item
            for item in cockpit_module.COCKPIT_POST_ACTIONS
            if item["path"].startswith("/api/r2-adam/")
        }
        self.assertEqual(
            set(cards),
            {
                "/api/r2-adam/connect",
                "/api/r2-adam/send",
            },
        )
        self.assertEqual(cards["/api/r2-adam/connect"]["risk"], "local_service")
        self.assertEqual(cards["/api/r2-adam/send"]["risk"], "private_write")
        self.assertNotIn("/api/r2-adam/development", cards)
        self.assertNotIn("/api/r2-adam/tvbcp", cards)


if __name__ == "__main__":
    unittest.main()
