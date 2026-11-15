from __future__ import annotations

import os
import json
import shutil
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from app.backup.activity_state import record_backup_completed
from app.backup.incremental import run_backup


class BackupIncrementalTests(unittest.TestCase):
    @contextmanager
    def _shared_activity_state(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "PythonMF"
            project = source / "Samantha_Agent"
            state = project / "data/backup/activity_state.json"
            state.parent.mkdir(parents=True)
            state.write_text('{"last_backup_at": "2026-11-08"}\n', encoding="utf-8")
            state.chmod(0o600)
            target = base / "backup"
            old_states = []
            for stamp in ("20261101_000000", "20261108_000000"):
                snapshot = target / "snapshots" / stamp
                old = snapshot / "PythonMF/Samantha_Agent/data/backup/activity_state.json"
                old.parent.mkdir(parents=True)
                if old_states:
                    os.link(old_states[0], old)
                else:
                    shutil.copy2(state, old)
                (snapshot / "backup_manifest.txt").write_text("complete\n", encoding="utf-8")
                old_states.append(old)
            new_state = target / "snapshots/20261115_000000/PythonMF/Samantha_Agent/data/backup/activity_state.json"

            def complete(**kwargs):
                # Exercise the real inode sharing before final state publication.
                self.assertTrue(new_state.samefile(old_states[0]))
                self.assertEqual(new_state.stat().st_nlink, 3)
                record_backup_completed(path=state, **kwargs)

            with (
                patch("app.backup.incremental.SAMANTHA_DIR", project),
                patch("app.backup.incremental._copy_codex_home"),
                patch("app.backup.incremental.RECOVERY_GUIDE", base / "missing"),
                patch("app.backup.incremental.record_backup_completed", side_effect=complete),
            ):
                yield source, target, state, old_states, new_state

    def test_completion_keeps_older_hardlinked_activity_states_unchanged(self):
        with self._shared_activity_state() as (source, target, state, old_states, new_state):
            before = [(p.read_bytes(), p.stat().st_ino, p.stat().st_mtime_ns,
                       p.stat().st_mode) for p in old_states]
            run_backup(mode="execute", profile="safe", backup_root=target,
                       source_root=source, timestamp="20261115_000000", progress_every=0)
            for old, expected in zip(old_states, before):
                self.assertEqual((old.read_bytes(), old.stat().st_ino,
                                  old.stat().st_mtime_ns, old.stat().st_mode), expected)
            self.assertEqual(new_state.read_bytes(), state.read_bytes())
            self.assertEqual(new_state.stat().st_nlink, 1)
            self.assertFalse(new_state.samefile(old_states[0]))
            self.assertEqual(new_state.stat().st_mtime_ns, state.stat().st_mtime_ns)
            self.assertEqual(new_state.stat().st_mode, state.stat().st_mode)
            self.assertEqual(json.loads(new_state.read_text())["last_backup_target"],
                             str(new_state.parents[3]))

    def test_interrupted_activity_replace_preserves_complete_old_bytes(self):
        with self._shared_activity_state() as (source, target, state, old_states, new_state):
            before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in old_states]
            real_replace = os.replace

            def interrupted(src, dst):
                if Path(dst) == new_state:
                    raise OSError("synthetic interrupted activity replacement")
                return real_replace(src, dst)

            with patch("app.file_persistence.os.replace", side_effect=interrupted):
                with self.assertRaisesRegex(OSError, "synthetic interrupted"):
                    run_backup(mode="execute", profile="safe", backup_root=target,
                               source_root=source, timestamp="20261115_000000", progress_every=0)
            for old, expected in zip(old_states, before):
                self.assertEqual((old.read_bytes(), old.stat().st_mtime_ns), expected)
            self.assertEqual(new_state.read_bytes(), before[0][0])
            self.assertEqual(json.loads(new_state.read_text()), {"last_backup_at": "2026-11-08"})
            self.assertEqual(list(new_state.parent.glob(f".{new_state.name}.*.tmp")), [])

    def test_recovery_includes_camino_and_does_not_complete_if_it_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            source.mkdir()
            (source / "example.txt").write_text("synthetic")
            target = base / "target"
            with (patch("app.backup.incremental._is_secure_recovery_target", return_value=True),
                  patch("app.backup.incremental._copy_codex_home"),
                  patch("app.backup.incremental.RECOVERY_GUIDE", base / "missing"),
                  patch("app.backup.incremental.record_backup_completed") as completed,
                  patch("app.backup.camino.backup_camino") as camino):
                camino.return_value = {"state": "completed", "snapshot_id": "verified-camino"}
                run_backup(mode="execute", profile="recovery", backup_root=target,
                           source_root=source, timestamp="one", progress_every=0)
                manifest = target / "snapshots/one/backup_manifest.txt"
                self.assertIn("Camino supplement: verified-camino", manifest.read_text())
                camino.assert_called_once_with(backup_root=target, mode="execute")
                completed.reset_mock()
                camino.side_effect = RuntimeError("copy failed")
                with self.assertRaises(RuntimeError):
                    run_backup(mode="execute", profile="recovery", backup_root=target,
                               source_root=source, timestamp="two", progress_every=0)
                self.assertFalse((target / "snapshots/two/backup_manifest.txt").exists())
                completed.assert_not_called()
                self.assertTrue(manifest.is_file())

    def test_execute_skips_venv_globs_and_uses_completed_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "PythonMF"
            backup_root = root / "backup"
            home = root / "home"
            source.mkdir()
            (source / "Samantha_Agent").mkdir()
            (source / "Samantha_Agent" / ".venv_f5tts2").mkdir()
            (source / "Samantha_Agent" / ".venv_f5tts2" / "ignored.py").write_text("skip\n", encoding="utf-8")
            keep = source / "Samantha_Agent" / "keep.txt"
            keep.write_text("keep\n", encoding="utf-8")

            incomplete = backup_root / "snapshots" / "20260603_120000"
            incomplete.mkdir(parents=True)
            previous = backup_root / "snapshots" / "20260602_120000"
            previous_file = previous / "PythonMF" / "Samantha_Agent" / "keep.txt"
            previous_file.parent.mkdir(parents=True)
            previous_file.write_text("keep\n", encoding="utf-8")
            os.utime(previous_file, (keep.stat().st_atime, keep.stat().st_mtime))
            (previous / "backup_manifest.txt").write_text("complete\n", encoding="utf-8")

            with (
                patch("app.backup.incremental.Path.home", return_value=home),
                patch("app.backup.incremental.record_backup_completed"),
            ):
                output = run_backup(
                    mode="execute",
                    profile="safe",
                    backup_root=backup_root,
                    source_root=source,
                    timestamp="20260603_130000",
                    progress_every=0,
                )

            snapshot = backup_root / "snapshots" / "20260603_130000"
            copied = snapshot / "PythonMF" / "Samantha_Agent" / "keep.txt"
            ignored = snapshot / "PythonMF" / "Samantha_Agent" / ".venv_f5tts2" / "ignored.py"

            self.assertIn("Previous snapshot: " + str(previous), output)
            self.assertTrue((snapshot / "backup_manifest.txt").exists())
            self.assertTrue(copied.exists())
            self.assertFalse(ignored.exists())
            self.assertEqual(copied.stat().st_ino, previous_file.stat().st_ino)

    def test_dry_run_does_not_create_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "PythonMF"
            backup_root = root / "backup"
            home = root / "home"
            source.mkdir()
            (source / "file.txt").write_text("x\n", encoding="utf-8")

            with patch("app.backup.incremental.Path.home", return_value=home):
                output = run_backup(
                    mode="dry-run",
                    profile="safe",
                    backup_root=backup_root,
                    source_root=source,
                    timestamp="20260603_130000",
                    progress_every=0,
                )

            self.assertIn("Dry-run hotov", output)
            self.assertFalse((backup_root / "snapshots").exists())


if __name__ == "__main__":
    unittest.main()
