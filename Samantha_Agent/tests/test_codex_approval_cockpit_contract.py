from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CodexApprovalCockpitContractTests(unittest.TestCase):
    def test_cockpit_uses_generic_state_and_top_level_payload(self) -> None:
        source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")
        voice_import_start = source.index("from app.speech.adam_voice_mode import (")
        voice_import_end = source.index(")\n", voice_import_start)
        voice_import = source[voice_import_start:voice_import_end]

        self.assertIn("from app.codex_approval_state import (", source)
        self.assertNotIn("clear_codex_approval_request", voice_import)
        self.assertIn("codex_approval=load_codex_approval_request", source)
        self.assertIn("codex_approval_loader=codex_approval_loader or load_codex_approval_request", source)
        self.assertIn("codex_approval: data.codex_approval || {}", source)
        self.assertIn("renderCodexApproval(data.codex_approval || {});", source)
        self.assertNotIn("voiceMode.codex_approval", source)

    def test_approval_card_remains_after_voice_section_retirement(self) -> None:
        source = (PROJECT_ROOT / "app" / "cockpit.py").read_text(encoding="utf-8")

        self.assertIn('id="codexApprovalCard"', source)
        self.assertNotIn('id="voiceCommandDetails"', source)
        self.assertIn('id="codexApprovalOpenHumanAdamBtn"', source)
        self.assertIn('window.location.href = "/human-adam/"', source)
        self.assertIn('postJson("/api/codex-approval/clear"', source)
        self.assertNotIn("/api/voice-mode/codex-approval/clear", source)
        self.assertNotIn("codexApprovalSendConfirmationBtn", source)
        self.assertNotIn("sendCodexApprovalConfirmation", source)
        self.assertNotIn('data-safe-readonly="git_status"', source)
        self.assertNotIn('data-safe-readonly="backup_status"', source)

    def test_voice_mode_and_notice_script_no_longer_own_approval_state(self) -> None:
        voice_source = (PROJECT_ROOT / "app" / "speech" / "adam_voice_mode.py").read_text(encoding="utf-8")
        script_source = (PROJECT_ROOT / "scripts" / "codex_approval_notice.py").read_text(encoding="utf-8")

        self.assertNotIn("CODEX_APPROVAL_REQUEST_PATH", voice_source)
        self.assertNotIn("def save_codex_approval_request", voice_source)
        self.assertNotIn("def clear_codex_approval_request", voice_source)
        self.assertNotIn("def load_codex_approval_request", voice_source)
        self.assertIn(
            "from app.codex_approval_state import clear_codex_approval_request, save_codex_approval_request",
            script_source,
        )


if __name__ == "__main__":
    unittest.main()
