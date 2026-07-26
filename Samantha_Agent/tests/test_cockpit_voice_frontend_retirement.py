from __future__ import annotations

import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def cockpit_html() -> str:
    source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "COCKPIT_HTML" for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("COCKPIT_HTML nebyl nalezen.")


class CockpitVoiceFrontendRetirementTests(unittest.TestCase):
    def test_legacy_voice_section_and_exclusive_javascript_are_absent(self) -> None:
        html = cockpit_html()
        legacy_markers = (
            '<summary>Hlas</summary>',
            '<span class="dashboard-label">Hlas</span>',
            'id="voiceCommandDetails"',
            'id="voiceRecordBtn"',
            'id="voiceTranscript"',
            'id="voiceModeStartBtn"',
            'id="voiceBridgeSwitcher"',
            "renderVoiceStatus",
            "renderVoiceLastResponse",
            "refreshVoiceLatestResponse",
            "startVoiceReplyPolling",
            "startVoiceRecording",
            "submitVoiceTranscript",
            "recordVoiceFrontendEvent",
            "/api/speech/transcribe",
            "/api/speech/voice-text",
            "/api/voice-mode/start",
            "/api/voice-mode/stop",
            "/api/voice-mode/approval",
            "/api/voice-mode/latest-response",
            "/api/voice-bridge/marker",
            "/api/voice-bridge/terminate-stale",
            "/api/voice-bridge/frontend-event",
        )

        for marker in legacy_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, html)

    def test_generic_speech_codex_approval_and_tvbcp_access_remain(self) -> None:
        html = cockpit_html()

        self.assertIn('id="dashboardSpeakBtn"', html)
        self.assertIn('id="dashboardSpeakSelectionBtn"', html)
        self.assertIn("async function speakText(", html)
        self.assertIn("/api/speech/speak", html)
        self.assertIn("/api/speech/edge-tts", html)
        self.assertIn('id="codexApprovalCard"', html)
        self.assertIn("renderCodexApproval(data.codex_approval || {});", html)
        self.assertIn('id="tvbcpOpenBtn"', html)
        self.assertIn("openTvbcpModal", html)

    def test_human_adam_microphone_and_legacy_backend_routes_remain(self) -> None:
        cockpit_source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")
        human_adam_source = (
            PROJECT_ROOT / "app" / "communication" / "human_adam_ui.py"
        ).read_text(encoding="utf-8")

        self.assertIn('id="voiceRecordBtn"', human_adam_source)
        self.assertIn("navigator.mediaDevices.getUserMedia", human_adam_source)
        self.assertIn("/api/human-adam/transcribe", human_adam_source)
        for route in (
            "/api/speech/transcribe",
            "/api/speech/voice-text",
            "/api/voice-mode/start",
            "/api/voice-mode/stop",
            "/api/voice-mode/approval",
            "/api/voice-mode/latest-response",
            "/api/voice-bridge/marker",
            "/api/voice-bridge/terminate-stale",
            "/api/voice-bridge/frontend-event",
        ):
            with self.subTest(route=route):
                self.assertIn(route, cockpit_source)


if __name__ == "__main__":
    unittest.main()
