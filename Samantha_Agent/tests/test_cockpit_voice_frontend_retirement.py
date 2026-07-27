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

    def test_orphaned_cockpit_voice_handlers_and_glue_are_retired(self) -> None:
        source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")
        retired_markers = (
            "from app.voice_bridge_coordinator import (",
            "def terminate_stale_codex_sessions_action(",
            "def set_adam_voice_bridge_marker_action(",
            "def start_adam_voice_mode_action(",
            "def stop_adam_voice_mode_action(",
            "def cockpit_voice_approval_action(",
            "SAFE_READONLY_CAPABILITIES",
            "def cockpit_safe_readonly_capabilities_action(",
            "def cockpit_safe_readonly_run_action(",
            "def safe_readonly_codex_sessions_result(",
            "def safe_readonly_voice_bridge_result(",
            "def safe_readonly_git_status_result(",
            "def safe_readonly_backup_status_result(",
            "def default_safe_readonly_handlers(",
            "def cockpit_voice_latest_response_action(",
            "def cockpit_voice_frontend_event_action(",
            "def deliver_saved_voice_command_inline(",
            "def deliver_voice_command_via_managed_screen(",
            "def deliver_voice_command_by_configured_transport(",
            "def record_voice_transcription_failure(",
            "def cockpit_transcribe_voice_action(",
            "def cockpit_save_voice_text_action(",
            "def voice_bridge_frozen_result(",
            "VOICE_BRIDGE_FROZEN",
            "ADAM_VOICE_MODE_SCRIPT",
            "ADAM_VOICE_MODE_LOG_FILE",
            "VOICE_COMMAND_INBOX_DIR",
            "voice_bridge_status as build_voice_bridge_status",
            "def adam_voice_bridge_status(",
            "CURRENT_CODEX_TTY_PATH",
            "protected_by_voice_marker",
            "Mílův hlasový bridge:",
            "from app.adam_service import (",
            "def managed_codex_session_tty_labels(",
            "def discover_codex_process_sessions(",
            "def janicka_chat_memory_context(",
            "def janicka_chat_action(",
            "def janicka_orphaned_codex_session_report(",
            "def terminate_orphaned_janicka_sessions_action(",
            "def janicka_latest_codex_reply_action(",
            "def open_janicka_full_adam_action(",
        )
        preserved_markers = (
            "def transcribe_audio_base64_isolated(",
            "def human_adam_transcribe_action(",
            "def cockpit_speak_action(",
            "def cockpit_edge_tts_action(",
        )

        for marker in retired_markers:
            with self.subTest(retired=marker):
                self.assertNotIn(marker, source)
        for marker in preserved_markers:
            with self.subTest(preserved=marker):
                self.assertIn(marker, source)

    def test_janicka_legacy_communication_surface_is_retired(self) -> None:
        source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")
        post_paths = cockpit_post_action_paths()
        html = cockpit_html()
        retired_paths = {
            "/api/janicka/chat",
            "/api/janicka/chat/latest",
            "/api/adam/status",
            "/api/adam/start",
            "/api/adam/restart",
            "/api/adam/stop",
            "/api/janicka/light/status",
            "/api/janicka/light/start",
            "/api/janicka/light/stop",
            "/api/janicka/light/cleanup-orphans",
            "/api/janicka/full-adam/open",
        }
        retired_frontend_markers = (
            "janickaAskAdamBtn",
            "janickaFullAdamBtn",
            "janickaChatModal",
            "janickaLightStatus",
            "janickaAdamStatus",
            "submitJanickaChat",
            "pollJanickaCodexReply",
            "openFullAdamForJanicka",
            "Servisní fallback",
        )

        self.assertTrue(retired_paths.isdisjoint(post_paths))
        for path in retired_paths:
            with self.subTest(retired_path=path):
                self.assertNotIn(path, source)
        for marker in retired_frontend_markers:
            with self.subTest(retired_frontend=marker):
                self.assertNotIn(marker, html)

        for preserved_marker in (
            "janickaFindDocumentBtn",
            "janickaEmailBtn",
            "janickaLekarnaBtn",
            "janickaFamilyBtn",
            "janickaRemindersBtn",
            "janickaRecoveryBtn",
            "janickaCookbookBtn",
            "speakText",
        ):
            with self.subTest(preserved_frontend=preserved_marker):
                self.assertIn(preserved_marker, html)

        human_adam_ui = (PROJECT_ROOT / "app" / "communication" / "human_adam_ui.py").read_text(encoding="utf-8")
        self.assertIn('id="voiceRecordBtn"', human_adam_ui)
        self.assertIn("/api/human-adam/transcribe", human_adam_ui)

        adam_service = (PROJECT_ROOT / "app" / "adam_service.py").read_text(encoding="utf-8")
        self.assertIn("def submit_janicka_text_request(", adam_service)
        self.assertIn("def start_janicka_light_session(", adam_service)

    def test_live_diagnostics_do_not_depend_on_voice_bridge_marker(self) -> None:
        quick_check = (PROJECT_ROOT / "scripts" / "system_quick_check.py").read_text(encoding="utf-8")
        session_report = (PROJECT_ROOT / "scripts" / "codex_session_report.py").read_text(encoding="utf-8")
        readiness = (PROJECT_ROOT / "scripts" / "adam_bridge_readiness_report.py").read_text(encoding="utf-8")
        adam_service = (PROJECT_ROOT / "app" / "adam_service.py").read_text(encoding="utf-8")

        for name, source in (
            ("quick_check", quick_check),
            ("session_report", session_report),
            ("readiness", readiness),
            ("adam_service", adam_service),
        ):
            with self.subTest(source=name):
                self.assertNotIn("current_codex_tty", source)
                self.assertNotIn("CURRENT_CODEX_TTY_PATH", source)
                self.assertNotIn("load_marked_codex_tty", source)
        self.assertNotIn("adam_voice_bridge_status", quick_check)
        self.assertIn("from scripts.codex_session_report import main", readiness)


if __name__ == "__main__":
    unittest.main()
