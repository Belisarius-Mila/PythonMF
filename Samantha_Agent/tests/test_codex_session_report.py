from __future__ import annotations

from pathlib import Path
import unittest

from scripts.codex_session_report import (
    build_report,
    discover_sessions,
    format_age,
    parse_etime,
    parse_process_rows,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class CodexSessionReportTests(unittest.TestCase):
    def test_parse_etime_supports_days_hours_and_minutes(self) -> None:
        self.assertEqual(parse_etime("2-09:05:05"), 2 * 86400 + 9 * 3600 + 5 * 60 + 5)
        self.assertEqual(parse_etime("01:09:32"), 3600 + 9 * 60 + 32)
        self.assertEqual(parse_etime("22:45"), 22 * 60 + 45)

    def test_discover_sessions_marks_only_stale_non_current_non_bridge_as_candidate(self) -> None:
        rows = parse_process_rows(
            "\n".join(
                [
                    "23045 22995 ttys001 2-09:05:05 node /usr/local/bin/codex -C /repo .",
                    "23106 23045 ttys001 2-09:05:05 /vendor/bin/codex -C /repo .",
                    "73759 73747 ttys002 01:09:33 node /usr/local/bin/codex -C /repo .",
                    "73760 73759 ttys002 01:09:32 /vendor/bin/codex -C /repo .",
                    "75845 75764 ttys004 1-10:17:16 node /usr/local/bin/codex -C /repo .",
                    "75848 75845 ttys004 1-10:17:16 /vendor/bin/codex -C /repo .",
                    "76785 76707 ttys005 1-10:12:26 node /usr/local/bin/codex -C /repo .",
                    "76790 76785 ttys005 1-10:12:26 /vendor/bin/codex -C /repo .",
                    "73746 73735 ?? 01:09:41 sshd-session: miloslavfalta@ttys002",
                    "55578 55561 ?? 09:08:02 codex app-server --analytics-default-enabled",
                ]
            )
        )

        sessions = discover_sessions(
            rows,
            current_tty_value="ttys005",
            marked_tty="ttys005",
            labels={"ttys004": {"label": "USA", "protected": True}},
            stale_after_hours=36,
        )

        by_tty = {session.tty: session for session in sessions}
        self.assertEqual(set(by_tty), {"ttys001", "ttys002", "ttys004", "ttys005"})
        self.assertTrue(by_tty["ttys001"].candidate)
        self.assertIn("SSH", by_tty["ttys002"].role)
        self.assertFalse(by_tty["ttys004"].candidate)
        self.assertIn("chráněná", by_tty["ttys004"].role)
        self.assertFalse(by_tty["ttys005"].candidate)
        self.assertIn("hlasový bridge", by_tty["ttys005"].role)

    def test_build_report_includes_exact_shutdown_instruction(self) -> None:
        rows = parse_process_rows(
            "23045 22995 ttys001 2-09:05:05 node /usr/local/bin/codex -C /repo .\n"
            "23106 23045 ttys001 2-09:05:05 /vendor/bin/codex -C /repo .\n"
        )
        sessions = discover_sessions(rows, current_tty_value="ttys005", marked_tty="ttys005", stale_after_hours=36)

        report = build_report(sessions, current_tty_value="ttys005", marked_tty="ttys005")

        self.assertIn("ttys001", report)
        self.assertIn("Kandidáti na ukončení", report)
        self.assertIn("Ukonči relaci ttysXXX", report)

    def test_format_age_is_compact_for_startup_report(self) -> None:
        self.assertEqual(format_age(2 * 86400 + 9 * 3600), "2d 9h")
        self.assertEqual(format_age(10 * 3600 + 5 * 60), "10h 5m")

    def test_screen_entry_prompts_for_voice_marker_with_default_yes(self) -> None:
        script = (REPO_ROOT / "scripts" / "samantha_screen_entry.sh").read_text(encoding="utf-8")

        self.assertIn("Mám nastavit voice marker na tuto relaci? [Y/n]", script)
        self.assertIn("SAMANTHA_MARK_VOICE_TTY", script)
        self.assertIn("scripts/mark_current_codex_tty.py", script)
        self.assertIn('""|1|true|yes|y|ano|a', script)

    def test_manual_voice_marker_takeover_requires_confirmation(self) -> None:
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        rules = (REPO_ROOT / "memory" / "technical" / "session_recovery_rules.md").read_text(encoding="utf-8")

        for text in (agents, rules):
            self.assertIn("Prosím převezmi voice marker", text)
            self.assertIn("Mám převzít voice marker? y/n", text)
            self.assertIn(".venv/bin/python scripts/mark_current_codex_tty.py", text)


if __name__ == "__main__":
    unittest.main()
