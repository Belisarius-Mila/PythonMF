from __future__ import annotations

import unittest

from app.communication.human_adam_ui import HUMAN_ADAM_HTML


class HumanAdamUiTests(unittest.TestCase):
    def test_ui_exposes_explicit_connection_send_time_and_delivery_evidence(self) -> None:
        for element_id in (
            "connectBtn",
            "refreshBtn",
            "connectionBadge",
            "threadBadge",
            "workspaceBadge",
            "chat",
            "messageInput",
            "sendBtn",
            "tvbcpOpenBtn",
            "tvbcpPanel",
            "tvbcpCloseBtn",
            "tvbcpRefreshBtn",
            "tvbcpContent",
        ):
            self.assertIn(f'id="{element_id}"', HUMAN_ADAM_HTML)
        self.assertIn("Odesláno", HUMAN_ADAM_HTML)
        self.assertIn("Adam pracuje…", HUMAN_ADAM_HTML)
        self.assertIn("Doručení potvrzeno", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/status", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/connect", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/send", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/tvbcp", HUMAN_ADAM_HTML)
        self.assertIn("TVBCP se načte až po otevření.", HUMAN_ADAM_HTML)
        self.assertIn("Workspace: ${workspace.change_count} změn", HUMAN_ADAM_HTML)

    def test_ui_is_manual_refresh_only_and_uses_safe_dom_text(self) -> None:
        self.assertNotIn("setInterval", HUMAN_ADAM_HTML)
        self.assertNotIn("innerHTML", HUMAN_ADAM_HTML)
        self.assertIn("textContent", HUMAN_ADAM_HTML)
        self.assertIn("replaceChildren", HUMAN_ADAM_HTML)

    def test_ui_does_not_depend_on_legacy_delivery_paths(self) -> None:
        lowered = HUMAN_ADAM_HTML.lower()
        self.assertNotIn("watcher", lowered)
        self.assertNotIn("voicebridge", lowered)
        self.assertNotIn("tty", lowered)
        self.assertNotIn("terminal tab", lowered)


if __name__ == "__main__":
    unittest.main()
