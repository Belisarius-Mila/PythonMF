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
            "workOpenBtn",
            "workPanel",
            "workCloseBtn",
            "workRefreshBtn",
            "workChanges",
            "checkpointMessage",
            "checkpointBtn",
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
        self.assertIn("/api/human-adam/workspace", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/checkpoint", HUMAN_ADAM_HTML)
        self.assertIn("Checkpoint bez pushnutí", HUMAN_ADAM_HTML)
        self.assertIn("window.confirm", HUMAN_ADAM_HTML)

    def test_ui_is_manual_refresh_only_and_uses_safe_dom_text(self) -> None:
        self.assertNotIn("setInterval", HUMAN_ADAM_HTML)
        self.assertNotIn("innerHTML", HUMAN_ADAM_HTML)
        self.assertIn("textContent", HUMAN_ADAM_HTML)
        self.assertIn("replaceChildren", HUMAN_ADAM_HTML)

    def test_header_places_connect_left_and_cockpit_right(self) -> None:
        connect = HUMAN_ADAM_HTML.index('id="connectBtn"')
        title = HUMAN_ADAM_HTML.index("<h1>Human–Adam</h1>")
        tools = HUMAN_ADAM_HTML.index('class="head-tools"', title)
        cockpit = HUMAN_ADAM_HTML.index('<a class="back" href="/">← Cockpit</a>')
        self.assertLess(connect, title)
        self.assertLess(title, tools)
        self.assertLess(tools, cockpit)
        self.assertIn("grid-template-columns:auto minmax(0,1fr) auto", HUMAN_ADAM_HTML)
        self.assertIn(".head-tools { grid-column:1/-1; grid-row:2; justify-content:center; }", HUMAN_ADAM_HTML)

    def test_ui_does_not_depend_on_legacy_delivery_paths(self) -> None:
        lowered = HUMAN_ADAM_HTML.lower()
        self.assertNotIn("watcher", lowered)
        self.assertNotIn("voicebridge", lowered)
        self.assertNotIn("tty", lowered)
        self.assertNotIn("terminal tab", lowered)


if __name__ == "__main__":
    unittest.main()
