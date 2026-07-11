from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.email.work_repository import pending_email_purge_items, read_email_work_decisions, save_email_work_decision


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class EmailWorkRepositoryTests(unittest.TestCase):
    def test_same_decision_is_semantically_idempotent_without_replace(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "decisions.json"
            first = save_email_work_decision(
                path=path,
                item_id="one",
                action="process",
                item={"uid": "1"},
            )
            with patch("app.work_repository.atomic_replace_text_under_external_lock") as replace:
                second = save_email_work_decision(
                    path=path,
                    item_id="one",
                    action="process",
                    item={"uid": "1"},
                )

            self.assertTrue(first.changed)
            self.assertFalse(second.changed)
            replace.assert_not_called()

    def test_adapter_preserves_unknown_top_level_fields(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "decisions.json"
            path.write_text('{"decisions": {}, "legacy": {"keep": true}}\n', encoding="utf-8")

            save_email_work_decision(path=path, item_id="one", action="ignore", item={"uid": "1"})

            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(document["legacy"], {"keep": True})
            self.assertEqual(read_email_work_decisions(path)["one"]["action"], "ignore")

    def test_same_operation_id_replays_original_result_without_new_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "decisions.json"
            first = save_email_work_decision(
                path=path,
                item_id="one",
                action="process",
                item={"uid": "1"},
                operation_id="request-one",
            )
            second = save_email_work_decision(
                path=path,
                item_id="one",
                action="trash_requested",
                item={"uid": "1"},
                operation_id="request-one",
            )

            self.assertTrue(first.changed)
            self.assertTrue(second.idempotent_replay)
            self.assertEqual(second.result, {"item_id": "one", "action": "process"})
            self.assertEqual(read_email_work_decisions(path)["one"]["action"], "process")

    def test_two_processes_save_different_decisions_without_lost_update(self) -> None:
        script = """
import sys
from pathlib import Path
from app.email.work_repository import save_email_work_decision

save_email_work_decision(
    path=Path(sys.argv[1]),
    item_id=sys.argv[2],
    action="process",
    item={"uid": sys.argv[2]},
)
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "decisions.json"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path), item_id],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for item_id in ("one", "two")
            ]
            outputs = [process.communicate(timeout=20) for process in processes]

            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(set(read_email_work_decisions(path)), {"one", "two"})

    def test_pending_purge_recovery_uses_only_durable_identity_and_removes_purged(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "actions.jsonl"
            rows = [
                {
                    "action": "process_email_work_queue_batch",
                    "items": [
                        {
                            "item_id": "recoverable",
                            "provider": "iCloud",
                            "folder": "INBOX",
                            "uid": "10",
                            "trash_folder": "Deleted Messages",
                            "trash_uid": "110",
                            "message_id": "<recoverable@example.test>",
                            "status": "trashed",
                            "subject": "must not be recovered",
                        },
                        {
                            "item_id": "legacy-missing-identity",
                            "provider": "iCloud",
                            "status": "trashed",
                        },
                    ],
                },
                {
                    "action": "process_email_work_queue_batch",
                    "items": [
                        {
                            "item_id": "already-purged",
                            "provider": "Seznam",
                            "trash_folder": "Trash",
                            "trash_uid": "210",
                            "status": "trashed",
                        }
                    ],
                },
                {
                    "action": "purge_email_work_queue_trash_batch",
                    "items": [{"item_id": "already-purged", "status": "purged"}],
                },
            ]
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            result = pending_email_purge_items(path)

            self.assertEqual(result["count"], 1)
            self.assertEqual(result["unrecoverable_count"], 1)
            self.assertEqual(result["items"][0]["item_id"], "recoverable")
            self.assertNotIn("subject", result["items"][0])


if __name__ == "__main__":
    unittest.main()
