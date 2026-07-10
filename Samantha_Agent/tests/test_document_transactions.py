from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from app.cockpit import set_document_reading_status_action, update_document_classification_metadata_action
from app.documents import transactions as document_transactions
from app.documents.transactions import DOCUMENT_TRANSACTION_MARKER
from app.documents.vault import read_jsonl, write_json, write_jsonl


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SimulatedCrash(BaseException):
    pass


class DocumentTransactionTests(unittest.TestCase):
    def test_unchanged_metadata_creates_no_backup_audit_or_marker(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = _create_vault(Path(temp_dir), ("doc-a",))

            result = update_document_classification_metadata_action(
                "doc-a",
                {"domain": "other"},
                vault_dir=vault,
            )

            self.assertTrue(result["ok"])
            self.assertIn("nezměnila", result["message"])
            self.assertFalse((vault / "index" / "metadata_backups").exists())
            self.assertFalse((vault / "index" / "document_metadata_actions.jsonl").exists())
            self.assertFalse((vault / "index" / DOCUMENT_TRANSACTION_MARKER).exists())

    def test_two_processes_update_different_documents_without_lost_change(self) -> None:
        script = """
import json
import sys
import time
from pathlib import Path
from app.cockpit import update_document_classification_metadata_action

vault = Path(sys.argv[1])
start_path = Path(sys.argv[2])
document_id = sys.argv[3]
domain = sys.argv[4]
while not start_path.exists():
    time.sleep(0.01)
result = update_document_classification_metadata_action(
    document_id=document_id,
    metadata={"domain": domain},
    vault_dir=vault,
)
print(json.dumps({"ok": result.get("ok"), "message": result.get("message", "")}, ensure_ascii=False))
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = _create_vault(Path(temp_dir), ("doc-a", "doc-b"))
            start_path = Path(temp_dir) / "start"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(vault), str(start_path), document_id, domain],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for document_id, domain in (("doc-a", "insurance"), ("doc-b", "energy"))
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=30) for process in processes]
            for process, (stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
                self.assertTrue(json.loads(stdout)["ok"], stdout)

            records = {row["document_id"]: row for row in _read_index(vault)}
            manifests = {document_id: _read_manifest(vault, document_id) for document_id in records}
            audits = read_jsonl(vault / "index" / "document_metadata_actions.jsonl")

        self.assertEqual(records["doc-a"]["domain"], "insurance")
        self.assertEqual(records["doc-b"]["domain"], "energy")
        self.assertEqual(manifests["doc-a"]["domain"], "insurance")
        self.assertEqual(manifests["doc-b"]["domain"], "energy")
        self.assertEqual(len(audits), 2)
        self.assertEqual({row["document_id"] for row in audits}, {"doc-a", "doc-b"})
        self.assertEqual(len({row["transaction_id"] for row in audits}), 2)

    def test_concurrent_metadata_and_reading_status_preserve_both_changes(self) -> None:
        metadata_script = """
import json
import sys
import time
from pathlib import Path
from app.cockpit import update_document_classification_metadata_action
vault = Path(sys.argv[1]); start = Path(sys.argv[2])
while not start.exists(): time.sleep(0.01)
print(json.dumps(update_document_classification_metadata_action("doc-a", {"domain": "insurance"}, vault_dir=vault), ensure_ascii=False))
"""
        reading_script = """
import json
import sys
import time
from pathlib import Path
from app.cockpit import set_document_reading_status_action
vault = Path(sys.argv[1]); start = Path(sys.argv[2])
while not start.exists(): time.sleep(0.01)
print(json.dumps(set_document_reading_status_action("doc-a", "unreadable", "OCR později", vault_dir=vault), ensure_ascii=False))
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = _create_vault(Path(temp_dir), ("doc-a",))
            start_path = Path(temp_dir) / "start"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(vault), str(start_path)],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for script in (metadata_script, reading_script)
            ]
            start_path.write_text("start\n", encoding="utf-8")
            outputs = [process.communicate(timeout=30) for process in processes]
            for process, (stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
                self.assertTrue(json.loads(stdout)["ok"], stdout)

            record = _read_index(vault)[0]
            manifest = _read_manifest(vault, "doc-a")

        self.assertEqual(record["domain"], "insurance")
        self.assertEqual(record["reading_status"], "unreadable")
        self.assertEqual(manifest["domain"], "insurance")
        self.assertEqual(manifest["reading_status"], "unreadable")

    def test_manifest_failure_rolls_back_index_and_manifest_without_audit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = _create_vault(Path(temp_dir), ("doc-a",))
            index_path = vault / "index" / "documents_index.jsonl"
            manifest_path = _manifest_path(vault, "doc-a")
            original_index = index_path.read_bytes()
            original_manifest = manifest_path.read_bytes()

            with patch("app.documents.transactions._write_manifest", side_effect=OSError("manifest failed")):
                result = update_document_classification_metadata_action(
                    "doc-a",
                    {"domain": "insurance"},
                    vault_dir=vault,
                )

            self.assertFalse(result["ok"])
            self.assertEqual(index_path.read_bytes(), original_index)
            self.assertEqual(manifest_path.read_bytes(), original_manifest)
            self.assertFalse((vault / "index" / DOCUMENT_TRANSACTION_MARKER).exists())
            self.assertFalse((vault / "index" / "document_metadata_actions.jsonl").exists())

    def test_next_transaction_recovers_crash_after_index_before_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = _create_vault(Path(temp_dir), ("doc-a",))
            marker_path = vault / "index" / DOCUMENT_TRANSACTION_MARKER

            with patch("app.documents.transactions._write_manifest", side_effect=SimulatedCrash("crash")):
                with self.assertRaises(SimulatedCrash):
                    update_document_classification_metadata_action(
                        "doc-a",
                        {"domain": "insurance"},
                        vault_dir=vault,
                    )
            self.assertTrue(marker_path.exists())
            self.assertEqual(_read_index(vault)[0]["domain"], "insurance")
            self.assertEqual(_read_manifest(vault, "doc-a")["domain"], "other")

            result = set_document_reading_status_action("doc-a", "unreadable", vault_dir=vault)
            record = _read_index(vault)[0]
            manifest = _read_manifest(vault, "doc-a")

            self.assertTrue(result["ok"])
            self.assertEqual(record["domain"], "other")
            self.assertEqual(manifest["domain"], "other")
            self.assertEqual(record["reading_status"], "unreadable")
            self.assertEqual(manifest["reading_status"], "unreadable")
            self.assertFalse(marker_path.exists())

    def test_audited_transaction_is_kept_after_crash_before_committed_marker(self) -> None:
        original_set_phase = document_transactions._set_marker_phase

        def crash_on_committed(path, marker, phase):
            if phase == "committed":
                raise SimulatedCrash("crash after audit")
            return original_set_phase(path, marker, phase)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            vault = _create_vault(Path(temp_dir), ("doc-a",))
            marker_path = vault / "index" / DOCUMENT_TRANSACTION_MARKER
            with patch("app.documents.transactions._set_marker_phase", side_effect=crash_on_committed):
                with self.assertRaises(SimulatedCrash):
                    update_document_classification_metadata_action(
                        "doc-a",
                        {"domain": "insurance"},
                        vault_dir=vault,
                    )
            self.assertTrue(marker_path.exists())
            self.assertEqual(len(read_jsonl(vault / "index" / "document_metadata_actions.jsonl")), 1)

            result = set_document_reading_status_action("doc-a", "unreadable", vault_dir=vault)
            record = _read_index(vault)[0]
            manifest = _read_manifest(vault, "doc-a")

            self.assertTrue(result["ok"])
            self.assertEqual(record["domain"], "insurance")
            self.assertEqual(manifest["domain"], "insurance")
            self.assertEqual(record["reading_status"], "unreadable")
            self.assertFalse(marker_path.exists())


def _create_vault(root: Path, document_ids: tuple[str, ...]) -> Path:
    vault = root / "documents"
    index_dir = vault / "index"
    index_dir.mkdir(parents=True)
    records = []
    for document_id in document_ids:
        document_dir = vault / "vault" / "tax" / document_id
        document_dir.mkdir(parents=True)
        source = document_dir / f"{document_id}.pdf"
        source.write_bytes(b"%PDF-1.4\n")
        record = {
            "document_id": document_id,
            "title": f"Test {document_id}",
            "domain": "other",
            "document_type": "contract",
            "counterparty": "",
            "related_asset": "",
            "stored_path": str(source),
        }
        records.append(record)
        write_json(document_dir / "manifest.json", record)
    write_jsonl(index_dir / "documents_index.jsonl", records)
    return vault


def _read_index(vault: Path) -> list[dict[str, object]]:
    return read_jsonl(vault / "index" / "documents_index.jsonl")


def _manifest_path(vault: Path, document_id: str) -> Path:
    return vault / "vault" / "tax" / document_id / "manifest.json"


def _read_manifest(vault: Path, document_id: str) -> dict[str, object]:
    return json.loads(_manifest_path(vault, document_id).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
