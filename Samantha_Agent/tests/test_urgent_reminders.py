from __future__ import annotations

import errno
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from app.file_persistence import lock_path_for
from app.urgent_reminders import (
    deliver_urgent_reminder,
    mark_urgent_reminder_done,
    sync_urgent_reminders_index,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class UrgentRemindersTests(unittest.TestCase):
    def test_direct_delivery_is_idempotent_and_survives_icloud_sync(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "inbox"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"

            first, first_created = deliver_urgent_reminder(
                "Zavolat zítra ráno.",
                created_at="2026-08-02T08:15:00+02:00",
                index_path=index_path,
            )
            duplicate, duplicate_created = deliver_urgent_reminder(
                "Zavolat zítra ráno.",
                created_at="2026-08-02T18:45:00+02:00",
                index_path=index_path,
            )
            after_sync = sync_urgent_reminders_index(
                inbox_dir=inbox,
                index_path=index_path,
            )
            stored = json.loads(index_path.read_text(encoding="utf-8"))["reminders"]

        self.assertTrue(first_created)
        self.assertFalse(duplicate_created)
        self.assertEqual(first.reminder_number, duplicate.reminder_number)
        self.assertEqual([item.reminder_number for item in after_sync], [first.reminder_number])
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["source_kind"], "direct_tailscale")

    def test_direct_delivery_validates_input(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            index_path = Path(temp_dir) / "index.json"

            with self.assertRaisesRegex(ValueError, "nesmí být prázdné"):
                deliver_urgent_reminder("  ", index_path=index_path)
            with self.assertRaisesRegex(ValueError, "delivery_id"):
                deliver_urgent_reminder(
                    "Platný text",
                    delivery_id="not allowed!",
                    index_path=index_path,
                )

        self.assertFalse(index_path.exists())

    def test_sync_and_done_use_lock_and_preserve_done_status(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "inbox"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"
            source = inbox / "samantha_reminder_test.md"
            _write_reminder(source, "První důležité připomenutí")

            first = sync_urgent_reminders_index(inbox_dir=inbox, index_path=index_path)
            done = mark_urgent_reminder_done(1, index_path=index_path)
            second = sync_urgent_reminders_index(inbox_dir=inbox, index_path=index_path)

            self.assertEqual([item.reminder_number for item in first], [1])
            self.assertIsNotNone(done)
            self.assertEqual(done.status, "done")
            self.assertEqual(second[0].status, "done")
            self.assertTrue(lock_path_for(index_path).exists())

    def test_missing_done_target_does_not_rewrite_index(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            index_path = root / "index.json"
            index_path.write_text('{"reminders": []}\n', encoding="utf-8")

            with patch("app.file_persistence.os.replace", side_effect=OSError("must not replace")):
                result = mark_urgent_reminder_done(999, index_path=index_path)

            self.assertIsNone(result)
            self.assertEqual(json.loads(index_path.read_text(encoding="utf-8")), {"reminders": []})

    def test_sync_replace_failure_preserves_previous_index(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "inbox"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"
            _write_reminder(inbox / "samantha_reminder_a.md", "První připomenutí")
            sync_urgent_reminders_index(inbox_dir=inbox, index_path=index_path)
            original = index_path.read_bytes()
            _write_reminder(inbox / "samantha_reminder_b.md", "Druhé připomenutí")

            with patch("app.file_persistence.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    sync_urgent_reminders_index(inbox_dir=inbox, index_path=index_path)

            self.assertEqual(index_path.read_bytes(), original)
            self.assertEqual(list(index_path.parent.glob(f".{index_path.name}.*.tmp")), [])

    def test_sync_retries_one_hydrating_file_and_reports_it_without_losing_index(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "inbox"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"
            readable = inbox / "samantha_reminder_a.md"
            pending = inbox / "samantha_reminder_b.md"
            _write_reminder(readable, "První připomenutí")
            _write_reminder(pending, "Čekající připomenutí")
            diagnostics: dict[str, int] = {}

            def read_with_pending(path: Path) -> str:
                if path == pending:
                    raise OSError(errno.EDEADLK, "Resource deadlock avoided")
                return path.read_text(encoding="utf-8")

            with (
                patch("app.urgent_reminders._read_text", side_effect=read_with_pending),
                patch("app.urgent_reminders.time.sleep", return_value=None) as sleep_mock,
            ):
                reminders = sync_urgent_reminders_index(
                    inbox_dir=inbox,
                    index_path=index_path,
                    sync_diagnostics=diagnostics,
                    hydration_retry_delays=(0.5, 1.0),
                    sleeper=time.sleep,
                )

            self.assertEqual([item.reminder_number for item in reminders], [1])
            self.assertEqual(diagnostics["checked_file_count"], 2)
            self.assertEqual(diagnostics["readable_file_count"], 1)
            self.assertEqual(diagnostics["pending_download_count"], 1)
            self.assertGreaterEqual(diagnostics["pending_oldest_age_seconds"], 0)
            self.assertEqual(sleep_mock.call_count, 2)
            self.assertEqual(len(json.loads(index_path.read_text(encoding="utf-8"))["reminders"]), 1)

    def test_pending_download_diagnostics_report_oldest_file_age(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "inbox"
            inbox.mkdir()
            index_path = root / "index.json"
            pending = inbox / "samantha_reminder_pending.md"
            _write_reminder(pending, "Čekající připomenutí")
            old_timestamp = time.time() - 420
            os.utime(pending, (old_timestamp, old_timestamp))
            diagnostics: dict[str, int] = {}

            def deadlocked_read(_path: Path) -> str:
                raise OSError(errno.EDEADLK, "Resource deadlock avoided")

            with patch("app.urgent_reminders._read_text", side_effect=deadlocked_read):
                sync_urgent_reminders_index(
                    inbox_dir=inbox,
                    index_path=index_path,
                    sync_diagnostics=diagnostics,
                    hydration_retry_delays=(),
                )

        self.assertEqual(diagnostics["pending_download_count"], 1)
        self.assertGreaterEqual(diagnostics["pending_oldest_age_seconds"], 419)

    def test_sync_indexes_file_when_hydration_finishes_during_retry(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "inbox"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"
            source = inbox / "samantha_reminder_a.md"
            _write_reminder(source, "Po hydrataci")
            diagnostics: dict[str, int] = {}
            original_read_text = source.read_text

            with (
                patch(
                    "app.urgent_reminders._read_text",
                    side_effect=[
                        OSError(errno.EDEADLK, "Resource deadlock avoided"),
                        OSError(errno.EDEADLK, "Resource deadlock avoided"),
                        original_read_text(encoding="utf-8"),
                    ],
                ),
                patch("app.urgent_reminders.time.sleep", return_value=None) as sleep_mock,
            ):
                reminders = sync_urgent_reminders_index(
                    inbox_dir=inbox,
                    index_path=index_path,
                    sync_diagnostics=diagnostics,
                    hydration_retry_delays=(0.5, 1.0, 2.0),
                    sleeper=time.sleep,
                )

            self.assertEqual([item.reminder_number for item in reminders], [1])
            self.assertEqual(diagnostics["pending_download_count"], 0)
            self.assertEqual(sleep_mock.call_count, 2)

    def test_two_processes_merge_urgent_reminders_with_unique_stable_numbers(self) -> None:
        script = """
import sys
import time
from pathlib import Path
from app.urgent_reminders import sync_urgent_reminders_index

inbox = Path(sys.argv[1])
index_path = Path(sys.argv[2])
start_path = Path(sys.argv[3])
while not start_path.exists():
    time.sleep(0.01)
sync_urgent_reminders_index(inbox_dir=inbox, index_path=index_path)
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inboxes = (root / "inbox-a", root / "inbox-b")
            for worker, inbox in zip(("a", "b"), inboxes, strict=True):
                inbox.mkdir()
                for index in range(20):
                    _write_reminder(
                        inbox / f"samantha_reminder_{worker}_{index:02d}.md",
                        f"Důležité připomenutí {worker}-{index}",
                    )
            index_path = root / "private" / "urgent_reminders" / "index.json"
            start_path = root / "start"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(inbox), str(index_path), str(start_path)],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for inbox in inboxes
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=20) for process in processes]
            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            records = json.loads(index_path.read_text(encoding="utf-8"))["reminders"]

        self.assertEqual(len(records), 40)
        self.assertEqual({item["reminder_number"] for item in records}, set(range(1, 41)))
        self.assertEqual(len({item["source_path"] for item in records}), 40)

    def test_concurrent_sync_does_not_overwrite_done_status(self) -> None:
        script = """
import sys
import time
from pathlib import Path
import app.urgent_reminders as urgent

inbox = Path(sys.argv[1])
index_path = Path(sys.argv[2])
paused_path = Path(sys.argv[3])
release_path = Path(sys.argv[4])
original_read_text = urgent._read_text

def paused_read_text(path):
    if not paused_path.exists():
        paused_path.write_text("paused\\n", encoding="utf-8")
        while not release_path.exists():
            time.sleep(0.01)
    return original_read_text(path)

urgent._read_text = paused_read_text
urgent.sync_urgent_reminders_index(inbox_dir=inbox, index_path=index_path)
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            inbox = root / "inbox"
            inbox.mkdir()
            index_path = root / "private" / "urgent_reminders" / "index.json"
            paused_path = root / "paused"
            release_path = root / "release"
            _write_reminder(inbox / "samantha_reminder_a.md", "První připomenutí")
            sync_urgent_reminders_index(inbox_dir=inbox, index_path=index_path)
            _write_reminder(inbox / "samantha_reminder_b.md", "Druhé připomenutí")

            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    script,
                    str(inbox),
                    str(index_path),
                    str(paused_path),
                    str(release_path),
                ],
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            deadline = time.monotonic() + 10
            while not paused_path.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(paused_path.exists(), "Sync proces se nepozastavil v očekávaném bodě.")

            done = mark_urgent_reminder_done(1, index_path=index_path)
            self.assertIsNotNone(done)
            self.assertEqual(done.status, "done")
            release_path.write_text("release\n", encoding="utf-8")
            stdout, stderr = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, stderr or stdout)
            records = json.loads(index_path.read_text(encoding="utf-8"))["reminders"]

        by_number = {item["reminder_number"]: item for item in records}
        self.assertEqual(by_number[1]["status"], "done")
        self.assertEqual(by_number[2]["status"], "open")
        self.assertEqual(len(records), 2)


def _write_reminder(path: Path, text: str) -> None:
    path.write_text(
        "# Důležité připomenutí\n\n"
        "Datum: 2026-07-10 18:00:00\n"
        "Priorita: urgent\n\n"
        "Připomenutí:\n"
        f"{text}.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
