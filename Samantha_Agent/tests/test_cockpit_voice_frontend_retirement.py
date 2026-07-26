from __future__ import annotations

import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def cockpit_tree() -> ast.Module:
    source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")
    return ast.parse(source)


def cockpit_html() -> str:
    for node in cockpit_tree().body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "COCKPIT_HTML" for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("COCKPIT_HTML nebyl nalezen.")


def cockpit_post_action_paths() -> set[str]:
    for node in cockpit_tree().body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "COCKPIT_POST_ACTIONS"
            and node.value is not None
        ):
            return {item["path"] for item in ast.literal_eval(node.value)}
    raise AssertionError("COCKPIT_POST_ACTIONS nebyl nalezen.")


def cockpit_http_routes(method_name: str) -> set[str]:
    for node in ast.walk(cockpit_tree()):
        if not isinstance(node, ast.FunctionDef) or node.name != method_name:
            continue
        routes: set[str] = set()
        for candidate in ast.walk(node):
            if not isinstance(candidate, ast.Compare):
                continue
            left = candidate.left
            if not (
                isinstance(left, ast.Attribute)
                and left.attr == "path"
                and isinstance(left.value, ast.Name)
                and left.value.id == "parsed"
            ):
                continue
            for comparator in candidate.comparators:
                if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                    routes.add(comparator.value)
        return routes
    raise AssertionError(f"{method_name} nebyl nalezen.")


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
        self.assertIn("/api/codex-approval/clear", html)
        self.assertNotIn("/api/voice-mode/codex-approval/clear", html)
        self.assertIn('id="tvbcpOpenBtn"', html)
        self.assertIn("openTvbcpModal", html)
        self.assertIn("/api/tvbcp", html)
        self.assertNotIn("/api/voice-bridge/tvbcp", html)

    def test_human_adam_microphone_and_generic_backend_routes_remain(self) -> None:
        cockpit_source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")
        human_adam_source = (
            PROJECT_ROOT / "app" / "communication" / "human_adam_ui.py"
        ).read_text(encoding="utf-8")

        self.assertIn('id="voiceRecordBtn"', human_adam_source)
        self.assertIn("navigator.mediaDevices.getUserMedia", human_adam_source)
        self.assertIn("/api/human-adam/transcribe", human_adam_source)
        for route in (
            "/api/speech/speak",
            "/api/speech/edge-tts",
            "/api/codex-approval/clear",
            "/api/tvbcp",
        ):
            with self.subTest(route=route):
                self.assertIn(route, cockpit_source)

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
            "/api/voice-mode/safe-readonly",
            "/api/voice-mode/safe-readonly/run",
        ):
            with self.subTest(route=route):
                self.assertNotIn(route, cockpit_source)

    def test_surviving_generic_routes_have_no_voice_aliases(self) -> None:
        source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")

        self.assertIn('"path": "/api/codex-approval/clear"', source)
        self.assertIn('if parsed.path == "/api/codex-approval/clear"', source)
        self.assertIn('if parsed.path == "/api/tvbcp"', source)
        self.assertNotIn("/api/voice-mode/codex-approval/clear", source)
        self.assertNotIn("/api/voice-bridge/tvbcp", source)

    def test_legacy_voice_bridge_public_routes_are_retired(self) -> None:
        registered_paths = cockpit_post_action_paths()
        post_routes = cockpit_http_routes("do_POST")
        get_routes = cockpit_http_routes("do_GET")
        retired_post_routes = {
            "/api/speech/transcribe",
            "/api/speech/voice-text",
            "/api/voice-bridge/frontend-event",
            "/api/voice-mode/start",
            "/api/voice-mode/stop",
            "/api/voice-mode/approval",
            "/api/voice-mode/safe-readonly/run",
            "/api/voice-bridge/marker",
            "/api/voice-bridge/terminate-stale",
        }
        retired_get_routes = {
            "/api/voice-mode/latest-response",
            "/api/voice-mode/safe-readonly",
        }

        self.assertTrue(retired_post_routes.isdisjoint(registered_paths))
        self.assertTrue(retired_post_routes.isdisjoint(post_routes))
        self.assertTrue(retired_get_routes.isdisjoint(get_routes))
        for route in (
            "/api/human-adam/transcribe",
            "/api/speech/speak",
            "/api/speech/edge-tts",
            "/api/codex-approval/clear",
        ):
            with self.subTest(route=route):
                self.assertIn(route, registered_paths)
                self.assertIn(route, post_routes)
        self.assertIn("/api/tvbcp", get_routes)


if __name__ == "__main__":
    unittest.main()
