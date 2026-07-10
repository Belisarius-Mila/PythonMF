from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.documents.vault import append_jsonl, read_jsonl, write_json, write_jsonl
from app.file_persistence import lock_path_for


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DocumentPersistenceTests(unittest.TestCase):
    def test_two_processes_append_document_events_without_mixed_rows(self) -> None:
        script = """
import sys
import time
from pathlib import Path
from app.documents.vault import append_jsonl

path = Path(sys.argv[1])
start_path = Path(sys.argv[2])
worker = sys.argv[3]
while not start_path.exists():
    time.sleep(0.01)
for index in range(30):
    append_jsonl(path, {"worker": worker, "index": index})
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            path = root / "index" / "document_actions.jsonl"
            start_path = root / "start"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path), str(start_path), worker],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for worker in ("a", "b")
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=20) for process in processes]
            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            rows = read_jsonl(path)
            lock_exists = lock_path_for(path).exists()

        self.assertEqual(len(rows), 60)
        self.assertEqual(
            {(row["worker"], row["index"]) for row in rows},
            {(worker, index) for worker in ("a", "b") for index in range(30)},
        )
        self.assertTrue(lock_exists)

    def test_whole_jsonl_replace_failure_preserves_previous_registry(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "documents_index.jsonl"
            original_rows = [{"document_id": "doc-a", "status": "open"}]
            write_jsonl(path, original_rows)
            original = path.read_bytes()

            with patch("app.file_persistence.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    write_jsonl(path, [{"document_id": "doc-a", "status": "done"}])

            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(read_jsonl(path), original_rows)
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])
            self.assertTrue(lock_path_for(path).exists())

    def test_manifest_replace_failure_preserves_previous_json(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            original_payload = {"document_id": "doc-a", "reading_status": "open"}
            write_json(path, original_payload)
            original = path.read_bytes()

            with patch("app.file_persistence.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    write_json(path, {"document_id": "doc-a", "reading_status": "done"})

            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), original_payload)
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])
            self.assertTrue(lock_path_for(path).exists())


if __name__ == "__main__":
    unittest.main()
