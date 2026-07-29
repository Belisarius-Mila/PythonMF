from __future__ import annotations

import unittest
from pathlib import Path

from app.cockpit_frontend import COCKPIT_HTML


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CodexApprovalCockpitContractTests(unittest.TestCase):
    def test_cockpit_uses_generic_state_and_top_level_payload(self) -> None:
        source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")

        self.assertIn("from app.codex_approval_state import (", source)
        self.assertNotIn("from app.speech.adam_voice_mode import", source)
        self.assertIn("codex_approval=load_codex_approval_request", source)
        self.assertIn("codex_approval_loader=codex_approval_loader or load_codex_approval_request", source)
        self.assertIn("codex_approval: data.codex_approval || {}", COCKPIT_HTML)
        self.assertIn("renderCodexApproval(data.codex_approval || {});", COCKPIT_HTML)
        self.assertNotIn("voiceMode.codex_approval", COCKPIT_HTML)

    def test_approval_card_remains_after_voice_section_retirement(self) -> None:
        self.assertIn('id="codexApprovalCard"', COCKPIT_HTML)
        self.assertNotIn('id="voiceCommandDetails"', COCKPIT_HTML)
        self.assertIn('id="codexApprovalOpenHumanAdamBtn"', COCKPIT_HTML)
        self.assertIn('window.location.href = "/human-adam/"', COCKPIT_HTML)
        self.assertIn('postJson("/api/codex-approval/clear"', COCKPIT_HTML)
        self.assertNotIn("/api/voice-mode/codex-approval/clear", COCKPIT_HTML)
        self.assertNotIn("codexApprovalSendConfirmationBtn", COCKPIT_HTML)
        self.assertNotIn("sendCodexApprovalConfirmation", COCKPIT_HTML)
        self.assertNotIn('data-safe-readonly="git_status"', COCKPIT_HTML)
        self.assertNotIn('data-safe-readonly="backup_status"', COCKPIT_HTML)

    def test_notice_script_owns_approval_state_without_voice_mode(self) -> None:
        script_source = (PROJECT_ROOT / "scripts" / "codex_approval_notice.py").read_text(encoding="utf-8")

        self.assertFalse((PROJECT_ROOT / "app" / "speech" / "adam_voice_mode.py").exists())
        self.assertIn(
            "from app.codex_approval_state import clear_codex_approval_request, save_codex_approval_request",
            script_source,
        )


if __name__ == "__main__":
    unittest.main()
