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
            "tvbcpScroll",
            "tvbcpContent",
            "tvbcpEnd",
            "workOpenBtn",
            "workPanel",
            "workCloseBtn",
            "workRefreshBtn",
            "workChanges",
            "checkpointMessage",
            "checkpointBtn",
            "deployMeta",
            "deployAuditBtn",
            "deployConfirmation",
            "deployBtn",
            "deploymentReceipt",
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
        self.assertIn("/api/human-adam/deploy-audit", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/deploy", HUMAN_ADAM_HTML)
        self.assertIn("Checkpoint bez pushnutí", HUMAN_ADAM_HTML)
        self.assertIn("Audit nasazení", HUMAN_ADAM_HTML)
        self.assertIn("Ověřit a nasadit", HUMAN_ADAM_HTML)
        self.assertIn('id="deployConfirmation"', HUMAN_ADAM_HTML)
        self.assertIn('autocomplete="off"', HUMAN_ADAM_HTML)
        self.assertIn('autocorrect="off"', HUMAN_ADAM_HTML)
        self.assertIn("window.confirm", HUMAN_ADAM_HTML)
        self.assertIn("checkpointMessage.blur();", HUMAN_ADAM_HTML)
        self.assertIn("const checkpointTitle = checkpointMessage.value.trim();", HUMAN_ADAM_HTML)
        self.assertIn("Zadej krátký název WIP checkpointu.", HUMAN_ADAM_HTML)
        self.assertIn("message:checkpointTitle", HUMAN_ADAM_HTML)
        self.assertLess(
            HUMAN_ADAM_HTML.index("const checkpointTitle = checkpointMessage.value.trim();"),
            HUMAN_ADAM_HTML.index("window.confirm", HUMAN_ADAM_HTML.index("async function createCheckpoint()")),
        )
        self.assertIn("checkpoint_token:deploymentAudit.checkpoint_token", HUMAN_ADAM_HTML)
        self.assertIn("confirmation.trim() !== required", HUMAN_ADAM_HTML)
        self.assertIn("const confirmation = deployConfirmation.value.trim();", HUMAN_ADAM_HTML)
        self.assertIn('deployConfirmation.addEventListener("input"', HUMAN_ADAM_HTML)
        self.assertNotIn("window.prompt", HUMAN_ADAM_HTML)
        failure = HUMAN_ADAM_HTML.index("const deploymentFailure =")
        refresh = HUMAN_ADAM_HTML.index("await loadWork();", failure)
        restore = HUMAN_ADAM_HTML.index("deployMeta.textContent = deploymentFailure;", refresh)
        self.assertLess(refresh, restore)
        self.assertIn("await waitForCockpitAndReload(Number(payload.restart.pid || previousPid));", HUMAN_ADAM_HTML)

    def test_ui_renders_persistent_safe_deployment_confirmation(self) -> None:
        self.assertIn("payload.deployment_confirmation", HUMAN_ADAM_HTML)
        self.assertIn("confirmation.gate_passed === true", HUMAN_ADAM_HTML)
        self.assertIn("/^[0-9a-f]{7}$/.test(shortCommit)", HUMAN_ADAM_HTML)
        self.assertIn(
            "`Nasazeno ${shortCommit} · plná brána prošla · ${completedTime}`",
            HUMAN_ADAM_HTML,
        )
        self.assertIn("deploymentReceipt.hidden = !showConfirmation;", HUMAN_ADAM_HTML)

    def test_ui_is_manual_refresh_only_and_uses_safe_dom_text(self) -> None:
        self.assertNotIn("setInterval", HUMAN_ADAM_HTML)
        self.assertNotIn("innerHTML", HUMAN_ADAM_HTML)
        self.assertIn("textContent", HUMAN_ADAM_HTML)
        self.assertIn("replaceChildren", HUMAN_ADAM_HTML)
        self.assertIn("#tvbcpScroll { flex:1; min-height:0; overflow:auto;", HUMAN_ADAM_HTML)
        self.assertIn('data-scroll-mode="end-anchor-v3"', HUMAN_ADAM_HTML)
        self.assertIn("function scrollTvbcpToEnd()", HUMAN_ADAM_HTML)
        self.assertGreaterEqual(HUMAN_ADAM_HTML.count("requestAnimationFrame"), 2)
        self.assertIn("tvbcpScroll.scrollTop = tvbcpScroll.scrollHeight;", HUMAN_ADAM_HTML)
        self.assertIn('tvbcpEnd.scrollIntoView({block:"end",inline:"nearest",behavior:"auto"});', HUMAN_ADAM_HTML)
        self.assertIn("window.setTimeout(applyEndPosition, 120);", HUMAN_ADAM_HTML)
        self.assertIn("scrollTvbcpToEnd();", HUMAN_ADAM_HTML)
        self.assertNotIn("scrollTop = 0;", HUMAN_ADAM_HTML)

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

    def test_submit_clears_input_before_api_and_blocks_safari_restore(self) -> None:
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]
        capture = send_source.index("const text = input.value.trim();")
        clear = send_source.index("clearMessageInput();")
        api_call = send_source.index('await api("/api/human-adam/send"')

        self.assertLess(capture, clear)
        self.assertLess(clear, api_call)
        self.assertIn("renderSession(optimistic);", send_source)
        self.assertNotIn("input.value = text", send_source)
        self.assertNotIn('input.value = ""', send_source)
        self.assertIn('function clearMessageInput() {\n    input.value = "";\n    input.defaultValue = "";', HUMAN_ADAM_HTML)
        self.assertIn('<form class="composer" id="composer" autocomplete="off">', HUMAN_ADAM_HTML)
        self.assertIn('id="messageInput" maxlength="12000" autocomplete="off"', HUMAN_ADAM_HTML)
        self.assertIn('window.addEventListener("pageshow", clearMessageInput);', HUMAN_ADAM_HTML)

    def test_ui_does_not_depend_on_legacy_delivery_paths(self) -> None:
        lowered = HUMAN_ADAM_HTML.lower()
        self.assertNotIn("watcher", lowered)
        self.assertNotIn("voicebridge", lowered)
        self.assertNotIn("tty", lowered)
        self.assertNotIn("terminal tab", lowered)


if __name__ == "__main__":
    unittest.main()
