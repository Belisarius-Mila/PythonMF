from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app import cockpit as cockpit_module
from app.communication.human_adam_service import HumanAdamService
from app.communication.janicka_r2_backend import JanickaR2Backend
from app.communication.janicka_r2_chat import (
    R2_ADAM_CHAT_HTML,
    R2_CHAT_DEVELOPER_INSTRUCTIONS,
    R2_CHAT_PROFILE_ID,
    JanickaR2ChatAdapter,
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
                "nikdy nevyvijej",
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

    def test_cockpit_opens_r2_chat_and_exposes_only_chat_post_actions(self) -> None:
        self.assertIn('id="janickaR2ChatBtn"', cockpit_module.COCKPIT_HTML)
        self.assertNotIn('id="janickaR2DocumentsBtn"', cockpit_module.COCKPIT_HTML)
        self.assertIn("/r2-adam/", cockpit_module.COCKPIT_HTML)
        source = Path(cockpit_module.__file__).read_text(encoding="utf-8")
        self.assertIn('if parsed.path == "/r2-adam/":', source)
        self.assertIn('if parsed.path == "/api/r2-adam/status":', source)

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
