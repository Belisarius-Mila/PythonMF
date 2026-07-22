from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.file_persistence import (
    append_jsonl_locked,
    atomic_create_text,
    atomic_write_json,
    lock_path_for,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FilePersistenceTests(unittest.TestCase):
    def test_atomic_create_text_refuses_to_replace_existing_target(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "private.json"

            atomic_create_text(path, '{"first": true}\n')
            with self.assertRaisesRegex(RuntimeError, "already exists"):
                atomic_create_text(path, '{"second": true}\n')

            self.assertEqual(path.read_text(encoding="utf-8"), '{"first": true}\n')
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_two_processes_atomic_create_exactly_one_complete_target(self) -> None:
        script = """
import sys
from pathlib import Path
from app.file_persistence import FilePersistenceError, atomic_create_text

try:
    atomic_create_text(Path(sys.argv[1]), sys.argv[2])
except FilePersistenceError:
    print("existing")
else:
    print("created")
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "create-once.txt"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path), payload],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for payload in ("complete-a", "complete-b")
            ]
            outputs = [process.communicate(timeout=20) for process in processes]

            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(
                sorted(stdout.strip() for stdout, _stderr in outputs),
                ["created", "existing"],
            )
            self.assertIn(path.read_text(encoding="utf-8"), {"complete-a", "complete-b"})
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_atomic_json_write_replaces_complete_file_and_keeps_stable_lock(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "state.json"
            path.write_text('{"old": true}\n', encoding="utf-8")

            atomic_write_json(path, {"message": "Příliš žluťoučký", "ok": True}, sort_keys=True)

            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"message": "Příliš žluťoučký", "ok": True},
            )
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))
            self.assertTrue(lock_path_for(path).exists())
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_failed_replace_preserves_original_and_removes_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "state.json"
            path.write_text('{"safe": "original"}\n', encoding="utf-8")

            with patch("app.file_persistence.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    atomic_write_json(path, {"safe": "new"})

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"safe": "original"})
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_two_processes_update_json_without_lost_writes(self) -> None:
        script = """
import sys
from pathlib import Path
from app.file_persistence import update_json_file

path = Path(sys.argv[1])
iterations = int(sys.argv[2])
for _ in range(iterations):
    def increment(data):
        data["count"] = int(data.get("count", 0)) + 1
        return data
    update_json_file(path, increment, default={"count": 0}, sort_keys=True)
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "counter.json"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path), "30"],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for _ in range(2)
            ]
            outputs = [process.communicate(timeout=20) for process in processes]

            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"count": 60})

    def test_two_processes_append_complete_jsonl_records(self) -> None:
        script = """
import sys
from pathlib import Path
from app.file_persistence import append_jsonl_locked

path = Path(sys.argv[1])
worker = sys.argv[2]
iterations = int(sys.argv[3])
for index in range(iterations):
    append_jsonl_locked(path, {"worker": worker, "index": index}, sort_keys=True)
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path), worker, "30"],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for worker in ("a", "b")
            ]
            outputs = [process.communicate(timeout=20) for process in processes]

            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 60)
            self.assertEqual(
                {(item["worker"], item["index"]) for item in records},
                {(worker, index) for worker in ("a", "b") for index in range(30)},
            )

    def test_single_jsonl_append_remains_one_valid_line(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "events.jsonl"

            append_jsonl_locked(path, {"event": "safe", "ok": True}, sort_keys=True)

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0]), {"event": "safe", "ok": True})


if __name__ == "__main__":
    unittest.main()
