from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.health_check import format_samantha_health_check, run_samantha_health_check


class HealthCheckTests(unittest.TestCase):
    def test_health_check_reports_clean_git_a1_and_pending_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = _memory_dir(Path(temp_dir))

            result = run_samantha_health_check(
                mode="quick",
                repo_root=Path(temp_dir),
                memory_dir=memory_dir,
                runner=_runner("## main...origin/main\n"),
            )

        self.assertEqual(result.git_summary, "clean, ## main...origin/main")
        self.assertEqual(result.reminder_count, 1)
        self.assertIn("Commitove odpoledne", result.a1_items[0])
        self.assertTrue(any("fyzicky ověřit tisk" in item for item in result.pending_items))
        self.assertEqual(result.warnings, ())

    def test_health_check_reports_dirty_git_and_relative_time_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = _memory_dir(Path(temp_dir))
            (memory_dir / "MEMORY_INDEX.md").write_text(
                "- `handoffs/old.md` - [PRIPOMENOUT] historicky mezistav, pushnout zitra\n",
                encoding="utf-8",
            )

            result = run_samantha_health_check(
                mode="full",
                repo_root=Path(temp_dir),
                memory_dir=memory_dir,
                runner=_runner("## main...origin/main\n M file.md\n?? new.md\n"),
            )

        self.assertIn("dirty (2 changed/untracked)", result.git_summary)
        self.assertTrue(any("Historicky/prekrity" in warning for warning in result.warnings))
        self.assertTrue(any("relativni" in warning for warning in result.warnings))
        self.assertIn("commitovy uklid", result.suggested_next_action)

    def test_format_health_check_is_human_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = _memory_dir(Path(temp_dir))

            text = format_samantha_health_check(
                mode="quick",
                repo_root=Path(temp_dir),
                memory_dir=memory_dir,
                runner=_runner("## main...origin/main\n"),
            )

        self.assertIn("Samantha Health Check", text)
        self.assertIn("Git: clean", text)
        self.assertIn("A1+ pravidla:", text)
        self.assertIn("Pending / hlidane veci:", text)

    def test_quick_mode_keeps_pending_summary_shorter_than_full_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = _memory_dir(Path(temp_dir))

            quick = run_samantha_health_check(
                mode="quick",
                repo_root=Path(temp_dir),
                memory_dir=memory_dir,
                runner=_runner("## main...origin/main\n"),
            )
            full = run_samantha_health_check(
                mode="full",
                repo_root=Path(temp_dir),
                memory_dir=memory_dir,
                runner=_runner("## main...origin/main\n"),
            )

        self.assertFalse(any(item.startswith("`handoffs/document.md`") for item in quick.pending_items))
        self.assertTrue(any(item.startswith("`handoffs/document.md`") for item in full.pending_items))

    def test_dirty_repo_threshold_adds_cleanup_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = _memory_dir(Path(temp_dir))

            result = run_samantha_health_check(
                mode="quick",
                repo_root=Path(temp_dir),
                memory_dir=memory_dir,
                runner=_runner(
                    "## main...origin/main\n"
                    " M one.py\n"
                    " M two.py\n"
                    "?? three.py\n"
                    "?? four.py\n"
                ),
            )

        self.assertTrue(any("ad hoc commitovy uklid" in warning for warning in result.warnings))

    def test_health_check_skips_archived_project_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir) / "memory"
            memory_dir.mkdir()
            (memory_dir / "ACTIVE_PROJECTS.md").write_text(
                "| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| Commitove odpoledne | A1+ | active | Aktivni pravidlo | x | x | Drzet cisty stul. |\n"
                "| Stary projekt | A1+ | archived | Hotovo | x | x | Archiv. |\n",
                encoding="utf-8",
            )
            (memory_dir / "MEMORY_INDEX.md").write_text("", encoding="utf-8")

            result = run_samantha_health_check(
                mode="quick",
                repo_root=Path(temp_dir),
                memory_dir=memory_dir,
                runner=_runner("## main...origin/main\n"),
            )

        self.assertEqual(len(result.a1_items), 1)
        self.assertIn("Commitove odpoledne", result.a1_items[0])
        self.assertNotIn("Stary projekt", " ".join(result.a1_items))


def _memory_dir(root: Path) -> Path:
    memory_dir = root / "memory"
    memory_dir.mkdir()
    (memory_dir / "ACTIVE_PROJECTS.md").write_text(
        "| Oblast | Priorita | Stav | Memory soubor | Handoff | Dalsi krok |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| Commitove odpoledne | A1+ | Aktivni pravidlo | x | x | Drzet cisty stul. |\n"
        "| Dokumenty | 1 | Fyzicky tisk pending | x | x | fyzicky ověřit tisk. |\n",
        encoding="utf-8",
    )
    (memory_dir / "MEMORY_INDEX.md").write_text(
        "- `handoffs/document.md` - [PRIPOMENOUT] fyzicky ověřit tisk\n",
        encoding="utf-8",
    )
    return memory_dir


def _runner(stdout: str):
    def run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=stdout, stderr="")

    return run


if __name__ == "__main__":
    unittest.main()
